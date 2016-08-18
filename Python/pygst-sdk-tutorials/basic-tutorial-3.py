#!/usr/bin/env python3
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
# GObject.threads_init() needed to avoid seg fault
from gi.repository import GObject
GObject.threads_init()
from gi.repository import Gst
Gst.init(None)


data = dict()

# Handler for the pad-added signal


def pad_added_handler(src, new_pad, data):
    print("Received new pad '%s' from '%s':" % (new_pad.get_name(),
          src.get_name()))

    # If our converter is already linked, we have nothing to do here
    if new_pad.is_linked():
        print("We are already linked. Ignoring.")
        return

    # Check the new pad's type
    new_pad_type = new_pad.query_caps(None).to_string()
    
    if not new_pad_type.startswith("audio/x-raw"):
        print("  It has type '%s' which is not raw audio. Ignoring." %
              new_pad_type)
        return

    # Attempt the link
    ret = new_pad.link(data["convert"].get_static_pad("sink"))
    return


# Create the elements
data["source"] = Gst.ElementFactory.make("uridecodebin", "source")
data["convert"] = Gst.ElementFactory.make("audioconvert", "convert")
data["sink"] = Gst.ElementFactory.make("autoaudiosink", "sink")

# Create the empty pipeline
pipeline = Gst.Pipeline.new("test-pipeline")

if not data["source"] or not data["convert"] or not data["sink"] or not pipeline:
    print("Not all elements could be created.", file=sys.stderr)
    exit(-1)

# Build the pipeline
# Note that we are NOT linking the source at this point. We will do it later.
pipeline.add(data["source"])
pipeline.add(data["convert"])
pipeline.add(data["sink"])
if not Gst.Element.link(data["convert"], data["sink"]):
    print("Elements could not be linked.", file=sys.stderr)
    exit(-1)

# Set the URI to play
data["source"].set_property(
    "uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Connect to the pad-added signal
data["source"].connect("pad-added", pad_added_handler, data)

# Start playing
ret = pipeline.set_state(Gst.State.PLAYING)
if ret == Gst.StateChangeReturn.FAILURE:
    print("Unable to set the pipeline to the playing state.", file=sys.stderr)
    exit(-1)

# Wait until error or EOS
bus = pipeline.get_bus()

# Parse message
while True:
    message = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS)
    if message.type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("Error received from element %s: %s" % (
            message.src.get_name(), err), file=sys.stderr)
        print("Debugging information: %s" % debug, file=sys.stderr)
        break
    elif message.type == Gst.MessageType.EOS:
        print("End-Of-Stream reached.")
        break
    elif message.type == Gst.MessageType.STATE_CHANGED:
        if isinstance(message.src, Gst.Pipeline):
            old_state, new_state, pending_state = message.parse_state_changed()
            print("Pipeline state changed from %s to %s." %
                   (old_state.value_nick, new_state.value_nick))
    else:
        print("Unexpected message received.", file=sys.stderr)

# Free resources
pipeline.set_state(Gst.State.NULL)
