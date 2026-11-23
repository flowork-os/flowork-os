#!/usr/bin/env python3
import os
import subprocess
import shutil

THEME_DIR = "/usr/share/icons/Flowork-Quantum-Glass"
os.makedirs(THEME_DIR, exist_ok=True)

# 1. Write index.theme
INDEX_THEME = """[Icon Theme]
Name=Flowork-Quantum-Glass
Comment=Flowork OS Sovereign Pure Optical Crystal Glass Icon Theme
Inherits=Papirus-Dark,WhiteSur-dark,breeze-dark,Adwaita,hicolor
Directories=places/scalable,apps/scalable,actions/scalable,categories/scalable,devices/scalable,status/scalable,mimetypes/scalable,places/48,apps/48,actions/48,categories/48,devices/48,status/48,places/32,apps/32,actions/32,places/22,apps/22,actions/22,places/16,apps/16,actions/16

[places/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Places

[places/48]
Size=48
Type=Fixed
Context=Places

[places/32]
Size=32
Type=Fixed
Context=Places

[places/22]
Size=22
Type=Fixed
Context=Places

[places/16]
Size=16
Type=Fixed
Context=Places

[apps/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Applications

[apps/48]
Size=48
Type=Fixed
Context=Applications

[apps/32]
Size=32
Type=Fixed
Context=Applications

[apps/22]
Size=22
Type=Fixed
Context=Applications

[apps/16]
Size=16
Type=Fixed
Context=Applications

[actions/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Actions

[actions/48]
Size=48
Type=Fixed
Context=Actions

[actions/32]
Size=32
Type=Fixed
Context=Actions

[actions/22]
Size=22
Type=Fixed
Context=Actions

[actions/16]
Size=16
Type=Fixed
Context=Actions

[categories/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Categories

[categories/48]
Size=48
Type=Fixed
Context=Categories

[categories/32]
Size=32
Type=Fixed
Context=Categories

[categories/22]
Size=22
Type=Fixed
Context=Categories

[categories/16]
Size=16
Type=Fixed
Context=Categories

[devices/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Devices

[devices/48]
Size=48
Type=Fixed
Context=Devices

[devices/32]
Size=32
Type=Fixed
Context=Devices

[devices/22]
Size=22
Type=Fixed
Context=Devices

[devices/16]
Size=16
Type=Fixed
Context=Devices

[status/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=Status

[status/48]
Size=48
Type=Fixed
Context=Status

[mimetypes/scalable]
Size=256
Type=Scalable
MinSize=16
MaxSize=512
Context=MimeTypes
"""

with open(os.path.join(THEME_DIR, "index.theme"), "w") as fp:
    fp.write(INDEX_THEME)

for cat in ["places", "apps", "actions", "categories", "devices", "status", "mimetypes"]:
    os.makedirs(os.path.join(THEME_DIR, cat, "scalable"), exist_ok=True)
    for sz in ["48", "32", "22", "16"]:
        os.makedirs(os.path.join(THEME_DIR, cat, sz), exist_ok=True)

