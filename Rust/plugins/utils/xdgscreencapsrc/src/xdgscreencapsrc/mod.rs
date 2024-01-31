// Copyright (C) 2023 Ruben Gonzalez <rgonzalez@fluendo.com
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// <https://mozilla.org/MPL/2.0/>.
//
// SPDX-License-Identifier: MPL-2.0

use gst::glib;
use gst::prelude::*;

mod imp;

glib::wrapper! {
    pub struct XdpScreenCast(ObjectSubclass<imp::XdpScreenCast>) @extends gst::Bin, gst::Element, gst::Object;
}

pub fn register(plugin: &gst::Plugin) -> Result<(), glib::BoolError> {
    gst::Element::register(
        Some(plugin),
        "xdgscreencapsrc",
        gst::Rank::NONE,
        XdpScreenCast::static_type(),
    )
}
