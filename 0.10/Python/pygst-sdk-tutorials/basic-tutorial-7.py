#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-7
#
"""
basic-tutorial-7: Multithreading and Pad Availability
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+7%3A+Multithreading+and+Pad+Availability
"""

import sys
import gst

# Create the elements
audio_source = gst.element_factory_make("audiotestsrc", "audio_source")
tee = gst.element_factory_make("tee", "tee")
audio_queue = gst.element_factory_make("queue", "audio_queue")
audio_convert = gst.element_factory_make("audioconvert", "audio_convert")
audio_resample = gst.element_factory_make("audioresample", "audio_resample")
audio_sink = gst.element_factory_make("autoaudiosink", "audio_sink")
video_queue = gst.element_factory_make("queue", "video_queue")
visual = gst.element_factory_make("wavescope", "visual")
video_convert = gst.element_factory_make("ffmpegcolorspace", "csp")
video_sink = gst.element_factory_make("autovideosink", "video_sink")

# Create the empty pipeline
pipeline = gst.Pipeline("test-pipeline")

if (not audio_source or not tee or not audio_queue or not audio_convert or not audio_resample 
    or not audio_sink or not video_queue or not visual or not video_convert or not video_sink or not pipeline):
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)


# Configure elements
audio_source.set_property("freq", 215.0)
visual.set_property("shader", 0)
visual.set_property("style", 1)

# Link all elements that can be automatically linked because they have "Always" pads

pipeline.add(audio_source, tee, audio_queue, audio_convert, audio_resample, audio_sink, video_queue, visual, video_convert, video_sink)
if (not gst.element_link_many(audio_source, tee) or
    not gst.element_link_many(audio_queue, audio_convert, audio_resample, audio_sink) or
    not gst.element_link_many(video_queue, visual, video_convert, video_sink)):
    print >> sys.stderr, "Elements could not be linked."
    exit(-1)

# Manually link the Tee, which has "Request" pads
tee_audio_pad = tee.get_request_pad("src%d")
print "Obtained request pad %s for audio branch."% tee_audio_pad.get_name()
queue_audio_pad = audio_queue.get_static_pad("sink")
tee_video_pad = tee.get_request_pad("src%d")
print "Obtained request pad %s for video branch."% tee_video_pad.get_name()
queue_video_pad = video_queue.get_static_pad("sink")
if (tee_audio_pad.link(queue_audio_pad) != gst.PAD_LINK_OK or
    tee_video_pad.link(queue_video_pad) != gst.PAD_LINK_OK):
    print >> sys.stderr, "Tee could not be linked."
    exit(-1)
  
# Start playing the pipeline
ret = pipeline.set_state(gst.STATE_PLAYING)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)

# Free resources
pipeline.set_state(gst.STATE_NULL)
