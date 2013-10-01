#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 4: Progressive streaming
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+4%3A+Progressive+streaming
"""
import sys
from array import array
import gobject
gobject.threads_init()
import pygst
pygst.require("0.10")
import gst

GRAPH_LENGTH = 80

class GstPlayFlags:
    GST_PLAY_FLAG_DOWNLOAD = 1 << 7 # Enable progressive download (on selected formats)

class CustomData:
    is_live = False
    pipeline = None
    loop = None
    buffering_level = 0

def got_location(playbin, prop_object, prop):
    location = prop_object.props.temp_location
    print (">>>> Temporary file: {0}".format(location))
    #Uncomment this line to keep the temporary file after the program exits
    #prop_object.set_property("temp-remove", False)

def cb_message(bus, msg, data):
    if (msg.type == gst.MESSAGE_ERROR):
        err, debug = msg.parse_error()
        print ("Error: {0}".format(err.message))
        data.pipeline.set_state(gst.STATE_READY)
        data.loop.quit()
    elif (msg.type == gst.MESSAGE_EOS):
        #end-of-stream
        pipeline.set_state(gst.STATE_READY)
        data.loop.quit()
    elif (msg.type == gst.MESSAGE_BUFFERING):
        #If the stream is live, we do not care about buffering.
        if (data.is_live):
            return

        #Wait until buffering is complete before start/resume playing
        data.buffering_level = msg.parse_buffering()
        if (data.buffering_level < 100):
            data.pipeline.set_state(gst.STATE_PAUSED)
        else:
            data.pipeline.set_state(gst.STATE_PLAYING)
    elif (msg.type == gst.MESSAGE_CLOCK_LOST):
        #Get a new clock
        data.pipeline.set_state(gst.STATE_PAUSED)
        data.pipeline.set_state(gst.STATE_PLAYING)
    else:
        #Unhandled message
        pass

def refresh_ui(data):
    query = gst.query_new_buffering(gst.FORMAT_PERCENT)
    result = pipeline.query(query)
    if (result):
        graph = array('c', ' ' * GRAPH_LENGTH)
        format = gst.FORMAT_TIME
        position = 0
        duration = 0
        n_ranges = query.get_n_buffering_ranges()
        fmt, start, stop, total = query.parse_buffering_range()  # no parse_nth_buffering_range method ?!
        start = start / 10000
        stop = stop / 10000
        start = start * GRAPH_LENGTH / 100
        stop = stop * GRAPH_LENGTH / 100

        i = 0
        for i in xrange(start, stop):
            graph[i] = '-'

        try:
            position = data.pipeline.query_position(format)[0]
            if (position != gst.CLOCK_TIME_NONE):
                duration = data.pipeline.query_duration(format)[0]
                if (duration != gst.CLOCK_TIME_NONE):
                    i = (int)(GRAPH_LENGTH * float(position) / float(duration + 1))
        except:
            pass

        graph[i] = 'X' if (data.buffering_level < 100) else '>'
        sys.stdout.write("\r[{0}]".format(graph.tostring()))
        if (data.buffering_level < 100):
            sys.stdout.write(" Buffering {0}%".format(data.buffering_level))
        else:
            sys.stdout.write("                ")
        sys.stdout.write("\r")

    return True

#Initialize our data structure
data = CustomData()

#Build the pipeline
pipeline = gst.parse_launch("playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm")
bus = pipeline.get_bus()

#Set the download flag
flags = pipeline.get_property("flags")
flags |= GstPlayFlags.GST_PLAY_FLAG_DOWNLOAD
pipeline.set_property("flags", flags)

#Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, "Unable to set pipeline to playing state"
    exit(-1)
elif (ret == gst.STATE_CHANGE_NO_PREROLL):
    data.is_live = True

main_loop = gobject.MainLoop(None, False)
data.loop = main_loop
data.pipeline = pipeline

bus.add_signal_watch()
bus.connect("message", cb_message, data)
pipeline.connect("deep-notify::temp-location", got_location)

#Register a function that GLib will call every second
gobject.timeout_add_seconds(1, refresh_ui, data)
main_loop.run()

#Free resources
pipeline.set_state(gst.STATE_NULL)
print ""


