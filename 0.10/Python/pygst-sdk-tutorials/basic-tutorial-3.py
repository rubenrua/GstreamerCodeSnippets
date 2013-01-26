#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-3
#
"""
basic-tutorial-3: Dynamic pipelines
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+3%3A+Dynamic+pipelines
"""

import sys
import gst


data = dict()

# Handler for the pad-added signa
def pad_added_handler(src, new_pad, data):
    print "Received new pad '%s' from '%s':"%( new_pad.get_name(), src.get_name())

    # If our converter is already linked, we have nothing to do here
    if new_pad.is_linked():
        print "  We are already linked. Ignoring."
        return

    # Check the new pad's type
    new_pad_type = new_pad.get_caps()[0].get_name()
    if not new_pad_type.startswith("audio/x-raw"):
        print "  It has type '%s' which is not raw audio. Ignoring."% new_pad_type
        return

    # Attempt the link
    ret = new_pad.link(data["convert"].get_pad("sink"))
    return
    

# Create the elements
data["source"] = gst.element_factory_make("uridecodebin", "source")
data["convert"] = gst.element_factory_make("audioconvert", "convert")
data["sink"] = gst.element_factory_make("autoaudiosink", "sink")

# Create the empty pipeline
pipeline = gst.Pipeline("test-pipeline")

if not data["source"] or not data["convert"] or not data["sink"] or not pipeline:
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

# Build the pipeline
# Note that we are NOT linking the source at this point. We will do it later.
pipeline.add(data["source"], data["convert"], data["sink"])
if not gst.element_link_many(data["convert"], data["sink"]):
    print >> sys.stderr, "Elements could not be linked."
    exit(-1)

# Set the URI to play
data["source"].set_property("uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Connect to the pad-added signal
data["source"].connect("pad-added", pad_added_handler, data)

# Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

# Wait until error or EOS
bus = pipeline.get_bus()

# Parse message
while True:
    message = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_STATE_CHANGED | gst.MESSAGE_ERROR | gst.MESSAGE_EOS)
    if message.type == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print >> sys.stderr, "Error received from element %s: %s"% (message.src.get_name(), err)
        print >> sys.stderr, "Debugging information: %s"% debug
        break
    elif message.type == gst.MESSAGE_EOS:
        print "End-Of-Stream reached."
        break
    elif message.type == gst.MESSAGE_STATE_CHANGED:
        if isinstance(message.src, gst.Pipeline):
            old_state, new_state, pending_state = message.parse_state_changed()
            print ("Pipeline state changed from %s to %s."% 
                   (gst.element_state_get_name(old_state), gst.element_state_get_name (new_state)))
    else:
        print >> sys.stderr, "Unexpected message received."

# Free resources
pipeline.set_state(gst.STATE_NULL)
