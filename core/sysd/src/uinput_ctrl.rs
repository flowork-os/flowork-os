// [FL_INDEX: global_uinput_singleton, oncelock, persistent_virtual_device, rust_uinput, uinput_ctrl | COT: Provide persistent global singleton for Virtual UInput device so kernel registration is permanent.| AT: 2026-11-01T16:30:57Z]
// =============================================================================
// 🚀 Flowork Sovereign OS — Virtual Hardware HID Controller via /dev/uinput
// Pure Rust | Kernel evdev Event Injection | 100% Anti-Bot Immunity
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================

use std::fs::{File, OpenOptions};
use std::os::unix::fs::OpenOptionsExt;
use std::os::unix::io::AsRawFd;
use std::sync::{Arc, Mutex};
use serde::{Deserialize, Serialize};

// Linux uinput & input subsystem constants
const EV_SYN: u16 = 0x00;
const EV_KEY: u16 = 0x01;
const EV_REL: u16 = 0x02;

const SYN_REPORT: u16 = 0;
const REL_X: u16 = 0x00;
const REL_Y: u16 = 0x01;
const REL_WHEEL: u16 = 0x08;

const BTN_LEFT: u16 = 0x110;
const BTN_RIGHT: u16 = 0x111;
const BTN_MIDDLE: u16 = 0x112;

// ioctls for x86_64
const UI_SET_EVBIT: libc::c_ulong = 0x40045564;
const UI_SET_KEYBIT: libc::c_ulong = 0x40045565;
const UI_SET_RELBIT: libc::c_ulong = 0x40045566;
const UI_DEV_CREATE: libc::c_ulong = 0x5501;
const UI_DEV_DESTROY: libc::c_ulong = 0x5502;

#[repr(C)]
struct input_id {
    bustype: u16,
    vendor: u16,
    product: u16,
    version: u16,
}

#[repr(C)]
struct uinput_user_dev {
    name: [libc::c_char; 80],
    id: input_id,
    ff_effects_max: u32,
    absmax: [i32; 64],
    absmin: [i32; 64],
    absfuzz: [i32; 64],
    absflat: [i32; 64],
}

#[repr(C)]
struct input_event {
    time: libc::timeval,
    type_: u16,
    code: u16,
    value: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputStatus {
    pub backend: String,
    pub uinput_available: bool,
    pub device_name: String,
    pub vendor_id: String,
    pub bot_detection_immune: bool,
}

pub struct UInputController {
    file: Option<File>,
    device_created: bool,
}

impl UInputController {
    pub fn new() -> Self {
        let mut ctrl = Self {
            file: None,
            device_created: false,
        };
        let _ = ctrl.init();
        ctrl
    }

    pub fn init(&mut self) -> Result<(), String> {
        // Attempt to open /dev/uinput in non-blocking read/write mode
        let file = match OpenOptions::new()
            .read(true)
            .write(true)
            .custom_flags(libc::O_NONBLOCK)
            .open("/dev/uinput")
        {
            Ok(f) => f,
            Err(e) => {
                return Err(format!("/dev/uinput not accessible ({})", e));
            }
        };

        let fd = file.as_raw_fd();

        unsafe {
            // Enable EV_SYN, EV_KEY, EV_REL
            if libc::ioctl(fd, UI_SET_EVBIT, EV_SYN as libc::c_int) < 0
                || libc::ioctl(fd, UI_SET_EVBIT, EV_KEY as libc::c_int) < 0
                || libc::ioctl(fd, UI_SET_EVBIT, EV_REL as libc::c_int) < 0
            {
                return Err("Failed to set event bits on uinput".to_string());
            }

            // Register Mouse Buttons
            libc::ioctl(fd, UI_SET_KEYBIT, BTN_LEFT as libc::c_int);
            libc::ioctl(fd, UI_SET_KEYBIT, BTN_RIGHT as libc::c_int);
            libc::ioctl(fd, UI_SET_KEYBIT, BTN_MIDDLE as libc::c_int);

            // Register Standard Relative Axes
            libc::ioctl(fd, UI_SET_RELBIT, REL_X as libc::c_int);
            libc::ioctl(fd, UI_SET_RELBIT, REL_Y as libc::c_int);
            libc::ioctl(fd, UI_SET_RELBIT, REL_WHEEL as libc::c_int);

            // Register Keyboard Keys (1 to 255)
            for key in 1..256 {
                libc::ioctl(fd, UI_SET_KEYBIT, key as libc::c_int);
            }

            // Setup device metadata
            let mut dev: uinput_user_dev = std::mem::zeroed();
            let dev_name = "Flowork Sovereign Physical Input Controller\0";
            for (i, b) in dev_name.bytes().enumerate() {
                if i < 80 {
                    dev.name[i] = b as libc::c_char;
                }
            }
            dev.id.bustype = 0x03; // BUS_USB
            dev.id.vendor = 0x1234; // Sovereign Vendor ID
            dev.id.product = 0x5678; // Sovereign Product ID
            dev.id.version = 1;

            let dev_bytes = std::slice::from_raw_parts(
                &dev as *const _ as *const u8,
                std::mem::size_of::<uinput_user_dev>(),
            );

            if libc::write(fd, dev_bytes.as_ptr() as *const _, dev_bytes.len()) < 0 {
                return Err("Failed to write uinput_user_dev".to_string());
            }

            if libc::ioctl(fd, UI_DEV_CREATE) < 0 {
                return Err("Failed to create uinput device".to_string());
            }
        }

        self.file = Some(file);
        self.device_created = true;
        println!("  [flowork-sysd] 🔌 Virtual USB Hardware Input Device active via /dev/uinput");
        Ok(())
    }

