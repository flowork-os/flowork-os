#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for Flowork OS Metaphysics Oracle Engine.
Verifies all 7 subsystems execute accurately with Exit Code 0.
"""

import unittest
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORACLE_SCRIPT = os.path.join(BASE_DIR, "oracle.py")


class TestMetaphysicsOracleEngine(unittest.TestCase):

    def test_bazi_calculation(self):
        """Test BaZi Four Pillars calculation"""
        cmd = [sys.executable, ORACLE_SCRIPT, "bazi", "--solar", "1990-05-15", "--hour", "10:30", "--gender", "男"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("庚午", res.stdout)
        self.assertIn("辛巳", res.stdout)
        self.assertIn("庚辰", res.stdout)
        self.assertIn("神煞", res.stdout)

    def test_qimen_dunjia(self):
        """Test Qi Men Dun Jia time-space calculation"""
        cmd = [sys.executable, ORACLE_SCRIPT, "qimen", "--datetime", "2026-11-19 12:00"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("奇门遁甲", res.stdout)
        self.assertIn("值符星曜", res.stdout)
        self.assertIn("值使八门", res.stdout)
        self.assertIn("九宫盘面", res.stdout)

    def test_ziwei_doushu(self):
        """Test Zi Wei Dou Shu 12 palaces calculation"""
        cmd = [sys.executable, ORACLE_SCRIPT, "ziwei", "--datetime", "1990-05-15 10:30", "--gender", "男"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("紫微斗数", res.stdout)
        self.assertIn("火六局", res.stdout)
        self.assertIn("命宫", res.stdout)
        self.assertIn("身宫", res.stdout)

    def test_fengshui_feixing(self):
        """Test Period 9 Flying Stars Feng Shui"""
        cmd = [sys.executable, ORACLE_SCRIPT, "fengshui", "feixing", "--sit", "子", "--facing", "午", "--yun", "9"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("9运 · 子山午向", res.stdout)
        self.assertIn("双星到坐", res.stdout)

    def test_yinyuan_zodiac_and_sticks(self):
        """Test Yue Lao fortune stick and zodiac compatibility"""
        cmd1 = [sys.executable, ORACLE_SCRIPT, "yinyuan", "--zodiac", "鼠", "牛"]
        res1 = subprocess.run(cmd1, capture_output=True, text=True)
        self.assertEqual(res1.returncode, 0)
        self.assertIn("六合相生", res1.stdout)

        cmd2 = [sys.executable, ORACLE_SCRIPT, "yinyuan", "--draw", "--name", "李雷", "--question", "姻缘前景"]
        res2 = subprocess.run(cmd2, capture_output=True, text=True)
        self.assertEqual(res2.returncode, 0)
        self.assertIn("月老灵签", res2.stdout)
        self.assertIn("签诗曰", res2.stdout)

    def test_tarot_spread(self):
        """Test Western 78-card Tarot draw"""
        cmd = [sys.executable, ORACLE_SCRIPT, "tarot", "--spread", "three", "--question", "AI autonomy"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("三牌阵", res.stdout)
        self.assertIn("cards", res.stdout)

    def test_wisdom_counseling(self):
        """Test Classical Scripture wisdom consultation"""
        cmd = [sys.executable, ORACLE_SCRIPT, "wisdom", "--query", "心烦意乱，执念太深"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("智者心语", res.stdout)
        self.assertIn("应机经偈", res.stdout)


if __name__ == "__main__":
    unittest.main()
