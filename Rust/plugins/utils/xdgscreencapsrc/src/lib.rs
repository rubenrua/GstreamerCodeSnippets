// Copyright (C) 2023 Ruben Gonzalez <rgonzalez@fluendo.com
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// <https://mozilla.org/MPL/2.0/>.
//
// SPDX-License-Identifier: MPL-2.0
#![allow(clippy::non_send_fields_in_send_ty, unused_doc_comments)]

/**
 * plugin-xdgscreencapsrc:
 *
 * Since: plugins-rs-0.12.0
 */
use gst::glib;

mod xdgscreencapsrc;

fn plugin_init(plugin: &gst::Plugin) -> Result<(), glib::BoolError> {
    xdgscreencapsrc::register(plugin)
}

gst::plugin_define!(
    xdgscreencapsrc,
    env!("CARGO_PKG_DESCRIPTION"),
    plugin_init,
    concat!(env!("CARGO_PKG_VERSION"), "-", "COMMIT_ID"),
    // FIXME: MPL-2.0 is only allowed since 1.18.3 (as unknown) and 1.20 (as known)
    "MPL",
    env!("CARGO_PKG_NAME"),
    env!("CARGO_PKG_NAME"),
    env!("CARGO_PKG_REPOSITORY"),
    env!("BUILD_REL_DATE")
);
