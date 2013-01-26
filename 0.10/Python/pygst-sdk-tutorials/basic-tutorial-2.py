#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-2
#
"""
basic-tutorial-2: GStreamer concepts
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+2%3A+GStreamer+concepts
"""

import sys
import gst

# Create the elements
source = gst.element_factory_make("videotestsrc", "source")
sink = gst.element_factory_make("autovideosink", "sink")

# Create the empty pipeline
pipeline = gst.Pipeline("test-pipeline")

if not source or not sink or not pipeline:
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

# Build the pipeline
pipeline.add(source, sink)
if not gst.element_link_many(source, sink):
    print >> sys.stderr, "Elements could not be linked."
    exit(-1)

# Modify the source's properties 
source.set_property("pattern", 0)

# Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)

# Parse message
if (msg):
    if msg.type == gst.MESSAGE_ERROR:
        err, debug = msg.parse_error()
        print >> sys.stderr, "Error received from element %s: %s"% (msg.src.get_name(), err)
        print >> sys.stderr, "Debugging information: %s"% debug
    elif msg.type == gst.MESSAGE_EOS:
        print "End-Of-Stream reached."
    else:
        print >> sys.stderr, "Unexpected message received."

# Free resources
pipeline.set_state(gst.STATE_NULL)
