#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-1
#
"""
basic-tutorial-1: Hello world!
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+2%3A+GStreamer+concepts
"""

from gi.repository import Gst
Gst.init(None)

# Build the pipeline
pipeline = Gst.parse_launch(
    "playbin uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Start playing
pipeline.set_state(Gst.State.PLAYING)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Free resources
pipeline.set_state(Gst.State.NULL)
