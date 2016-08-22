/**
 * 16/08/2016
 *
 * gcc takepic.c -o takepic `pkg-config --cflags --libs gstreamer-1.0 gstreamer-video-1.0`
 *
 * See:
 * - http://gstreamer-devel.966125.n4.nabble.com/Take-snapshot-from-running-pipeline-in-gstreamer-with-iOS-td4678410.html
 * - https://github.com/GStreamer/gst-editing-services/blob/1.9.1/ges/ges-pipeline.c#L1235
 */

#include <gst/gst.h>
#include <gst/video/video.h>

#define PIC_LOCATION "out.png"

/* Structure to contain all our information, so we can pass it around */
typedef struct _CustomData {
  GstElement *pipeline;  /* Our one and only element */
  GstElement *sink;  /* Our one and only element */
  gboolean terminate;    /* Should we terminate execution? */
} CustomData;

/* Forward definition of the message processing function */
static void take_pic (CustomData *data);
static void handle_message (CustomData *data, GstMessage *msg);

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
  data.pipeline = gst_parse_launch ("v4l2src name=src ! video/x-raw,framerate=24/1,width=640 ! fakesink enable-last-sample=true name=sink", NULL);

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
    msg = gst_bus_timed_pop_filtered (bus, 2 * GST_SECOND,
        GST_MESSAGE_STATE_CHANGED | GST_MESSAGE_ERROR | GST_MESSAGE_EOS);

    /* Parse message */
    if (msg != NULL) {
      handle_message (&data, msg);
    } else {
      g_print ("DO IT!!\n");
      take_pic (&data);
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



static void take_pic(CustomData *data)
{
    GstCaps *caps;
    GstSample *from_sample, *to_sample;
    GError *err = NULL;
    GstBuffer *buf;
    GstMapInfo map_info;

    data->terminate = TRUE;

    g_object_get (data->sink, "last-sample", &from_sample, NULL);
    if (from_sample == NULL) {
        GST_ERROR ("Error getting last sample form sink");
        return;
    }

    caps = gst_caps_from_string ("image/png");
    to_sample = gst_video_convert_sample (from_sample, caps, GST_CLOCK_TIME_NONE, &err);

    gst_caps_unref (caps);
    gst_sample_unref (from_sample);

    if (to_sample == NULL && err) {
        GST_ERROR ("Error converting frame: %s", err->message);
        g_error_free (err);
        return;
    }

    buf = gst_sample_get_buffer (to_sample);
    if (gst_buffer_map (buf, &map_info, GST_MAP_READ)) {
        if (!g_file_set_contents (PIC_LOCATION, (const char *) map_info.data,
                                  map_info.size, &err)) {
            GST_WARNING ("Could not save thumbnail: %s", err->message);
            g_error_free (err);
        }
    }

    gst_sample_unref (to_sample);
    gst_buffer_unmap (buf, &map_info);
}
