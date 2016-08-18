/**
 * 05/11/2012
 * 
 * gcc multifilesink.c -o multifilesink `pkg-config --cflags --libs gstreamer-0.10`
 */

#include <gst/gst.h>

#define GST_VIDEO_EVENT_FORCE_KEY_UNIT_NAME "GstForceKeyUnit"
  
/* Structure to contain all our information, so we can pass it around */
typedef struct _CustomData {
  GstElement *pipeline;  /* Our one and only element */
  GstElement *sink;  /* Our one and only element */
  gboolean terminate;    /* Should we terminate execution? */
} CustomData;
  
/* Forward definition of the message processing function */
static void handle_message (CustomData *data, GstMessage *msg);
static GstEvent * event_new_downstream_force_key_unit (GstClockTime timestamp,
					       GstClockTime stream_time, GstClockTime running_time, gboolean all_headers,
					       guint count);

  
int main(int argc, char *argv[]) {
  CustomData data;
  GstBus *bus;
  GstMessage *msg;
  GstStateChangeReturn ret;
  GstEvent *event;
  guint ii = 0;

  data.terminate = FALSE;
  
  /* Initialize GStreamer */
  gst_init (&argc, &argv);
   
  /* Create the elements */
  data.pipeline = gst_parse_launch ("v4l2src name=src ! video/x-raw-yuv,framerate=24/1,width=640 ! queue ! ffmpegcolorspace ! x264enc threads=0 bitrate=400 tune=zerolatency ! avimux ! multifilesink name=sink next-file=3 location=out%d.avi", NULL);
  
  data.sink = gst_bin_get_by_name( GST_BIN( data.pipeline), "sink");

  if (!data.pipeline) {
    g_printerr ("Not all elements could be created.\n");
    return -1;
  }
  
  /* Start playing */
  ret = gst_element_set_state (data.pipeline, GST_STATE_PLAYING);
  if (ret == GST_STATE_CHANGE_FAILURE) {
    g_printerr ("Unable to set the pipeline to the playing state.\n");
    gst_object_unref (data.pipeline);
    return -1;
  }
  
  /* Listen to the bus */
  bus = gst_element_get_bus (data.pipeline);
  do {
    msg = gst_bus_timed_pop_filtered (bus, 10 * GST_SECOND,
        GST_MESSAGE_STATE_CHANGED | GST_MESSAGE_ERROR | GST_MESSAGE_EOS);
  
    /* Parse message */
    if (msg != NULL) {
      handle_message (&data, msg);
    } else {
      g_print ("DO IT!!\n");
      event = event_new_downstream_force_key_unit (GST_CLOCK_TIME_NONE, GST_CLOCK_TIME_NONE, GST_CLOCK_TIME_NONE, TRUE, ii++);
      gst_pad_send_event( gst_element_get_static_pad (data.sink, "sink"), event);
    }
  } while (!data.terminate);
  
  /* Free resources */
  gst_object_unref (bus);
  gst_element_set_state (data.pipeline, GST_STATE_NULL);
  gst_object_unref (data.pipeline);
  return 0;
}
  
static void handle_message (CustomData *data, GstMessage *msg) {
  GError *err;
  gchar *debug_info;
  
  switch (GST_MESSAGE_TYPE (msg)) {
    case GST_MESSAGE_ERROR:
      gst_message_parse_error (msg, &err, &debug_info);
      g_printerr ("Error received from element %s: %s\n", GST_OBJECT_NAME (msg->src), err->message);
      g_printerr ("Debugging information: %s\n", debug_info ? debug_info : "none");
      g_clear_error (&err);
      g_free (debug_info);
      data->terminate = TRUE;
      break;
    case GST_MESSAGE_EOS:
      g_print ("End-Of-Stream reached.\n");
      data->terminate = TRUE;
      break;
    case GST_MESSAGE_STATE_CHANGED:{
      GstState old_state, new_state, pending_state;
      gst_message_parse_state_changed (msg, &old_state, &new_state, &pending_state);
      g_print ("%s state changed from %s to %s:\n", GST_OBJECT_NAME (GST_MESSAGE_SRC (msg)),
	       gst_element_state_get_name (old_state), gst_element_state_get_name (new_state)); 
      } break;
    default:
      /* We should not reach here */
      g_printerr ("Unexpected message received.\n");
      break;
  }
  gst_message_unref (msg);
}


static GstEvent * event_new_downstream_force_key_unit (GstClockTime timestamp,
					       GstClockTime stream_time, GstClockTime running_time, gboolean all_headers,
					       guint count)
{
  GstEvent *force_key_unit_event;
  GstStructure *s;

  s = gst_structure_new (GST_VIDEO_EVENT_FORCE_KEY_UNIT_NAME,
			 "timestamp", G_TYPE_UINT64, timestamp,
			 "stream-time", G_TYPE_UINT64, stream_time,
			 "running-time", G_TYPE_UINT64, running_time,
			 "all-headers", G_TYPE_BOOLEAN, all_headers,
			 "count", G_TYPE_UINT, count, NULL);
  force_key_unit_event = gst_event_new_custom (GST_EVENT_CUSTOM_DOWNSTREAM, s);

  return force_key_unit_event;
}
