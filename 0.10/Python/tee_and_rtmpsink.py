#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
"""
# Use a queue to rtmpsink not block the pipeline
"""

import sys
import gst

from datetime import datetime
from time import sleep



pipeline_str = """
v4l2src name=src ! video/x-raw-yuv,framerate=24/1,width=640 ! tee name=t num-src-pads=2 !
queue name=q1 ! ffmpegcolorspace ! 
x264enc threads=0 bitrate=400 tune=zerolatency ! flvmux streamable=true ! queue leaky=2 max-size-buffers=0 max-size-bytes=0 max-size-time=500000 name=q ! 
rtmpsink name=sink location="rtmp://fms.uvigo.es/live/directo2" 
t. ! queue name=q2 ! xvimagesink qos=false handle-events=false
"""

# Create the empty pipeline
pipeline = gst.parse_launch(pipeline_str)
src = pipeline.get_by_name("src")
sink = pipeline.get_by_name("sink")
q = pipeline.get_by_name("q")
q1 = pipeline.get_by_name("q1")
q2 = pipeline.get_by_name("q2")


if not pipeline or not src or not sink:
    print "Not all elements could be created."
    exit(-1)

# Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print "Unable to set the pipeline to the playing state."
    exit(-1)

print "Set the pipeline to the playing state."

# Wait until error or EOS
bus = pipeline.get_bus()
bus.add_signal_watch()

while True:
    message = bus.timed_pop_filtered(35 * gst.SECOND, gst.MESSAGE_ANY)
    if not message:
        print "DO IT !!", pipeline.get_clock().get_time()
        print q.get_property("current-level-buffers"), q.get_property("current-level-bytes"), q.get_property("current-level-time")
        #event = gst.event_new_eos()
        #sink.send_event(event)
    elif message.type == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print "Error received from element %s: %s"% (message.src.get_name(), err)
        print "Debugging information: %s"% debug
        break
    elif message.type == gst.MESSAGE_EOS:
        print " - gst.MESSAGE_EOS: End-Of-Stream reached."
        break
    elif message.type == gst.MESSAGE_STATE_CHANGED:
        old_state, new_state, pending_state = message.parse_state_changed()
        print (" - gst.MESSAGE_STATE_CHANGED: %s state changed from %s to %s."% 
               (message.src.get_name(), gst.element_state_get_name(old_state), gst.element_state_get_name (new_state)))
    elif message.type == gst.MESSAGE_ELEMENT:
        print " - gst.MESSAGE_ELEMENT: src %s ."% message.src.get_name()
    else:
        print "Unexpected message (%s) received." % message.type


# Free resources
pipeline.set_state(gst.STATE_NULL)
