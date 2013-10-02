#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 13: Playback speed
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+13%3A+Playback+speed
"""
import sys, os
import gobject, glib
gobject.threads_init()
import pygst
pygst.require("0.10")
import gst

class CustomData:
    pipeline = None
    video_sink = None
    loop = None
    playing = False
    rate = 1.0

def send_seek_event(data):
    format = gst.FORMAT_TIME
    (position, fmt) = data.pipeline.query_position(format)
    if (not position):
        print >> sys.stderr, ("Unable to retrieve current position.")
        return

    seek_event = None
    #Create the seek event
    #http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/gstreamer-GstEvent.html#gst-event-new-seek
    if (data.rate > 0.0):
        seek_event = gst.event_new_seek(data.rate, gst.FORMAT_TIME, 
                        (gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE),
                        gst.SEEK_TYPE_SET, position, gst.SEEK_TYPE_SET, -1)
    else:
        seek_event = gst.event_new_seek(data.rate, gst.FORMAT_TIME, 
                        (gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_ACCURATE),
                        gst.SEEK_TYPE_SET, 0, gst.SEEK_TYPE_SET, position)
    if (not data.video_sink):
        data.video_sink = data.pipeline.get_property("video_sink")
    data.video_sink.send_event(seek_event)
    print ("Current rate: {0.rate}".format(data))

def handle_keyboard(source, cond, data):
    str = source.readline()
    x = str[0].lower()
    if (x == 'p'):
        data.playing = not data.playing
        data.pipeline.set_state(gst.STATE_PLAYING if data.playing else gst.STATE_PAUSED)
        print ("Setting state to {0}".format("PLAYING" if data.playing else "PAUSE"))
    elif (x == 's'):
        if (str[0].isupper()):
            data.rate *= 2.0
        else:
            data.rate /= 2.0
        send_seek_event(data)
    elif (x == 'd'):
        data.rate *= -1.0
        send_seek_event(data)
    elif (x == 'n'):
        if (not data.video_sink):
            #If we have not done so, obtain the sink through which we will send the step events
            data.video_sink = data.pipeline.get_property("video_sink")
        data.video_sink.send_event(gst.event_new_step(gst.FORMAT_BUFFERS, 1, data.rate, True, False))
        print ("Stepping one frame")
    elif (x == 'q'):
        data.loop.quit()
    return True


print (
    "USAGE: Choose one of the following options, then press enter:\n"
    " 'P' to toggle between PAUSE and PLAY\n"
    " 'S' to increase playback speed, 's' to decrease playback speed\n"
    " 'D' to toggle playback direction\n"
    " 'N' to move to next frame(s)  (in the current direction, better in PAUSE)\n"
    " 'Q' to quit\n");

data = CustomData()
data.pipeline = gst.parse_launch('playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm')
io_stdin = glib.IOChannel(sys.stdin.fileno())
io_stdin.add_watch(glib.IO_IN, handle_keyboard, data)

ret = data.pipeline.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, ("Unable to set pipeline to the playing state")
    exit(-1)

data.playing = True
data.rate = 1.0
data.loop = gobject.MainLoop(None, False)
data.loop.run()
data.pipeline.set_state(gst.STATE_NULL)


