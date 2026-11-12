// =============================================================================
// 🚀 Flowork Sovereign OS — Landlock LSM & cgroups v2 Kernel Sandboxing
// Pure Rust | In-Kernel Unprivileged VFS Jailing | Subagent Resource Capping
// Co-authored-by: Flowork OS <agent@floworkos.com>
// =============================================================================

use std::fs;
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;
use serde::{Deserialize, Serialize};

// x86_64 Landlock Syscall Numbers
const SYS_LANDLOCK_CREATE_RULESET: libc::c_long = 444;
const SYS_LANDLOCK_ADD_RULE: libc::c_long = 445;
const SYS_LANDLOCK_RESTRICT_SELF: libc::c_long = 446;

const LANDLOCK_CREATE_RULESET_VERSION: u32 = 1 << 0;

// Landlock Rule Types
const LANDLOCK_RULE_PATH_BENEATH: u32 = 1;

// Access FS bit flags
pub const ACCESS_FS_EXECUTE: u64 = 1 << 0;
pub const ACCESS_FS_WRITE_FILE: u64 = 1 << 1;
pub const ACCESS_FS_READ_FILE: u64 = 1 << 2;
pub const ACCESS_FS_READ_DIR: u64 = 1 << 3;
pub const ACCESS_FS_REMOVE_DIR: u64 = 1 << 4;
pub const ACCESS_FS_REMOVE_FILE: u64 = 1 << 5;
pub const ACCESS_FS_MAKE_CHAR: u64 = 1 << 6;
pub const ACCESS_FS_MAKE_DIR: u64 = 1 << 7;
pub const ACCESS_FS_MAKE_REG: u64 = 1 << 8;
pub const ACCESS_FS_MAKE_SOCK: u64 = 1 << 9;
pub const ACCESS_FS_MAKE_FIFO: u64 = 1 << 10;
pub const ACCESS_FS_MAKE_BLOCK: u64 = 1 << 11;
pub const ACCESS_FS_MAKE_SYM: u64 = 1 << 12;
pub const ACCESS_FS_REFER: u64 = 1 << 13;
pub const ACCESS_FS_TRUNCATE: u64 = 1 << 14;

#[repr(C)]
struct landlock_ruleset_attr {
    handled_access_fs: u64,
}

#[repr(C)]
struct landlock_path_beneath_attr {
    allowed_access: u64,
    parent_fd: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxStatus {
    pub landlock_supported: bool,
    pub landlock_abi_version: i64,
    pub cgroups_v2_active: bool,
    pub user_slice_writable: bool,
    pub default_jailed_root: String,
}

pub struct LandlockSandbox;

impl LandlockSandbox {
    pub fn get_abi_version() -> i64 {
        unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                std::ptr::null::<landlock_ruleset_attr>(),
                0,
                LANDLOCK_CREATE_RULESET_VERSION,
            ) as i64
        }
    }

    pub fn get_status() -> SandboxStatus {
        let abi = Self::get_abi_version();
        let cgroups_active = Path::new("/sys/fs/cgroup/cgroup.controllers").exists();
        let user_slice = Path::new("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice");
        let user_slice_writable = user_slice.exists() && {
            match fs::OpenOptions::new().write(true).open(user_slice.join("cgroup.procs")) {
                Ok(_) => true,
                Err(_) => false,
            }
        };

        SandboxStatus {
            landlock_supported: abi > 0,
            landlock_abi_version: abi,
            cgroups_v2_active: cgroups_active,
            user_slice_writable,
            default_jailed_root: {
                let home_dir = std::env::var("HOME").unwrap_or_else(|_| "/opt".to_string());
                if std::path::Path::new(&format!("{}/floworkos", home_dir)).exists() {
                    format!("{}/floworkos", home_dir)
                } else {
                    "/opt/floworkos".to_string()
                }
            },
        }
    }

    pub fn supported_fs_mask() -> u64 {
        let abi = Self::get_abi_version();
        let mut mask = ACCESS_FS_EXECUTE
            | ACCESS_FS_WRITE_FILE
            | ACCESS_FS_READ_FILE
            | ACCESS_FS_READ_DIR
            | ACCESS_FS_REMOVE_DIR
            | ACCESS_FS_REMOVE_FILE
            | ACCESS_FS_MAKE_CHAR
            | ACCESS_FS_MAKE_DIR
            | ACCESS_FS_MAKE_REG
            | ACCESS_FS_MAKE_SOCK
            | ACCESS_FS_MAKE_FIFO
            | ACCESS_FS_MAKE_BLOCK
            | ACCESS_FS_MAKE_SYM;
        if abi >= 2 {
            mask |= ACCESS_FS_REFER;
        }
        if abi >= 3 {
            mask |= ACCESS_FS_TRUNCATE;
        }
        mask
    }

    pub fn create_sovereign_ruleset(
        read_only_paths: &[&str],
        read_write_paths: &[&str],
    ) -> Result<i32, String> {
        let full_access = Self::supported_fs_mask();

        let attr = landlock_ruleset_attr {
            handled_access_fs: full_access,
        };

        let ruleset_fd = unsafe {
            libc::syscall(
                SYS_LANDLOCK_CREATE_RULESET,
                &attr as *const _,
                std::mem::size_of::<landlock_ruleset_attr>(),
                0,
            ) as i32
        };

        if ruleset_fd < 0 {
            return Err("Failed to create Landlock ruleset".to_string());
        }

        // Add Read-Only Paths (e.g. /usr, /lib, /dev)
        let ro_access = (ACCESS_FS_EXECUTE | ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR) & full_access;
        for &path_str in read_only_paths {
            if let Ok(file) = fs::OpenOptions::new().read(true).custom_flags(libc::O_PATH).open(path_str) {
                use std::os::unix::io::AsRawFd;
                let path_attr = landlock_path_beneath_attr {
                    allowed_access: ro_access,
                    parent_fd: file.as_raw_fd(),
                };
                unsafe {
                    libc::syscall(
                        SYS_LANDLOCK_ADD_RULE,
                        ruleset_fd,
                        LANDLOCK_RULE_PATH_BENEATH,
                        &path_attr as *const _,
                        0,
                    );
                }
            }
        }

        // Add Read-Write Paths (e.g. workspace)
        for &path_str in read_write_paths {
            if let Ok(file) = fs::OpenOptions::new().read(true).custom_flags(libc::O_PATH).open(path_str) {
                use std::os::unix::io::AsRawFd;
                let path_attr = landlock_path_beneath_attr {
                    allowed_access: full_access,
                    parent_fd: file.as_raw_fd(),
                };
                unsafe {
                    libc::syscall(
                        SYS_LANDLOCK_ADD_RULE,
                        ruleset_fd,
                        LANDLOCK_RULE_PATH_BENEATH,
                        &path_attr as *const _,
                        0,
                    );
                }
            }
        }

        Ok(ruleset_fd)
    }

    #[allow(dead_code)]
    pub fn apply_ruleset(ruleset_fd: i32) -> Result<(), String> {
        unsafe {
            // PR_SET_NO_NEW_PRIVS is required by Landlock
            if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0 {
                libc::close(ruleset_fd);
                return Err("Failed to set PR_SET_NO_NEW_PRIVS".to_string());
            }

            if libc::syscall(SYS_LANDLOCK_RESTRICT_SELF, ruleset_fd, 0) < 0 {
                libc::close(ruleset_fd);
                return Err("Failed to restrict process with Landlock".to_string());
            }

            libc::close(ruleset_fd);
        }
        Ok(())
    }
}
