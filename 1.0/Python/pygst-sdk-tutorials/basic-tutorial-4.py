#!/usr/bin/env python3
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
from gi.repository import Gst
Gst.init(None)

# Python version of GST_TIME_ARGS


def convert_ns(t):
    s, ns = divmod(t, 1000000000)
    m, s = divmod(s, 60)

    if m < 60:
        return "0:%02i:%02i.%i" % (m, s, ns)
    else:
        h, m = divmod(m, 60)
        return "%i:%02i:%02i.%i" % (h, m, s, ns)


def handle_message(data, msg):
    if message.type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("Error received from element %s: %s" % (message.src.get_name(), err), file=sys.stderr)
        print("Debugging information: %s" % debug, file=sys.stderr)
        data["terminate"] = True
    elif message.type == Gst.MessageType.EOS:
        print("End-Of-Stream reached.")
        data["terminate"] = True
    elif message.type == Gst.MessageType.DURATION_CHANGED:
        # The duration has changed, mark the current one as invalid
        data["duration"] = Gst.CLOCK_TIME_NONE
    elif message.type == Gst.MessageType.STATE_CHANGED:
        if message.src == data["playbin"]:
            old_state, new_state, pending_state = message.parse_state_changed()
            print("Pipeline state changed from %s to %s." % (old_state.value_nick, new_state.value_nick))
            data["playing"] = (new_state == Gst.State.PLAYING)
            if data["playing"]:
                query = Gst.Query.new_seeking(Gst.Format.TIME)
                if data["playbin"].query(query):
                    (aux, data["seek_enabled"], start, end) = query.parse_seeking()
                    if data["seek_enabled"]:
                        print("Seeking is ENABLED from %s to %s" % (convert_ns(start), convert_ns(end)))
                    else:
                        print("Seeking is DISABLED for this stream.")
                else:
                    print("Seeking query failed.", file=sys.stderr)
    else:
        print("Unexpected message received.", file=sys.stderr)
 

data = dict()

data["playing"] = False
data["terminate"] = False
data["seek_enabled"] = False
data["seek_done"] = False
data["duration"] = Gst.CLOCK_TIME_NONE

# Create the elements
data["playbin"] = Gst.ElementFactory.make("playbin", "playbin")

if not data["playbin"]:
    print("Not all elements could be created.", file=sys.stderr)
    exit(-1)

# Set the URI to play
data["playbin"].set_property(
    "uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Start playing
ret = data["playbin"].set_state(Gst.State.PLAYING)
if ret == Gst.StateChangeReturn.FAILURE:
    print("Unable to set the pipeline to the playing state.", file=sys.stderr)
    exit(-1)

# Listen to the bus
bus = data["playbin"].get_bus()
while not data["terminate"]:
    message = bus.timed_pop_filtered(100 * Gst.MSECOND,
                                     Gst.MessageType.STATE_CHANGED | 
                                     Gst.MessageType.ERROR | 
                                     Gst.MessageType.EOS | 
                                     Gst.MessageType.DURATION_CHANGED)

    # Parse message
    if message:
        handle_message(data, message)
    else:
        if data["playing"]:
            fmt = Gst.Format.TIME
            current = -1
            # Query the current position of the stream
            _, current = data['playbin'].query_position(fmt)
            if not current:
                print("Could not query current position", file=sys.stderr)

            # If we didn't know it yet, query the stream duration
            if data["duration"] == Gst.CLOCK_TIME_NONE:
                _, data["duration"] = data['playbin'].query_duration(fmt)
                if not data["duration"]:
                    print("Could not query current duration", file=sys.stderr)

            print("Position %s / %s\r" % (
                convert_ns(current), convert_ns(data["duration"])), end=' ')
            sys.stdout.flush()

            # If seeking is enabled, we have not done it yet, and the time is
            # right, seek
            if data["seek_enabled"] and not data["seek_done"] and current > 10 * Gst.SECOND:
                print("\nReached 10s, performing seek...")
                data['playbin'].seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 30 * Gst.SECOND)
                data["seek_done"] = True


# Free resources
data["playbin"].set_state(Gst.State.NULL)
