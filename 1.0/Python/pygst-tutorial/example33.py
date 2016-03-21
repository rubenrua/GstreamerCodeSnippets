#!/usr/bin/env python

import sys, os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk, Gdk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo

class GTK_Main(object):

    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("MP4-Player")
        window.set_default_size(500, 400)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        self.entry = Gtk.Entry()
        hbox.add(self.entry)
        self.button = Gtk.Button("Start")
        hbox.pack_start(self.button, False, False, 0)
        self.button.connect("clicked", self.start_stop)
        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        demuxer = Gst.ElementFactory.make("qtdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)
        self.video_decoder = Gst.ElementFactory.make("avdec_h264", "video-decoder")
        self.audio_decoder = Gst.ElementFactory.make("avdec_aac", "audio-decoder")
        audioconv = Gst.ElementFactory.make("audioconvert", "converter")
        audiosink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        videosink = Gst.ElementFactory.make("autovideosink", "video-output")
        self.queuea = Gst.ElementFactory.make("queue", "queuea")
        self.queuev = Gst.ElementFactory.make("queue", "queuev")
        colorspace = Gst.ElementFactory.make("videoconvert", "colorspace")

        self.player.add(source)
        self.player.add(demuxer)
        self.player.add(self.video_decoder)
        self.player.add(self.audio_decoder)
        self.player.add(audioconv)
        self.player.add(audiosink)
        self.player.add(videosink)
        self.player.add(self.queuea)
        self.player.add(self.queuev)
        self.player.add(colorspace)

        source.link(demuxer)

        self.queuev.link(self.video_decoder)
        self.video_decoder.link(colorspace)
        colorspace.link(videosink)

        self.queuea.link(self.audio_decoder)
        self.audio_decoder.link(audioconv)
        audioconv.link(audiosink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text()
            if os.path.isfile(filepath):
                self.button.set_label("Stop")
                self.player.get_by_name("file-source").set_property("location", filepath)
                self.player.set_state(Gst.State.PLAYING)
        else:
            self.player.set_state(Gst.State.NULL)
            self.movie_window.override_background_color(0, Gdk.RGBA.from_color(Gdk.color_parse("black")))
            self.button.set_label("Start")

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

    def on_sync_message(self, bus, message):
        if message.get_structure().get_name() == 'prepare-window-handle':
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_window_handle(self.movie_window.get_property('window').get_xid())

    def demuxer_callback(self, demuxer, pad):
        if pad.get_property("template").name_template == "video_%u":
            qv_pad = self.queuev.get_static_pad("sink")
            pad.link(qv_pad)
        elif pad.get_property("template").name_template == "audio_%u":
            qa_pad = self.queuea.get_static_pad("sink")
            pad.link(qa_pad)


Gst.init(None)
GTK_Main()
GObject.threads_init()
Gtk.main()
