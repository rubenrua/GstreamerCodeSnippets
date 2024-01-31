// Copyright (C) 2023 Ruben Gonzalez <rgonzalez@fluendo.com
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// <https://mozilla.org/MPL/2.0/>.
//
// SPDX-License-Identifier: MPL-2.0

/**
 * element-xdgscreencapsrc:
 *
 * TODO
 * {{ utils/xdgscreencapsrc/README.md[2:30] }}
 *
 */
use gst::glib;
use gst::prelude::*;
use gst::subclass::prelude::*;

use ashpd::{
    desktop::screencast::{CursorMode, PersistMode, Screencast, SourceType},
    WindowIdentifier,
};

use gst::glib::once_cell::sync::Lazy;
use parking_lot::Mutex;

pub fn block_on<F: std::future::Future>(future: F) -> F::Output {
    static TOKIO_RT: once_cell::sync::Lazy<tokio::runtime::Runtime> =
        once_cell::sync::Lazy::new(|| {
            tokio::runtime::Builder::new_current_thread()
                .enable_io()
                .enable_time()
                .build()
                .expect("launch of single-threaded tokio runtime")
        });
    TOKIO_RT.block_on(future)
}

async fn portal_main() -> ashpd::Result<(String, String)> {
    let proxy = Screencast::new().await?;
    let session = proxy.create_session().await?;
    proxy
        .select_sources(
            &session,
            CursorMode::Metadata,
            SourceType::Monitor | SourceType::Window,
            true,
            None,
            PersistMode::DoNot,
        )
        .await?;

    let response = proxy
        .start(&session, &WindowIdentifier::default())
        .await?
        .response()?;

    if let Some(first_value) = response.streams().iter().next() {
        let id = first_value.pipe_wire_node_id();
        println!("node id: {}", id);
        println!("size: {:?}", first_value.size());
        println!("position: {:?}", first_value.position());
        Ok((format!("{id}"), format!("{id}")))
    } else {
        Err(ashpd::Error::NoResponse)
    }
}

const DEFAULT_RECORD: bool = false;
const DEFAULT_LIVE: bool = false;

#[derive(Debug, Clone, Copy)]
struct Settings {
    record: bool,
    live: bool,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            record: DEFAULT_RECORD,
            live: DEFAULT_LIVE,
        }
    }
}

pub struct XdpScreenCast {
    settings: Mutex<Settings>,
    src: gst::Element,
    srcpad: gst::GhostPad,
}

static CAT: Lazy<gst::DebugCategory> = Lazy::new(|| {
    gst::DebugCategory::new(
        "xdgscreencapsrc",
        gst::DebugColorFlags::empty(),
        Some("XDP Screen Cast Bin"),
    )
});

impl XdpScreenCast {}

#[glib::object_subclass]
impl ObjectSubclass for XdpScreenCast {
    const NAME: &'static str = "GstXdpScreenCast";
    type Type = super::XdpScreenCast;
    type ParentType = gst::Bin;

    fn with_class(klass: &Self::Class) -> Self {
        let settings = Mutex::new(Settings::default());
        let src = gst::ElementFactory::make("pipewiresrc").build().unwrap();
        let templ = klass.pad_template("src").unwrap();
        let srcpad = gst::GhostPad::from_template(&templ);

        Self {
            settings,
            src,
            srcpad,
        }
    }
}

impl ObjectImpl for XdpScreenCast {
    // TODO fix properties
    fn properties() -> &'static [glib::ParamSpec] {
        static PROPERTIES: Lazy<Vec<glib::ParamSpec>> = Lazy::new(|| {
            vec![
                glib::ParamSpecBoolean::builder("record")
                    .nick("Record")
                    .blurb("Enable/disable recording")
                    .default_value(DEFAULT_RECORD)
                    .mutable_playing()
                    .build(),
                glib::ParamSpecBoolean::builder("recording")
                    .nick("Recording")
                    .blurb("Whether recording is currently taking place")
                    .default_value(DEFAULT_RECORD)
                    .read_only()
                    .build(),
                glib::ParamSpecBoolean::builder("is-live")
                    .nick("Live output mode")
                    .blurb(
                        "Live output mode: no \"gap eating\", \
                        forward incoming segment for live input, \
                        create a gap to fill the paused duration for non-live input",
                    )
                    .default_value(DEFAULT_LIVE)
                    .mutable_ready()
                    .build(),
            ]
        });

        PROPERTIES.as_ref()
    }

    fn set_property(&self, _id: usize, value: &glib::Value, pspec: &glib::ParamSpec) {
        match pspec.name() {
            "record" => {
                let mut settings = self.settings.lock();
                let record = value.get().expect("type checked upstream");
                gst::debug!(
                    CAT,
                    imp: self,
                    "Setting record from {:?} to {:?}",
                    settings.record,
                    record
                );

                settings.record = record;
            }
            "is-live" => {
                let mut settings = self.settings.lock();
                let live = value.get().expect("type checked upstream");
                gst::debug!(
                    CAT,
                    imp: self,
                    "Setting live from {:?} to {:?}",
                    settings.live,
                    live
                );

                settings.live = live;
            }
            _ => unimplemented!(),
        }
    }

    fn property(&self, _id: usize, pspec: &glib::ParamSpec) -> glib::Value {
        match pspec.name() {
            "record" => {
                let settings = self.settings.lock();
                settings.record.to_value()
            }
            "recording" => (true).to_value(),
            "is-live" => {
                let settings = self.settings.lock();
                settings.live.to_value()
            }
            _ => unimplemented!(),
        }
    }

    fn constructed(&self) {
        self.parent_constructed();

        let obj = self.obj();

        obj.add(&self.src).unwrap();
        self.srcpad
            .set_target(Some(&self.src.static_pad("src").unwrap()))
            .unwrap();

        obj.add_pad(&self.srcpad).unwrap();
    }
}

impl GstObjectImpl for XdpScreenCast {}

impl ElementImpl for XdpScreenCast {
    fn metadata() -> Option<&'static gst::subclass::ElementMetadata> {
        static ELEMENT_METADATA: Lazy<gst::subclass::ElementMetadata> = Lazy::new(|| {
            gst::subclass::ElementMetadata::new(
                "xdg-desktop-portal screen capture",
                "Generic",
                "Source element wrapping pipewiresrc using \
                xdg-desktop-portal to start a screencast session.",
                "Ruben Gonzalez <rgonzalez@fluendo.com>",
            )
        });

        Some(&*ELEMENT_METADATA)
    }

    fn pad_templates() -> &'static [gst::PadTemplate] {
        static PAD_TEMPLATES: Lazy<Vec<gst::PadTemplate>> = Lazy::new(|| {
            let caps = gst::Caps::new_any();
            let src_pad_template = gst::PadTemplate::new(
                "src",
                gst::PadDirection::Src,
                gst::PadPresence::Always,
                &caps,
            )
            .unwrap();

            vec![src_pad_template]
        });

        PAD_TEMPLATES.as_ref()
    }

    fn change_state(
        &self,
        transition: gst::StateChange,
    ) -> Result<gst::StateChangeSuccess, gst::StateChangeError> {
        gst::debug!(CAT, imp: self, "Changing state {:?}", transition);

        let success = self.parent_change_state(transition)?;

        if transition == gst::StateChange::NullToReady {
            let (fd, path) = block_on(portal_main()).unwrap();
            self.src.set_property("fd", fd.parse::<i32>().unwrap());
            self.src.set_property("path", path);
        }

        Ok(success)
    }
}

impl BinImpl for XdpScreenCast {}
