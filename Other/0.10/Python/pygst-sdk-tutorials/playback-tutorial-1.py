#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Playback tutorial 1: Playbin2 usage
http://docs.gstreamer.com/display/GstSDK/Playback+tutorial+1%3A+Playbin2+usage
"""
import sys
import pygst
pygst.require("0.10")
import gst
import glib, gobject

class CustomData:
    def __init__(self):
        self.playbin2 = None
        self.n_video = 0
        self.n_audio = 0
        self.n_text = 0
        self.current_video = 0
        self.current_audio = 0
        self.current_text = 0
        self.main_loop = None

class GstPlayFlags:
    GST_PLAY_FLAG_VIDEO = 1 << 0 # We want video output 
    GST_PLAY_FLAG_AUDIO = 1 << 1 # We want audio output 
    GST_PLAY_FLAG_TEXT = 1 << 3 # We want subtitle output

def analyze_streams(data):
    #Read some properties
    data.n_video = data.playbin2.get_property("n-video")
    data.n_audio = data.playbin2.get_property("n-audio")
    data.n_text = data.playbin2.get_property("n-text")

    print ("{0.n_video} video stream(s), {0.n_audio} audio stream(s), {0.n_text} text streams".format(data))
    for i in xrange(data.n_video):
         #Retrieve the stream's video tags
        tags = data.playbin2.emit("get-video-tags", i)
        str = tags[gst.TAG_VIDEO_CODEC]
        print ("  codec: {0}".format(str if str else "unknown"))

    print ""
    for i in xrange(data.n_audio):
        # Retrieve the stream's audio tags 
        tags = data.playbin2.emit("get-audio-tags", i)
        if (tags):
            print ("audio stream {0}:".format(i))
            if (gst.TAG_AUDIO_CODEC in tags):
                str = tags[gst.TAG_AUDIO_CODEC]
                print ("  codec: {0}".format(str))
            if (gst.TAG_LANGUAGE_CODE in tags):
                str = tags[gst.TAG_LANGUAGE_CODE]
                print ("  language: {0}".format(str))
            if (gst.TAG_BITRATE in tags):
                rate = tags[gst.TAG_BITRATE]
                print ("  bitrate: {0}".format(rate))

    print ""
    for i in xrange(data.n_text):
        #Retrieve the stream's subtitle tags 
        tags = data.playbin2.emit("get-text-tags", i)
        if (tags):
            print ("subtitle stream {0}".format(i))
            if (gst.TAG_LANGUAGE_CODE in tags):
                str = tags[gst.TAG_LANGUAGE_CODE]
                print ("  language: {0}".format(str))

    data.current_video = data.playbin2.get_property("current-video")
    data.current_audio = data.playbin2.get_property("current-audio")
    data.current_text = data.playbin2.get_property("current-text")
    print ("Currently playing video stream {0.current_video}, audio stream {0.current_audio} and text stream {0.current_text}".format(data))

def handle_message(bus, msg, data):
    if (msg.type == gst.MESSAGE_ERROR):
        err, debug_info = msg.parse_error()
        print >> sys.stderr, "Error received from element {0} : {1}".format(msg.src.get_name(), err.message)
        print >> sys.stderr, "Debugging information: {0}".format(debug_info if debug_info else "none")
        data.main_loop.quit()
    elif (msg.type == gst.MESSAGE_EOS):
        print ("End of Stream reached.")
        data.main_loop.quit()
    elif (msg.type == gst.MESSAGE_STATE_CHANGED):
        old_state, new_state, pending_state = msg.parse_state_changed()
        if (msg.src == data.playbin2):
            if (new_state == gst.STATE_PLAYING):
                analyze_streams(data)
    return True

def handle_keyboard(source, cond, data):
    str = source.readline()
    x = str[0];
    if (x == 'q' or x == 'Q'):
        data.main_loop.quit()
        return True
    index = int(str)
    if (index < 0 or index >= data.n_audio):
        print >> sys.stderr, "Index out of bounds"
    else:
        #If the input was a valid audio stream index, set the current audio stream
        print ("Setting current audio stream to {0}".format(index))
        data.playbin2.set_property("current-audio", index)
    return True


data = CustomData()

#Create the elements
data.playbin2 = gst.element_factory_make("playbin2", "playbin2")
if (not data.playbin2):
    print >> sys.stderr , "Not all elements could be created"
    exit(-1)

#Set the URI to play
data.playbin2.set_property("uri", "http://docs.gstreamer.com/media/sintel_cropped_multilingual.webm")

#Set flags to show Audio and Video but ignore Subtitles
flags = data.playbin2.get_property("flags")
flags |= (GstPlayFlags.GST_PLAY_FLAG_VIDEO | GstPlayFlags.GST_PLAY_FLAG_AUDIO)
flags &= ~GstPlayFlags.GST_PLAY_FLAG_TEXT
data.playbin2.set_property("flags", flags)

#Set connection speed. This will affect some internal decisions of playbin2 
data.playbin2.set_property("connection_speed", 56)

#Add a bus watch, so we get notified when a message arrives
bus = data.playbin2.get_bus()
bus.add_watch(handle_message, data)

#Add a keyboard watch so we get notified of keystrokes
io_stdin = glib.IOChannel(sys.stdin.fileno())
io_stdin.add_watch(glib.IO_IN, handle_keyboard, data)

#Start playing
ret = data.playbin2.set_state(gst.STATE_PLAYING)
if (ret == gst.STATE_CHANGE_FAILURE):
    print >> sys.stderr, ("Unable to set pipeline to the playing state")
    exit(-1)

#Create a GLib Main Loop and set it to run 
data.main_loop = gobject.MainLoop(None, False)
data.main_loop.run()

#Free resources
data.playbin2.set_state(gst.STATE_NULL)

