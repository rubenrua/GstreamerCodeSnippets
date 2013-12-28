#!/bin/sh

# edgetv: EdgeTV effect
gst-launch v4l2src ! ffmpegcolorspace ! edgetv ! ffmpegcolorspace ! autovideosink

# agingtv: AgingTV effect
gst-launch v4l2src ! ffmpegcolorspace ! agingtv ! ffmpegcolorspace ! autovideosink

# dicetv: DiceTV effect
gst-launch v4l2src ! ffmpegcolorspace ! dicetv ! ffmpegcolorspace ! autovideosink

# warptv: WarpTV effect
gst-launch v4l2src ! ffmpegcolorspace ! warptv ! ffmpegcolorspace ! autovideosink

# shagadelictv: ShagadelicTV
gst-launch v4l2src ! ffmpegcolorspace ! shagadelictv ! ffmpegcolorspace ! autovideosink

# vertigotv: VertigoTV effect
gst-launch v4l2src ! ffmpegcolorspace ! vertigotv ! ffmpegcolorspace ! autovideosink

# revtv: RevTV effect
gst-launch v4l2src ! ffmpegcolorspace ! revtv ! ffmpegcolorspace ! autovideosink

# quarktv: QuarkTV effect
gst-launch v4l2src ! ffmpegcolorspace ! quarktv ! ffmpegcolorspace ! autovideosink

# optv: OpTV effect
gst-launch v4l2src ! ffmpegcolorspace ! optv ! ffmpegcolorspace ! autovideosink

# radioactv: RadioacTV effect
gst-launch v4l2src ! ffmpegcolorspace ! radioactv ! ffmpegcolorspace ! autovideosink

# streaktv: StreakTV effect
gst-launch v4l2src ! ffmpegcolorspace ! streaktv ! ffmpegcolorspace ! autovideosink

# rippletv: RippleTV effect
gst-launch v4l2src ! ffmpegcolorspace ! rippletv ! ffmpegcolorspace ! autovideosink

