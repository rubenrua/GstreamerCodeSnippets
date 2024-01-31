// Copyright (C) 2023 Ruben Gonzalez <rgonzalez@fluendo.com
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// <https://mozilla.org/MPL/2.0/>.
//
// SPDX-License-Identifier: MPL-2.0
/**
 * element-xdgscreencapsrc:
 * @short_description: Source element wrapping pipewiresrc using xdg-desktop-portal to start a screencast session.
 *
 * Based on https://gitlab.gnome.org/-/snippets/19 using https://crates.io/crates/ashpd
 *
 * ## Example pipeline
 * ```bash
 * gst-launch-1.0 -v xdgscreencapsrc ! videoconvert ! identity silent=false ! gtkwaylandsink
 * ```
 *
 * Since: plugins-rs-0.12.0
 */
use gst::glib;
use gst::prelude::*;
use gst::subclass::prelude::*;

use ashpd::{
    desktop::screencast::{PersistMode, Screencast},
    WindowIdentifier,
};

#[derive(Debug, Eq, PartialEq, Ord, PartialOrd, Hash, Clone, Copy, glib::Enum)]
#[repr(u32)]
#[enum_type(name = "SourceType")]
pub enum SourceType {
    #[enum_value(name = "A monitor", nick = "monitor")]
    Monitor,
    #[enum_value(name = "A specific window", nick = "window")]
    Window,
    #[enum_value(name = "Virtual", nick = "virtual")]
    Virtual,
    #[enum_value(name = "monitor+window+virtual", nick = "all")]
    All,
}

impl From<SourceType> for ashpd::enumflags2::BitFlags<ashpd::desktop::screencast::SourceType, u32> {
    fn from(v: SourceType) -> Self {
        use ashpd::desktop::screencast;

        match v {
            SourceType::Monitor => screencast::SourceType::Monitor.into(),
            SourceType::Window => screencast::SourceType::Window.into(),
            SourceType::Virtual => screencast::SourceType::Virtual.into(),
            SourceType::All => {
                screencast::SourceType::Monitor
                    | screencast::SourceType::Window
                    | screencast::SourceType::Virtual
            }
        }
    }
}

#[derive(Debug, Eq, PartialEq, Ord, PartialOrd, Hash, Clone, Copy, glib::Enum)]
#[repr(u32)]
#[enum_type(name = "CursorMode")]
pub enum CursorMode {
    #[enum_value(
        name = "The cursor is not part of the screen cast stream",
        nick = "hidden"
    )]
    Hidden,
    #[enum_value(
        name = "The cursor is embedded as part of the stream buffers",
        nick = "embedded"
    )]
    Embedded,
    #[enum_value(
        name = "The cursor is not part of the screen cast stream, but sent as PipeWire stream metadata. Not implemented",
        nick = "metadata"
    )]
    Metadata,
}

impl From<CursorMode> for ashpd::desktop::screencast::CursorMode {
    fn from(v: CursorMode) -> Self {
        use ashpd::desktop::screencast;

        match v {
            CursorMode::Hidden => screencast::CursorMode::Hidden,
            CursorMode::Embedded => screencast::CursorMode::Embedded,
            CursorMode::Metadata => unimplemented!(),
        }
    }
}

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

async fn portal_main(
    cursor_mode: CursorMode,
    source_type: SourceType,
) -> ashpd::Result<(String, String)> {
    let proxy = Screencast::new().await?;
    let session = proxy.create_session().await?;
    proxy
        .select_sources(
            &session,
            cursor_mode.into(),
            source_type.into(),
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

const DEFAULT_CURSOR_MODE: CursorMode = CursorMode::Hidden;
const DEFAULT_SOURCE_TYPE: SourceType = SourceType::All;

#[derive(Debug, Clone, Copy)]
struct Settings {
    cursor_mode: CursorMode,
    source_type: SourceType,
}

impl Default for Settings {
    fn default() -> Self {
        Settings {
            cursor_mode: DEFAULT_CURSOR_MODE,
            source_type: DEFAULT_SOURCE_TYPE,
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
    // based on https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html#org-freedesktop-portal-screencast-selectsources
    fn properties() -> &'static [glib::ParamSpec] {
        static PROPERTIES: Lazy<Vec<glib::ParamSpec>> = Lazy::new(|| {
            vec![
                glib::ParamSpecEnum::builder_with_default::<CursorMode>(
                    "cursor-mode",
                    DEFAULT_CURSOR_MODE,
                )
                .nick("cursor mode")
                .blurb("Determines how the cursor will be drawn in the screen cast stream")
                .mutable_ready()
                .build(),
                glib::ParamSpecEnum::builder_with_default::<SourceType>(
                    "source-type",
                    DEFAULT_SOURCE_TYPE,
                )
                .nick("source type")
                .blurb("Sets the types of content to record")
                .mutable_ready()
                .build(),
            ]
        });

        PROPERTIES.as_ref()
    }

    fn set_property(&self, _id: usize, value: &glib::Value, pspec: &glib::ParamSpec) {
        match pspec.name() {
            "cursor-mode" => {
                let mut settings = self.settings.lock();
                let cursor_mode = value.get().expect("type checked upstream");
                gst::debug!(
                    CAT,
                    imp: self,
                    "Setting cursor-mode from {:?} to {:?}",
                    settings.cursor_mode,
                    cursor_mode
                );

                settings.cursor_mode = cursor_mode;
            }
            "source-type" => {
                let mut settings = self.settings.lock();
                let source_type = value.get().expect("type checked upstream");
                gst::debug!(
                    CAT,
                    imp: self,
                    "Setting source-type from {:?} to {:?}",
                    settings.source_type,
                    source_type
                );

                settings.source_type = source_type;
            }
            _ => unimplemented!(),
        }
    }

    fn property(&self, _id: usize, pspec: &glib::ParamSpec) -> glib::Value {
        match pspec.name() {
            "cursor-mode" => {
                let settings = self.settings.lock();
                settings.cursor_mode.to_value()
            }
            "source-type" => {
                let settings = self.settings.lock();
                settings.source_type.to_value()
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

        let settings = self.settings.lock();

        let success = self.parent_change_state(transition)?;

        if transition == gst::StateChange::NullToReady {
            let (fd, path) =
                block_on(portal_main(settings.cursor_mode, settings.source_type)).unwrap();
            self.src.set_property("fd", fd.parse::<i32>().unwrap());
            self.src.set_property("path", path);
        }

        Ok(success)
    }
}

impl BinImpl for XdpScreenCast {}
