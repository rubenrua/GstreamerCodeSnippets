/**
 * 19/09/2023
 *
 * gcc switchbintest.c -Wall -o switchbintest `pkg-config --cflags --libs gstreamer-1.0 gstreamer-video-1.0`
 *
 * See:
 */

#include <gst/gst.h>


static gboolean handle_message (GstElement *pipeline, GstMessage *msg);

int main(int argc, char *argv[]) {
  GstElement *pipeline;
  GstElement *capsfilter;
  gboolean terminate;
  GstBus *bus;
  GstMessage *msg;
  GstStateChangeReturn ret;
  guint ii = 0;
  GstCaps *caps;

  terminate = FALSE;

  /* Initialize GStreamer */
  gst_init (&argc, &argv);

  /* Create the elements */
  pipeline = gst_parse_launch (
    "videotestsrc ! capsfilter name=capsfilter caps=video/x-raw,width=640,height=480 ! switchbin num-paths=2 "
    "   path0::element=\"videoscale dither=none ! capsfilter caps=video/x-raw,width=64,height=48 ! videoscale dither=none\" path0::caps=\"video/x-raw,input=b\" "
    "   path1::element=\"identity\" path1::caps=\"ANY\" ! "
    "capsfilter caps=video/x-raw,width=640,height=480 ! autovideosink", NULL);
  capsfilter = gst_bin_get_by_name( GST_BIN( pipeline), "capsfilter");


  if (!pipeline || !capsfilter) {
    g_printerr ("Not all elements could be created.\n");
    return -1;
  }

  /* Start playing */
  ret = gst_element_set_state (pipeline, GST_STATE_PLAYING);
  if (ret == GST_STATE_CHANGE_FAILURE) {
    g_printerr ("Unable to set the pipeline to the playing state.\n");
    gst_object_unref (pipeline);
    return -1;
  }

  /* Listen to the bus */
  bus = gst_element_get_bus (pipeline);
  do {
    msg = gst_bus_timed_pop_filtered (bus, 2 * GST_SECOND,
        GST_MESSAGE_ERROR | GST_MESSAGE_EOS);

    /* Parse message */
    if (msg != NULL) {
      terminate = handle_message (pipeline, msg);
    } else {
      char caps_raw[] = "video/x-raw,width=640,height=480,input=a";
      caps_raw[strlen(caps_raw)-1] = (97 + (ii % 2)); //97 is a
      g_print ("DO IT!! %s\n", caps_raw);

      caps = gst_caps_from_string (caps_raw);
      g_object_set (capsfilter, "caps", caps, NULL);
      gst_caps_unref (caps);
      ii++;
    }
  } while (!terminate);

  /* Free resources */
  gst_object_unref (bus);
  gst_element_set_state (pipeline, GST_STATE_NULL);
  gst_object_unref (pipeline);
  return 0;
}

static gboolean handle_message (GstElement *pipeline, GstMessage *msg) {
  GError *err;
  gchar *debug_info;
  gboolean terminate;

  terminate = FALSE;


  switch (GST_MESSAGE_TYPE (msg)) {
    case GST_MESSAGE_ERROR:
      gst_message_parse_error (msg, &err, &debug_info);
      g_printerr ("Error received from element %s: %s\n", GST_OBJECT_NAME (msg->src), err->message);
      g_printerr ("Debugging information: %s\n", debug_info ? debug_info : "none");
      g_clear_error (&err);
      g_free (debug_info);
      terminate = TRUE;
      break;
    case GST_MESSAGE_EOS:
      g_print ("End-Of-Stream reached.\n");
      terminate = TRUE;
      break;
    default:
      /* We should not reach here */
      g_printerr ("Unexpected message received: %s.\n", GST_MESSAGE_TYPE_NAME(msg));
      break;
  }
  gst_message_unref (msg);

  return terminate;
}
