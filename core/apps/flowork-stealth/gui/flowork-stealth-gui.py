#!/usr/bin/env python3
"""
Flowork Sovereign Stealth Browser - Glass HUD Dashboard (PyQt6)
Sovereign Anti-Detect & Hardware Fingerprint Masking Dashboard.
"""

import sys
import os
import json
import random
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QComboBox, QTextEdit, QDialog, QMessageBox, QFrame, QSplitter,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette

BASE_DIR = Path("/opt/floworkos/apps/flowork-stealth")
PROFILES_DIR = BASE_DIR / "profiles"
ENGINE_DIR = BASE_DIR / "engine"
DB_FILE = BASE_DIR / "profiles.json"
ICON_PATH = BASE_DIR / "assets" / "flowork-stealth.png"

# Import presets and launcher from CLI
sys.path.insert(0, str(BASE_DIR / "bin"))
from importlib.machinery import SourceFileLoader
cli_module = SourceFileLoader("flowork_stealth", str(BASE_DIR / "bin" / "flowork-stealth")).load_module()
PRESETS = cli_module.PRESETS

STYLE_SHEET = """
QMainWindow {
    background-color: #080c10;
}
QWidget {
    font-family: 'JetBrains Mono', 'Segoe UI', monospace;
    color: #e6edf3;
    font-size: 13px;
}
QFrame.glassCard {
    background-color: #0f1722;
    border: 1px solid #1c2736;
    border-radius: 8px;
}
QFrame.headerCard {
    background-color: #0b121b;
    border-bottom: 2px solid #00ff66;
}
QLabel.hudTitle {
    color: #00ff66;
    font-size: 18px;
    font-weight: bold;
}
QLabel.badge {
    background-color: #0d2618;
    color: #00ff66;
    border: 1px solid #00ff66;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
}
QLabel.sectionHeader {
    color: #58a6ff;
    font-size: 14px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QListWidget {
    background-color: #0a0f16;
    border: 1px solid #1c2736;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item {
    background-color: #121b27;
    border: 1px solid #1e2c3e;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 6px;
}
QListWidget::item:selected {
    background-color: #172a24;
    border: 1px solid #00ff66;
    color: #ffffff;
}
QListWidget::item:hover {
    background-color: #162332;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #090e15;
    border: 1px solid #233144;
    border-radius: 6px;
    padding: 8px;
    color: #e6edf3;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #00ff66;
}
QPushButton {
    background-color: #152232;
    border: 1px solid #283a52;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e6edf3;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1c2e44;
    border-color: #00e5ff;
    color: #00e5ff;
}
QPushButton.btnLaunch {
    background-color: #00ff66;
    color: #080c10;
    font-size: 14px;
    font-weight: 800;
    border: none;
    border-radius: 6px;
    padding: 12px;
}
QPushButton.btnLaunch:hover {
    background-color: #33ff85;
}
QPushButton.btnTest {
    background-color: #0d2238;
    color: #58a6ff;
    border: 1px solid #1f4266;
}
QPushButton.btnTest:hover {
    background-color: #163659;
    color: #79c0ff;
    border-color: #58a6ff;
}
QPushButton.btnDelete {
    background-color: #261214;
    color: #ff7b72;
    border: 1px solid #4a1d21;
}
QPushButton.btnDelete:hover {
    background-color: #3d1b1f;
    border-color: #ff7b72;
}
"""

class CreateProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Sovereign Stealth Profile")
        self.setFixedSize(500, 480)
        self.setStyleSheet(STYLE_SHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("⚡ NEW STEALTH IDENTITY")
        hdr.setStyleSheet("color: #00ff66; font-size: 16px; font-weight: bold;")
        layout.addWidget(hdr)

        # Name
        layout.addWidget(QLabel("Profile Name / Tag:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Crypto Twitter, Binance Whale, OSINT Bot")
        layout.addWidget(self.name_input)

        # Preset
        layout.addWidget(QLabel("Hardware DNA Preset:"))
        self.preset_combo = QComboBox()
        for k, v in PRESETS.items():
            self.preset_combo.addItem(f"{v['name']}", k)
        layout.addWidget(self.preset_combo)

        # Proxy
        layout.addWidget(QLabel("Proxy Endpoint (Optional):"))
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("e.g. socks5://127.0.0.1:9050 or http://user:pass@ip:port")
        layout.addWidget(self.proxy_input)

        # Notes
        layout.addWidget(QLabel("Notes / Purpose:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Specific accounts or operational directives...")
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)

        # Buttons
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save = QPushButton("✨ Create Profile")
        self.btn_save.setStyleSheet("background-color: #00ff66; color: #080c10; font-weight: bold;")
        self.btn_save.clicked.connect(self.accept_data)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def accept_data(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Profile name cannot be empty.")
            return
        preset_key = self.preset_combo.currentData()
        proxy = self.proxy_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        success = cli_module.create_profile(name, preset_key, proxy, notes)
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Profile '{name}' already exists.")


class FloworkStealthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flowork Sovereign Stealth Browser | Anti-Detect System")
        self.resize(1020, 680)
        self.setStyleSheet(STYLE_SHEET)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.selected_slug = None
        self.init_ui()
        self.refresh_profiles()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # Top Sovereign HUD Header
        hdr_frame = QFrame()
        hdr_frame.setProperty("class", "glassCard headerCard")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(14, 12, 14, 12)

        title_box = QVBoxLayout()
        title_lbl = QLabel("FLOWORK STEALTH BROWSER")
        title_lbl.setProperty("class", "hudTitle")
        sub_lbl = QLabel("Sovereign Anti-Detect Fingerprint Isolation Engine • Linux 7.3 Rust")
        sub_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        hdr_layout.addLayout(title_box)

        hdr_layout.addStretch()

        badge = QLabel("● SOVEREIGN HARDENED")
        badge.setProperty("class", "badge")
        hdr_layout.addWidget(badge)

        main_layout.addWidget(hdr_frame)

        # Splitter Layout (Left: Profiles, Right: DNA Inspector)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # LEFT PANEL: Profiles
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_header = QHBoxLayout()
        left_title = QLabel("PROFILES")
        left_title.setProperty("class", "sectionHeader")
        left_header.addWidget(left_title)
        left_header.addStretch()

        self.btn_new = QPushButton("+ New Profile")
        self.btn_new.setStyleSheet("background-color: #172a24; border: 1px solid #00ff66; color: #00ff66;")
        self.btn_new.clicked.connect(self.open_create_dialog)
        left_header.addWidget(self.btn_new)
        left_layout.addLayout(left_header)

        self.profile_list = QListWidget()
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        left_layout.addWidget(self.profile_list)

        splitter.addWidget(left_widget)

        # RIGHT PANEL: DNA Inspector & Launcher
        right_card = QFrame()
        right_card.setProperty("class", "glassCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(14)

        right_title = QLabel("HARDWARE DNA INSPECTOR")
        right_title.setProperty("class", "sectionHeader")
        right_layout.addWidget(right_title)

        self.profile_name_lbl = QLabel("Select a profile to view synthetic fingerprint")
        self.profile_name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        right_layout.addWidget(self.profile_name_lbl)

        # Grid / Details Display
        self.details_box = QVBoxLayout()
        self.details_box.setSpacing(8)

        self.lbl_os = QLabel("Platform: -")
        self.lbl_gpu = QLabel("GPU Renderer: -")
        self.lbl_hw = QLabel("Cores / RAM: -")
        self.lbl_screen = QLabel("Resolution: -")
        self.lbl_seeds = QLabel("Canvas / Audio Seed: -")
        self.lbl_proxy = QLabel("Proxy: -")

        for lbl in [self.lbl_os, self.lbl_gpu, self.lbl_hw, self.lbl_screen, self.lbl_seeds, self.lbl_proxy]:
            lbl.setStyleSheet("background-color: #0b1118; padding: 8px; border-radius: 4px; border-left: 3px solid #00ff66;")
            self.details_box.addWidget(lbl)

        right_layout.addLayout(self.details_box)
        right_layout.addStretch()

        # Action Buttons
        self.btn_launch = QPushButton("🚀 LAUNCH STEALTH BROWSER")
        self.btn_launch.setProperty("class", "btnLaunch")
        self.btn_launch.clicked.connect(lambda: self.launch_selected("https://iphey.com"))
        right_layout.addWidget(self.btn_launch)

        test_row = QHBoxLayout()
        self.btn_test_iphey = QPushButton("🛡 Iphey Audit")
        self.btn_test_iphey.setProperty("class", "btnTest")
        self.btn_test_iphey.clicked.connect(lambda: self.launch_selected("https://iphey.com"))

        self.btn_test_yt = QPushButton("📺 YouTube (Ad-Free)")
        self.btn_test_yt.setProperty("class", "btnTest")
        self.btn_test_yt.clicked.connect(lambda: self.launch_selected("https://www.youtube.com"))

        self.btn_test_pixelscan = QPushButton("🧪 Pixelscan")
        self.btn_test_pixelscan.setProperty("class", "btnTest")
        self.btn_test_pixelscan.clicked.connect(lambda: self.launch_selected("https://pixelscan.net"))

        self.btn_test_leaks = QPushButton("🌐 BrowserLeaks")
        self.btn_test_leaks.setProperty("class", "btnTest")
        self.btn_test_leaks.clicked.connect(lambda: self.launch_selected("https://browserleaks.com/javascript"))

        test_row.addWidget(self.btn_test_iphey)
        test_row.addWidget(self.btn_test_yt)
        test_row.addWidget(self.btn_test_pixelscan)
        test_row.addWidget(self.btn_test_leaks)
        right_layout.addLayout(test_row)

        bottom_row = QHBoxLayout()
        self.btn_delete = QPushButton("🗑 Delete Profile")
        self.btn_delete.setProperty("class", "btnDelete")
        self.btn_delete.clicked.connect(self.delete_selected)
        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_delete)
        right_layout.addLayout(bottom_row)

        splitter.addWidget(right_card)
        splitter.setSizes([380, 640])
        main_layout.addWidget(splitter)

    def refresh_profiles(self):
        self.profile_list.clear()
        db = cli_module.load_db()
        for slug, p in db.items():
            preset_name = PRESETS.get(p.get("preset"), {}).get("name", p.get("os", "Custom"))
            proxy_txt = p.get("proxy") or "Direct IP"
            item_text = f"🛡 {p.get('profileName', slug)}\n   Persona: {preset_name}\n   Proxy  : {proxy_txt}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, slug)
            self.profile_list.addItem(item)

        if self.profile_list.count() > 0:
            self.profile_list.setCurrentRow(0)
            self.on_profile_selected(self.profile_list.item(0))

    def on_profile_selected(self, item):
        if not item:
            return
        slug = item.data(Qt.ItemDataRole.UserRole)
        self.selected_slug = slug
        db = cli_module.load_db()
        p = db.get(slug)
        if not p:
            return

        preset = PRESETS.get(p.get("preset"), {})
        self.profile_name_lbl.setText(f"🛡 {p.get('profileName', slug)} [ID: {slug}]")
        self.lbl_os.setText(f"🖥 Platform: {p.get('platform')} ({p.get('os').upper()})")
        self.lbl_gpu.setText(f"🎮 GPU: {p.get('webglRenderer')}")
        self.lbl_hw.setText(f"⚡ CPU Cores: {p.get('hardwareConcurrency')} | RAM: {p.get('deviceMemory')} GB")
        self.lbl_screen.setText(f"📐 Screen: {p.get('screenWidth')} x {p.get('screenHeight')}")
        self.lbl_seeds.setText(f"🎨 Canvas Seed: {p.get('canvasSeed')} | Audio Seed: {p.get('audioSeed')}")
        self.lbl_proxy.setText(f"🌐 Proxy: {p.get('proxy') or 'Direct Connection'}")

    def open_create_dialog(self):
        dlg = CreateProfileDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh_profiles()

    def launch_selected(self, url="https://pixelscan.net"):
        if not self.selected_slug:
            QMessageBox.information(self, "Selection Required", "Please select a profile to launch.")
            return
        cli_module.launch_profile(self.selected_slug, url)

    def delete_selected(self):
        if not self.selected_slug:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete profile '{self.selected_slug}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            cli_module.delete_profile(self.selected_slug)
            self.refresh_profiles()

def main():
    app = QApplication(sys.argv)
    window = FloworkStealthWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
