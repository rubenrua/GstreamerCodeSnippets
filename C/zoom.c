/**
 * 21/01/2023
 *
 * gcc -Wall -Wextra zoom.c -o zoom `pkg-config --cflags --libs gstreamer-1.0 gstreamer-video-1.0`
 */

#include <gst/gst.h>
#include <gst/video/navigation.h>


#define WIDTH 640
#define HEIGHT 480

/* Structure to contain all our information, so we can pass it around */
typedef struct _CustomData {
    GstElement *pipeline;
    GstPad * mixer_pad;
    gboolean terminate;
} CustomData;


static GstPadProbeReturn
events_cb (GstPad * pad __attribute__((unused)), GstPadProbeInfo * probe_info, gpointer user_data)
{
    CustomData *data = (CustomData *) user_data;
    GstEvent *event = GST_PAD_PROBE_INFO_EVENT (probe_info);

    if (GST_EVENT_TYPE (event) == GST_EVENT_NAVIGATION) {

        gdouble x = 0, y = 0;
        // static OMG!!!!
        static gboolean clicked = FALSE;
        static gdouble clicked_x = 0, clicked_y = 0;
        static gint clicked_xpos = 0, clicked_ypos = 0;
        const gchar *key;
        gint button = 0;
        gint xpos = 0, ypos = 0;
        gint new_xpos = 0, new_ypos = 0;
        gint width = 0, height = 0;

        g_object_get(G_OBJECT(data->mixer_pad), "xpos", &xpos, "ypos", &ypos, "width", &width, "height", &height, NULL);

        switch (gst_navigation_event_get_type (event)) {
        case GST_NAVIGATION_EVENT_KEY_PRESS:

            gst_navigation_event_parse_key_event (event, &key);
            g_return_val_if_fail (key != NULL, GST_PAD_PROBE_OK);

            if (strcmp (key, "Left") == 0) {
                //g_object_set(G_OBJECT(data->mixer_pad), "xpos", xpos - 10, "ypos", ypos, NULL);
                g_object_set(G_OBJECT(data->mixer_pad), "xpos", xpos - 10, NULL);
            } else if (strcmp (key, "Right") == 0) {
                g_object_set(G_OBJECT(data->mixer_pad), "xpos", xpos + 10, NULL);
            } else if (strcmp (key, "Up") == 0) {
                g_object_set(G_OBJECT(data->mixer_pad), "ypos", ypos - 10, NULL);
            } else if (strcmp (key, "Down") == 0) {
                g_object_set(G_OBJECT(data->mixer_pad), "ypos", ypos + 10, NULL);
            } else if (strcmp (key, "plus") == 0) {
                g_object_set(G_OBJECT(data->mixer_pad), "width", width + 64, "height", height + 48, NULL);
            } else if (strcmp (key, "minus") == 0) {
                g_object_set(G_OBJECT(data->mixer_pad), "width", width - 64, "height", height - 48, NULL);
            } else if (strcmp (key, "r") == 0) {
                //DEBUG only notify if all values change????? (and implement a reset)
                if (xpos != 0)
                    g_object_set(G_OBJECT(data->mixer_pad), "xpos", 0, NULL);
                if (ypos != 0)
                    g_object_set(G_OBJECT(data->mixer_pad), "ypos", 0.0, NULL);
                if (width != WIDTH)
                    g_object_set(G_OBJECT(data->mixer_pad), "width", WIDTH, NULL);
                if (height != HEIGHT)
                    g_object_set(G_OBJECT(data->mixer_pad), "height", HEIGHT, NULL);

            }

            break;

        case GST_NAVIGATION_EVENT_MOUSE_MOVE:
            if (gst_navigation_event_parse_mouse_move_event (event, &x, &y)) {


                if (clicked) {
                    new_xpos = clicked_xpos + (x - clicked_x);
                    new_ypos = clicked_ypos + (y - clicked_y);

                    if (new_xpos != xpos)
                        g_object_set(G_OBJECT(data->mixer_pad), "xpos", new_xpos, NULL);

                    if (new_ypos != ypos)
                        g_object_set(G_OBJECT(data->mixer_pad), "ypos", new_ypos, NULL);

                }
            }
            break;
        case GST_NAVIGATION_EVENT_MOUSE_BUTTON_PRESS:
            if (gst_navigation_event_parse_mouse_button_event (event, &button, &clicked_x, &clicked_y)) {

                if (button == 1) {
                    clicked = TRUE;
                    clicked_xpos = xpos;
                    clicked_ypos = ypos;
                } else if (button == 2 || button == 3){
                    if (xpos != 0)
                        g_object_set(G_OBJECT(data->mixer_pad), "xpos", 0, NULL);
                    if (ypos != 0)
                        g_object_set(G_OBJECT(data->mixer_pad), "ypos", 0.0, NULL);
                    if (width != WIDTH)
                        g_object_set(G_OBJECT(data->mixer_pad), "width", WIDTH, NULL);
                    if (height != HEIGHT)
                        g_object_set(G_OBJECT(data->mixer_pad), "height", HEIGHT, NULL);
                } else if (button == 4 ) {
                    g_object_set(G_OBJECT(data->mixer_pad), "width", width + 64, "height", height + 48, NULL);

                    new_xpos = xpos - (clicked_x / 640) * 64;
                    new_ypos = ypos - (clicked_y / 480) * 48;

                    if (new_xpos != xpos)
                        g_object_set(G_OBJECT(data->mixer_pad), "xpos", new_xpos, NULL);

                    if (new_ypos != ypos)
                        g_object_set(G_OBJECT(data->mixer_pad), "ypos", new_ypos, NULL);

                } else if (button == 5 ) {
                    g_object_set(G_OBJECT(data->mixer_pad), "width", width - 64, "height", height - 48, NULL);

                    new_xpos = xpos + (clicked_x / 640) * 64;
                    new_ypos = ypos + (clicked_y / 480) * 48;

                    if (new_xpos != xpos)
                        g_object_set(G_OBJECT(data->mixer_pad), "xpos", new_xpos, NULL);

                    if (new_ypos != ypos)
                        g_object_set(G_OBJECT(data->mixer_pad), "ypos", new_ypos, NULL);
                }

            }
            break;
        case GST_NAVIGATION_EVENT_MOUSE_BUTTON_RELEASE:
            if (gst_navigation_event_parse_mouse_button_event (event, &button, &x, &y)) {
                if (button == 1) {
                    clicked = FALSE;
                }
            }
            break;
        default:
            break;
        }
    }

    return GST_PAD_PROBE_OK;
}

