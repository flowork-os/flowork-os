#!/usr/bin/env python3
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

DOMAIN = "https://dramapendek.asia"
TODAY = datetime.now().strftime("%Y-%m-%d")

def generate():
    with open('/opt/floworkos/apps/dramaboxflow/web/public/melolo_catalog.json', 'r') as f:
        melolo_data = json.load(f)
    with open('/opt/floworkos/apps/dramaboxflow/web/public/dramabox_catalog.json', 'r') as f:
        dramabox_data = json.load(f)

    melolo_list = melolo_data.get('dramas', melolo_data) if isinstance(melolo_data, dict) else melolo_data
    dramabox_list = dramabox_data.get('dramas', dramabox_data) if isinstance(dramabox_data, dict) else dramabox_data

    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Static roots
    static_urls = [
        ("/", "1.0", "daily"),
        ("/melolo.html", "0.9", "daily"),
        ("/dramabox.html", "0.9", "daily"),
    ]

    for path, prio, freq in static_urls:
        u = ET.SubElement(root, "url")
        ET.SubElement(u, "loc").text = f"{DOMAIN}{path}"
        ET.SubElement(u, "lastmod").text = TODAY
        ET.SubElement(u, "changefreq").text = freq
        ET.SubElement(u, "priority").text = prio

    # Melolo dramas (both overview .html and episode-1.html)
    for d in melolo_list:
        slug = d.get('slug') or d.get('bookId') or ''
        if not slug:
            continue
        slug = slug.strip()

        # Episode 1 SEO URL
        u_ep = ET.SubElement(root, "url")
        ET.SubElement(u_ep, "loc").text = f"{DOMAIN}/melolo/{slug}/episode-1.html"
        ET.SubElement(u_ep, "lastmod").text = TODAY
        ET.SubElement(u_ep, "changefreq").text = "weekly"
        ET.SubElement(u_ep, "priority").text = "0.8"

        # Series Overview SEO URL
        u_series = ET.SubElement(root, "url")
        ET.SubElement(u_series, "loc").text = f"{DOMAIN}/melolo/{slug}.html"
        ET.SubElement(u_series, "lastmod").text = TODAY
        ET.SubElement(u_series, "changefreq").text = "weekly"
        ET.SubElement(u_series, "priority").text = "0.7"

    # Dramabox dramas
    for d in dramabox_list:
        bid = d.get('bookId') or ''
        if not bid:
            continue
        bid = str(bid).strip()

        # Episode 1 SEO URL
        u_ep = ET.SubElement(root, "url")
        ET.SubElement(u_ep, "loc").text = f"{DOMAIN}/dramabox/{bid}/episode-1.html"
        ET.SubElement(u_ep, "lastmod").text = TODAY
        ET.SubElement(u_ep, "changefreq").text = "weekly"
        ET.SubElement(u_ep, "priority").text = "0.8"

        # Series Overview SEO URL
        u_series = ET.SubElement(root, "url")
        ET.SubElement(u_series, "loc").text = f"{DOMAIN}/dramabox/{bid}.html"
        ET.SubElement(u_series, "lastmod").text = TODAY
        ET.SubElement(u_series, "changefreq").text = "weekly"
        ET.SubElement(u_series, "priority").text = "0.7"

    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # remove empty lines minidom adds
    lines = [line for line in pretty_xml.splitlines() if line.strip()]
    cleaned_xml = "\n".join(lines) + "\n"

    out_file = '/opt/floworkos/apps/dramaboxflow/web/public/sitemap.xml'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_xml)
    print(f"Sitemap successfully generated at {out_file} with {len(lines)} lines.")

if __name__ == '__main__':
    generate()
