#!/usr/bin/env python3
"""
FLOWORK OS — STRICT BYTE CALCULATOR & VERIFIER (fl_byte_calc.py)
Standard: Zero Byte Deviation.
Author: Dr. Flow (System Architect) for USER (Supreme Authority).
"""

import sys
import os
import argparse

def calculate_bytes(text: str, target_slot: int = None):
    # Ensure text has Unix newlines
    normalized_text = text.replace('\r\n', '\n')
    encoded = normalized_text.encode('utf-8')
    byte_count = len(encoded)
    char_count = len(normalized_text)
    
    print("=" * 65)
    print("  FLOWORK OS — STRICT BYTE CALCULATION & AUDIT REPORT")
    print("=" * 65)
    print(f"  Total Ukuran Byte (UTF-8) : {byte_count} bytes")
    print(f"  Total Jumlah Karakter     : {char_count} chars")
    
    # Check multi-byte characters
    multi_bytes = [(i, c, len(c.encode('utf-8'))) for i, c in enumerate(normalized_text) if len(c.encode('utf-8')) > 1]
    print(f"  Karakter Multi-Byte       : {len(multi_bytes)} terdeteksi")
    if multi_bytes:
        for idx, char, blen in multi_bytes[:10]:
            print(f"    - Karakter '{char}' di indeks {idx}: {blen} bytes")
        if len(multi_bytes) > 10:
            print(f"    - ... dan {len(multi_bytes) - 10} karakter lainnya.")

    if target_slot is not None:
        delta = target_slot - byte_count
        print("-" * 65)
        print(f"  Target Kapasitas Slot     : {target_slot} bytes")
        print(f"  Selisih (Delta)           : {delta} bytes")
        if delta == 0:
            print("  STATUS AUDIT              : [LOLOS / PASS] Presisi 100% (Delta: 0 bytes)")
            print("                              Aman diinjeksi tanpa risiko SIGSEGV/crash.")
        elif delta > 0:
            print(f"  STATUS AUDIT              : [GAGAL / REJECT] Kurang {delta} bytes!")
            print("                              Wajib diisi atau dipadatkan hingga Delta = 0.")
        else:
            print(f"  STATUS AUDIT              : [BAHAYA / REJECT] OVERFLOW {-delta} bytes!")
            print("                              FATAL: Akan merusak tabel pointer Go & CRASH!")
    print("=" * 65)
    return byte_count, (delta if target_slot is not None else 0)

def extract_prompt_from_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if '```text\n' in content:
        idx1 = content.find('```text\n') + len('```text\n')
        idx2 = content.rfind('\n```')
        if idx2 > idx1:
            return content[idx1:idx2]
    return content

def main():
    parser = argparse.ArgumentParser(description="Flowork OS Strict Byte Calculator")
    parser.add_argument("--file", "-f", type=str, help="Path ke file prompt (.md / .txt)")
    parser.add_argument("--text", "-t", type=str, help="Teks prompt langsung")
    parser.add_argument("--slot", "-s", type=int, help="Target slot biner dalam bytes")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: Berkas {args.file} tidak ditemukan!", file=sys.stderr)
            sys.exit(1)
        raw_text = extract_prompt_from_file(args.file)
        print(f"Membaca berkas: {args.file}")
        byte_count, delta = calculate_bytes(raw_text, args.slot)
    elif args.text:
        byte_count, delta = calculate_bytes(args.text, args.slot)
    else:
        print("Gunakan flag --file [path] atau --text [string]. Contoh:")
        print("  ./fl_byte_calc.py -f /home/awenkaudico/Downloads/agent/done/015_expert_developer_persona.md -s 5209")
        sys.exit(1)

    if args.slot is not None and delta != 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