/* Forward definition of the message processing function */
static void handle_message (CustomData *data, GstMessage *msg);


int main(int argc, char *argv[]) {
    CustomData data;
    GstBus *bus;
    GstMessage *msg;
    GstStateChangeReturn ret;
    GstElement *mixer;
    GstPad * mixer_src_pad;

    data.terminate = FALSE;

    /* Initialize GStreamer */
    gst_init (&argc, &argv);

    /* Create the elements */
    data.pipeline = gst_parse_launch(
                                     "glvideomixer name=mix background=1 sink_0::xpos=0 sink_0::ypos=0 sink_0::zorder=0 sink_0::width=640 sink_0::height=480 ! glimagesinkelement "
                                     "v4l2src name=src ! video/x-raw,framerate=30/1,width=640,height=480 ! queue ! videoconvert ! mix.sink_0",
                                     //"gltestsrc pattern=mandelbrot name=src ! video/x-raw(memory:GLMemory),framerate=30/1,width=640,height=480,pixel-aspect-ratio=1/1 ! queue ! mix.sink_0",
                                     NULL);

    mixer = gst_bin_get_by_name( GST_BIN( data.pipeline), "mix");
    data.mixer_pad = gst_element_get_static_pad( mixer, "sink_0");
    mixer_src_pad =  gst_element_get_static_pad( mixer, "src");

    gst_pad_add_probe (mixer_src_pad, GST_PAD_PROBE_TYPE_EVENT_UPSTREAM, events_cb, &data, NULL);

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
