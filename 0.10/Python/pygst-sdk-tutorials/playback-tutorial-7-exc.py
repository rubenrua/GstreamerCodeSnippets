#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 7: Custom playbin2 sinks -- Exercise
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+7%3A+Custom+playbin2+sinks
"""
import sys, os
os.environ["GST_DEBUG"] = "2"
import pygst
pygst.require("0.10")
import gst

#Build the pipeline
pipeline = gst.parse_launch("playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm") 

#effect = gst.element_factory_make("solarize", "effect")
effect = gst.element_factory_make("agingtv", "effect")
videoconvert = gst.element_factory_make("ffmpegcolorspace", "videoconvert")
videosink = gst.element_factory_make("autovideosink", "videosink")

if (not effect or not videoconvert or not videosink):
    print >> sys.stderr, "Not all elements could be created"
    exit(-1)

bin = gst.Bin("video_sink_bin")
bin.add_many(effect, videoconvert, videosink)
gst.element_link_many(effect, videoconvert, videosink)
pad = effect.get_static_pad("sink")
ghost_pad = gst.GhostPad("sink", pad)
ghost_pad.set_active(True)
bin.add_pad(ghost_pad)

effect.set_property("scratch-lines", 19)

pipeline.set_property("video-sink", bin)

#Start playing
pipeline.set_state(gst.STATE_PLAYING)

#Wait until error or EOS
bus = pipeline.get_bus()
bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)

#Free resources
pipeline.set_state(gst.STATE_NULL)
