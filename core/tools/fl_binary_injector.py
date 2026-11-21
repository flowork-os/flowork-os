#!/usr/bin/env python3
"""
FLOWORK OS — STRICT BINARY INJECTOR WITH ZERO TOLERANCE GATE (fl_binary_injector.py)
Doctrine: If byte length != target slot, REJECT OUTRIGHT (DITOLAK MENTAH-MENTAH).
Author: Dr. Flow (System Architect) for USER (Supreme Authority).
"""

import sys
import os
import argparse
import subprocess
import shutil

def extract_prompt_from_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if '```text\n' in content:
        idx1 = content.find('```text\n') + len('```text\n')
        idx2 = content.rfind('\n```')
        if idx2 > idx1:
            return content[idx1:idx2]
    return content

def inject_prompt_strictly(bin_path: str, offset: int, target_slot: int, prompt_file: str):
    print("=" * 70)
    print("  FLOWORK OS — STRICT BINARY INJECTION GATEWAY")
    print("=" * 70)
    print(f"  Target Binary       : {bin_path}")
    print(f"  Target Offset       : {hex(offset)} ({offset})")
    print(f"  Alokasi Slot Biner  : {target_slot} bytes")
    print(f"  File Sumber Prompt  : {prompt_file}")
    print("-" * 70)

    # 1. Validasi Keberadaan Berkas
    if not os.path.exists(bin_path):
        print(f"  [ERROR FATAL] Berkas biner {bin_path} tidak ditemukan!", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(prompt_file):
        print(f"  [ERROR FATAL] Berkas prompt {prompt_file} tidak ditemukan!", file=sys.stderr)
        sys.exit(1)

    # 2. Ekstraksi dan Pengukuran Byte UTF-8
    raw_prompt = extract_prompt_from_file(prompt_file)
    raw_prompt = raw_prompt.replace('\r\n', '\n')
    encoded = raw_prompt.encode('utf-8')
    actual_len = len(encoded)

    print(f"  Ukuran Byte Prompt  : {actual_len} bytes")
    delta = target_slot - actual_len

    # 3. GERBANG TOLAK MENTAH-MENTAH (ZERO TOLERANCE GATE)
    if actual_len != target_slot:
        print("!" * 70)
        print("  [DITOLAK MENTAH-MENTAH] ATURAN KETAT DILANGGAR!")
        if delta > 0:
            print(f"  Alasan: Ukuran prompt KURANG {delta} bytes dari kapasitas slot ({target_slot} bytes)!")
            print("  Tindakan: Padatkan teks atau isi doktrin hingga Delta == 0 bytes.")
        else:
            print(f"  Alasan: Ukuran prompt OVERFLOW {-delta} bytes melampaui slot ({target_slot} bytes)!")
            print("  BAHAYA: Injeksi ini PASTI menghancurkan tabel pointer Go dan memicu CRASH!")
        print("  STATUS: INJEKSI DIBATALKAN TOTAL. BINER TIDAK DISENTUH SAMA SEKALI.")
        print("!" * 70)
        sys.exit(1)

    print("  [GERBANG LOLOS] Ukuran byte TEPAT 100% (Delta: 0 bytes). Injeksi diizinkan.")
    print("-" * 70)

    # 4. Backup Otomatis Sebelum Modifikasi
    backup_path = bin_path + ".bak_safety"
    try:
        shutil.copyfile(bin_path, backup_path)
        print(f"  [SAFETY BACKUP] Cadangan darurat disimpan di: {backup_path}")
    except Exception as e:
        print(f"  [ERROR] Gagal membuat safety backup: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Injeksi Bedah Presisi
    try:
        with open(bin_path, 'r+b') as f:
            f.seek(offset)
            f.write(encoded)
            f.flush()
            os.fsync(f.fileno())
        print(f"  [INJEKSI SUKSES] Berhasil menanam {actual_len} bytes pada offset {hex(offset)}.")
    except Exception as e:
        print(f"  [ERROR FATAL] Kegagalan penulisan biner: {e}", file=sys.stderr)
        print("  Melakukan pemulihan biner dari safety backup...")
        shutil.copyfile(backup_path, bin_path)
        sys.exit(1)

    # 6. Verifikasi Pembacaan Ulang & Self-Test Eksekusi
    with open(bin_path, 'rb') as f:
        f.seek(offset)
        verify_bytes = f.read(target_slot)
    if verify_bytes != encoded:
        print("  [ERROR FATAL] Verifikasi read-back gagal! Memulihkan biner...", file=sys.stderr)
        shutil.copyfile(backup_path, bin_path)
        sys.exit(1)

    print("  [VERIFIKASI MEMORI] Read-back biner identik 100% bit-for-bit.")
    print("-" * 70)
    print("  Menjalankan Uji Integritas Biner (-stamp)...")
    
    test_res = subprocess.run([bin_path, '-stamp'], capture_output=True, text=True)
    if test_res.returncode != 0:
        print(f"  [CRASH TERDETEKSI] Biner gagal dieksekusi! Kode: {test_res.returncode}", file=sys.stderr)
        print(f"  Keluaran Galat: {test_res.stderr}", file=sys.stderr)
        print("  Memulihkan biner dari safety backup secara darurat...", file=sys.stderr)
        shutil.copyfile(backup_path, bin_path)
        sys.exit(1)

    # Bersihkan safety backup jika sukses
    if os.path.exists(backup_path):
        os.remove(backup_path)

    print(f"  [HASIL UJI BINER] LOLOS EXIT CODE 0! Biner stabil, tidak crash.")
    print("=" * 70)
    print("  OPERASI INJEKSI SELESAI DENGAN SEMPURNA!")
    print("=" * 70)
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Flowork OS Strict Binary Injector")
    parser.add_argument("--bin", "-b", required=True, type=str, help="Path ke berkas biner target")
    parser.add_argument("--offset", "-o", required=True, type=lambda x: int(x, 0), help="Offset biner (heksadesimal atau desimal)")
    parser.add_argument("--slot", "-s", required=True, type=int, help="Target alokasi slot dalam bytes")
    parser.add_argument("--file", "-f", required=True, type=str, help="Path ke berkas prompt yang akan diinjeksi")
    args = parser.parse_args()

    inject_prompt_strictly(args.bin, args.offset, args.slot, args.file)

if __name__ == "__main__":
    main()