# Helper function to generate Pure Optical Crystal Glass Folder SVG
def make_folder_svg(badge_markup):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <filter id="crystalGlow" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="3.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    
    <linearGradient id="backFlapGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
      <stop offset="30%" stop-color="#cffafe" stop-opacity="0.85"/>
      <stop offset="70%" stop-color="#38bdf8" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#00f2fe" stop-opacity="0.85"/>
    </linearGradient>

    <linearGradient id="frontShieldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
      <stop offset="20%" stop-color="#e0f7fe" stop-opacity="0.85"/>
      <stop offset="55%" stop-color="#bae6fd" stop-opacity="0.70"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.85"/>
    </linearGradient>

    <linearGradient id="specularCrest" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="1.0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#a5f3fc" stop-opacity="0.85"/>
    </linearGradient>

    <linearGradient id="docPlateGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.90"/>
      <stop offset="100%" stop-color="#e0f2fe" stop-opacity="0.70"/>
    </linearGradient>
  </defs>

  <!-- 1. Folder Back Flap (Fluid Curved Silhouette) -->
  <path d="M 38 68 C 38 52 48 44 64 44 L 102 44 C 112 44 120 48 126 56 L 138 72 L 192 72 C 208 72 218 82 218 98 L 218 190 C 218 206 208 216 192 216 L 64 216 C 48 216 38 206 38 190 Z" 
        fill="url(#backFlapGrad)" 
        stroke="#ffffff" 
        stroke-width="1.5"
        filter="drop-shadow(0 8px 24px rgba(0, 242, 254, 0.25))"/>

  <!-- 2. Inner Document Plate (Reflective Ice Sheet) -->
  <rect x="54" y="64" width="148" height="62" rx="14" 
        fill="url(#docPlateGrad)" 
        stroke="#ffffff" 
        stroke-width="1.2"/>
  <line x1="68" y1="82" x2="136" y2="82" stroke="#0284c7" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="68" y1="96" x2="112" y2="96" stroke="#00ff66" stroke-width="2.5" stroke-linecap="round"/>

  <!-- 3. Front Optical Crystal Shield (Fluid Convex Curved Dome) -->
  <path d="M 28 92 C 28 74 42 66 60 66 L 196 66 C 214 66 228 74 228 92 L 228 196 C 228 214 214 222 196 222 L 60 222 C 42 222 28 214 28 196 Z" 
        fill="url(#frontShieldGrad)" 
        stroke="url(#specularCrest)" 
        stroke-width="2.0"
        filter="url(#crystalGlow)"/>

  <!-- 4. Specular White Top Crest Reflection -->
  <line x1="46" y1="68" x2="210" y2="68" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M 34 94 Q 128 108 222 94" stroke="rgba(255, 255, 255, 0.45)" stroke-width="1.5" fill="none"/>

  <!-- 5. Center Badge -->
  <g transform="translate(128, 148)">
    {badge_markup}
  </g>
