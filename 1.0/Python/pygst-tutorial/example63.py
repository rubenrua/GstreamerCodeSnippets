#!/usr/bin/env python

import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst

class GTK_Main:
    
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Video-Player")
        window.set_default_size(500, 400)
        window.connect("destroy", gtk.main_quit, "WM destroy")
        vbox = gtk.VBox()
        window.add(vbox)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)
        self.entry = gtk.Entry()
        hbox.add(self.entry)
        self.button = gtk.Button("Start")
        hbox.pack_start(self.button, False)
        self.button.connect("clicked", self.start_stop)
        self.movie_window = gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()
        
        self.player = gst.element_factory_make("playbin", "player")
        self.bin = gst.Bin("my-bin")
        videoscale = gst.element_factory_make("videoscale")
        videoscale.set_property("method", 1)
        pad = videoscale.get_pad("sink")
        ghostpad = gst.GhostPad("sink", pad)
        self.bin.add_pad(ghostpad)
        caps = gst.Caps("video/x-raw-yuv, width=720")
        filter = gst.element_factory_make("capsfilter", "filter")
        filter.set_property("caps", caps)
        textoverlay = gst.element_factory_make('textoverlay')
        textoverlay.set_property("text", "GNUTV")
        textoverlay.set_property("font-desc", "normal 14")
        textoverlay.set_property("halign", "right")
        textoverlay.set_property("valign", "top")
        conv = gst.element_factory_make ("ffmpegcolorspace", "conv")
        videosink = gst.element_factory_make("autovideosink")
        
        self.bin.add(videoscale, filter, textoverlay, conv, videosink)
        gst.element_link_many(videoscale, filter, textoverlay, conv, videosink)
        self.player.set_property("video-sink", self.bin)
        
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text()
            if os.path.exists(filepath):
                self.button.set_label("Stop")
                self.player.set_property("uri", "file://" + filepath)
                self.player.set_state(gst.STATE_PLAYING)
            else:
                self.player.set_state(gst.STATE_NULL)
                self.button.set_label("Start")

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
    
    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid)
    
GTK_Main()
gtk.gdk.threads_init()
gtk.main()
