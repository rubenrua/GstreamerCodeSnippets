#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 3: Dynamic pipelines -- exercise
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+3%3A+Dynamic+pipelines
"""
import sys
import pygst
pygst.require("0.10")
import gst

class CustomData:
    def __init__(self):
        self.pipeline = None
        self.source = None
        self.convert = None
        self.sink = None
        self.videoconvert = None
        self.videosink = None

def pad_added_handler(src, new_pad, data):
    print "Received new pad '{0.props.name}' from '{1.props.name}'".format(new_pad, src)

    sink_pad = None
    new_pad_type = new_pad.get_caps()[0].get_name()

    if new_pad_type.startswith("audio/x-raw"):
        sink_pad = gst.Element.get_static_pad(data.convert, "sink")
    elif new_pad_type.startswith("video/x-raw"):
        sink_pad = gst.Element.get_static_pad(data.videoconvert, "sink")
    else:
        print >> sys.stderr, "Invalid type. Ignoring"
        return 

    if (sink_pad.is_linked()):
        print "We are already linked. Ignoring"
        return

    #Attempt the link
    ret = None
    try:
        ret = new_pad.link(sink_pad)
    except gst.LinkError, e:
        print >> sys.stderr , "Link Err " + str(e.message.value_name)
    except BaseException, e:
        print >> sys.stderr , "Link Err " + str(e.message)

data = CustomData()

#Create the elements
data.source = gst.element_factory_make("uridecodebin", "source")
data.convert = gst.element_factory_make("audioconvert", "convert")
data.sink = gst.element_factory_make("autoaudiosink", "sink")
data.videosink = gst.element_factory_make("autovideosink", "videosink")
data.videoconvert = gst.element_factory_make("ffmpegcolorspace", "videoconvert")

#Create the empty pipeline
data.pipeline = gst.Pipeline("test-pipeline")

if (not data.pipeline or not data.source or not data.convert or not data.sink 
    or not data.videosink or not data.videoconvert):
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

#Build the pipeline. Note that we are NOT linking the source at this point. We will do it later.
gst.Bin.add_many(data.pipeline, data.source, data.convert, data.sink, data.videoconvert, data.videosink) 
#Link audio elements
if (not gst.element_link_many(data.convert, data.sink)):
    print >> sys.stderr, "Elements could not be linked"
    exit(-1)
#Link video elements
if (not gst.element_link_many(data.videoconvert, data.videosink)):
    print >> sys.stderr, "Elements could not be linked"
    exit(-1)

#Set the URI to play
data.source.set_property("uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Connect to the pad-added signal
data.source.connect("pad-added", pad_added_handler, data)

#Start playing
ret = data.pipeline.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

# Listen to the bus
bus = data.pipeline.get_bus()
while True:
    msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, 
                                    gst.MESSAGE_STATE_CHANGED | gst.MESSAGE_ERROR | gst.MESSAGE_EOS)
    if (msg.type == gst.MESSAGE_ERROR):
        err, debug = msg.parse_error()
        print >> sys.stderr, "Error received from element {0}: {1}\n".format(msg.src, err)
        print >> sys.stderr, "Debugging information {0}".format(debug)
    elif (msg.type == gst.MESSAGE_EOS):
        print "End-Of-Stream reached."
        break
    elif (msg.type == gst.MESSAGE_STATE_CHANGED):
        # We are only interested in state-changed messages from the pipeline
        if ( isinstance(msg.src, gst.Pipeline) ):
            old_state, new_state, pending_state = msg.parse_state_changed()
                
            print "Pipeline state changed from {0} to {1}".format(
                gst.element_state_get_name(old_state), gst.element_state_get_name(new_state))
    else:
        print >> sys.stderr, "Unexpected message received"

pipeline.set_state(gst.STATE_NULL)
