#!/usr/bin/env python

import sys, os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk

class GTK_Main(object):
    
    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Vorbis-Player")
        window.set_default_size(500, 200)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, False, 0)
        self.button = Gtk.Button("Start")
        vbox.add(self.button)
        self.button.connect("clicked", self.start_stop)
        window.show_all()
        
        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        demuxer = Gst.ElementFactory.make("oggdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)
        self.audio_decoder = Gst.ElementFactory.make("vorbisdec", "vorbis-decoder")
        audioconv = Gst.ElementFactory.make("audioconvert", "converter")
        audiosink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        
        self.player.add(source)
        self.player.add(demuxer)
        self.player.add(self.audio_decoder)
        self.player.add(audioconv)
        self.player.add(audiosink)

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
            else:
                self.player.set_state(Gst.State.NULL)
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
    
    def demuxer_callback(self, demuxer, pad):
        adec_pad = self.audio_decoder.get_pad("sink")
        pad.link(adec_pad)


GObject.threads_init()
Gst.init(None)        
GTK_Main()
Gtk.main()
