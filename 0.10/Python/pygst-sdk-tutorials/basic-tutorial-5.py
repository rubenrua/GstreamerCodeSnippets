#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-5
#
"""
basic-tutorial-5: GUI toolkit integration
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+5%3A+GUI+toolkit+integration

TODO:
 #1 - GstXOverlay in Python???? Use sync message
 #2 - Cairo
"""

import sys
import gst
import gtk
import gobject

# This function is called when the GUI toolkit creates the physical window that will hold the video.
# At this point we can retrieve its handler (which has a different meaning depending on the windowing system)
# and pass it to GStreamer through the XOverlay interface.
def realize_cb(widget, data):
    window = widget.get_window()

    if not window.ensure_native():
        print >> sys.stderr, "Couldn't create native window needed for GstXOverlay!"

    # TODO #1 
    # GstXOverlay in Python???? Use sync message
    # window_handle = GDK_WINDOW_XID (window);
    # /* Pass it to playbin2, which implements XOverlay and will forward it to the video sink */
    # gst_x_overlay_set_window_handle (GST_X_OVERLAY (data->playbin2), window_handle);
    # /*gst_x_overlay_set_window_handle ((GstXOverlay *) gst_implements_interface_cast (data->playbin2, gst_x_overlay_get_type ()), window_handle); */

# See TODO 1
def sync_message_cb(bus, message, data):
    if message.structure is None:
        return
    if message.structure.get_name() == 'prepare-xwindow-id':
        message.src.set_xwindow_id(data["video_window"].window.xid)


# This function is called when the PLAY button is clicked
def play_cb(button, data):
    data["playbin2"].set_state(gst.STATE_PLAYING)

# This function is called when the PAUSE button is clicked
def pause_cb(button, data):
    data["playbin2"].set_state(gst.STATE_PAUSED)

# This function is called when the STOP button is clicked
def stop_cb(button, data):
    data["playbin2"].set_state(gst.STATE_READY)

# This function is called when the main window is closed
def delete_event_cb(widget, data):
    stop_cb(None, data)
    gtk.main_quit()

# This function is called everytime the video window needs to be redrawn (due to damage/exposure,
# rescaling, etc). GStreamer takes care of this in the PAUSED and PLAYING states, otherwise,
# we simply draw a black rectangle to avoid garbage showing up.
def expose_cb(widget, event, data):
  if data["state"] < gst.STATE_PAUSED:
      # TODO #2 Cairo
      pass

  return False

# This function is called when the slider changes its position. We perform a seek to the
# new position here.
def slider_cb(range, data):
    value = data["slider"].get_value()
    data['playbin2'].seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, value * gst.SECOND)

# This creates all the GTK+ widgets that compose our application, and registers the callbacks
def create_ui(data):
    main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    main_window.connect("destroy", delete_event_cb, data)

    video_window = gtk.DrawingArea()
    data["video_window"] = video_window # See TODO #1
    video_window.set_double_buffered(False)
    video_window.connect("realize", realize_cb, data) # TODO Review
    video_window.connect("expose_event", expose_cb, data)

    play_button = gtk.Button(stock=gtk.STOCK_MEDIA_PLAY);
    play_button.connect("clicked", play_cb, data)
  
    pause_button = gtk.Button(stock=gtk.STOCK_MEDIA_PAUSE)
    pause_button.connect("clicked", pause_cb, data)
    
    stop_button = gtk.Button(stock=gtk.STOCK_MEDIA_STOP)
    stop_button.connect("clicked", stop_cb, data)
  
    data["slider"] = gtk.HScale()
    data["slider"].set_range(0, 100) #REVIEW 
    data["slider"].set_draw_value(0)
    data["slider_update_signal_id"] = data["slider"].connect("value-changed", slider_cb, data)
  
    data["streams_list"] = gtk.TextView()
    data["streams_list"].set_editable(False)
  
    controls = gtk.HBox(False, 0)
    controls.pack_start(play_button, False, False, 2)
    controls.pack_start(pause_button, False, False, 2)
    controls.pack_start(stop_button, False, False, 2)
    controls.pack_start(data["slider"], True, True, 2)
  
    main_hbox = gtk.HBox(False, 0);
    main_hbox.pack_start(video_window, True, True, 0)
    main_hbox.pack_start(data["streams_list"], False, False, 2)
  
    main_box = gtk.VBox(False, 0)
    main_box.pack_start(main_hbox, True, True, 0)
    main_box.pack_start(controls, False, False, 0)
    main_window.add(main_box)
    main_window.set_default_size(640, 480)
  
    main_window.show_all()


# This function is called periodically to refresh the GUI
def refresh_ui (data):
    fmt = gst.FORMAT_TIME
    current = -1

    # We do not want to update anything unless we are in the PAUSED or PLAYING states 
    if data["state"] < gst.STATE_PAUSED:
        return True

    # If we didn't know it yet, query the stream duration
    if data["duration"] == gst.CLOCK_TIME_NONE:
        data["duration"] = data['playbin2'].query_duration(fmt, None)[0]
        if not data["duration"]:
            print >> sys.stderr, "Could not query current duration"
        else:
            # Set the range of the slider to the clip duration, in SECONDS
            data["slider"].set_range(0, data["duration"] / gst.SECOND)
    
    current = data['playbin2'].query_position(fmt, None)[0]
    if current:
        # Block the "value-changed" signal, so the slider_cb function is not called
        # (which would trigger a seek the user has not requested)
        data["slider"].handler_block(data["slider_update_signal_id"])
        # Set the position of the slider to the current pipeline positoin, in SECONDS
        data["slider"].set_value(current / gst.SECOND)
        # Re-enable the signal
        data["slider"].handler_unblock(data["slider_update_signal_id"])
        
    return True
        

