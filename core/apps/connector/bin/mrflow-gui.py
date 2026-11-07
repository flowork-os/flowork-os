#!/usr/bin/env python3
"""
MrFlow Router — Native Linux Desktop GUI (GTK3 / PyGObject)
Pure offline native interface. Zero Google Chrome dependency.
Zero prompt injection. Clean engineering terminology.
"""

import sys
import os
import json
import urllib.request
import urllib.error
import threading
import subprocess
import shutil
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf, Pango

def get_base_dir():
    if os.environ.get("MRFLOW_CONNECTOR_DIR") and os.path.isdir(os.environ["MRFLOW_CONNECTOR_DIR"]):
        return os.environ["MRFLOW_CONNECTOR_DIR"]
    script_path = os.path.realpath(__file__)
    candidate = os.path.abspath(os.path.join(os.path.dirname(script_path), ".."))
    if os.path.exists(os.path.join(candidate, "server", "index.js")):
        return candidate
    for p in ["/opt/floworkos/apps/connector", os.path.expanduser("~/mrflow/connector")]:
        if os.path.exists(os.path.join(p, "server", "index.js")):
            return p
    return candidate

BASE_DIR = get_base_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "gui", "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")

PORT = 9099
BASE_URL = f"http://127.0.0.1:{PORT}"

DARK_CSS = b"""
window, dialog {
    background-color: #0d1826;
    color: #f1f5f9;
    font-family: 'Inter', 'Segoe UI', 'Ubuntu', sans-serif;
}

headerbar, .header-card {
    background: linear-gradient(180deg, #16283f 0%, #0e1c2d 100%);
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    padding: 14px 20px;
}

.glass-panel {
    background: linear-gradient(135deg, #16273e 0%, #111e30 100%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.card {
    background: linear-gradient(135deg, #14243b 0%, #0f1c2e 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 10px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

button {
    background: linear-gradient(180deg, #1e334f 0%, #16273d 100%);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
    padding: 7px 16px;
    font-weight: 600;
    transition: all 150ms ease-in-out;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

button:hover {
    background: linear-gradient(180deg, #274368 0%, #1c324f 100%);
    border-color: rgba(56, 189, 248, 0.6);
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25);
}

button:active {
    background: #142338;
}

button.suggested-action, .btn-emerald {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.85) 0%, rgba(5, 150, 105, 0.75) 100%);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #ffffff;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35);
}

button.suggested-action:hover, .btn-emerald:hover {
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.9) 0%, rgba(16, 185, 129, 0.85) 100%);
    border-color: rgba(255, 255, 255, 0.5);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
}

button.destructive-action, .btn-danger {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.8) 0%, rgba(185, 28, 28, 0.7) 100%);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #ffffff;
}

button.destructive-action:hover, .btn-danger:hover {
    background: linear-gradient(135deg, rgba(248, 113, 113, 0.9) 0%, rgba(220, 38, 38, 0.85) 100%);
}

entry {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 12px;
    padding: 8px 14px;
}

entry:focus {
    border-color: #38bdf8;
    background: rgba(255, 255, 255, 0.12);
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
}

treeview {
    background-color: #0b1523;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 12px;
}

treeview:selected {
    background: linear-gradient(90deg, rgba(14, 165, 233, 0.5) 0%, rgba(14, 165, 233, 0.2) 100%);
    color: #ffffff;
}

treeview header button {
    background: #14243b;
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #94a3b8;
    font-size: 11px;
    font-weight: bold;
    padding: 6px;
}

.badge-online {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 16px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

.badge-offline {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.45);
    border-radius: 16px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

.badge-user {
    background: rgba(56, 189, 248, 0.18);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 16px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

stackswitcher button {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 10px;
    margin-right: 4px;
}

stackswitcher button:checked {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.75) 0%, rgba(2, 132, 199, 0.65) 100%);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #ffffff;
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35);
}
"""

class MrFlowRouterWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="MrFlow Router")
        self.set_default_size(980, 680)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Set App Icon
        if os.path.exists(ICON_PATH):
            try:
                self.set_icon_from_file(ICON_PATH)
            except Exception:
                pass

        # Apply Dark Theme CSS
        self.apply_css()

        self.current_state = {}
        self.active_provider = "connector"
        self.accounts_data = []

        # Build Main Layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)

        # 1. Top Header Bar
        header = self.build_header()
        main_vbox.pack_start(header, False, False, 0)

        # 2. Provider Navigation Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(180)

        # Tab 1: Sovereign Connector
        self.connector_view = self.build_connector_tab()
        self.stack.add_titled(self.connector_view, "connector", "Sovereign Connector")

        # Tab 2: Ollama Local Engine
        self.ollama_view = self.build_ollama_tab()
        self.stack.add_titled(self.ollama_view, "ollama", "Ollama Local Engine")

        # Tab 3: 9Router Gateway
        self.nine_router_view = self.build_nine_router_tab()
        self.stack.add_titled(self.nine_router_view, "9router", "9Router Gateway")

        # Stack Switcher Tab Bar
        switcher_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        switcher_box.set_margin_start(16)
        switcher_box.set_margin_end(16)
        switcher_box.set_margin_top(12)
        switcher_box.set_margin_bottom(8)

        lbl_engine = Gtk.Label(label="<b>Inference Engine:</b>", use_markup=True)
        switcher_box.pack_start(lbl_engine, False, False, 0)

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)
        switcher_box.pack_start(self.stack_switcher, True, True, 0)

        btn_activate_engine = Gtk.Button(label="Apply Engine Mode")
        btn_activate_engine.connect("clicked", self.on_apply_engine_clicked)
        switcher_box.pack_start(btn_activate_engine, False, False, 0)

        main_vbox.pack_start(switcher_box, False, False, 0)
        main_vbox.pack_start(self.stack, True, True, 0)

        # 3. Bottom Status Footer
        self.footer_bar = self.build_footer()
        main_vbox.pack_start(self.footer_bar, False, False, 0)

        # Periodic refresh
        GLib.timeout_add(3500, self.auto_refresh_tick)
        self.refresh_status_async()

    def apply_css(self):
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(DARK_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def build_header(self):
        header_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_card.get_style_context().add_class("header-card")

        # Left: App Title and Icon
        if os.path.exists(ICON_PATH):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(ICON_PATH, 32, 32, True)
                app_icon = Gtk.Image.new_from_pixbuf(pixbuf)
                header_card.pack_start(app_icon, False, False, 0)
            except Exception:
                pass

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label="<span size='large' weight='bold'>MrFlow Router</span>", use_markup=True)
        title_lbl.set_xalign(0)
        sub_lbl = Gtk.Label(label="<span size='small' color='#94a3b8'>Universal AI Gateway &amp; Multi-Account Rotator</span>", use_markup=True)
        sub_lbl.set_xalign(0)
        title_vbox.pack_start(title_lbl, False, False, 0)
        title_vbox.pack_start(sub_lbl, False, False, 0)
        header_card.pack_start(title_vbox, False, False, 0)

        # Right: User Passport Badge & Status Badge
        header_card.pack_start(Gtk.Box(), True, True, 0)

        self.user_badge = Gtk.Label(label="👤 Unauthenticated")
        self.user_badge.get_style_context().add_class("badge-user")
        header_card.pack_start(self.user_badge, False, False, 0)

        self.status_badge = Gtk.Label(label="● Checking Server...")
        self.status_badge.get_style_context().add_class("badge-offline")
        header_card.pack_start(self.status_badge, False, False, 0)

        btn_passport = Gtk.Button(label="Flowork Login")
        btn_passport.connect("clicked", self.on_passport_login_clicked)
        header_card.pack_start(btn_passport, False, False, 0)

        return header_card

    def build_connector_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(8)
        box.set_margin_bottom(12)

        # Action Toolbar
        tb_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tb_card.get_style_context().add_class("card")

        btn_sync = Gtk.Button(label="☁️ Sync Cloud Vault")
        btn_sync.connect("clicked", self.on_sync_cloud_clicked)
        tb_card.pack_start(btn_sync, False, False, 0)

        btn_backup = Gtk.Button(label="⬆️ Backup to Cloud")
        btn_backup.connect("clicked", self.on_push_cloud_clicked)
        tb_card.pack_start(btn_backup, False, False, 0)

        btn_oauth = Gtk.Button(label="➕ Connect Google Account")
        btn_oauth.get_style_context().add_class("btn-emerald")
        btn_oauth.connect("clicked", self.on_connect_google_clicked)
        tb_card.pack_start(btn_oauth, False, False, 0)

        btn_add_manual = Gtk.Button(label="➕ Add Manually")
        btn_add_manual.connect("clicked", self.on_add_account_dialog)
        tb_card.pack_start(btn_add_manual, False, False, 0)

        btn_clear = Gtk.Button(label="⚡ Reset Cooldowns")
        btn_clear.connect("clicked", self.on_clear_cooldowns_clicked)
        tb_card.pack_start(btn_clear, False, False, 0)

        tb_card.pack_start(Gtk.Box(), True, True, 0)

        btn_refresh = Gtk.Button(label="🔄 Refresh")
        btn_refresh.connect("clicked", lambda _: self.refresh_status_async())
        tb_card.pack_start(btn_refresh, False, False, 0)

        box.pack_start(tb_card, False, False, 0)

        # Strategy Controls & Summary (Single Focus Exhaustion Queue)
        strat_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        strat_card.get_style_context().add_class("card")

        lbl_strat_badge = Gtk.Label(
            label="<span background='#0c4a6e' foreground='#38bdf8' font_weight='bold'>  ⚡ SINGLE FOCUS ROTATION  </span>  <span foreground='#e2e8f0'>Locks on 1 account until limit/error, then moves to end of line</span>",
            use_markup=True
        )
        strat_card.pack_start(lbl_strat_badge, False, False, 0)

        strat_card.pack_start(Gtk.Box(), True, True, 0)

        self.lbl_pool_summary = Gtk.Label(label="Pool: 0 accounts loaded", use_markup=True)
        strat_card.pack_start(self.lbl_pool_summary, False, False, 0)

        box.pack_start(strat_card, False, False, 0)

        # Accounts TreeView
        # Model columns: [is_active_str, email, status_str, requests_str, last_used_str, account_id]
        self.account_store = Gtk.ListStore(str, str, str, str, str, str)

        self.treeview = Gtk.TreeView(model=self.account_store)

        col_active = Gtk.TreeViewColumn("Active", Gtk.CellRendererText(), text=0)
        col_active.set_min_width(70)
        self.treeview.append_column(col_active)

        col_email = Gtk.TreeViewColumn("Account Email", Gtk.CellRendererText(), text=1)
        col_email.set_expand(True)
        self.treeview.append_column(col_email)

        col_status = Gtk.TreeViewColumn("Status", Gtk.CellRendererText(), text=2)
        col_status.set_min_width(120)
        self.treeview.append_column(col_status)

        col_reqs = Gtk.TreeViewColumn("Requests", Gtk.CellRendererText(), text=3)
        col_reqs.set_min_width(90)
        self.treeview.append_column(col_reqs)

        col_used = Gtk.TreeViewColumn("Last Used", Gtk.CellRendererText(), text=4)
        col_used.set_min_width(160)
        self.treeview.append_column(col_used)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.treeview)
        box.pack_start(scrolled, True, True, 0)

        # Row Action Buttons for Selected Account
        row_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row_actions.set_margin_top(6)

        btn_set_active = Gtk.Button(label="Set as Primary")
        btn_set_active.connect("clicked", self.on_set_primary_clicked)
        row_actions.pack_start(btn_set_active, False, False, 0)

        btn_test_token = Gtk.Button(label="Test Token")
        btn_test_token.connect("clicked", self.on_test_token_clicked)
        row_actions.pack_start(btn_test_token, False, False, 0)

        btn_remove = Gtk.Button(label="Remove Account")
        btn_remove.get_style_context().add_class("btn-danger")
        btn_remove.connect("clicked", self.on_remove_account_clicked)
        row_actions.pack_start(btn_remove, False, False, 0)

        box.pack_start(row_actions, False, False, 0)
        return box

    def build_ollama_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        desc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        desc_card.get_style_context().add_class("card")
        d_title = Gtk.Label(label="<b>Ollama Local Inference Engine</b>", use_markup=True)
        d_title.set_xalign(0)
        d_sub = Gtk.Label(label="Forward AI completions to local Ollama instance running on your machine GPU/CPU.", use_markup=True)
        d_sub.set_xalign(0)
        desc_card.pack_start(d_title, False, False, 0)
        desc_card.pack_start(d_sub, False, False, 0)
        box.pack_start(desc_card, False, False, 0)

        form_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form_card.get_style_context().add_class("card")

        lbl_h = Gtk.Label(label="<b>Ollama Host URL:</b>", use_markup=True)
        lbl_h.set_xalign(0)
        self.entry_ollama_host = Gtk.Entry()
        self.entry_ollama_host.set_text("http://127.0.0.1:11434")
        form_card.pack_start(lbl_h, False, False, 0)
        form_card.pack_start(self.entry_ollama_host, False, False, 0)

        lbl_m = Gtk.Label(label="<b>Default Model:</b>", use_markup=True)
        lbl_m.set_xalign(0)
        self.entry_ollama_model = Gtk.Entry()
        self.entry_ollama_model.set_text("llama3.3:latest")
        form_card.pack_start(lbl_m, False, False, 0)
        form_card.pack_start(self.entry_ollama_model, False, False, 0)

        lbl_c = Gtk.Label(label="<b>Custom Models (comma separated):</b>", use_markup=True)
        lbl_c.set_xalign(0)
        self.entry_ollama_custom = Gtk.Entry()
        self.entry_ollama_custom.set_text("qwen2.5-coder:latest, mistral:latest, deepseek-r1:latest")
        form_card.pack_start(lbl_c, False, False, 0)
        form_card.pack_start(self.entry_ollama_custom, False, False, 0)

        act_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_test = Gtk.Button(label="Test Connection")
        btn_test.connect("clicked", self.on_test_ollama_clicked)
        btn_save = Gtk.Button(label="Save Ollama Settings")
        btn_save.get_style_context().add_class("btn-emerald")
        btn_save.connect("clicked", self.on_save_ollama_clicked)

        act_box.pack_start(btn_test, False, False, 0)
        act_box.pack_start(btn_save, False, False, 0)
        self.lbl_ollama_test_result = Gtk.Label(label="")
        act_box.pack_start(self.lbl_ollama_test_result, False, False, 0)

        form_card.pack_start(act_box, False, False, 0)
        box.pack_start(form_card, False, False, 0)
        box.pack_start(Gtk.Box(), True, True, 0)
        return box

    def build_nine_router_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        desc_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        desc_card.get_style_context().add_class("card")
        d_title = Gtk.Label(label="<b>9Router Universal Gateway</b>", use_markup=True)
        d_title.set_xalign(0)
        d_sub = Gtk.Label(label="Forward AI requests to 9Router universal proxy for commercial/open-source API aggregation.", use_markup=True)
        d_sub.set_xalign(0)
        desc_card.pack_start(d_title, False, False, 0)
        desc_card.pack_start(d_sub, False, False, 0)
        box.pack_start(desc_card, False, False, 0)

        form_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form_card.get_style_context().add_class("card")

        lbl_h = Gtk.Label(label="<b>9Router Host URL:</b>", use_markup=True)
        lbl_h.set_xalign(0)
        self.entry_9r_host = Gtk.Entry()
        self.entry_9r_host.set_text("http://127.0.0.1:20128")
        form_card.pack_start(lbl_h, False, False, 0)
        form_card.pack_start(self.entry_9r_host, False, False, 0)

        lbl_k = Gtk.Label(label="<b>API Key:</b>", use_markup=True)
        lbl_k.set_xalign(0)
        self.entry_9r_key = Gtk.Entry()
        self.entry_9r_key.set_visibility(False)
        form_card.pack_start(lbl_k, False, False, 0)
        form_card.pack_start(self.entry_9r_key, False, False, 0)

        lbl_m = Gtk.Label(label="<b>Default Model:</b>", use_markup=True)
        lbl_m.set_xalign(0)
        self.entry_9r_model = Gtk.Entry()
        self.entry_9r_model.set_text("clinepass/cline-pass/glm-5.2")
        form_card.pack_start(lbl_m, False, False, 0)
        form_card.pack_start(self.entry_9r_model, False, False, 0)

        act_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_test = Gtk.Button(label="Test Connection")
        btn_test.connect("clicked", self.on_test_9r_clicked)
        btn_save = Gtk.Button(label="Save 9Router Settings")
        btn_save.get_style_context().add_class("btn-emerald")
        btn_save.connect("clicked", self.on_save_9r_clicked)

        act_box.pack_start(btn_test, False, False, 0)
        act_box.pack_start(btn_save, False, False, 0)
        self.lbl_9r_test_result = Gtk.Label(label="")
        act_box.pack_start(self.lbl_9r_test_result, False, False, 0)

        form_card.pack_start(act_box, False, False, 0)
        box.pack_start(form_card, False, False, 0)
        box.pack_start(Gtk.Box(), True, True, 0)
        return box

    def build_footer(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        bar.set_margin_top(6)
        bar.set_margin_bottom(8)

        self.lbl_footer_status = Gtk.Label(label="Ready.")
        self.lbl_footer_status.set_xalign(0)
        bar.pack_start(self.lbl_footer_status, True, True, 0)

        lbl_binding = Gtk.Label(label=f"<span color='#64748b'>Port {PORT}</span>", use_markup=True)
        bar.pack_start(lbl_binding, False, False, 0)
        return bar

    # ── Logic & API Interactions ──
    def auto_refresh_tick(self):
        self.refresh_status_async()
        return True

    def refresh_status_async(self):
        def worker():
            try:
                req = urllib.request.Request(f"{BASE_URL}/auth/router/status", headers={"User-Agent": "MrFlow-GUI/1.0"})
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    GLib.idle_add(self.update_ui_state, data)
            except Exception as e:
                GLib.idle_add(self.update_ui_offline, str(e))
        threading.Thread(target=worker, daemon=True).start()

    def update_ui_offline(self, err_msg):
        self.status_badge.set_text("● Server Offline")
        self.status_badge.get_style_context().remove_class("badge-online")
        self.status_badge.get_style_context().add_class("badge-offline")
        self.lbl_footer_status.set_text(f"Unable to reach server on {BASE_URL}: {err_msg}")

    def update_ui_state(self, data):
        self.current_state = data
        self.status_badge.set_text("● Online (Port 9099)")
        self.status_badge.get_style_context().remove_class("badge-offline")
        self.status_badge.get_style_context().add_class("badge-online")

        # Update User Passport
        user = data.get("user")
        if user and user.get("username"):
            tier = user.get("tier", "pro").upper()
            self.user_badge.set_text(f"👤 @{user.get('username')} [{tier}]")
        else:
            self.user_badge.set_text("👤 Unauthenticated")

        # Update Active Provider
        prov = data.get("active_provider", "connector").lower()
        self.active_provider = prov
        current_visible = self.stack.get_visible_child_name()
        if not current_visible:
            self.stack.set_visible_child_name(prov)

        # Update Accounts Table
        accounts = data.get("accounts", [])
        self.accounts_data = accounts
        self.account_store.clear()

        healthy = data.get("healthy_count", 0)
        cooldown = data.get("cooldown_count", 0)
        total = len(accounts)
        active_email = data.get("active_email", "None")

        self.lbl_pool_summary.set_markup(
            f"<b>Accounts Pool:</b> <span color='#34d399'>{healthy} Ready</span> | "
            f"<span color='#f59e0b'>{cooldown} Cooldown</span> | "
            f"Total: {total} | Primary: <b>{active_email}</b>"
        )

        for a in accounts:
            is_active_str = "● Active" if a.get("is_active") else "○"
            status_raw = a.get("status", "ready")
            if status_raw == "cooldown":
                cd_rem = a.get("cooldown_remaining_sec", 0)
                status_str = f"Cooldown ({cd_rem}s)"
            elif status_raw == "error":
                status_str = "Error"
            else:
                status_str = "Ready"

            reqs_str = str(a.get("requests_count", 0))
            last_used = a.get("last_used_at") or a.get("added_at") or "-"
            if len(last_used) > 19:
                last_used = last_used[:19].replace("T", " ")

            self.account_store.append([
                is_active_str,
                a.get("email", ""),
                status_str,
                reqs_str,
                last_used,
                a.get("id", "")
            ])

        # Fill Provider Settings
        providers_cfg = data.get("providers", {})
        ollama_cfg = providers_cfg.get("ollama", {})
        if ollama_cfg.get("host") and not self.entry_ollama_host.has_focus():
            self.entry_ollama_host.set_text(ollama_cfg.get("host"))
        if ollama_cfg.get("default_model") and not self.entry_ollama_model.has_focus():
            self.entry_ollama_model.set_text(ollama_cfg.get("default_model"))
        if isinstance(ollama_cfg.get("custom_models"), list) and not self.entry_ollama_custom.has_focus():
            self.entry_ollama_custom.set_text(", ".join(ollama_cfg.get("custom_models")))

        r9_cfg = providers_cfg.get("9router", {})
        if r9_cfg.get("host") and not self.entry_9r_host.has_focus():
            self.entry_9r_host.set_text(r9_cfg.get("host"))
        if r9_cfg.get("default_model") and not self.entry_9r_model.has_focus():
            self.entry_9r_model.set_text(r9_cfg.get("default_model"))
        if r9_cfg.get("api_key") and not self.entry_9r_key.has_focus():
            self.entry_9r_key.set_text(r9_cfg.get("api_key"))

        self.lbl_footer_status.set_text(f"Engine [{prov.upper()}] active. All local endpoints operating.")

    # ── Button Handlers ──
    def on_apply_engine_clicked(self, widget):
        selected_prov = self.stack.get_visible_child_name()
        if not selected_prov:
            return
        def worker():
            try:
                payload = json.dumps({"active_provider": selected_prov}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/provider-config", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    pass
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to switch provider: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_rotation_mode_changed(self, combo):
        mode = combo.get_active_id()
        if not mode:
            return
        def worker():
            try:
                payload = json.dumps({"mode": mode}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/set-rotation-mode", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0):
                    pass
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to set rotation strategy: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_sync_cloud_clicked(self, widget):
        self.lbl_footer_status.set_text("Syncing accounts from auth.floworkos.com Cloud Vault...")
        def worker():
            try:
                req = urllib.request.Request(f"{BASE_URL}/auth/router/sync-cloud", data=b"{}", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    msg = res.get("message", "Cloud Vault synchronized.")
                    GLib.idle_add(self.show_info_dialog, "Cloud Sync Successful", msg)
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Cloud Sync Failed: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_push_cloud_clicked(self, widget):
        self.lbl_footer_status.set_text("Backing up accounts pool to auth.floworkos.com...")
        def worker():
            try:
                # We can call push by saving rotation mode or via index
                payload = json.dumps({"mode": self.current_state.get("rotation_mode", "failover")}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/set-rotation-mode", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=8.0):
                    GLib.idle_add(self.show_info_dialog, "Cloud Backup", "Accounts pool successfully backed up to auth.floworkos.com!")
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Cloud Backup Failed: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_connect_google_clicked(self, widget):
        self.lbl_footer_status.set_text("Opening Google authorization in active browser...")
        def worker():
            try:
                req = urllib.request.Request(f"{BASE_URL}/auth/router/login-url")
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    login_url = data.get("loginUrl") or data.get("login_url")
                    if login_url:
                        self.open_url_in_active_browser(login_url)
                        GLib.idle_add(self.lbl_footer_status.set_text, "Authorization tab opened in your active browser.")
                    else:
                        GLib.idle_add(self.show_error_dialog, "Server did not return a valid login URL.")
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to start OAuth flow: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_passport_login_clicked(self, widget):
        self.lbl_footer_status.set_text("Opening Flowork login in active browser...")
        def worker():
            try:
                req = urllib.request.Request(f"{BASE_URL}/auth/login-url?no_open=1")
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    gate_url = data.get("gate_url") or data.get("login_url")
                    if gate_url:
                        self.open_url_in_active_browser(gate_url)
                        GLib.idle_add(self.lbl_footer_status.set_text, "Flowork login tab opened in your active browser.")
                    else:
                        GLib.idle_add(self.show_error_dialog, "Server did not return a valid gate URL.")
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to start login: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def open_url_in_active_browser(self, target_url):
        env = dict(os.environ)
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"

        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(target_url, -1)
        except Exception:
            pass

        try:
            subprocess.Popen(["xdg-open", target_url], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            pass

        for cmd in ["google-chrome-stable", "google-chrome", "chromium", "firefox"]:
            if shutil.which(cmd):
                try:
                    subprocess.Popen([cmd, target_url], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except Exception:
                    pass

    def on_clear_cooldowns_clicked(self, widget):
        def worker():
            try:
                req = urllib.request.Request(f"{BASE_URL}/auth/router/clear-cooldown", data=b"{}", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    c = res.get("cleared_count", 0)
                    GLib.idle_add(self.lbl_footer_status.set_text, f"Cleared cooldown state for {c} accounts.")
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Error clearing cooldowns: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def get_selected_account_id(self):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            return model[treeiter][5]
        return None

    def on_set_primary_clicked(self, widget):
        acc_id = self.get_selected_account_id()
        if not acc_id:
            self.show_error_dialog("Please select an account from the table first.")
            return
        def worker():
            try:
                payload = json.dumps({"id": acc_id}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/select-account", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0):
                    pass
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to switch primary account: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_test_token_clicked(self, widget):
        acc_id = self.get_selected_account_id()
        if not acc_id:
            self.show_error_dialog("Please select an account from the table first.")
            return
        self.lbl_footer_status.set_text(f"Refreshing and testing token for account {acc_id}...")
        def worker():
            try:
                payload = json.dumps({"id": acc_id}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/test-account", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    if res.get("success"):
                        GLib.idle_add(self.show_info_dialog, "Token Test OK", f"Token for {res.get('email')} is valid and ready!")
                    else:
                        GLib.idle_add(self.show_error_dialog, f"Token test failed: {res.get('error') or res.get('details')}")
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Token verification error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_remove_account_clicked(self, widget):
        acc_id = self.get_selected_account_id()
        if not acc_id:
            self.show_error_dialog("Please select an account from the table first.")
            return
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove Account from Pool?"
        )
        dialog.format_secondary_text(f"Are you sure you want to delete account {acc_id}? Cloud backup will be synchronized.")
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.YES:
            return

        def worker():
            try:
                payload = json.dumps({"id": acc_id}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/remove-account", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5.0):
                    pass
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to remove account: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def on_add_account_dialog(self, widget):
        dialog = Gtk.Dialog(title="Add Google Account Manually", transient_for=self, flags=0)
        dialog.set_default_size(440, 260)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        btn_add = dialog.add_button("Add & Backup to Cloud", Gtk.ResponseType.OK)
        btn_add.get_style_context().add_class("btn-emerald")

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)

        lbl_e = Gtk.Label(label="<b>Email Address:</b>", use_markup=True)
        lbl_e.set_xalign(0)
        entry_email = Gtk.Entry()
        entry_email.set_placeholder_text("developer@gmail.com")
        content.pack_start(lbl_e, False, False, 0)
        content.pack_start(entry_email, False, False, 0)

        lbl_rt = Gtk.Label(label="<b>OAuth Refresh Token:</b>", use_markup=True)
        lbl_rt.set_xalign(0)
        entry_rt = Gtk.Entry()
        entry_rt.set_placeholder_text("1//0g...")
        content.pack_start(lbl_rt, False, False, 0)
        content.pack_start(entry_rt, False, False, 0)

        content.show_all()
        response = dialog.run()
        email_val = entry_email.get_text().strip()
        rt_val = entry_rt.get_text().strip()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            if not email_val or not rt_val:
                self.show_error_dialog("Both Email and Refresh Token are required.")
                return
            def worker():
                try:
                    payload = json.dumps({"email": email_val, "refresh_token": rt_val}).encode("utf-8")
                    req = urllib.request.Request(f"{BASE_URL}/auth/router/add-account", data=payload, headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=8.0) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        bk = res.get("cloud_backup", {})
                        bk_msg = "Cloud Backup OK" if bk.get("success") else "Saved locally"
                        GLib.idle_add(self.show_info_dialog, "Account Added", f"Account {email_val} added to pool.\n{bk_msg}")
                    GLib.idle_add(self.refresh_status_async)
                except Exception as e:
                    GLib.idle_add(self.show_error_dialog, f"Failed to add account: {e}")
            threading.Thread(target=worker, daemon=True).start()

    # ── Ollama Handlers ──
    def on_test_ollama_clicked(self, widget):
        host = self.entry_ollama_host.get_text().strip()
        self.lbl_ollama_test_result.set_text("Testing connection...")
        def worker():
            try:
                payload = json.dumps({"provider": "ollama", "host": host}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/test-provider", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    if res.get("success"):
                        models = res.get("models", [])
                        m_count = len(models)
                        GLib.idle_add(self.lbl_ollama_test_result.set_markup, f"<span color='#34d399'>● Connected ({m_count} models found)</span>")
                    else:
                        GLib.idle_add(self.lbl_ollama_test_result.set_markup, f"<span color='#ef4444'>● Failed: {res.get('error')}</span>")
            except Exception as e:
                GLib.idle_add(self.lbl_ollama_test_result.set_markup, f"<span color='#ef4444'>● Error: {e}</span>")
        threading.Thread(target=worker, daemon=True).start()

    def on_save_ollama_clicked(self, widget):
        host = self.entry_ollama_host.get_text().strip()
        model = self.entry_ollama_model.get_text().strip()
        custom = [m.strip() for m in self.entry_ollama_custom.get_text().split(",") if m.strip()]
        def worker():
            try:
                payload = json.dumps({
                    "ollama": {
                        "host": host,
                        "default_model": model,
                        "custom_models": custom
                    }
                }).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/provider-config", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0):
                    GLib.idle_add(self.show_info_dialog, "Settings Saved", "Ollama provider configuration updated!")
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to save Ollama config: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ── 9Router Handlers ──
    def on_test_9r_clicked(self, widget):
        host = self.entry_9r_host.get_text().strip()
        key = self.entry_9r_key.get_text().strip()
        self.lbl_9r_test_result.set_text("Testing connection...")
        def worker():
            try:
                payload = json.dumps({"provider": "9router", "host": host, "api_key": key}).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/test-provider", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    if res.get("success"):
                        GLib.idle_add(self.lbl_9r_test_result.set_markup, "<span color='#34d399'>● Connected successfully!</span>")
                    else:
                        GLib.idle_add(self.lbl_9r_test_result.set_markup, f"<span color='#ef4444'>● Failed: {res.get('error')}</span>")
            except Exception as e:
                GLib.idle_add(self.lbl_9r_test_result.set_markup, f"<span color='#ef4444'>● Error: {e}</span>")
        threading.Thread(target=worker, daemon=True).start()

    def on_save_9r_clicked(self, widget):
        host = self.entry_9r_host.get_text().strip()
        key = self.entry_9r_key.get_text().strip()
        model = self.entry_9r_model.get_text().strip()
        def worker():
            try:
                payload = json.dumps({
                    "9router": {
                        "host": host,
                        "api_key": key,
                        "default_model": model
                    }
                }).encode("utf-8")
                req = urllib.request.Request(f"{BASE_URL}/auth/router/provider-config", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0):
                    GLib.idle_add(self.show_info_dialog, "Settings Saved", "9Router provider configuration updated!")
                GLib.idle_add(self.refresh_status_async)
            except Exception as e:
                GLib.idle_add(self.show_error_dialog, f"Failed to save 9Router config: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ── Dialog Utilities ──
    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_info_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

def main():
    # Ensure server daemon is active
    try:
        req = urllib.request.Request(f"{BASE_URL}/auth/router/status", headers={"User-Agent": "MrFlow-GUI/1.0"})
        urllib.request.urlopen(req, timeout=1.0)
    except Exception:
        # Start server daemon
        daemon_bin = shutil.which("mrflow-router-daemon") or "/usr/local/bin/mrflow-router-daemon"
        if os.path.exists(daemon_bin):
            subprocess.Popen([daemon_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            server_script = os.path.join(BASE_DIR, "server", "index.js")
            subprocess.Popen(["node", server_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    win = MrFlowRouterWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
