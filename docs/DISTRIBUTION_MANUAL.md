# 👑 FLOWORK OS — MASTER DISTRIBUTION, OTA UPDATER & LIVE ISO BUILDER MANUAL

Buku panduan resmi arsitektur distribusi **Flowork OS**: tata cara unggah repositori ke GitHub publik, mekanisme *Content-Addressable Delta OTA Auto-Updater*, teknik mastering *Live ISO Hybrid*, hingga prosedur *flashing* ke USB flashdisk.

---

## 📑 DAFTAR ISI
1. [Bagian 1: Panduan Unggah ke GitHub (`upload-flowork-os.sh`)](#bagian-1-panduan-unggah-ke-github-upload-flowork-ossh)
2. [Bagian 2: Cara Kerja Sistem Auto-Update (Delta OTA)](#bagian-2-cara-kerja-sistem-auto-update-delta-ota)
3. [Bagian 3: Panduan Mastering & Build Live ISO (`build-live-iso.sh`)](#bagian-3-panduan-mastering--build-live-iso-build-live-isosh)
4. [Bagian 4: Cara Flashing ISO ke USB Flashdisk](#bagian-4-cara-flashing-iso-ke-usb-flashdisk)
5. [Bagian 5: Daftar Hitam Berkas (Strict Anti-Leak Blacklist)](#bagian-5-daftar-hitam-berkas-strict-anti-leak-blacklist)
6. [Bagian 6: Troubleshooting & Penanganan Masalah Kritis](#bagian-6-troubleshooting--penanganan-masalah-kritis)

---

## BAGIAN 1: PANDUAN UNGGAH KE GITHUB (`upload-flowork-os.sh`)

Alat sinkronisasi terarah (`upload-flowork-os.sh`) berfungsi mentransfer pembaruan dari sistem inti `/opt/floworkos` ke repositori staging `$HOME/flowork-os-repo/`, memindai kebocoran kredensial, menghasilkan manifest delta, dan melakukan `git push` ke GitHub publik ([`flowork-os/flowork-os`](https://github.com/flowork-os/flowork-os)).

### 1. Persiapan Token GitHub
1. Buat **Personal Access Token (Classic)** di GitHub dengan hak akses:
   - `repo` (Full control of private/public repositories)
   - `write:packages` (Opsional untuk package registry)
2. Simpan token mentah ke berkas:
   ```text
   $HOME/Downloads/github uploader/token
   ```
3. Kunci izin berkas agar aman dari proses lain:
   ```bash
   chmod 600 "$HOME/Downloads/github uploader/token"
   ```

### 2. Cara Menjalankan Unggah

#### A. Eksekusi Standar (Pesan Commit Otomatis)
```bash
cd "$HOME/Downloads/github uploader"
./upload-flowork-os.sh
```

#### B. Eksekusi dengan Pesan Commit Kustom
```bash
cd "$HOME/Downloads/github uploader"
./upload-flowork-os.sh "feat(core): modernisasi audio engine dan update dock profile"
```

### 3. Tahapan Pipeline Otomatis (5 Stages Protection)
Skrip mengeksekusi 5 tahap pengamanan secara ketat:
- **STAGE 1/5 — Validasi Token & API**: Menguji token langsung ke endpoint GitHub API (`https://api.github.com/repos/flowork-os/flowork-os`). Jika token salah atau kadaluarsa (HTTP 401/403/404), proses **langsung berhenti**.
- **STAGE 2/5 — Sinkronisasi Terarah (Targeted Staging)**: Menyalin berkas yang baru diedit dari `/opt/floworkos` ke `$HOME/flowork-os-repo/core/`. Komponen berat seperti binary di atas 50MB atau direktori build otomatis diabaikan.
- **STAGE 3/5 — Deep Anti-Leak Shield**:
  - *Rule A*: Memastikan `vault.json` tidak ada di staging dan tidak berstatus staged di git.
  - *Rule B*: Regex scanner mendeteksi token OAuth (`ya29.*`), refresh token (`1//0.*`), dan JWT (`eyJ.*`).
  - *Rule C*: Memindai kunci privat SSH/TLS (`id_rsa`, `id_ed25519`, `*.pfx`).
  - *Aksi*: Jika ditemukan satu saja potensi kebocoran, upload **BATAL INSTAN (Fail-Safe Kill)**.
- **STAGE 4/5 — Cryptographic Manifest Generation**: Menjalankan `/opt/floworkos/bin/flowork-manifest-gen` untuk merekam hash SHA-256 seluruh berkas ke `manifest.json` dan `manifest.json.gz`.
- **STAGE 5/5 — GitHub Remote Push**: Mendorong perubahan ke branch `main` menggunakan kredensial sementara (`x-access-token`), lalu membersihkan kredensial dari remote URL lokal.

### 4. Cara Menambah Berkas Baru ke Skrip Unggah
Jika Anda baru saja membuat aplikasi baru di `/opt/floworkos/apps/nama-app`:
1. Buka `upload-flowork-os.sh`.
2. Di bagian **`[STAGE 2/5]`**, tambahkan sinkronisasi foldernya:
   ```bash
   mkdir -p "${STAGE_DIR}/core/apps/nama-app"
   cp -rf "${FLOWORK_ROOT}/apps/nama-app/"* "${STAGE_DIR}/core/apps/nama-app/"
   cp -f "${FLOWORK_ROOT}/bin/nama-app" "${STAGE_DIR}/core/bin/nama-app" 2>/dev/null || true
   cp -f "${FLOWORK_ROOT}/icons/nama-app.png" "${STAGE_DIR}/core/icons/nama-app.png" 2>/dev/null || true
   ```
3. Jalankan kembali `./upload-flowork-os.sh`.

---

## BAGIAN 2: CARA KERJA SISTEM AUTO-UPDATE (DELTA OTA)

Flowork OS menganut prinsip **Single-Build Reproducibility**:
> *"ISO Live hanya perlu di-build satu kali. Seluruh perbaikan bug, fitur baru, dan rilis aplikasi berikutnya didistribusikan langsung ke komputer pengguna melalui Content-Addressable Delta OTA Update."*

```
               [ GITHUB REPOSITORY: flowork-os/flowork-os ]
                                    │
                                    ▼
                         [ manifest.json.gz ] (~1.2 MB)
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
[ Komputasi SHA-256 Lokal ]                               [ Evaluasi Diff ]
Menghitung hash SHA-256 file                              Membandingkan hash lokal
di /opt/floworkos & /usr                                  dengan isi manifest GitHub
        │                                                       │
        └───────────────────────────┬───────────────────────────┘
                                    ▼
                       [ Download Terarah (Delta) ]
                  Hanya mengunduh file yang BERUBAH/BARU
                      dari GitHub Raw Content CDN
                                    │
                                    ▼
                     [ 3-Tier Atomic File Sync ]
              Tier 1: /opt/floworkos  (Core Framework)
              Tier 2: /usr/local/bin  (System Wrappers)
              Tier 3: /etc/skel       (Template Pengguna Baru)
                                    │
                                    ▼
                     [ Post-Update Health Check ]
            Validasi sintaks Python & biner sebelum selesai.
```

### 1. Komponen Utama Updater
- **`/opt/floworkos/bin/flowork-update`**: Mesin penarik pembaruan (*OTA client*).
- **`/opt/floworkos/bin/flowork-manifest-gen`**: Generator manifes kriptografis berbasis SHA-256.
- **`manifest.json.gz`**: Daftar kompresi yang memuat path seluruh file sistem beserta checksum SHA-256 dan izin filenya (*chmod*).
- **`/etc/systemd/system/flowork-autoupdate.timer`**: Timer background yang menjalankan update terjadwal secara senyap.

### 2. Keunggulan Arsitektur Delta OTA
1. **Ultra Hemat Kuota & Cepat**: Komputer pengguna **tidak pernah melakukan `git clone` atau `git pull` multi-gigabyte**. Klien hanya mengunduh `manifest.json.gz` (~1.2 MB), menghitung file mana yang berbeda, lalu hanya mengunduh beberapa KB/MB file yang mengalami perubahan langsung dari CDN mentah GitHub.
2. **Passwordless Background Execution**:
   - Dikonfigurasi melalui `/etc/sudoers.d/flowork-updater`:
     ```text
     ALL ALL=(ALL) NOPASSWD: /opt/floworkos/bin/flowork-update, /opt/floworkos/bin/flowork-manifest-gen
     ```
   - Dan aturan Polkit di `/etc/polkit-1/rules.d/99-flowork-updater.rules`.
   - Pengguna tidak akan pernah diganggu oleh prompt kata sandi saat update background berjalan.
3. **Developer Mode Protection (`flowork.dev`)**:
   - Jika file penanda `/opt/floworkos/flowork.dev` atau `~/flowork.dev` terdeteksi, atau variabel `FLOWORK_ENV=dev` aktif, sistem auto-update **otomatis mati secara total**.
   - Ini melindungi kode yang sedang dikerjakan developer agar tidak tertimpa oleh versi publik GitHub.
4. **Three-Tier Atomic Sync & User Data Safety**:
   - Update hanya menyentuh `/opt/floworkos`, `/usr/local/bin`, dan template `/etc/skel`.
   - File di direktori `$HOME` pengguna **tidak akan pernah ditimpa atau dihapus**.
5. **Self-Healing & Auto-Rollback**:
   - Sebelum mengunci versi baru, updater memverifikasi sintaks modul utama (`python3 -m py_compile`). Jika terjadi kesalahan sintaks, sistem langsung melakukan rollback otomatis dari backup lokal.

### 3. Perintah Manual untuk Mengelola Update
```bash
# Memeriksa apakah ada pembaruan baru di GitHub (Dry-Run):
flowork-update --check

# Memaksa sinkronisasi pembaruan sekarang:
flowork-update --force

# Melihat versi dan commit aktif:
cat /opt/floworkos/system/version.json
```

---

## BAGIAN 3: PANDUAN MASTERING & BUILD LIVE ISO (`build-live-iso.sh`)

Script mastering berada di `/opt/floworkos/iso-builder/build-live-iso.sh` (tersedia alias global: `flowork-iso-master`).

### 1. Inovasi Kunci: Non-Destructive Pseudo-Files (`-pf`)
Pada versi lama, script mencoba memodifikasi `/etc/passwd` di sistem host yang berisiko merusak akun admin host (`sudo: you do not exist in the passwd database`).

Pada arsitektur baru:
- **Host Tidak Pernah Disentuh**: File asli di PC host Anda tidak diubah 1 byte pun.
- **Injeksi Kustom Langsung ke SquashFS**: Script membuat file sanitasi bersih di folder sementara, lalu menggunakan parameter `-pf` (pseudo-file) milik `mksquashfs`:
  ```bash
  mksquashfs / "$SQUASHFS_FILE" \
      -comp xz -b 1048576 -wildcards \
      -ef "$EXCLUDE_FILE" \
      -pf "$PSEUDO_FILE" \
      -noappend
  ```
- File yang disuntikkan secara virtual:
  - `etc/passwd`: Akun tunggal Live OS `flowork:1000:1000` (akun operator host non-`flowork` dibersihkan).
  - `etc/shadow`: Hash user `flowork` terverifikasi.
  - `etc/group`: Pembersihan grup untuk user operator host, pendaftaran `flowork` ke `autologin` & `sudo`.
  - `etc/fstab`: `# UNCONFIGURED FSTAB FOR BASE SYSTEM` (menghilangkan crash duplicate mount NVMe).
  - `etc/machine-id`: `uninitialized`.
  - `etc/lightdm/lightdm.conf`: Autologin permanen ke user `flowork`.

### 2. Standar Autologin Langsung ke Desktop
Agar Live ISO boot langsung masuk ke desktop Flowork tanpa berhenti di login screen:
1. **Binding Kernel Bootloader**: Di `boot-skeleton/boot/grub/grub.cfg` dan `boot-skeleton/isolinux/isolinux.cfg`, kernel dioperkan parameter:
   ```text
   boot=live components nofstab username=flowork hostname=flowork-os quiet splash
   ```
2. **Grup PAM Autologin**: User `flowork` wajib masuk ke grup `autologin` dan `nopasswdlogin`.
3. **Pembersihan Session Wayland Ganda**: Menghapus `/usr/share/wayland-sessions/cinnamon-wayland.desktop` dari ISO agar hanya ada `flowork.desktop`, mencegah munculnya dialog pemilihan desktop environment (*Select desktop environment*).

### 3. Tampilan Login Menu Rapi (Slick-Greeter)
Jika layar greeter terbuka, konfigurasinya di `/etc/lightdm/slick-greeter.conf` dijamin rapi:
- `content-align=center`: Kotak dialog login berada tepat di tengah layar.
- `logo=/usr/share/icons/flowork/flowork-logo-compact.svg`: Menggunakan logo SVG kompak 64px.
- `background=/opt/floworkos/theme/flowork-quantum-wallpaper.png`: Latar belakang Quantum Glass gelap.
- `draw-user-backgrounds=false`: Mencegah greeter mengambil wallpaper acak host.

### 4. Cara Menjalankan Kompilasi ISO
```bash
# 1. Menjalankan audit kelayakan pra-build:
flowork-iso-master check

# 2. Menjalankan simulasi dry-run:
flowork-iso-master dry-run

# 3. Memulai proses build ISO resmi (Multi-threaded XZ):
flowork-iso-master build
```

Hasil build akan tersimpan di:
```text
~/Downloads/flowork-iso-build/FloworkOS-1.0-x86_64-Sovereign-Rust.iso
```

---

## BAGIAN 4: CARA FLASHING ISO KE USB FLASHDISK

Setelah file ISO selesai dibuat, ikuti langkah berikut untuk menulisnya ke flashdisk secara aman:

### 1. Identifikasi Device Flashdisk
Tancapkan flashdisk, lalu jalankan:
```bash
lsblk -o NAME,SIZE,TYPE,TRAN,MODEL,VENDOR,MOUNTPOINTS
```
Pastikan nama devicenya (misal: `/dev/sda` atau `/dev/sdb` dengan `TRAN=usb`). **JANGAN SALAH MEMILIH DRIVE SSD/NVMe INTERNAL!**

### 2. Pastikan Partisi Flashdisk Unmounted
Jika ada partisi flashdisk yang otomatis ter-mount:
```bash
sudo umount /dev/sda* 2>/dev/null || true
```

### 3. Eksekusi Flashing dengan `dd` Direct & Fsync
Jalankan penulisan dengan mode direct I/O agar proses sinkronisasi akurat:
```bash
sudo dd if=~/Downloads/flowork-iso-build/FloworkOS-1.0-x86_64-Sovereign-Rust.iso \
        of=/dev/sda \
        bs=4M \
        oflag=direct \
        conv=fsync \
        status=progress
```

### 4. Sinkronisasi Kernel & Reload Partisi
```bash
sync
sudo partprobe /dev/sda
```

### 5. Verifikasi Partisi ISO Hybrid
Periksa kembali tabel partisi:
```bash
lsblk -f /dev/sda
```
Output yang benar akan menampilkan 2 partisi:
- `sda1` (FSTYPE: `iso9660`, LABEL: `FLOWORK_OS`)
- `sda2` (FSTYPE: `vfat`, LABEL: `FLOWORK_EFI`)

Flashdisk sekarang siap dicabut dan langsung digunakan untuk booting di PC UEFI maupun BIOS Legacy!

---

## BAGIAN 5: DAFTAR HITAM BERKAS (STRICT ANTI-LEAK BLACKLIST)

> [!CAUTION]
> DILARANG KERAS mengunggah berkas-berkas di bawah ini ke repositori publik GitHub maupun menyertakannya ke dalam file SquashFS Live ISO!

| Kategori | Berkas Terlarang | Alasan Bahaya |
| :--- | :--- | :--- |
| **Kredensial Cloud** | `vault.json`, `flowork-session.json` | Berisi token autentikasi Google, refresh token, dan rotasi API cloud. |
| **Token Pribadi** | `token`, `.env`, `*.env` | Berisi Personal Access Token GitHub dan kredensial developer. |
| **Kunci Keamanan** | `id_rsa*`, `id_ed25519*`, `*.pem`, `*.pfx` | Kunci otentikasi SSH server dan sertifikat privat. |
| **Privasi Pengguna** | Transkrip AI (`chats/*.jsonl`), database chat | Riwayat percakapan pengguna dan memori agen. |
| **Data Download** | `*Downloads*`, `*downloads*` | File unduhan pribadi pengguna di host. |
| **Sisa Sesi** | `.bash_history`, `.zsh_history`, cache browser | Jejak riwayat perintah dan histori penjelajahan web. |
| **Build Artifacts** | `*.iso`, `initrd`, `flowork-iso-build/`, `*.blend` | File biner raksasa yang melanggar batas kuota GitHub (maks 50-100MB). |

---

## BAGIAN 6: TROUBLESHOOTING & PENANGANAN MASALAH KRITIS

### 1. Masalah: `sudo: you do not exist in the passwd database`
- **Penyebab**: Script build lama menghapus akun `<host_user>` langsung di `/etc/passwd` komputer host saat build berjalan.
- **Solusi**: Jangan pernah mengedit `/etc/passwd` di host. Gunakan fitur pseudo-file `mksquashfs -pf` seperti yang sudah diimplementasikan di `build-live-iso.sh` terbaru.
- **Pemulihan Cepat jika Terlanjur Terjadi**:
  Masuk via user `flowork`:
  ```bash
  echo flowork | su - flowork -c "echo '<host_user>:x:1001:1001:<host_user>:/home/<host_user>:/bin/bash' | sudo tee -a /etc/passwd"
  ```

### 2. Masalah: Boot Live USB Muncul Duplicate `-.mount` / `systemd-fstab-generator failed`
- **Penyebab**: File `/etc/fstab` host (dengan UUID internal NVMe) ikut masuk ke ISO Live CD.
- **Solusi**: File `/etc/fstab` di ISO Live harus berisi `# UNCONFIGURED FSTAB FOR BASE SYSTEM` dan bootloader menyertakan opsi kernel `nofstab`.

### 3. Masalah: Live USB Berhenti di Layar Login / "Select desktop environment"
- **Penyebab**: Parameter `username=flowork` tidak ada di cmdline kernel bootloader, atau ada file session ganda di `/usr/share/wayland-sessions/`.
- **Solusi**:
  1. Pastikan bootloader memuat `username=flowork hostname=flowork-os`.
  2. Pastikan file session sisa Wayland (`cinnamon-wayland.desktop`) sudah dihapus sehingga hanya ada `flowork.desktop`.
  3. Pastikan user `flowork` terdaftar di grup `autologin` dan `nopasswdlogin`.

### 4. Masalah: GitHub Push Gagal (HTTP 401 / 403 / "Repository not found")
- **Penyebab**: Token di berkas `token` kadaluarsa atau tidak memiliki izin `repo`.
- **Solusi**: Generate ulang GitHub Personal Access Token (PAT) dengan izin `repo`, lalu perbarui berkas `$HOME/Downloads/github uploader/token`.

---

*Dokumen ini disusun dan distandarisasi oleh Sovereign Architecture Board & Dr. Flow System Division.*  
*Hak Cipta © 2026 Flowork OS. Bebas didistribusikan di bawah Lisensi Open Sovereign.*