    pub fn is_available(&self) -> bool {
        self.device_created && self.file.is_some()
    }

    pub fn send_event(&self, type_: u16, code: u16, value: i32) -> Result<(), String> {
        let file = self.file.as_ref().ok_or("uinput device not initialized")?;
        let fd = file.as_raw_fd();

        unsafe {
            let mut ev: input_event = std::mem::zeroed();
            libc::gettimeofday(&mut ev.time, std::ptr::null_mut());
            ev.type_ = type_;
            ev.code = code;
            ev.value = value;

            let ev_bytes = std::slice::from_raw_parts(
                &ev as *const _ as *const u8,
                std::mem::size_of::<input_event>(),
            );

            if libc::write(fd, ev_bytes.as_ptr() as *const _, ev_bytes.len()) < 0 {
                return Err("Failed to write input_event".to_string());
            }
        }
        Ok(())
    }

    pub fn sync_report(&self) -> Result<(), String> {
        self.send_event(EV_SYN, SYN_REPORT, 0)
    }

    pub fn mouse_move_relative(&self, dx: i32, dy: i32) -> Result<(), String> {
        if dx != 0 {
            self.send_event(EV_REL, REL_X, dx)?;
        }
        if dy != 0 {
            self.send_event(EV_REL, REL_Y, dy)?;
        }
        self.sync_report()
    }

    pub fn mouse_click(&self, button: &str) -> Result<(), String> {
        let code = match button {
            "right" => BTN_RIGHT,
            "middle" => BTN_MIDDLE,
            _ => BTN_LEFT,
        };
        // Press
        self.send_event(EV_KEY, code, 1)?;
        self.sync_report()?;
        std::thread::sleep(std::time::Duration::from_millis(20));
        // Release
        self.send_event(EV_KEY, code, 0)?;
        self.sync_report()
    }

    pub fn key_press(&self, code: u16) -> Result<(), String> {
        self.send_event(EV_KEY, code, 1)?;
        self.sync_report()?;
        std::thread::sleep(std::time::Duration::from_millis(15));
        self.send_event(EV_KEY, code, 0)?;
        self.sync_report()
    }

    pub fn get_status(&self) -> InputStatus {
        if self.is_available() {
            InputStatus {
                backend: "kernel_uinput".to_string(),
                uinput_available: true,
                device_name: "Flowork Sovereign Physical Input Controller".to_string(),
                vendor_id: "0x1234:0x5678 (Virtual USB HID)".to_string(),
                bot_detection_immune: true,
            }
        } else {
            InputStatus {
                backend: "x11_xtest_hybrid_fallback".to_string(),
                uinput_available: false,
                device_name: "Standard X11 Display Server".to_string(),
                vendor_id: "DISPLAY=:0".to_string(),
                bot_detection_immune: false,
            }
        }
    }
}

impl Drop for UInputController {
    fn drop(&mut self) {
        if self.device_created {
            if let Some(ref file) = self.file {
                let fd = file.as_raw_fd();
                unsafe {
                    libc::ioctl(fd, UI_DEV_DESTROY);
                }
            }
        }
    }
}

pub type SharedUInput = Arc<Mutex<UInputController>>;

static GLOBAL_UINPUT: std::sync::OnceLock<SharedUInput> = std::sync::OnceLock::new();

pub fn get_global_uinput() -> SharedUInput {
    GLOBAL_UINPUT.get_or_init(|| {
        Arc::new(Mutex::new(UInputController::new()))
    }).clone()
}

