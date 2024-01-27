#!/bin/bash

set -eux

cargo build -p gst-plugin-xdgscreencapsrc
GST_DEBUG=2 gst-launch-1.0 -v --gst-plugin-load=target/debug/libgstxdgscreencapsrc.so  -v xdgscreencapsrc ! videoconvert ! identity silent=false ! gtkwaylandsink
