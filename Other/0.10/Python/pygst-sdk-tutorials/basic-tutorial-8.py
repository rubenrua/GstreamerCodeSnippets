#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Basic tutorial 8: Short-cutting the pipeline
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+8%3A+Short-cutting+the+pipeline
"""
import sys
from array import array
import gobject
#GC object already tracked
#http://stackoverflow.com/questions/7496629/gstreamer-appsrc-causes-random-crashes
gobject.threads_init()
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
    tee = None
    audio_queue = None
    audio_convert1 = None
    audio_resample = None
    audio_sink = None
    video_queue = None
    audio_convert2 = None
    visual = None
    video_convert = None
    video_sink = None
    app_queue = None
    app_sink = None
    num_samples = 0
    a = 0.0
    b = 0.0
    c = 0.0
    d = 0.0
    sourceid = 0
    main_loop = None

#This method is called by the idle GSource in the mainloop, to feed CHUNK_SIZE bytes into appsrc. 
#The idle handler is added to the mainloop when appsrc requests us to start sending data (need-data signal)
#and is removed when appsrc has enough data (enough-data signal)
def push_data(data):
    num_samples = CHUNK_SIZE / 2 # Because each sample is 16 bits

    #Generate some psychodelic waveforms
    data.c += data.d
    data.d -= data.c / 1000.0
    freq = 1100.0 + 1000.0*data.d

    ##version 1, using struct.pack    
    #b_data = ''
    #for i in xrange(num_samples):
    #    data.a += data.b
    #    data.b -= data.a / freq
    #    a5 = (int(500 * data.a))% 65535
    #    b_data = b_data + struct.pack('H', a5)

    ##version 2, using array
    raw = array('H')
    for i in xrange(num_samples):
        data.a += data.b
        data.b -= data.a / freq
        a5 = (int(500 * data.a))% 65535
        raw.append(a5)
    b_data = raw.tostring()

    data.num_samples += num_samples
    buffer = gst.Buffer(b_data)

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

#The appsink has received a buffer
def new_buffer(sink, data):
    #Retrieve the buffer
    buffer = sink.emit("pull-buffer")
    if (buffer):
        # The only thing we do in this example is print a * to indicate a received buffer
        print "*", 

#This function is called when an error message is posted on the bus 
def error_cb(bus, msg, data):
    err, debug_info = msg.parse_error()
    print >> sys.stderr, ("Error received from element %s: %s"% (message.src.get_name(), err))
    print >> sys.stderr, ("Debugging information: %s"% debug)
    data.main_loop.quit()


data = CustomData() 
# Initialize custom data structure
data.a = 0.0
data.b = 1.0
data.c = 0.0
data.d = 1.0
    
# Create the elements
data.app_source = gst.element_factory_make("appsrc", "app_source")
data.tee = gst.element_factory_make("tee", "tee")
data.audio_queue = gst.element_factory_make("queue", "audio_queue")
data.audio_convert1 = gst.element_factory_make("audioconvert", "audio_convert1")
data.audio_resample = gst.element_factory_make("audioresample", "audio_resample")
data.audio_sink = gst.element_factory_make("autoaudiosink", "audio_sink")
data.video_queue = gst.element_factory_make("queue", "video_queue")
data.audio_convert2 = gst.element_factory_make("audioconvert", "audio_convert2")
data.visual = gst.element_factory_make("wavescope", "visual")
data.video_convert = gst.element_factory_make("ffmpegcolorspace", "csp")
data.video_sink = gst.element_factory_make("autovideosink", "video_sink")
data.app_queue = gst.element_factory_make("queue", "app_queue")
data.app_sink = gst.element_factory_make("appsink", "app_sink")
data.pipeline = gst.Pipeline("test-pipeline")
    
if (not data.app_source or not data.tee or not data.audio_queue or not data.audio_convert1 or not data.audio_resample
    or not data.audio_sink or not data.video_queue or not data.audio_convert2 or not data.visual
    or not data.video_convert or not data.video_sink or not data.app_queue or not data.app_sink
    or not data.pipeline):
    print >> sys.stderr, ("Not all elements could be created.")
    exit(-1)
    
#Configure wavescope
data.visual.set_property("shader", 0)
data.visual.set_property("style", 0)
    
#Configure appsrc
audio_caps_text = AUDIO_CAPS.format(SAMPLE_RATE)
audio_caps = gst.caps_from_string(audio_caps_text)
data.app_source.set_property("caps", audio_caps)
data.app_source.connect("need-data", start_feed, data)
data.app_source.connect("enough-data", stop_feed, data)
    
# Configure appsink
data.app_sink.set_property("emit-signals", True)
data.app_sink.set_property("caps", audio_caps)
data.app_sink.connect("new-buffer", new_buffer, data)
    
#Link all elements that can be automatically linked because they have "Always" pads 
data.pipeline.add(data.app_source, data.tee, 
                    data.audio_queue, data.audio_convert1, data.audio_resample, data.audio_sink, 
                    data.video_queue, data.audio_convert2, data.visual, data.video_convert, data.video_sink, 
                    data.app_queue, data.app_sink)
if (not data.app_source.link(data.tee) or
    not gst.element_link_many(data.audio_queue, data.audio_convert1, data.audio_resample, data.audio_sink) or
    not gst.element_link_many(data.video_queue, data.audio_convert2, data.visual, data.video_convert, data.video_sink) or
    not gst.element_link_many(data.app_queue, data.app_sink)):
    print >> sys.stderr, "Elements could not be linked."
    exit(-1)
    
#Manually link the Tee, which has "Request" pads 
tee_audio_pad = data.tee.get_request_pad("src%d")
print ("Obtained request pad {0} for audio branch".format(tee_audio_pad.get_name()))
queue_audio_pad = data.audio_queue.get_static_pad("sink")
tee_video_pad = data.tee.get_request_pad("src%d")
print ("Obtained request pad {0} for video branch".format(tee_video_pad.get_name()))
queue_video_pad = data.video_queue.get_static_pad("sink")
tee_app_pad =  data.tee.get_request_pad("src%d")
print ("Obtained request pad {0} for app branch".format(tee_app_pad.get_name()))
queue_app_pad =  data.app_queue.get_static_pad("sink")
    
if (tee_audio_pad.link(queue_audio_pad) != gst.PAD_LINK_OK or
    tee_video_pad.link(queue_video_pad) != gst.PAD_LINK_OK or
    tee_app_pad.link(queue_app_pad) != gst.PAD_LINK_OK):
    print >> sys.stderr, "Tee could not be linked."
    exit(-1)
    
# Instruct the bus to emit signals for each received message, and connect to the interesting signals
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






