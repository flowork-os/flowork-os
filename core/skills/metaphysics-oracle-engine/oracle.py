#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flowork OS Sovereign Metaphysics & Oracle Engine (玄学与传统智慧统一引擎)
Consolidates 7 Eastern & Western Divination and Philosophical Subsystems:
  1. BaZi (四柱八字命理 · 纯Python确定性排盘)
  2. Qi Men Dun Jia (奇门遁甲 · 时家转盘奇门)
  3. Zi Wei Dou Shu (紫微斗数 · 十二宫星曜四化)
  4. Feng Shui & Kanyu (堪舆风水 · 八宅/九运玄空飞星/择日)
  5. Yinyuan & Yue Lao (月老���签 · 生肖合婚姻缘测算)
  6. Tarot (西方78张塔罗牌阵与心理原型)
  7. Classical Wisdom (东方儒释道心法 · 心经/金刚经/坛经/道德经)
"""

import os
import sys
import json
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODULES_DIR = os.path.join(BASE_DIR, "modules")

# Ensure submodules are in sys.path
for mod_name in ["bazi", "qimen", "ziwei", "fengshui", "yinyuan", "tarot", "wisdom"]:
    p = os.path.join(MODULES_DIR, mod_name)
    if p not in sys.path:
        sys.path.insert(0, p)


def handle_bazi(args, extra_args):
    """四柱八字排盘"""
    bazi_script = os.path.join(MODULES_DIR, "bazi", "pai_pan.py")
    cmd = [sys.executable, bazi_script]

    sex = "男"
    if args.gender in ["女", "female", "f"]:
        sex = "女"

    if args.solar:
        cmd.extend(["--solar", args.solar])
    if args.hour:
        cmd.extend(["--hour", args.hour])
    cmd.extend(["--sex", sex])

    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(cmd).returncode


def handle_qimen(args):
    """奇门遁甲时家转盘排盘"""
    import qimen_cli
    time_str = args.datetime or "now"
    payload = {
        "time_input": time_str,
        "question_type": args.type or "通用测事",
        "question_goal": args.goal or "分析当前时空局势能量吉凶",
        "timezone": args.timezone or "Asia/Shanghai",
        "use_now": True if time_str == "now" else False,
    }
    res = qimen_cli.build_output(payload)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    chart = res.get("chart", {})
    calendar = res.get("calendar", {})
    jieqi = calendar.get("jieqi", {})

    print("=" * 64)
    print("      🧭 奇门遁甲 · 时家转盘排盘 (Qi Men Dun Jia)")
    print("=" * 64)
    print(f"公历时间：{calendar.get('solar', {}).get('ymd_hms', '')}")
    print(f"当前节气：{jieqi.get('active_jie', '')} (下一节气：{jieqi.get('next_jie', '')})")
    print(f"定局：{chart.get('dun_type', '')}{chart.get('yuan', '')}{chart.get('ju_number', '')}局 | 旬首：{chart.get('xunshou', '')} (仪：{chart.get('hidden_yi', '')})")
    zhifu = chart.get('zhifu', {})
    zhishi = chart.get('zhishi', {})
    zf_star = zhifu.get('star', '') if isinstance(zhifu, dict) else str(zhifu)
    zs_door = zhishi.get('door', '') if isinstance(zhishi, dict) else str(zhishi)
    yima = chart.get('hour_yima', {})
    yima_str = yima.get('branch', '') if isinstance(yima, dict) else str(yima)
    print(f"值符星曜：{zf_star} | 值使八门：{zs_door}")
    print(f"时马星位：{yima_str}方 | 旬空地支：{chart.get('kongwang', [])}")
    print("-" * 64)
    print("【九宫盘面 (洛书九宫八门九星八神)】")
    palaces = chart.get("palaces", [])
    for pal in palaces:
        p_id = pal.get("palace", 0)
        name = pal.get("name", "")
        direction = pal.get("direction", "")
        door = str(pal.get("door") or "-")
        star = str(pal.get("star") or "-")
        god = str(pal.get("god") or "-")
        sky = str(pal.get("sky_stem") or "-")
        earth = str(pal.get("earth_stem") or "-")
        print(f"  • [{p_id}宫 {name} · {direction}] 神:{god:<4} | 星:{star:<4} | 门:{door:<4} | 天干:{sky} 地干:{earth}")
    print("=" * 64)
    return 0


def handle_ziwei(args):
    """紫微斗数排盘"""
    import ziwei_cli
    gender = "男"
    if args.gender in ["女", "female", "f"]:
        gender = "女"

    payload = {
        "birth_time": args.datetime,
        "gender": gender,
    }
    res = ziwei_cli.build_output(payload)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    chart = res.get("chart", {})
    print("=" * 64)
    print("      ✨ 紫微斗数 · 十二宫星盘 (Zi Wei Dou Shu)")
    print("=" * 64)
    print(f"阳历生辰：{args.datetime} ({gender}命)")
    print(f"命主星：{chart.get('ming_zhu')} | 身主星：{chart.get('shen_zhu')} | 五行局：{chart.get('wuxing_ju', {}).get('name')}")
    ming_g = chart.get('ming_gong', {})
    shen_g = chart.get('shen_gong', {})
    print(f"命宫地支：{ming_g.get('branch')} ({ming_g.get('ganzhi')}) | 身宫归宿：{shen_g.get('palace')}宫")
    print("-" * 64)
    print("【十二宫主星分布】")
    palaces = chart.get("palaces", [])
    for pal in palaces:
        name = pal.get("name")
        branch = pal.get("branch")
        stem = pal.get("stem")
        stars_list = []
        for s in pal.get("major_stars", []):
            st_name = s.get("name", "")
            bright = s.get("brightness", "")
            sihua = s.get("sihua")
            item = f"{st_name}({bright})" if bright else st_name
            if sihua:
                item += f"[{sihua}]"
            stars_list.append(item)
        stars_str = ", ".join(stars_list) if stars_list else "无主星"
        is_shen = " [身宫]" if pal.get("is_shen_gong") else ""
        print(f"  • {stem}{branch}位 【{name}宫{is_shen}】: {stars_str}")
    print("=" * 64)
    return 0


def handle_fengshui(args, extra_args):
    """堪舆风水系统 (八宅/玄空飞星/择日)"""
    script_path = os.path.join(MODULES_DIR, "fengshui", "fengshui.py")
    cmd = [sys.executable, script_path] + extra_args
    return subprocess.run(cmd).returncode


def handle_yinyuan(args, extra_args):
    """月老灵签与生肖姻缘"""
    script_path = os.path.join(MODULES_DIR, "yinyuan", "matcher.py")
    cmd = [sys.executable, script_path]
    if args.draw:
        cmd.append("--draw")
    if args.stick:
        cmd.extend(["--stick", str(args.stick)])
    if args.name:
        cmd.extend(["--name", args.name])
    if args.question:
        cmd.extend(["--question", args.question])
    if args.zodiac:
        cmd.extend(["--zodiac", args.zodiac[0], args.zodiac[1]])
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd).returncode


def handle_tarot(args, extra_args):
    """西方78张塔罗排阵"""
    script_path = os.path.join(MODULES_DIR, "tarot", "draw.py")
    cmd = [sys.executable, script_path]
    if args.spread:
        cmd.extend(["--spread", args.spread])
    if args.question:
        cmd.extend(["--question", args.question])
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd).returncode


def handle_wisdom(args, extra_args):
    """东方哲学典籍智慧与释疑导师"""
    script_path = os.path.join(MODULES_DIR, "wisdom", "counselor.py")
    cmd = [sys.executable, script_path]
    if args.query:
        cmd.extend(["--query", args.query])
    if args.sutra:
        cmd.extend(["--sutra", args.sutra])
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(
        prog="flowork-oracle",
        description="Flowork OS 统一玄学与典籍智慧系统 (Metaphysics Oracle Engine)"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="选择子系统")

    # 1. BaZi
    p_bazi = subparsers.add_parser("bazi", help="四柱八字排盘与十神大运")
    p_bazi.add_argument("--solar", type=str, help="阳历出生日期 YYYY-MM-DD")
    p_bazi.add_argument("--hour", type=str, default="12:00", help="出生时间 HH:MM")
    p_bazi.add_argument("--gender", type=str, default="男", choices=["男", "女", "male", "female"], help="性别")

    # 2. Qi Men Dun Jia
    p_qimen = subparsers.add_parser("qimen", help="奇门遁甲时家转盘排盘")
    p_qimen.add_argument("--datetime", type=str, default="now", help="排盘时间 'YYYY-MM-DD HH:MM' 或 'now'")
    p_qimen.add_argument("--type", type=str, default="通用测事", help="求测事项类型")
    p_qimen.add_argument("--goal", type=str, default="决策时空吉凶判断", help="测事目标")
    p_qimen.add_argument("--timezone", type=str, default="Asia/Shanghai", help="时区")
    p_qimen.add_argument("--json", action="store_true", help="输出完整结构化 JSON")

    # 3. Zi Wei Dou Shu
    p_ziwei = subparsers.add_parser("ziwei", help="紫微斗数十二宫星曜排盘")
    p_ziwei.add_argument("--datetime", type=str, required=True, help="阳历生辰 'YYYY-MM-DD HH:MM'")
    p_ziwei.add_argument("--gender", type=str, default="男", choices=["男", "女", "male", "female"], help="性别")
    p_ziwei.add_argument("--json", action="store_true", help="输出完整结构化 JSON")

    # 4. Feng Shui
    p_fs = subparsers.add_parser("fengshui", help="堪舆风水 (八宅、九运玄空飞星、日历、择日)")

    # 5. Yinyuan
    p_yy = subparsers.add_parser("yinyuan", help="月老灵签与生肖合婚测算")
    p_yy.add_argument("--draw", action="store_true", help="摇一支月老灵签")
    p_yy.add_argument("--stick", type=int, help="查询指定签号 (1-100)")
    p_yy.add_argument("--name", type=str, help="求缘弟子姓名")
    p_yy.add_argument("--question", type=str, help="感情婚姻求问")
    p_yy.add_argument("--zodiac", nargs=2, help="双人生肖配对 (如: 龙 鸡)")

    # 6. Tarot
    p_tarot = subparsers.add_parser("tarot", help="西方78张塔罗牌阵与心理原型")
    p_tarot.add_argument("--spread", type=str, default="three", choices=["single", "three", "celtic", "love", "decision"], help="牌阵类型")
    p_tarot.add_argument("--question", type=str, default="", help="占卜求问事项")

    # 7. Wisdom
    p_wisdom = subparsers.add_parser("wisdom", help="东方哲学典籍智慧与心法解惑 (心经/金刚经/坛经/道德经)")
    p_wisdom.add_argument("--query", type=str, help="输入心中的生活困惑、焦虑或人际冲突")
    p_wisdom.add_argument("--sutra", choices=["heart_sutra", "diamond_sutra", "platform_sutra", "dao_de_jing"], help="直接查阅核心典籍")

    args, unknown = parser.parse_known_args()

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "bazi":
        return handle_bazi(args, unknown)
    elif args.subcommand == "qimen":
        return handle_qimen(args)
    elif args.subcommand == "ziwei":
        return handle_ziwei(args)
    elif args.subcommand == "fengshui":
        return handle_fengshui(args, unknown)
    elif args.subcommand == "yinyuan":
        return handle_yinyuan(args, unknown)
    elif args.subcommand == "tarot":
        return handle_tarot(args, unknown)
    elif args.subcommand == "wisdom":
        return handle_wisdom(args, unknown)

    return 0


if __name__ == "__main__":
    sys.exit(main())
