#!/usr/bin/env python

import os
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, Gtk, Gdk

# Needed for window.get_xid(), xvimagesink.set_window_handle(), respectively:
from gi.repository import GdkX11, GstVideo

class GTK_Main:

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
        png_decoder = Gst.ElementFactory.make("pngdec", "png-decoder") #avdec_png
        png_source = Gst.ElementFactory.make("filesrc", "png-source")
        png_source.set_property("location", os.path.realpath("tvlogo.png"))
        mixer = Gst.ElementFactory.make("videomixer", "mixer")
        self.audio_decoder = Gst.ElementFactory.make("avdec_aac", "audio-decoder")
        audioconv = Gst.ElementFactory.make("audioconvert", "converter")
        audiosink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        videosink = Gst.ElementFactory.make("autovideosink", "video-output")
        self.queuea = Gst.ElementFactory.make("queue", "queuea")
        self.queuev = Gst.ElementFactory.make("queue", "queuev")
        ffmpeg1 = Gst.ElementFactory.make("videoconvert", "ffmpeg1")
        ffmpeg2 = Gst.ElementFactory.make("videoconvert", "ffmpeg2")
        ffmpeg3 = Gst.ElementFactory.make("videoconvert", "ffmpeg3")
        videobox = Gst.ElementFactory.make("videobox", "videobox")
        alphacolor = Gst.ElementFactory.make("alphacolor", "alphacolor")

        for element in (source, demuxer, self.video_decoder, png_decoder, png_source, mixer,
                self.audio_decoder, audioconv, audiosink, videosink, self.queuea,
                self.queuev, ffmpeg1, ffmpeg2, ffmpeg3, videobox, alphacolor):
            self.player.add(element)

        source.link(demuxer)

        self.queuev.link(self.video_decoder)
        self.video_decoder.link(ffmpeg1)
        ffmpeg1.link(mixer)
        mixer.link(ffmpeg2)
        ffmpeg2.link(videosink)

        png_source.link(png_decoder)

        png_decoder.link(ffmpeg3)
        #png_decoder.link(alphacolor)
        #alphacolor.link(ffmpeg3)

        ffmpeg3.link(videobox)
        videobox.link(mixer)

        self.queuea.link(self.audio_decoder)
        self.audio_decoder.link(audioconv)
        audioconv.link(audiosink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

        videobox.set_property("border-alpha", 0)
        videobox.set_property("alpha", 0.5)
        videobox.set_property("left", -10)
        videobox.set_property("top", -10)

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
            Gdk.threads_enter()
            imagesink.set_window_handle(self.movie_window.get_property('window').get_xid())
            Gdk.threads_leave()

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
