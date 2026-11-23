#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
姻缘测算与月老灵签系统 (Affinity & Yue Lao Divination Engine)
支持：月老100灵签、生肖合婚配对、五行姻缘互补分析。
"""

import os
import re
import sys
import hashlib
import argparse
from datetime import datetime

REF_DIR = os.path.join(os.path.dirname(__file__), "references")
STICKS_FILE = os.path.join(REF_DIR, "fortune-sticks.md")

# 生肖关系表
ZODIAC_ANIMALS = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 六合 (六组上上配对)
LIU_HE = {
    "子": "丑", "丑": "子",  # 鼠牛
    "寅": "亥", "亥": "寅",  # 虎猪
    "卯": "戌", "戌": "卯",  # 兔狗
    "辰": "酉", "酉": "辰",  # 龙鸡
    "巳": "申", "申": "巳",  # 蛇猴
    "午": "未", "未": "午",  # 马羊
}

ZODIAC_TO_BRANCH = {
    "鼠": "子", "牛": "丑", "虎": "寅", "兔": "卯",
    "龙": "辰", "蛇": "巳", "马": "午", "羊": "未",
    "猴": "申", "鸡": "酉", "狗": "戌", "猪": "亥"
}
BRANCH_TO_ZODIAC = {v: k for k, v in ZODIAC_TO_BRANCH.items()}

# 三合 (四大三合格局)
SAN_HE_GROUPS = [
    {"申", "子", "辰"},  # 猴鼠龙 水局
    {"巳", "酉", "丑"},  # 蛇鸡牛 金局
    {"寅", "午", "戌"},  # 虎马狗 火局
    {"亥", "卯", "未"},  # 猪兔羊 木局
]

# 六冲 (六大相冲)
LIU_CHONG = {
    "子": "午", "午": "子",  # 鼠马冲
    "丑": "未", "未": "丑",  # 牛羊冲
    "寅": "申", "申": "寅",  # 虎猴冲
    "卯": "酉", "酉": "卯",  # 兔鸡冲
    "辰": "戌", "戌": "辰",  # 龙狗冲
    "巳": "亥", "亥": "巳",  # 蛇猪冲
}

# 六害
LIU_HAI = {
    "子": "未", "未": "子",
    "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申",
    "酉": "戌", "戌": "酉",
}

# 五行相生相克
WUXING_SHENG = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
WUXING_KE = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}


def parse_sticks():
    """解析 fortune-sticks.md 获取 100 支签文"""
    if not os.path.exists(STICKS_FILE):
        return {}
    
    with open(STICKS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    sticks = {}
    pattern = re.compile(r"第([一二三四五六七八九十百0-9]+)签[ ·\s]+([^\n\r]+)")
    
    # 切割每支签
    sections = re.split(r"(?=第[一二三四五六七八九十百0-9]+签)", content)
    chinese_num_map = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15, "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
        "二十一": 21, "二十二": 22, "二十三": 23, "二十四": 24, "二十五": 25, "二十六": 26, "二十七": 27, "二十八": 28, "二十九": 29, "三十": 30,
        "三十一": 31, "三十二": 32, "三十三": 33, "三十四": 34, "三十五": 35, "三十六": 36, "三十七": 37, "三十八": 38, "三十九": 39, "四十": 40,
        "四十一": 41, "四十二": 42, "四十三": 43, "四十四": 44, "四十五": 45, "四十六": 46, "四十七": 47, "四十八": 48, "四十九": 49, "五十": 50,
        "五十一": 51, "五十二": 52, "五十三": 53, "五十四": 54, "五十五": 55, "五十六": 56, "五十七": 57, "五十八": 58, "五十九": 59, "六十": 60,
        "六十一": 61, "六十二": 62, "六十三": 63, "六十四": 64, "六十五": 65, "六十六": 66, "六十七": 67, "六十八": 68, "六十九": 69, "七十": 70,
        "七十一": 71, "七十二": 72, "七十三": 73, "七十四": 74, "七十五": 75, "七十六": 76, "七十七": 77, "七十八": 78, "七十九": 79, "八十": 80,
        "八十一": 81, "八十二": 82, "八十三": 83, "八十四": 84, "八十五": 85, "八十六": 86, "八十七": 87, "八十八": 88, "八十九": 89, "九十": 90,
        "九十一": 91, "九十二": 92, "九十三": 93, "九十四": 94, "九十五": 95, "九十六": 96, "九十七": 97, "九十八": 98, "九十九": 99, "一百": 100
    }

    for sec in sections:
        sec = sec.strip()
        if not sec.startswith("第"):
            continue
        m = pattern.search(sec)
        if not m:
            continue
        num_str = m.group(1).strip()
        grade = m.group(2).strip()
        num = chinese_num_map.get(num_str)
        if not num:
            if num_str.isdigit():
                num = int(num_str)
            else:
                continue
        
        # 提取诗文
        poem = ""
        poem_match = re.search(r"```(.*?)```", sec, re.DOTALL)
        if poem_match:
            poem = poem_match.group(1).strip()

        # 提取签解与解读
        jie = ""
        jie_match = re.search(r"签解：([^\n\r]+)", sec)
        if jie_match:
            jie = jie_match.group(1).strip()

        jiedu = ""
        jiedu_match = re.search(r"姻缘解读：([^\n\r]+)", sec)
        if jiedu_match:
            jiedu = jiedu_match.group(1).strip()

        sticks[num] = {
            "number": num,
            "title": f"第{num}签",
            "grade": grade,
            "poem": poem,
            "explanation": jie,
            "interpretation": jiedu,
            "raw": sec
        }
    return sticks


def calculate_stick_number(name: str = "", question: str = "") -> int:
    """根据确定性哈希计算签号 (1-100)"""
    now = datetime.now()
    shichen_idx = (now.hour + 1) // 2 % 12
    day_num = now.day
    name_sum = sum(ord(c) for c in (name or "缘主"))
    q_sum = sum(ord(c) for c in (question or "求测姻缘"))
    
    stick_id = (name_sum + q_sum + shichen_idx + day_num) % 100 + 1
    return stick_id


def evaluate_zodiac(z1: str, z2: str) -> dict:
    """评估两个生肖的关系"""
    b1 = ZODIAC_TO_BRANCH.get(z1, z1)
    b2 = ZODIAC_TO_BRANCH.get(z2, z2)
    name1 = BRANCH_TO_ZODIAC.get(b1, z1)
    name2 = BRANCH_TO_ZODIAC.get(b2, z2)

    result = {
        "zodiac1": name1,
        "zodiac2": name2,
        "level": "中平",
        "relation": "平淡互洽",
        "score": 75,
        "analysis": ""
    }

    if LIU_HE.get(b1) == b2:
        result["level"] = "上上大吉"
        result["relation"] = "天作之合 · 六合相生"
        result["score"] = 98
        result["analysis"] = f"{name1}与{name2}互为六合贵人，天性相吸，心意相通，彼此包容，感情深厚稳固。"
    elif any(b1 in grp and b2 in grp for grp in SAN_HE_GROUPS):
        result["level"] = "上吉"
        result["relation"] = "情投意合 · 三合贵局"
        result["score"] = 90
        result["analysis"] = f"{name1}与{name2}属于三��格局，志同道合，互帮互助，能同甘共苦建立美满家业。"
    elif LIU_CHONG.get(b1) == b2:
        result["level"] = "下凶 (需化解)"
        result["relation"] = "性格相冲 · 六冲对立"
        result["score"] = 55
        result["analysis"] = f"{name1}与{name2}相冲，性格与行事风格差异较大，易生口角磨擦，需多沟通包容或以风水/贵人调和。"
    elif LIU_HAI.get(b1) == b2:
        result["level"] = "中下 (需注意)"
        result["relation"] = "暗耗相克 · 六害暗伤"
        result["score"] = 62
        result["analysis"] = f"{name1}与{name2}犯六害，外表客气但内心易存猜忌或产生隐性误会，须坦诚相见，不积心结。"
    else:
        result["level"] = "中平"
        result["relation"] = "平凡踏实 · 顺遂有常"
        result["score"] = 78
        result["analysis"] = f"{name1}与{name2}无大冲克亦无六合，属于自自然然之常态姻缘，事在人为，以德润身即可相守一生。"

    return result


def evaluate_wuxing(w1: str, w2: str) -> dict:
    """五行相生相克分析"""
    if w1 == w2:
        return {"relation": f"同气比和 ({w1}+{w2})", "level": "良配", "desc": "志同道合，旗鼓相当，但偶有争强之虞。"}
    if WUXING_SHENG.get(w1) == w2:
        return {"relation": f"{w1}生{w2}", "level": "大吉", "desc": f"一方主动付出滋养，感情顺遂而有润泽之功。"}
    if WUXING_SHENG.get(w2) == w1:
        return {"relation": f"{w2}生{w1}", "level": "大吉", "desc": f"对方对你呵护备至，深得照拂与关怀。"}
    if WUXING_KE.get(w1) == w2:
        return {"relation": f"{w1}克{w2}", "level": "相克制约", "desc": f"一方性格强势主导，需学会收敛柔和，相处之道贵在平衡。"}
    if WUXING_KE.get(w2) == w1:
        return {"relation": f"{w2}克{w1}", "level": "相克受制", "desc": f"易感对方施压或要求过高，须明立边界，以柔克刚。"}
    return {"relation": "五行互济", "level": "平平", "desc": "五行相平，随顺自然。"}


def main():
    parser = argparse.ArgumentParser(description="月老姻缘签诗与生肖合婚测算工具")
    parser.add_argument("--stick", type=int, help="直接查询第 N 支签 (1-100)")
    parser.add_argument("--draw", action="store_true", help="求测摇一支月老签")
    parser.add_argument("--name", type=str, default="", help="缘主姓名")
    parser.add_argument("--question", type=str, default="", help="求测婚姻感情问题")
    parser.add_argument("--zodiac", nargs=2, metavar=("生肖1", "生肖2"), help="测算两个生肖婚配 (如: 鼠 牛)")
    parser.add_argument("--wuxing", nargs=2, metavar=("五行1", "五行2"), help="五行生克配对 (如: 木 火)")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()
    sticks = parse_sticks()

    if args.zodiac:
        res = evaluate_zodiac(args.zodiac[0], args.zodiac[1])
        if args.json:
            import json
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 48)
            print(f"【生肖合婚测算】 {res['zodiac1']} ❤️ {res['zodiac2']}")
            print(f"姻缘评级：{res['level']} (契合度指数：{res['score']}/100)")
            print(f"格局格局：{res['relation']}")
            print(f"命理详解：{res['analysis']}")
            print("=" * 48)
        return 0

    if args.wuxing:
        res = evaluate_wuxing(args.wuxing[0], args.wuxing[1])
        print(f"【五行配对】 {args.wuxing[0]} ⇄ {args.wuxing[1]}: {res['level']} | {res['relation']} - {res['desc']}")
        return 0

    if args.draw or args.stick or (not args.zodiac and not args.wuxing):
        stick_id = args.stick if args.stick else calculate_stick_number(args.name, args.question)
        if stick_id not in sticks:
            # 容错 fallback
            stick_id = (stick_id % len(sticks)) or 1
        
        st = sticks.get(stick_id, {
            "number": stick_id,
            "title": f"第{stick_id}签",
            "grade": "吉",
            "poem": "有缘千里来相会，无缘对面不相逢。",
            "explanation": "随顺因缘，自得佳偶。",
            "interpretation": "静心修己，静待花开。"
        })

        if args.json:
            import json
            print(json.dumps(st, ensure_ascii=False, indent=2))
        else:
            print("=" * 50)
            print(f"  🎋 月老灵签 · 第 {st['number']} 签 【{st['grade']}】")
            print("=" * 50)
            if args.name or args.question:
                print(f"求测缘主：{args.name or '求缘弟子'} | 心愿：{args.question or '测算婚姻感情'}")
                print("-" * 50)
            print("【签诗曰】")
            for line in st["poem"].split("\n"):
                if line.strip():
                    print(f"    {line.strip()}")
            print("-" * 50)
            print(f"【签解】{st['explanation']}")
            print(f"【姻缘解读】{st['interpretation']}")
            print("=" * 50)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
