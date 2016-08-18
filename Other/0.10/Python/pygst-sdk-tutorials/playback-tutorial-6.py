#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 6: Audio visualization
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+6%3A+Audio+visualization
"""
import sys
import pygst
pygst.require("0.10")
import gst

#playbin2 flags
class GstPlayFlags:
    GST_PLAY_FLAG_VIS = 1 << 3 # Enable rendering of visualizations when there is no video stream.

#Return TRUE if this is a Visualization element
def filter_vis_features(f):
    return (f.get_klass().find("Visualization") >= 0)




selected_factory = None

#Get a list of all visualization plugins
defreg = gst.registry_get_default()
list = [f for f in defreg.get_feature_list(gst.ElementFactory) if filter_vis_features(f)]

#Print their names
for factory in list:
    name = factory.get_longname()
    print ("  " + name)
    if (not selected_factory or name.startswith("GOOM")):
        selected_factory = factory

#Don't use the factory if it's still empty 
#e.g. no visualization plugins found 
if (not selected_factory):
    print >> sys.stderr, "No visualization plugins found!"
    exit(-1)
  
#We have now selected a factory for the visualization element
print ("Selected '{0}'".format(selected_factory.get_longname()))
vis_plugin = selected_factory.create()
if (not vis_plugin):
    exit(-1)

#Build the pipeline
pipeline = gst.parse_launch("playbin2 uri=http://radio.hbr1.com:19800/ambient.ogg")

#Set the visualization flag
flags = pipeline.get_property("flags")
flags |= GstPlayFlags.GST_PLAY_FLAG_VIS
pipeline.set_property("flags", flags)

#Set vis plugin for playbin2
pipeline.set_property("vis-plugin", vis_plugin)

#Start playing
pipeline.set_state(gst.STATE_PLAYING)
bus = pipeline.get_bus() 
msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_ERROR | gst.MESSAGE_EOS)

#Free resources
pipeline.set_state(gst.STATE_NULL)

