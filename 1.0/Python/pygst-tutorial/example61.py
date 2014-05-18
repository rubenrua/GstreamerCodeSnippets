#!/usr/bin/env python

import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst

class GTK_Main:

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Videotestsrc-Player")
        window.set_default_size(300, -1)
        window.connect("destroy", gtk.main_quit, "WM destroy")
        vbox = gtk.VBox()
        window.add(vbox)
        self.button = gtk.Button("Start")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()
        
        self.player = gst.Pipeline("player")
        source = gst.element_factory_make("videotestsrc", "video-source")
        sink = gst.element_factory_make("xvimagesink", "video-output")
        caps = gst.Caps("video/x-raw-yuv, width=320, height=230")
        filter = gst.element_factory_make("capsfilter", "filter")
        filter.set_property("caps", caps)
        
        self.player.add(source, filter, sink)
        gst.element_link_many(source, filter, sink)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            self.button.set_label("Stop")
            self.player.set_state(gst.STATE_PLAYING)
        else:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")

GTK_Main()
gtk.gdk.threads_init()
gtk.main()
