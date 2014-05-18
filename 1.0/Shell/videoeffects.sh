#!/bin/sh

# edgetv: EdgeTV effect
gst-launch-1.0 v4l2src ! videoconvert ! edgetv ! videoconvert ! autovideosink

# agingtv: AgingTV effect
gst-launch-1.0 v4l2src ! videoconvert ! agingtv ! videoconvert ! autovideosink

# dicetv: DiceTV effect
gst-launch-1.0 v4l2src ! videoconvert ! dicetv ! videoconvert ! autovideosink

# warptv: WarpTV effect
gst-launch-1.0 v4l2src ! videoconvert ! warptv ! videoconvert ! autovideosink

# shagadelictv: ShagadelicTV
gst-launch-1.0 v4l2src ! videoconvert ! shagadelictv ! videoconvert ! autovideosink

# vertigotv: VertigoTV effect
gst-launch-1.0 v4l2src ! videoconvert ! vertigotv ! videoconvert ! autovideosink

# revtv: RevTV effect
gst-launch-1.0 v4l2src ! videoconvert ! revtv ! videoconvert ! autovideosink

# quarktv: QuarkTV effect
gst-launch-1.0 v4l2src ! videoconvert ! quarktv ! videoconvert ! autovideosink

# optv: OpTV effect
gst-launch-1.0 v4l2src ! videoconvert ! optv ! videoconvert ! autovideosink

# radioactv: RadioacTV effect
gst-launch-1.0 v4l2src ! videoconvert ! radioactv ! videoconvert ! autovideosink

# streaktv: StreakTV effect
gst-launch-1.0 v4l2src ! videoconvert ! streaktv ! videoconvert ! autovideosink

# rippletv: RippleTV effect
gst-launch-1.0 v4l2src ! videoconvert ! rippletv ! videoconvert ! autovideosink