# This function is called when new metadata is discovered in the stream
def tags_cb(playbin2, stream, data):
    # We are possibly in a GStreamer working thread, so we notify the main
    # thread of this event through a message in the bus */
    playbin2.post_message(gst.message_new_application(playbin2, gst.Structure("tags-changed")))


# This function is called when an error message is posted on the bus
def error_cb(bus, msg, data):
    # Print error details on the screen
    err, debug = message.parse_error()
    print >> sys.stderr, "Error received from element %s: %s"% (message.src.get_name(), err)
    print >> sys.stderr, "Debugging information: %s"% debug
    # Set the pipeline to READY (which stops playback)
    data["playbin2"].set_state(gst.STATE_READY)
    

# This function is called when an End-Of-Stream message is posted on the bus.
# We just set the pipeline to READY (which stops playback) */
def eos_cb(bus, msg, data):
    print "End-Of-Stream reached."
    data["playbin2"].set_state(gst.STATE_READY)


# This function is called when the pipeline changes states. We use it to
# keep track of the current state.
def state_changed_cb(bus, msg, data):
    old_state, new_state, pending_state = msg.parse_state_changed()
    if msg.src == data["playbin2"]:
        data["state"] = new_state;
        print "State set to %s"% gst.element_state_get_name(new_state)
        if old_state == gst.STATE_READY and new_state == gst.STATE_PAUSED:
            # For extra responsiveness, we refresh the GUI as soon as we reach the PAUSED state
            refresh_ui (data)


# Extract metadata from all the streams and write it to the text widget in the GUI
def analyze_streams (data):
    # Clean current contents of the widget
    text = data["streams_list"].get_buffer()
    text.set_text("")

    # Read some properties
    n_video = data["playbin2"].get_property("n-video")
    n_audio = data["playbin2"].get_property("n-audio")
    n_text  = data["playbin2"].get_property("n-text")
    
    for i in xrange(n_video):
        tags = data["playbin2"].emit("get-video-tags", i)
        if tags:
            text.insert_at_cursor ("video stream %d:\n"% i)
            vstr = "unknown" if "video-codec" not in tags else tags["video-codec"]
            text.insert_at_cursor("  codec: %s\n"% vstr)

    for i in xrange(n_audio):
        tags = data["playbin2"].emit("get-audio-tags", i)
        if tags:
            text.insert_at_cursor ("\naudio stream %d:\n"% i)
            vstr = "unknown" if "audio-codec" not in tags else tags["audio-codec"]
            text.insert_at_cursor("  codec: %s\n"% vstr)
            vstr = "unknown" if "language-code" not in tags else tags["language-code"]
            text.insert_at_cursor("  language: %s\n"% vstr)
            vstr = "unknown" if "bitrate" not in tags else tags["bitrate"]
            text.insert_at_cursor("  bitrate: %s"% vstr)

    for i in xrange(n_text):
        tags = data["playbin2"].emit("get-text-tags", i)
        if tags:
            text.insert_at_cursor ("\ntext stream %d:\n"% i)
            vstr = "unknown" if "language-code" not in tags else tags["language-code"]
            text.insert_at_cursor("  language: %s\n"% vstr)


# This function is called when an "application" message is posted on the bus.
# Here we retrieve the message posted by the tags_cb callback
def application_cb(bus, msg, data):
    if msg.structure.get_name() == "tags-changed":
        analyze_streams(data)



data = dict()

data["slider"] = None
data["streams_list"] = None
data["slider_update_signal_id"] = 0
data["state"] = gst.STATE_NULL
data["duration"] = gst.CLOCK_TIME_NONE

# Create the elements
data["playbin2"] = gst.element_factory_make("playbin2", "playbin2")

if not data["playbin2"]:
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

# Set the URI to play
data["playbin2"].set_property("uri", "http://docs.gstreamer.com/media/sintel_trailer-480p.webm")

# Connect to interesting signals in playbin2
data["playbin2"].connect("video-tags-changed", tags_cb, data)
data["playbin2"].connect("audio-tags-changed", tags_cb, data)
data["playbin2"].connect("text-tags-changed", tags_cb, data)

# Create the GUI
create_ui(data)

# Instruct the bus to emit signals for each received message, and connect to the interesting signals
bus = data["playbin2"].get_bus()
bus.add_signal_watch()
bus.connect("message::error", error_cb, data)
bus.connect("message::eos", eos_cb, data)
bus.connect("message::state-changed", state_changed_cb, data)
bus.connect("message::application", application_cb, data)
bus.enable_sync_message_emission()  #See TODO #1
bus.connect("sync-message::element", sync_message_cb, data) #See TODO #1

# Start playing
ret = data["playbin2"].set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print >> sys.stderr, "Unable to set the pipeline to the playing state."
    exit(-1)

# Register a function that GLib will call every second
gobject.timeout_add_seconds (1, refresh_ui, data)

# Start the GTK main loop. We will not regain control until gtk_main_quit is called.
gtk.main()

# Free resources
data["playbin2"].set_state(gst.STATE_NULL)
