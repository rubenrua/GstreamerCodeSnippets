#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 5: Color Balance
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+5%3A+Color+Balance
"""
import sys
import glib
import gobject
import pygst
pygst.require("0.10")
import gst
from gst.interfaces import ColorBalance

class CustomData:
    pipeline = None
    loop = None

def update_color_channel(channel_name, increase, cb):
    #Retrieve the list of channels and locate the requested one
    channel = None
    channels = ColorBalance.list_colorbalance_channels(cb)  
    for tmp in channels:
        if (tmp.label == channel_name):
            channel = tmp
            break
    
    if (not channel):
        return 

    #Change the channel's value
    step = 0.1 * (channel.max_value - channel.min_value)
    value = cb.get_value(channel)
    if (increase):
        value = int(value + step)
        if (value > channel.max_value):
            value = channel.max_value
    else:
        value = int(value - step)
        if (value < channel.min_value):
            value = channel.min_value

    cb.set_value(channel, value)

def print_current_values(pipeline):
    channels = pipeline.list_colorbalance_channels()

    #for channel in channels:
    #    value = pipeline.get_value(channel)
    #    perc = 100 * (value - channel.min_value)/(channel.max_value - channel.min_value)
    #    sys.stdout.write("{0}: {1:3}% ".format(channel.label, perc))

    def mapper(c):
        return ("{0}: {1:3}%".format(c.label, 100 * (pipeline.get_value(c) - c.min_value) / (c.max_value - c.min_value)))
    out = map(mapper, channels)
    print ("  ".join(out))

def handle_keyboard(source, cond, data):
    str = source.readline()
    cmap = dict({'c': "CONTRAST",
                 'b': "BRIGHTNESS",
                 'h': "HUE",
                 's': "SATURATION"
                })
    lc = str[0].lower()
    if (lc == 'q'):
        data.main_loop.quit()
    elif (lc in cmap.keys()):
        update_color_channel(cmap[lc], str[0].isupper(), data.pipeline)
    else:
        pass

    print_current_values(data.pipeline)
    return True

#Initialize our data structure
data = CustomData()

#print usage map
print ("USAGE: Choose one of the following options, then press enter:\n"
    " 'C' to increase contrast, 'c' to decrease contrast\n"
    " 'B' to increase brightness, 'b' to decrease brightness\n"
    " 'H' to increase hue, 'h' to decrease hue\n"
    " 'S' to increase saturation, 's' to decrease saturation\n"
    " 'Q' to quit")

#Build the pipeline
data.pipeline = gst.parse_launch("playbin2 uri=http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

#Add a keyboard watch so we get notified of keystrokes
io_stdin = gobject.IOChannel(sys.stdin.fileno())
io_stdin.add_watch(glib.IO_IN, handle_keyboard, data)

ret = data.pipeline.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

print_current_values(data.pipeline)

#Create a GLib Main loop and set it to run
data.loop = gobject.MainLoop(None, False)
data.loop.run()

data.pipeline.set_state(gst.STATE_NULL)



