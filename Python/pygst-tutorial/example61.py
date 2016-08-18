#!/usr/bin/env python

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, Gtk

class GTK_Main:

    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Videotestsrc-Player")
        window.set_default_size(300, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.button = Gtk.Button("Start")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()
        
        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("videotestsrc", "video-source")
        sink = Gst.ElementFactory.make("xvimagesink", "video-output")
        caps = Gst.Caps.from_string("video/x-raw, width=320, height=230")
        filter = Gst.ElementFactory.make("capsfilter", "filter")
        filter.set_property("caps", caps)
        for ele in [source, filter, sink]:
            self.player.add(ele)
        source.link(filter)
        filter.link(sink)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            self.button.set_label("Stop")
            self.player.set_state(Gst.State.PLAYING)
        else:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

GObject.threads_init()
Gst.init(None)
GTK_Main()
Gtk.main()
