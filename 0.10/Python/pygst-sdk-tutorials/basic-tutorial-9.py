#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-9
#
"""
basic-tutorial-9: Media information gathering
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+9%3A+Media+information+gathering
"""

import sys
import gobject
import gst
import gst.pbutils

# Python version of GST_TIME_ARGS
def convert_ns(t):
    s,ns = divmod(t, 1000000000)
    m,s = divmod(s, 60)

    if m < 60:
        return "0:%02i:%02i.%i" %(m,s,ns)
    else:
        h,m = divmod(m, 60)
        return "%i:%02i:%02i.%i" %(h,m,s,ns)

# Print a tag in a human-readable format (name: value) 
def print_tag_foreach(tags, depth):
    for tkey in tags.keys():
        print ("%s%s: %s"% ((2 * depth) * " ", tkey, tags[tkey]))

# Print information regarding a stream 
def print_stream_info(info, depth):
    caps = info.get_caps()
    desc = ""
    if (caps):
        if caps.is_fixed():
            desc = gst.pbutils.get_codec_description(caps)
        else:
            desc = caps.to_string()
  
    print "%s%s: %s"% (2 * depth * " ", info.get_stream_type_nick(), desc)

    tags = info.get_tags()
    if tags:
        print "%sTags:"% (" " * (2 * (depth + 1)))
        print_tag_foreach(tags, depth * 2) # TODO review
    

# Print information regarding a stream and its substreams, if any
def print_topology(info, depth):  
    if not info:
        return;
  
    print_stream_info(info, depth)
  
    next = info.get_next()
  
    if next:
        print_topology (next, depth + 1);
    elif isinstance(info, gst.pbutils.DiscovererContainerInfo):
        streams = info.get_streams()
        for tmp in streams:
            print_topology(tmp, depth + 1)

# This function is called every time the discoverer has information regarding
# one of the URIs we provided.
def on_discovered_cb (discoverer, info, err, data):
    uri = info.get_uri()
    result = info.get_result()

    if result == gst.pbutils.DISCOVERER_URI_INVALID:  
        print "Invalid URI '%s'\n"% uri
    elif result == gst.pbutils.DISCOVERER_ERROR:  
        print "Discoverer error: %s"% err.message
    elif result == gst.pbutils.DISCOVERER_TIMEOUT:
        print "Timeout"
    elif result == gst.pbutils.DISCOVERER_BUSY:
        print "Busy"
    elif result == gst.pbutils.DISCOVERER_MISSING_PLUGINS:
        print "Missing plugins: %s"% info.get_misc().to_string()
    elif result == gst.pbutils.DISCOVERER_OK:
        print "Discovered '%s'"% uri
        # If we got no error, show the retrieved information
        print "\nDuration: %s"% convert_ns(info.get_duration())
  
        tags = info.get_tags();
        if tags:
            print "Tags:"
            print_tag_foreach(tags, 1)

        print "Seekable: %s"% ("yes" if info.get_seekable() else "no")
        print ""
  
        sinfo = info.get_stream_info()
        if sinfo:
            print "Stream information:"
            print_topology(sinfo, 1)
            print ""


# This function is called when the discoverer has finished examining
# all the URIs we provided.
def on_finished_cb(discoverer, data):
    print "Finished discovering"
    data["loop"].quit()


uri = "http://docs.gstreamer.com/media/sintel_trailer-480p.webm"

# if a URI was provided, use it instead of the default one
if len(sys.argv) > 1:
    uri = sys.argv[1]

# Initialize
data = dict()
print "Discovering '%s'"% uri


# Instantiate the Discoverer
data["discoverer"] = gst.pbutils.Discoverer(5 * gst.SECOND)
if not data["discoverer"]:
    print >> sys.stderr, "Error creating discoverer instance."
    exit(-1)

# Connect to the interesting signals
data["discoverer"].connect("discovered", on_discovered_cb, data)
data["discoverer"].connect("finished", on_finished_cb, data)

# Start the discoverer process (nothing to do yet) 
data["discoverer"].start()

# Add a request to process asynchronously the URI passed through the command line
if not data["discoverer"].discover_uri_async(uri):
    print >> sys.stderr, "Failed to start discovering URI '%s'"% uri
    exit(-1)

# Create a GLib Main Loop and set it to run, so we can wait for the signals
data["loop"] = gobject.MainLoop()
data["loop"].run()

# Stop the discoverer process
data["discoverer"].stop()

