#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 7: Custom playbin2 sinks
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+7%3A+Custom+playbin2+sinks
"""
import sys
import pygst
pygst.require("0.10")
import gst

#Build the pipeline
pipeline = gst.parse_launch("playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm") 

#Create the elements inside the sink bin
equalizer = gst.element_factory_make("equalizer-3bands", "equalizer")
convert = gst.element_factory_make("audioconvert", "convert")
sink = gst.element_factory_make("autoaudiosink", "audio_sink")
if (not equalizer or not convert or not sink):
    print >> sys.stderr, "Not all elements could be created"
    exit(-1)

#Create the sink bin, add the elements and link them
bin = gst.Bin("audio_sink_bin")
bin.add_many(equalizer, convert, sink)
gst.element_link_many(equalizer, convert, sink)
pad = equalizer.get_static_pad("sink")
ghost_pad = gst.GhostPad("sink", pad)
ghost_pad.set_active(True)
bin.add_pad(ghost_pad)

#COnfigure the equalizer
equalizer.set_property("band1", -24.0)
equalizer.set_property("band2", -24.0)

#Set playbin2's audio sink to be our sink
pipeline.set_property("audio-sink", bin)

#Start playing
pipeline.set_state(gst.STATE_PLAYING)

#Wait until error or EOS
bus = pipeline.get_bus()
bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)

#Free resources
pipeline.set_state(gst.STATE_NULL)




