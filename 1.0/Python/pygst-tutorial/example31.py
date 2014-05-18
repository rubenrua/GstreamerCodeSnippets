#!/usr/bin/env python

import sys, os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk

class GTK_Main(object):
    
    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("MP3-Player")
        window.set_default_size(400, 200)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, True, 0)
        self.button = Gtk.Button("Start")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()
        
        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        decoder = Gst.ElementFactory.make("mad", "mp3-decoder")
        conv = Gst.ElementFactory.make("audioconvert", "converter")
        sink = Gst.ElementFactory.make("alsasink", "alsa-output")
        
        self.player.add(source)
        self.player.add(decoder)
        self.player.add(conv)
        self.player.add(sink)
        source.link(decoder)
        decoder.link(conv)
        conv.link(sink)
        
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
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

Gst.init(None)
GTK_Main()
GObject.threads_init()
Gtk.main()
