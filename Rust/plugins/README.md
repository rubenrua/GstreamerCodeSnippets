Rubenrua Rust GStreamer plugin set
====================================

A personal set of GStreamer plugins was implemented in Rust. Plugins
are for experimenting with ideas, debugging, or maybe good ideas that
will be tried upstream.

Another objective of the repository is to maintain the history of
creating the plugin, which may not be interesting for the community
but for me.


xdgscreencapsrc
---------------

Based on https://gitlab.gnome.org/-/snippets/19


TODOS:
[x] using ashpd
[x] properties
[x] documetation
[ ] bug width cursor-mode=embedded and gtkwaylandsink
```
GST_DEBUG=2 gst-launch-1.0 -v --gst-plugin-load=target/debug/libgstxdgscreencapsrc.so  -v xdgscreencapsrc cursor-mode=embedded ! videoconvert ! identity silent=false ! gtkwaylandsink
Setting pipeline to PAUSED ...
node id: 81
size: Some((1920, 1200))
position: None
Pipeline is live and does not need PREROLL ...
...
Setting pipeline to PLAYING ...
New clock: pipewireclock0
/GstPipeline:pipeline0/GstIdentity:identity0: last-message = event   ******* (identity0:sink) E (type: segment (17934), GstEventSegment, segment=(GstSegment)"segment, flags=(GstSegmentFlags)GST_SEGMENT_FLAG_NONE, rate=(double)1, applied-rate=(double)1, format=(GstFormat)time, base=(guint64)0, offset=(guint64)0, start=(guint64)0, stop=(guint64)18446744073709551615, time=(guint64)0, position=(guint64)0, duration=(guint64)18446744073709551615;";) 0x72868c006520
/GstPipeline:pipeline0/GstIdentity:identity0: last-message = chain   ******* (identity0:sink) (9216000 bytes, dts: 0:00:00.000097011, pts: 0:00:00.000097011, duration: none, offset: 0, offset_end: -1, flags: 00004040 discont tag-memory , meta: GstVideoMeta, GstParentBufferMeta) 0x72868c00e460
Redistribute latency...
/GstPipeline:pipeline0/GstIdentity:identity0: last-message = chain   ******* (identity0:sink) (9216000 bytes, dts: 0:00:00.016764011, pts: 0:00:00.016764011, duration: none, offset: 0, offset_end: -1, flags: 00004000 tag-memory , meta: GstVideoMeta, GstParentBufferMeta) 0x72868c008360
/GstPipeline:pipeline0/GstIdentity:identity0: last-message = chain   ******* (identity0:sink) (0 bytes, dts: 0:00:00.034552011, pts: 0:00:00.034552011, duration: none, offset: 0, offset_end: -1, flags: 00004100 corrupted tag-memory , meta: GstVideoMeta, GstParentBufferMeta) 0x72868c0123d0
0:00:03.619313323 482693 0x72869c000b90 ERROR              wl_dmabuf gstwllinuxdmabuf.c:130:gst_wl_linux_dmabuf_construct_wl_buffer:<dmabufallocator0> memory does not seem to contain enough data for the specified format
0:00:03.619329744 482693 0x72869c000b90 ERROR              wl_dmabuf gstwllinuxdmabuf.c:166:gst_wl_linux_dmabuf_construct_wl_buffer:<dmabufallocator0> can't create linux-dmabuf buffer
/GstPipeline:pipeline0/GstIdentity:identity0: last-message = chain   ******* (identity0:sink) (9216000 bytes, dts: 0:00:00.051218011, pts: 0:00:00.051218011, duration: none, offset: 0, offset_end: -1, flags: 00004000 tag-memory , meta: GstVideoMeta, GstParentBufferMeta) 0x72868c012ae0
0:00:03.620697677 482693 0x5b4281f40b70 ERROR              wldisplay gstwldisplay.c:330:gst_wl_display_thread_run: Error communicating with the wayland server
Gdk-Message: 19:57:44.683: Error reading events from display: Protocol error
```


UPSTREAM MR: https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/merge_requests/1405
