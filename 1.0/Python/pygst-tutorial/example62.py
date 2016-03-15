#!/usr/bin/env python

import os
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, Gtk

class GTK_Main:
    
    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Resolutionchecker")
        window.set_default_size(300, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, True, 0)
        self.button = Gtk.Button("Check")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()
        
        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        decoder = Gst.ElementFactory.make("decodebin", "decoder")
        decoder.connect("pad-added", self.decoder_callback)
        self.fakea = Gst.ElementFactory.make("fakesink", "fakea")
        self.fakev = Gst.ElementFactory.make("fakesink", "fakev")
        for ele in [source, decoder, self.fakea, self.fakev]:
            self.player.add(ele)
        source.link(decoder)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        
    def start_stop(self, w):
        filepath = self.entry.get_text()
        if os.path.isfile(filepath):
            self.player.set_state(Gst.State.NULL)
            self.player.get_by_name("file-source").set_property("location", filepath)
            self.player.set_state(Gst.State.PAUSED)
        
    def on_message(self, bus, message):
        typ = message.type
        if typ == Gst.MessageType.STATE_CHANGED:
            if message.parse_state_changed()[1] == Gst.State.PAUSED:
                decoder = self.player.get_by_name("decoder")
                for pad in decoder.srcpads:
#                   caps = pad.query_caps(None)
                    caps = pad.get_current_caps()
                    structure_name = caps.to_string()
                    width = caps.get_structure(0).get_int('width')[1]
                    height = caps.get_structure(0).get_int('height')[1]
                    if structure_name.startswith("video") and len(str(width)) < 6:
                        print "Width:%d, Height:%d" %(width, height)
                        self.player.set_state(Gst.State.NULL)
                        break
            elif typ == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                print "Error: %s" % err, debug
                self.player.set_state(Gst.State.NULL)

    def decoder_callback(self, decoder, pad):
        caps = pad.query_caps(None)
        structure_name = caps.to_string()
        if structure_name.startswith("video"):
            fv_pad = self.fakev.get_static_pad("sink")
            pad.link(fv_pad)
        elif structure_name.startswith("audio"):
            fa_pad = self.fakea.get_static_pad("sink")
            pad.link(fa_pad)

GObject.threads_init()
Gst.init(None)
GTK_Main()
Gtk.main()