#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 12: Streaming
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+12%3A+Streaming
"""
import sys
import pygst
pygst.require("0.10")
import gst
import gobject

class CustomData:
    is_live = False
    pipeline = None
    loop = None

def cb_message(bus, msg, data):
    def error():
        print >> sys.stderr, ("Error: {0}".format(err.message))
        data.pipeline.set_state(gst.STATE_READY)
        data.loop.quit()
    def eos():
        data.pipeline.set(gst.STATE_READY)
        data.loop.quit()
    def buffering():
        percent = 0
        #If the stream is live, we do not care about buffering.
        if (data.is_live):
            return
        percent = msg.parse_buffering()
        sys.stdout.write("\rBuffering ({0}%)".format(percent))
        sys.stdout.flush()
        #Wait until buffering is complete before start/resume playing
        if (percent < 0):
            data.pipeline.set_state(gst.STATE_PAUSED)
        else:
            data.pipeline.set_state(gst.STATE_PLAYING)
    def clock_lost():
        #Get a new clock
        data.pipeline.set_state(gst.STATE_PAUSED)
        data.pipeline.set_state(gst.STATE_PLAYING)
    def default():
        pass

    handlers = dict({gst.MESSAGE_ERROR: error, 
                     gst.MESSAGE_EOS: eos,
                     gst.MESSAGE_BUFFERING: buffering,
                     gst.MESSAGE_CLOCK_LOST: clock_lost
                     })
    if (handlers.has_key(msg.type)):
        handlers[msg.type]()

data = CustomData()
pipeline = gst.parse_launch('playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm')
bus = pipeline.get_bus()

#Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, ("Unable to set pipeline to the playing state")
    exit(-1)
elif (ret == gst.STATE_CHANGE_NO_PREROLL):
    data.is_live = True

main_loop = gobject.MainLoop(None, False)
data.loop = main_loop
data.pipeline = pipeline

bus.add_signal_watch()
bus.connect("message", cb_message, data)
data.loop.run()

pipeline.set_state(gst.STATE_PLAYING)



