#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 3: Short-cutting the pipeline
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+3%3A+Short-cutting+the+pipeline
"""
import sys
from array import array
import gobject
#gobject.threads_init()
import pygst
pygst.require("0.10")
import gst

CHUNK_SIZE = 1024 # Amount of bytes we are sending in each buffer
SAMPLE_RATE = 44100 # Samples per second we are sending
AUDIO_CAPS = "audio/x-raw-int,channels=1,rate={0},signed=(boolean)true,width=16,depth=16,endianness=BYTE_ORDER"

#Structure to contain all our information, so we can pass it to callbacks 
class CustomData:
    pipeline = None
    app_source = None
    num_samples = 0  # Number of samples generated so far (for timestamp generation)
    a = 0.0  # For waveform generation
    b = 0.0
    c = 0.0
    d = 0.0
    sourceid = 0 # To control the GSource
    main_loop = None  # GLib's main loop

#This method is called by the idle GSource in the mainloop, to feed CHUNK_SIZE bytes into appsrc. 
#The idle handler is added to the mainloop when appsrc requests us to start sending data (need-data signal)
#and is removed when appsrc has enough data (enough-data signal)
def push_data(data):
    num_samples = CHUNK_SIZE /2 # Because each sample is 16 bits 

    #Generate some psychodelic waveforms
    data.c += data.d
    data.d -= data.c / 1000.0
    freq = 1100.0 + 1000.0*data.d

    raw = array('H')
    for i in xrange(num_samples):
        data.a += data.b
        data.b -= data.a/freq
        a5 = (int(500 * data.a))% 65535
        raw.append(a5)
    data.num_samples += num_samples
    buffer = gst.Buffer(raw.tostring())

    #Set its timestamp and duration
    buffer.timestamp = gst.util_uint64_scale(data.num_samples, gst.SECOND, SAMPLE_RATE)
    buffer.duration = gst.util_uint64_scale(CHUNK_SIZE, gst.SECOND, SAMPLE_RATE)

    #Push the buffer into the appsrc
    ret = data.app_source.emit("push-buffer", buffer)
    if (ret != gst.FLOW_OK):
        return False
    return True

#This signal callback triggers when appsrc needs data. Here, we add an idle handler
#to the mainloop to start pushing data into the appsrc
def start_feed(source, size, data):
    if (data.sourceid == 0):
        print ("Start feeding")
        data.sourceid = gobject.idle_add(push_data, data)

#This callback triggers when appsrc has enough data and we can stop sending.
#We remove the idle handler from the mainloop
def stop_feed(source, data):
    if (data.sourceid != 0):
        print ("Stop feeding")
        gobject.source_remove(data.sourceid)
        data.sourceid = 0

#This function is called when an error message is posted on the bus 
def error_cb(bus, msg, data):
    err, debug_info = msg.parse_error()
    print >> sys.stderr, ("Error received from element %s: %s"% (message.src.get_name(), err))
    print >> sys.stderr, ("Debugging information: %s"% debug)
    data.main_loop.quit()

# This function is called when playbin2 has created the appsrc element, so we have
# a chance to configure it. 
def source_setup(pipeline, source, data):
    print ("Source has been created. Configuring")
    data.app_source = source
    #Configure appsrc
    audio_caps_text = AUDIO_CAPS.format(SAMPLE_RATE)
    audio_caps = gst.caps_from_string(audio_caps_text)
    source.set_property("caps", audio_caps)
    source.connect("need-data", start_feed, data)
    source.connect("enough-data", stop_feed, data)


data = CustomData()
# Initialize custom data structure
data.a = 0.0
data.b = 1.0
data.c = 0.0
data.d = 1.0

#Create the playbin2 element
data.pipeline = gst.parse_launch("playbin2 uri=appsrc://")
data.pipeline.connect("source-setup", source_setup, data)

#Instruct the bus to emit signals for each received message, and connect to the interesting signals */
bus = data.pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message::error", error_cb, data)

#Start playing the pipeline
data.pipeline.set_state(gst.STATE_PLAYING)

#Create a GLib Mainloop and set it to run
data.main_loop = gobject.MainLoop()
data.main_loop.run()

# Free resources 
data.pipeline.set_state(gst.STATE_NULL)
