#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-4
#
"""
basic-tutorial-4: Time management
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+4%3A+Time+management
"""

import sys
import gst

# Python version of GST_TIME_ARGS
def convert_ns(t):
    s,ns = divmod(t, 1000000000)
    m,s = divmod(s, 60)

    if m < 60:
        return "0:%02i:%02i.%i" %(m,s,ns)
    else:
        h,m = divmod(m, 60)
        return "%i:%02i:%02i.%i" %(h,m,s,ns)


def handle_message(data, msg):
    if message.type == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print >> sys.stderr, "Error received from element %s: %s"% (message.src.get_name(), err)
        print >> sys.stderr, "Debugging information: %s"% debug
        data["terminate"] = True
    elif message.type == gst.MESSAGE_EOS:
        print "End-Of-Stream reached."
        data["terminate"] = True
    elif message.type == gst.MESSAGE_DURATION:
        # The duration has changed, mark the current one as invalid
        data["duration"] = gst.CLOCK_TIME_NONE
    elif message.type == gst.MESSAGE_STATE_CHANGED:
        if message.src == data["playbin2"]:
            old_state, new_state, pending_state = message.parse_state_changed()
            print ("Pipeline state changed from %s to %s."% 
                   (gst.element_state_get_name(old_state), gst.element_state_get_name (new_state)))
            data["playing"] = (new_state == gst.STATE_PLAYING)
            if data["playing"]:
                query = gst.query_new_seeking(gst.FORMAT_TIME)
                if data["playbin2"].query(query):
                    (aux, data["seek_enabled"], start, end) = query.parse_seeking()
                    if data["seek_enabled"]:
                        print "Seeking is ENABLED from %s to %s"%(convert_ns(start), convert_ns(end))
                    else:
                        print "Seeking is DISABLED for this stream."
                else:
                    print >> sys.stderr, "Seeking query failed."

                                      
                
            
    else:
        print >> sys.stderr, "Unexpected message received."


data = dict()
    
data["playing"] = False
data["terminate"] = False
data["seek_enabled"] = False
data["seek_done"] = False
data["duration"] = gst.CLOCK_TIME_NONE

# Create the elements
data["playbin2"] = gst.element_factory_make("playbin2", "playbin2")

if not data["playbin2"]:
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

# Set the URI to play
data["playbin2"].set_property("uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Start playing
ret = data["playbin2"].set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

# Listen to the bus
bus = data["playbin2"].get_bus()
while not data["terminate"]:
    message = bus.timed_pop_filtered(100 * gst.MSECOND,
                                     gst.MESSAGE_STATE_CHANGED | gst.MESSAGE_ERROR | gst.MESSAGE_EOS | gst.MESSAGE_DURATION)

    # Parse message
    if message:
        handle_message(data, message)
    else:
        if data["playing"]:
            fmt = gst.FORMAT_TIME
            current = -1
            # Query the current position of the stream
            current = data['playbin2'].query_position(fmt, None)[0]
            if not current:
                print >> sys.stderr, "Could not query current position"

            # If we didn't know it yet, query the stream duration
            if data["duration"] == gst.CLOCK_TIME_NONE:
                data["duration"] = data['playbin2'].query_duration(fmt, None)[0]
                if not data["duration"]:
                    print >> sys.stderr, "Could not query current duration"
            
            print "Position %s / %s\r"% (convert_ns(current), convert_ns(data["duration"])),
            sys.stdout.flush()

            # If seeking is enabled, we have not done it yet, and the time is right, seek
            if data["seek_enabled"] and not data["seek_done"] and current > 10 * gst.SECOND:
                print "\nReached 10s, performing seek..."
                data['playbin2'].seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, 30 * gst.SECOND)
                data["seek_done"] = True
                

        


# Free resources
data["playbin2"].set_state(gst.STATE_NULL)