</svg>"""

BADGES = {
    "folder": """<polygon points="0,-24 20,-12 20,12 0,24 -20,12 -20,-12" fill="none" stroke="#00ff66" stroke-width="3.5"/>
                 <circle cx="0" cy="0" r="5" fill="#ffffff"/>""",
    "folder-home": """<path d="M -24 6 L 0 -18 L 24 6 L 16 6 L 16 22 L -16 22 L -16 6 Z" fill="none" stroke="#00f3ff" stroke-width="3.5" stroke-linejoin="round"/>
                      <circle cx="0" cy="10" r="4" fill="#00ff66"/>""",
    "folder-desktop": """<rect x="-24" y="-18" width="48" height="32" rx="10" fill="none" stroke="#00f3ff" stroke-width="3"/>
                        <line x1="-10" y1="18" x2="10" y2="18" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
                        <line x1="0" y1="14" x2="0" y2="18" stroke="#ffffff" stroke-width="3"/>
                        <circle cx="0" cy="-2" r="4" fill="#00ff66"/>""",
    "folder-documents": """<path d="M -16 -22 L 6 -22 L 18 -10 L 18 22 L -16 22 Z" fill="none" stroke="#00f3ff" stroke-width="3" stroke-linejoin="round"/>
                          <line x1="-10" y1="-8" x2="10" y2="-8" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
                          <line x1="-10" y1="0" x2="10" y2="0" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
                          <line x1="-10" y1="8" x2="4" y2="8" stroke="#00ff66" stroke-width="2.5" stroke-linecap="round"/>""",
    "folder-download": """<path d="M 0 -20 L 0 12 M -12 2 L 0 14 L 12 2" fill="none" stroke="#00ff66" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M -20 12 L -20 22 L 20 22 L 20 12" fill="none" stroke="#00f3ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>""",
    "folder-music": """<path d="M -12 16 C -12 11 -6 8 -2 8 L -2 -16 L 18 -20 L 18 10 C 18 6 24 3 28 3" fill="none" stroke="#00f3ff" stroke-width="3.5" stroke-linecap="round"/>
                      <circle cx="-10" cy="16" r="6" fill="#00ff66"/>
                      <circle cx="10" cy="12" r="6" fill="#ffffff"/>""",
    "folder-pictures": """<rect x="-24" y="-18" width="48" height="36" rx="10" fill="none" stroke="#00f3ff" stroke-width="3"/>
                         <circle cx="-12" cy="-6" r="4" fill="#00ff66"/>
                         <path d="M -22 12 L -8 -2 L 4 10 L 12 4 L 22 14" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linejoin="round"/>""",
    "folder-videos": """<rect x="-24" y="-18" width="48" height="36" rx="10" fill="none" stroke="#00f3ff" stroke-width="3"/>
                        <polygon points="-6,-10 10,0 -6,10" fill="#00ff66"/>""",
    "folder-remote": """<circle cx="0" cy="-14" r="7" fill="none" stroke="#00f3ff" stroke-width="3"/>
                        <circle cx="-16" cy="14" r="7" fill="none" stroke="#00ff66" stroke-width="3"/>
                        <circle cx="16" cy="14" r="7" fill="none" stroke="#00ff66" stroke-width="3"/>
                        <line x1="-12" y1="9" x2="-3" y2="-8" stroke="#ffffff" stroke-width="2.5"/>
                        <line x1="12" y1="9" x2="3" y2="-8" stroke="#ffffff" stroke-width="2.5"/>
                        <line x1="-10" y1="14" x2="10" y2="14" stroke="#ffffff" stroke-width="2.5"/>""",
    "folder-saved-search": """<circle cx="-4" cy="-4" r="14" fill="none" stroke="#00f3ff" stroke-width="3.5"/>
                              <line x1="7" y1="7" x2="20" y2="20" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
                              <circle cx="-4" cy="-4" r="4" fill="#00ff66"/>""",
    "folder-templates": """<rect x="-18" y="-18" width="36" height="36" rx="10" fill="none" stroke="#00f3ff" stroke-width="3" stroke-dasharray="4,3"/>
                           <circle cx="0" cy="0" r="5" fill="#00ff66"/>""",
    "folder-publicshare": """<circle cx="0" cy="0" r="6" fill="#00ff66"/>
                            <path d="M -12 -12 A 18 18 0 0 1 12 -12 M -18 -18 A 26 26 0 0 1 18 -18" fill="none" stroke="#00f3ff" stroke-width="3" stroke-linecap="round"/>""",
    "user-trash": """<path d="M -16 -12 L 16 -12 M -8 -12 L -6 -18 L 6 -18 L 8 -12 M -12 -12 L -10 20 L 10 20 L 12 -12" fill="none" stroke="#00f3ff" stroke-width="3" stroke-linejoin="round"/>
                     <line x1="-4" y1="-6" x2="-4" y2="14" stroke="#ffffff" stroke-width="2"/>
                     <line x1="4" y1="-6" x2="4" y2="14" stroke="#ffffff" stroke-width="2"/>""",
    "user-trash-full": """<path d="M -16 -12 L 16 -12 M -8 -12 L -6 -18 L 6 -18 L 8 -12 M -12 -12 L -10 20 L 10 20 L 12 -12" fill="none" stroke="#00f3ff" stroke-width="3" stroke-linejoin="round"/>
                          <circle cx="0" cy="4" r="5" fill="#00ff66"/>"""
}

PLACE_ALIASES = {
    "folder": ["folder", "inode-directory", "stock_folder"],
    "folder-home": ["folder-home", "user-home", "user-home-symbolic"],
    "folder-desktop": ["folder-desktop", "user-desktop", "user-desktop-symbolic"],
    "folder-documents": ["folder-documents", "folder-document", "folder-text"],
    "folder-download": ["folder-download", "folder-downloads", "stock_folder-download"],
    "folder-music": ["folder-music", "folder-audio", "stock_folder-music"],
    "folder-pictures": ["folder-pictures", "folder-picture", "folder-image", "stock_folder-pictures"],
    "folder-videos": ["folder-videos", "folder-video", "stock_folder-videos"],
    "folder-remote": ["folder-remote", "network-server", "network-workgroup"],
    "folder-saved-search": ["folder-saved-search", "folder-search"],
    "folder-templates": ["folder-templates"],
    "folder-publicshare": ["folder-publicshare"],
    "user-trash": ["user-trash", "trashcan_empty", "user-trash-symbolic"],
    "user-trash-full": ["user-trash-full", "trashcan_full", "user-trash-full-symbolic"]
}

