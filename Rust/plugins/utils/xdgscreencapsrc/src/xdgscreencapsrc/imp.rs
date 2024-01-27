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

use std::collections::HashMap;
use std::error::Error;
use std::sync::Arc;

use zbus::{
    blocking::Connection, dbus_proxy, zvariant::Array, zvariant::ObjectPath, zvariant::Value,
};

use gst::glib::once_cell::sync::Lazy;
use parking_lot::Mutex;

#[dbus_proxy(
    interface = "org.freedesktop.portal.ScreenCast",
    default_service = "org.freedesktop.portal.Desktop",
    default_path = "/org/freedesktop/portal/desktop",
    gen_blocking = true,
    gen_async = false
)]
trait ScreenCast {
    /// CreateSession method
    fn create_session(
        &self,
        options: HashMap<&str, zbus::zvariant::Value<'_>>,
    ) -> zbus::Result<zbus::zvariant::OwnedObjectPath>;

    /// SelectSources method
    fn select_sources(
        &self,
        session_handle: &ObjectPath<'_>,
        options: HashMap<&str, zbus::zvariant::Value<'_>>,
    ) -> zbus::Result<zbus::zvariant::OwnedObjectPath>;

    /// Start method
    fn start(
        &self,
        session_handle: &ObjectPath<'_>,
        parent_window: &str,
        options: HashMap<&str, zbus::zvariant::Value<'_>>,
    ) -> zbus::Result<zbus::zvariant::OwnedObjectPath>;

    /// OpenPipeWireRemote method
    fn open_pipe_wire_remote(
        &self,
        session_handle: &ObjectPath<'_>,
        options: HashMap<&str, zbus::zvariant::Value<'_>>,
    ) -> zbus::Result<zbus::zvariant::OwnedFd>;

    /// AvailableCursorModes property
    #[dbus_proxy(property)]
    fn available_cursor_modes(&self) -> zbus::Result<u32>;

    /// AvailableSourceTypes property
    #[dbus_proxy(property)]
    fn available_source_types(&self) -> zbus::Result<u32>;

    /// version property
    #[dbus_proxy(property, name = "version")]
    fn version(&self) -> zbus::Result<u32>;
}

fn call_portal(
    connection: &Connection,
    name: &str,
    token: &str,
    f: impl Fn(),
) -> zbus::Result<Arc<zbus::Message>> {
    let path = format!("/org/freedesktop/portal/desktop/request/{name}/{token}");
    let proxy2: zbus::blocking::Proxy = zbus::blocking::ProxyBuilder::new_bare(connection)
        .interface("org.freedesktop.portal.Request")?
        .path(path)?
        .destination("org.freedesktop.portal.Desktop")?
        .build()?;
    let mut request = proxy2.receive_signal("Response")?;

    f();
    let message = request.next();

    Ok(message.unwrap())
}

fn portal_main() -> Result<(String, String), Box<dyn Error>> {
    let connection = Connection::session()?;

    let name = connection
        .unique_name()
        .ok_or("error")?
        .replace(':', "")
        .replace('.', "_");
    println!("unique name: {name}");

    let proxy = ScreenCastProxy::new(&connection)?;

    let token = "u1";
    let f = || {
        let mut options = HashMap::new();
        options.insert("session_handle_token", token.into());
        options.insert("handle_token", token.into());
        proxy.create_session(options).unwrap();
    };
    let message = call_portal(&connection, &name, token, f)?;

    let body: (u32, HashMap<&str, zbus::zvariant::Value<'_>>) = message.body().unwrap();
    let v = &body.1["session_handle"];
    let session = ObjectPath::try_from(String::try_from(v).unwrap()).unwrap();

    let token = "u2";
    let f = || {
        let mut options = HashMap::new();
        options.insert("multiple", false.into());
        options.insert("types", 3u32.into()); // dbus.UInt32(1|2)
        options.insert("handle_token", token.into());
        proxy.select_sources(&session, options).unwrap();
    };
    let message = call_portal(&connection, &name, token, f)?;
    let _body: (u32, HashMap<&str, zbus::zvariant::Value<'_>>) = message.body().unwrap();

    let token = "u3";
    let f = || {
        let mut options = HashMap::new();
        options.insert("handle_token", token.into());
        proxy.start(&session, "", options).unwrap();
    };
    let message = call_portal(&connection, &name, token, f)?;
    let body: (u32, HashMap<&str, zbus::zvariant::Value<'_>>) = message.body().unwrap();

    if body.0 != 0 {
        return Err("No stream selected".into());
    }

    let v = &body.1["streams"];
    let av = <Array<'_>>::try_from(v).unwrap();
    let av = <Vec<Value<'_>>>::try_from(av).unwrap();
    for v in av {
        let vv = <(Value<'_>, Value<'_>)>::try_from(v).unwrap();
        let vv = u32::try_from(vv.0).unwrap();

        //# 4 open_pipe_wire_remote
        let options = HashMap::new();
        let fd = proxy.open_pipe_wire_remote(&session, options)?;
        let fdstr = format!("{}", fd); // TODO OwnedFd as gst property

        return Ok((fdstr, vv.to_string()));
    }

    Err("No path".into())
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

        match transition {
            gst::StateChange::NullToReady => {
                let (fd, path) = portal_main().unwrap();
                gst::debug!(CAT, imp: self, "xdg-desktop-portal values: fd={:?} path={:?}", fd, path);
                self.src.set_property("fd", fd.parse::<i32>().unwrap());
                self.src.set_property("path", path);
            }
            _ => (),
        }

        Ok(success)
    }
}

impl BinImpl for XdpScreenCast {}
