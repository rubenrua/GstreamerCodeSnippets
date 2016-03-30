#!/usr/bin/env python

import os, thread, time
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, Gtk, Gdk

class GTK_Main(object):

    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Vorbis-Player")
        window.set_default_size(500, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, False, 0)
        hbox = Gtk.HBox()
        vbox.add(hbox)
        buttonbox = Gtk.HButtonBox()
        hbox.pack_start(buttonbox, False, False, 0)
        rewind_button = Gtk.Button("Rewind")
        rewind_button.connect("clicked", self.rewind_callback)
        buttonbox.add(rewind_button)
        self.button = Gtk.Button("Start")
        self.button.connect("clicked", self.start_stop)
        buttonbox.add(self.button)
        forward_button = Gtk.Button("Forward")
        forward_button.connect("clicked", self.forward_callback)
        buttonbox.add(forward_button)
        self.time_label = Gtk.Label()
        self.time_label.set_text("00:00 / 00:00")
        hbox.add(self.time_label)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        demuxer = Gst.ElementFactory.make("oggdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)
        self.audio_decoder = Gst.ElementFactory.make("vorbisdec", "vorbis-decoder")
        audioconv = Gst.ElementFactory.make("audioconvert", "converter")
        audiosink = Gst.ElementFactory.make("autoaudiosink", "audio-output")

        for ele in [source, demuxer, self.audio_decoder, audioconv, audiosink]:
            self.player.add(ele)
        source.link(demuxer)
        self.audio_decoder.link(audioconv)
        audioconv.link(audiosink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text()
            if os.path.isfile(filepath):
                self.button.set_label("Stop")
                self.player.get_by_name("file-source").set_property("location", filepath)
                self.player.set_state(Gst.State.PLAYING)
                self.play_thread_id = thread.start_new_thread(self.play_thread, ())
        else:
            self.play_thread_id = None
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
            self.time_label.set_text("00:00 / 00:00")

    def play_thread(self):
        play_thread_id = self.play_thread_id
        Gdk.threads_enter()
        self.time_label.set_text("00:00 / 00:00")
        Gdk.threads_leave()

        while play_thread_id == self.play_thread_id:
            try:
                time.sleep(0.2)
                dur_int = self.player.query_duration(Gst.Format.TIME)[1]
                print "Total duration: %d ns" % dur_int
                if dur_int == -1:
                    continue
                dur_str = self.convert_ns(dur_int)
                Gdk.threads_enter()
                self.time_label.set_text("00:00 / " + dur_str)
                Gdk.threads_leave()
                break
            except:
                pass

        time.sleep(0.2)
        while play_thread_id == self.play_thread_id:
            pos_int = self.player.query_position(Gst.Format.TIME)[1]
            pos_str = self.convert_ns(pos_int)
            if play_thread_id == self.play_thread_id:
                Gdk.threads_enter()
                self.time_label.set_text(pos_str + " / " + dur_str)
                Gdk.threads_leave()
            time.sleep(1)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.play_thread_id = None
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
            self.time_label.set_text("00:00 / 00:00")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.play_thread_id = None
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
            self.time_label.set_text("00:00 / 00:00")

    def demuxer_callback(self, demuxer, pad):
        adec_pad = self.audio_decoder.get_static_pad("sink")
        pad.link(adec_pad)

    def rewind_callback(self, w):
        rc, pos_int = self.player.query_position(Gst.Format.TIME)
        seek_ns = pos_int - 10 * 1000000000
        if seek_ns < 0:
            seek_ns = 0
        print 'Backward: %d ns -> %d ns' % (pos_int, seek_ns)
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

    def forward_callback(self, w):
        rc, pos_int = self.player.query_position(Gst.Format.TIME)
        seek_ns = pos_int + 10 * 1000000000
        print 'Forward: %d ns -> %d ns' % (pos_int, seek_ns)
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, seek_ns)

    def convert_ns(self, t):
        # This method was submitted by Sam Mason.
        # It's much shorter than the original one.
        s,ns = divmod(t, 1000000000)
        m,s = divmod(s, 60)

        if m < 60:
            return "%02i:%02i" %(m,s)
        else:
            h,m = divmod(m, 60)
            return "%i:%02i:%02i" %(h,m,s)

GObject.threads_init()
Gst.init(None)
GTK_Main()
Gtk.main()