for key, badge_svg in BADGES.items():
    svg_content = make_folder_svg(badge_svg)
    aliases = PLACE_ALIASES.get(key, [key])
    for alias in aliases:
        target = os.path.join(THEME_DIR, "places", "scalable", f"{alias}.svg")
        with open(target, "w") as fp:
            fp.write(svg_content)

# 2. Bespoke Application Icons (Pure Optical Crystal Glass & Fluid Capsule Standards)
APPS_SVGS = {}

# File Manager / Nemo: Pure Optical Crystal Glass Vault
APPS_SVGS["system-file-manager"] = make_folder_svg("""<polygon points="0,-26 22,-13 22,13 0,26 -22,13 -22,-13" fill="rgba(0, 255, 102, 0.2)" stroke="#00ff66" stroke-width="3.0"/><polygon points="0,-14 12,0 0,14 -12,0" fill="#ffffff"/><circle cx="0" cy="0" r="4" fill="#00ff66"/>""")

# App Grid / Launchpad: Sovereign 9-Node Crystal Matrix
APPS_SVGS["view-app-grid"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="gridGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/>
      <stop offset="50%" stop-color="#e0f2fe" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00ff66" stop-opacity="0.22"/>
    </linearGradient>
    <linearGradient id="nodeCyan" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f3ff"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <linearGradient id="nodeGreen" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#00ff66"/>
    </linearGradient>
  </defs>
  <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#gridGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
  <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <g transform="translate(48, 48)">
    <!-- Row 1 -->
    <rect x="0" y="0" width="36" height="36" rx="14" fill="url(#nodeCyan)"/>
    <rect x="62" y="0" width="36" height="36" rx="14" fill="url(#nodeGreen)"/>
    <rect x="124" y="0" width="36" height="36" rx="14" fill="url(#nodeCyan)"/>
    <!-- Row 2 -->
    <rect x="0" y="62" width="36" height="36" rx="14" fill="url(#nodeGreen)"/>
    <!-- Center Radiant Core -->
    <rect x="62" y="62" width="36" height="36" rx="16" fill="#ffffff" stroke="#00ff66" stroke-width="3.5"/>
    <rect x="124" y="62" width="36" height="36" rx="14" fill="url(#nodeGreen)"/>
    <!-- Row 3 -->
    <rect x="0" y="124" width="36" height="36" rx="14" fill="url(#nodeCyan)"/>
    <rect x="62" y="124" width="36" height="36" rx="14" fill="url(#nodeGreen)"/>
    <rect x="124" y="124" width="36" height="36" rx="14" fill="url(#nodeCyan)"/>
  </g>
</svg>"""

# Settings: Quantum Cyber Reactor
APPS_SVGS["preferences-system"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="gearGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.36"/>
      <stop offset="50%" stop-color="#e0f2fe" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00f3ff" stop-opacity="0.20"/>
    </linearGradient>
    <linearGradient id="coreNeon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="50%" stop-color="#00f3ff"/>
      <stop offset="100%" stop-color="#00ff66"/>
    </linearGradient>
  </defs>
  <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#gearGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
  <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Quantum Rotor Blades -->
  <g transform="translate(128, 128)">
    <circle cx="0" cy="0" r="64" fill="none" stroke="rgba(255, 255, 255, 0.45)" stroke-width="3" stroke-dasharray="16,10"/>
    <circle cx="0" cy="0" r="46" fill="rgba(255, 255, 255, 0.16)" stroke="url(#coreNeon)" stroke-width="3"/>
    <!-- 8 Rotor Nodes -->
    <circle cx="0" cy="-64" r="8" fill="#00ff66"/>
    <circle cx="45" cy="-45" r="7" fill="#00f3ff"/>
    <circle cx="64" cy="0" r="8" fill="#ffffff"/>
    <circle cx="45" cy="45" r="7" fill="#00ff66"/>
    <circle cx="0" cy="64" r="8" fill="#00f3ff"/>
    <circle cx="-45" cy="45" r="7" fill="#ffffff"/>
    <circle cx="-64" cy="0" r="8" fill="#00ff66"/>
    <circle cx="-45" cy="-45" r="7" fill="#00f3ff"/>
    <!-- Center Core -->
    <polygon points="0,-18 16,-9 16,9 0,18 -16,9 -16,-9" fill="#00ff66"/>
    <circle cx="0" cy="0" r="6" fill="#ffffff"/>
  </g>
</svg>"""

# Wallpaper Settings
APPS_SVGS["preferences-desktop-wallpaper"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="wpGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.36"/>
      <stop offset="50%" stop-color="#e0f2fe" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00f3ff" stop-opacity="0.20"/>
    </linearGradient>
    <linearGradient id="wpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f3ff"/>
      <stop offset="50%" stop-color="#00ff66"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
  </defs>
  <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#wpGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
  <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <rect x="46" y="52" width="164" height="110" rx="18" fill="url(#wpGrad)"/>
  <path d="M 60 144 L 100 96 L 140 134 L 170 108 L 196 144 Z" fill="rgba(255, 255, 255, 0.4)"/>
  <circle cx="90" cy="84" r="10" fill="#ffffff"/>
  <line x1="100" y1="184" x2="156" y2="184" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
  <line x1="128" y1="162" x2="128" y2="184" stroke="#00f3ff" stroke-width="4"/>
</svg>"""

# Screenshot / Optic Lens
APPS_SVGS["accessories-screenshot"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="camGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.36"/>
      <stop offset="50%" stop-color="#e0f2fe" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00f3ff" stop-opacity="0.22"/>
    </linearGradient>
    <linearGradient id="lensNeon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="50%" stop-color="#00f3ff"/>
      <stop offset="100%" stop-color="#00ff66"/>
    </linearGradient>
  </defs>
  <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#camGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
  <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <g transform="translate(128, 128)">
    <circle cx="0" cy="0" r="56" fill="rgba(255, 255, 255, 0.16)" stroke="url(#lensNeon)" stroke-width="3"/>
    <circle cx="0" cy="0" r="36" fill="none" stroke="#00f3ff" stroke-width="2.5" stroke-dasharray="8,6"/>
    <circle cx="0" cy="0" r="16" fill="#00ff66"/>
    <!-- Optic Crosshairs -->
    <line x1="-66" y1="0" x2="-44" y2="0" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
    <line x1="44" y1="0" x2="66" y2="0" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
    <line x1="0" y1="-66" x2="0" y2="-44" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
    <line x1="0" y1="44" x2="0" y2="66" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
  </g>
</svg>"""

# Terminal / Alacritty
APPS_SVGS["utilities-terminal"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="termGlass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.38"/>
      <stop offset="50%" stop-color="#e0f2fe" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#00ff66" stop-opacity="0.25"/>
    </linearGradient>
    <linearGradient id="termNeon" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="50%" stop-color="#00f3ff"/>
      <stop offset="100%" stop-color="#00ff66"/>
    </linearGradient>
  </defs>
  <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#termGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
  <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Titlebar dots -->
  <circle cx="64" cy="58" r="6" fill="#00ff66"/>
  <circle cx="84" cy="58" r="6" fill="#00f3ff"/>
  <circle cx="104" cy="58" r="6" fill="#ffffff"/>
  <line x1="44" y1="76" x2="212" y2="76" stroke="rgba(255, 255, 255, 0.40)" stroke-width="1.5"/>
  <!-- Prompt Symbol >_ -->
  <path d="M 64 114 L 98 140 L 64 166" fill="none" stroke="#00ff66" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="114" y1="166" x2="148" y2="166" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>
</svg>"""

# Categories for Start Menu (Pure Optical Crystal Glass)
CATEGORIES_SVGS = {
    "applications-accessories": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="cGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.18"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#cGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 80 176 L 150 106 M 134 90 L 166 122 M 176 80 L 144 48 L 130 62 L 150 82 L 82 150 L 62 130 L 48 144 Z" fill="none" stroke="#00f3ff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="176" cy="80" r="12" fill="#00ff66"/>
    </svg>""",
    "applications-development": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="devGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00ff66" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#devGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 86 90 L 52 128 L 86 166 M 170 90 L 204 128 L 170 166 M 142 80 L 114 176" fill="none" stroke="#00ff66" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",
    "applications-graphics": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="gfGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#gfGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M 128 56 C 80 56 48 88 48 136 C 48 184 84 200 114 200 C 130 200 138 188 152 188 C 166 188 174 196 188 196 C 204 196 208 176 208 160 C 208 100 176 56 128 56 Z" fill="none" stroke="#00f3ff" stroke-width="5"/>
      <circle cx="88" cy="108" r="10" fill="#00ff66"/>
      <circle cx="128" cy="92" r="10" fill="#ffffff"/>
      <circle cx="168" cy="112" r="10" fill="#00f3ff"/>
      <circle cx="180" cy="152" r="10" fill="#fbbf24"/>
    </svg>""",
    "applications-internet": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="netGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#netGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="128" cy="128" r="64" fill="none" stroke="#00f3ff" stroke-width="5"/>
      <ellipse cx="128" cy="128" rx="28" ry="64" fill="none" stroke="#ffffff" stroke-width="4"/>
      <line x1="64" y1="128" x2="192" y2="128" stroke="#00ff66" stroke-width="4"/>
      <line x1="76" y1="96" x2="180" y2="96" stroke="rgba(255, 255, 255, 0.85)" stroke-width="3"/>
      <line x1="76" y1="160" x2="180" y2="160" stroke="rgba(255, 255, 255, 0.85)" stroke-width="3"/>
    </svg>""",
    "applications-multimedia": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="mediaGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00ff66" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#mediaGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="128" cy="128" r="60" fill="none" stroke="#00ff66" stroke-width="5"/>
      <polygon points="112,100 156,128 112,156" fill="#ffffff"/>
    </svg>""",
    "applications-office": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="offGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#offGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <rect x="52" y="80" width="152" height="116" rx="20" fill="none" stroke="#00f3ff" stroke-width="5"/>
      <path d="M 96 80 L 96 60 C 96 52 104 46 112 46 L 144 46 C 152 46 160 52 160 60 L 160 80" fill="none" stroke="#ffffff" stroke-width="5"/>
      <line x1="52" y1="120" x2="204" y2="120" stroke="#00ff66" stroke-width="4"/>
    </svg>""",
    "applications-system": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="sysGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00ff66" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#sysGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <polygon points="128,52 192,88 192,168 128,204 64,168 64,88" fill="none" stroke="#00f3ff" stroke-width="5" stroke-linejoin="round"/>
      <circle cx="128" cy="128" r="22" fill="#00ff66"/>
    </svg>""",
    "applications-other": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="othGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.22"/></linearGradient></defs>
      <rect x="28" y="28" width="200" height="200" rx="54" fill="url(#othGlass)" stroke="rgba(255, 255, 255, 0.70)" stroke-width="2.5"/>
      <line x1="56" y1="30" x2="200" y2="30" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="84" cy="128" r="16" fill="#00f3ff"/>
      <circle cx="128" cy="128" r="16" fill="#ffffff"/>
      <circle cx="172" cy="128" r="16" fill="#00ff66"/>
    </svg>"""
}

# Power Actions (Pure Optical Crystal Glass)
ACTIONS_SVGS = {
    "system-shutdown": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="pwrGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#f43f5e" stop-opacity="0.25"/></linearGradient></defs>
      <circle cx="128" cy="128" r="100" fill="url(#pwrGlass)" stroke="rgba(255, 255, 255, 0.75)" stroke-width="3"/>
      <path d="M 82 86 A 64 64 0 1 0 174 86" fill="none" stroke="#f43f5e" stroke-width="12" stroke-linecap="round"/>
      <line x1="128" y1="48" x2="128" y2="114" stroke="#ffffff" stroke-width="12" stroke-linecap="round"/>
    </svg>""",
    "system-reboot": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="rebGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.25"/></linearGradient></defs>
      <circle cx="128" cy="128" r="100" fill="url(#rebGlass)" stroke="rgba(255, 255, 255, 0.75)" stroke-width="3"/>
      <path d="M 128 64 A 64 64 0 1 1 68 152" fill="none" stroke="#00f3ff" stroke-width="12" stroke-linecap="round"/>
      <polygon points="50,116 88,142 54,166" fill="#ffffff"/>
    </svg>""",
    "system-lock-screen": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="lckGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00ff66" stop-opacity="0.25"/></linearGradient></defs>
      <circle cx="128" cy="128" r="100" fill="url(#lckGlass)" stroke="rgba(255, 255, 255, 0.75)" stroke-width="3"/>
      <rect x="74" y="112" width="108" height="88" rx="22" fill="none" stroke="#00f3ff" stroke-width="10"/>
      <path d="M 96 112 L 96 82 C 96 64 110 52 128 52 C 146 52 160 64 160 82 L 160 112" fill="none" stroke="#ffffff" stroke-width="10"/>
      <circle cx="128" cy="150" r="10" fill="#00ff66"/>
      <line x1="128" y1="156" x2="128" y2="174" stroke="#00ff66" stroke-width="6"/>
    </svg>""",
    "system-suspend": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="susGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00f3ff" stop-opacity="0.25"/></linearGradient></defs>
      <circle cx="128" cy="128" r="100" fill="url(#susGlass)" stroke="rgba(255, 255, 255, 0.75)" stroke-width="3"/>
      <path d="M 152 64 C 98 72 84 130 112 176 C 140 216 196 196 206 170 C 148 184 112 120 152 64 Z" fill="#00f3ff" stroke="#ffffff" stroke-width="3"/>
    </svg>""",
    "system-log-out": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
      <defs><linearGradient id="loGlass" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.35"/><stop offset="100%" stop-color="#00ff66" stop-opacity="0.25"/></linearGradient></defs>
      <circle cx="128" cy="128" r="100" fill="url(#loGlass)" stroke="rgba(255, 255, 255, 0.75)" stroke-width="3"/>
      <path d="M 144 68 L 78 68 C 66 68 56 78 56 90 L 56 166 C 56 178 66 188 78 188 L 144 188" fill="none" stroke="#00f3ff" stroke-width="10" stroke-linecap="round"/>
      <line x1="110" y1="128" x2="200" y2="128" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
      <polyline points="172,100 202,128 172,156" fill="none" stroke="#00ff66" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",
    "window-close": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#ff3b30" stroke="rgba(255,255,255,0.6)" stroke-width="0.8"/>
      <path d="M 5 5 L 11 11 M 11 5 L 5 11" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>
    </svg>""",
    "window-minimize": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#ff9500" stroke="rgba(255,255,255,0.6)" stroke-width="0.8"/>
      <line x1="4.5" y1="8" x2="11.5" y2="8" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>
    </svg>""",
    "window-maximize": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#34c759" stroke="rgba(255,255,255,0.6)" stroke-width="0.8"/>
      <path d="M 5 8 L 11 8 M 8 5 L 8 11" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round"/>
    </svg>""",
    "window-restore": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#34c759" stroke="rgba(255,255,255,0.6)" stroke-width="0.8"/>
      <rect x="5.5" y="5.5" width="5" height="5" fill="none" stroke="#ffffff" stroke-width="1.4" rx="0.5"/>
    </svg>"""
}

# App Aliases
APP_ALIASES = {
    "system-file-manager": ["system-file-manager", "nemo", "org.gnome.Nautilus", "file-manager", "thunar"],
    "view-app-grid": ["view-app-grid", "flowork-launchpad", "xfce4-appfinder", "gnome-applications"],
    "preferences-system": ["preferences-system", "flowork-settings", "xfce4-settings", "preferences-desktop"],
    "preferences-desktop-wallpaper": ["preferences-desktop-wallpaper", "flowork-wallpaper-settings", "wallpaper"],
    "accessories-screenshot": ["accessories-screenshot", "flowork-screenshot", "org.gnome.Screenshot"],
    "utilities-terminal": ["utilities-terminal", "terminal", "Alacritty", "alacritty", "org.gnome.Terminal"]
}

for base_key, svg_data in APPS_SVGS.items():
    aliases = APP_ALIASES.get(base_key, [base_key])
    for alias in aliases:
        target = os.path.join(THEME_DIR, "apps", "scalable", f"{alias}.svg")
        with open(target, "w") as fp:
            fp.write(svg_data)

for cat_key, svg_data in CATEGORIES_SVGS.items():
    target = os.path.join(THEME_DIR, "categories", "scalable", f"{cat_key}.svg")
    with open(target, "w") as fp:
        fp.write(svg_data)

ACTION_ALIASES = {
    "system-shutdown": ["system-shutdown", "system-shutdown-symbolic"],
    "system-reboot": ["system-reboot", "system-restart", "system-restart-symbolic"],
    "system-lock-screen": ["system-lock-screen", "system-lock-screen-symbolic"],
    "system-suspend": ["system-suspend", "system-suspend-symbolic"],
    "system-log-out": ["system-log-out", "system-log-out-symbolic"],
    "window-close": ["window-close", "window-close-symbolic"],
    "window-minimize": ["window-minimize", "window-minimize-symbolic"],
    "window-maximize": ["window-maximize", "window-maximize-symbolic"],
    "window-restore": ["window-restore", "window-restore-symbolic"]
}

for act_key, svg_data in ACTIONS_SVGS.items():
    aliases = ACTION_ALIASES.get(act_key, [act_key])
    for alias in aliases:
        target = os.path.join(THEME_DIR, "actions", "scalable", f"{alias}.svg")
        with open(target, "w") as fp:
            fp.write(svg_data)

# Copy Flowork logos and distributor logos
FLOWORK_LOGO = "/usr/share/icons/flowork/flowork-logo.svg"
FLOWORK_EMBLEM = "/usr/share/icons/flowork/flowork-emblem.svg"

for name in ["distributor-logo", "distributor-logo-debian", "distributor-logo-flowork", "start-here", "start-here-debian", "start-here-flowork", "debian-logo", "debian-swirl", "emblem-flowork", "emblem-debian"]:
    shutil.copyfile(FLOWORK_LOGO, os.path.join(THEME_DIR, "apps", "scalable", f"{name}.svg"))
    shutil.copyfile(FLOWORK_LOGO, os.path.join(THEME_DIR, "places", "scalable", f"{name}.svg"))

shutil.copyfile("/usr/share/icons/flowork/flowork-cyber-hub.svg", os.path.join(THEME_DIR, "apps", "scalable", "flowork-cyber-hub.svg"))
shutil.copyfile("/usr/share/icons/flowork/flowork-studio-hub.svg", os.path.join(THEME_DIR, "apps", "scalable", "flowork-studio-hub.svg"))

print("[Flowork Quantum Glass] Scalable SVG icons generated. Now rasterizing fixed sizes...")

for cat in ["places", "apps", "actions", "categories"]:
    scalable_dir = os.path.join(THEME_DIR, cat, "scalable")
    for f in os.listdir(scalable_dir):
        if not f.endswith(".svg"):
            continue
        src_svg = os.path.join(scalable_dir, f)
        base_name = f[:-4]
        for sz in ["48", "32", "22", "16"]:
            dst_png = os.path.join(THEME_DIR, cat, sz, f"{base_name}.png")
            dst_svg = os.path.join(THEME_DIR, cat, sz, f"{base_name}.svg")
            try:
                subprocess.run(["rsvg-convert", "-w", sz, "-h", sz, src_svg, "-o", dst_png], check=True, stderr=subprocess.DEVNULL)
                shutil.copyfile(src_svg, dst_svg)
            except Exception:
                pass

print("[Flowork Quantum Glass] Rasterization complete!")
