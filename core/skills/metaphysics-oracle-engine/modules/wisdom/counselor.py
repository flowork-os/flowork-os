#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方哲学典籍智慧与释疑导师系统 (Eastern Classical Philosophy & Wisdom Counseling Engine)
涵盖：心经、金刚经、六祖坛经、道德经及禅门智慧心法。
"""

import os
import sys
import argparse
import json

SCRIPTURES = {
    "heart_sutra": {
        "title": "般若波罗蜜多心经",
        "author": "唐玄奘法师译",
        "theme": "照见五蕴皆空，度一切苦厄",
        "key_verse": "色不异空，空不异色；色即是空，空即是色。受想行识，亦复如是。舍利子，是诸法空相，不生不灭，不垢不净，不增不减。是故空中无色，无受想行识……心无挂碍，无挂碍故，无有恐怖，远离颠倒梦想，究竟涅槃。",
        "remedy": "用于破除心念固执、过度焦虑、恐惧未来与患得患失。观照一切所执皆因缘和合，本无实法可得，从而放下重担，复归安宁。"
    },
    "diamond_sutra": {
        "title": "金刚般若波罗蜜经",
        "author": "姚秦鸠摩罗什译",
        "theme": "应无所住而生其心",
        "key_verse": "一切有为法，如梦幻泡影，如露亦如电，应作如是观。\n凡所有相，皆是虚妄。若见诸相非相，则见如来。\n不应住色生心，不应住声香味触法生心，应无所住而生其心。",
        "remedy": "用于破除成败执着、人我争端、名利枷锁。事来则应，事去不留。行一切善法，而不执著功劳与所得。"
    },
    "platform_sutra": {
        "title": "六祖法宝坛经",
        "author": "唐慧能大师",
        "theme": "自性本自清净，明心见性",
        "key_verse": "菩提本无树，明镜亦非台。本来无一物，何处惹尘埃！\n自性能含万法，名含藏识。若思量一切恶事，即行于恶；若思量一切善事，便修于善。\n外离相即禅，内不乱即定。外禅内定，是为禅定。",
        "remedy": "用于破除向外攀缘求助的疲惫，回归内在自性的圆满自足。烦恼即菩提，迷人念佛求生西方，悟人生处自净其心。"
    },
    "dao_de_jing": {
        "title": "道德经",
        "author": "老子",
        "theme": "道法自然，上善若水，无为而无不为",
        "key_verse": "上善若水。水善利万物而不争，处众人之所恶，故几于道。\n持而盈之，不如其已；揣而锐之，不可长保。金玉满堂，莫之能守；富贵而骄，自遗其咎。功成身退，天之道也。\n祸兮福之所倚，福兮祸之所伏。孰知其极？其无正也。",
        "remedy": "用于缓解内卷压力、处世焦虑与强求强为之疲惫。学水之至柔以克刚强，知止知足，顺应客观节律，不争而天下莫能与之争。"
    }
}

DILEMMAS = [
    {
        "keywords": ["焦虑", "担心", "未来", "恐惧", "压力", "失眠"],
        "source": "heart_sutra",
        "counsel": "【观照无常 · 心无挂碍】\n你所担忧之境，皆是大脑对未发生之事的虚构投射。世事如露如电，未来变幻莫测，过度预演痛苦只会徒耗精神。请深吸一口气，觉察当下身心：此时此刻你呼吸尚在、身体安稳。专注做好眼前这一步，其余皆由因缘定夺。"
    },
    {
        "keywords": ["失去", "失败", "被骗", "失恋", "遗憾", "痛苦"],
        "source": "diamond_sutra",
        "counsel": "【如梦如泡 · 缘聚缘散】\n凡有聚者必有散，凡有起者必有灭。你所痛苦的不是失去这件事本身，而是心中不甘接受因缘的变化。一切有为法如梦幻泡影，曾经拥有的体验与滋养已经化入你的生命，而物象自当随风归去。应无所住，放手便是新生。"
    },
    {
        "keywords": ["迷茫", "目标", "意义", "我是谁", "内耗", "自卑"],
        "source": "platform_sutra",
        "counsel": "【自性具足 · 莫向外求】\n你总以为缺少某种外在的认可、文凭、财富才算成功，因而不断在外界比较中产生耗损与自卑。六祖云：何期自性，本自具足！你的清净本心从未残缺，莫把别人的尺子用来量自己的生命。行你所愿，守你所爱，自心光明，何处惹尘。"
    },
    {
        "keywords": ["竞争", "冲突", "人际", "吵架", "愤怒", "不公"],
        "source": "dao_de_jing",
        "counsel": "【上善若水 · 不争之德】\n与人相争，胜者结怨，败者抱恨，双双困于情绪的浊流之中。水避高趋下，遇阻绕行，容纳百川却终成大海。面对挑衅与不公，以退为进，不把生命能量浪费在低维摩擦上。守住自己的德行与境界，时间自会给出最公正的裁决。"
    }
]


def counsel_query(query: str) -> dict:
    matched = None
    for item in DILEMMAS:
        for kw in item["keywords"]:
            if kw in query:
                matched = item
                break
        if matched:
            break

    if not matched:
        matched = DILEMMAS[0]

    sutra = SCRIPTURES[matched["source"]]
    return {
        "query": query,
        "sutra_title": sutra["title"],
        "author": sutra["author"],
        "theme": sutra["theme"],
        "key_verse": sutra["key_verse"],
        "counsel": matched["counsel"]
    }


def main():
    parser = argparse.ArgumentParser(description="东方哲学典籍智慧与心法解惑导师")
    parser.add_argument("--query", type=str, help="输入心中的困惑、情绪烦恼或生活议题")
    parser.add_argument("--sutra", choices=list(SCRIPTURES.keys()), help="直接阅读特定典籍原旨 (heart_sutra, diamond_sutra, platform_sutra, dao_de_jing)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    if args.sutra:
        st = SCRIPTURES[args.sutra]
        if args.json:
            print(json.dumps(st, ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print(f"📖 《{st['title']}》 ({st['author']})")
            print(f"核心旨归：{st['theme']}")
            print("-" * 60)
            print(f"【经文核心要义】\n{st['key_verse']}")
            print("-" * 60)
            print(f"【修心对治之法】\n{st['remedy']}")
            print("=" * 60)
        return 0

    q = args.query or "人生迷茫与焦虑"
    res = counsel_query(q)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"🪷 智者心语 · 答缘主之惑：『{res['query']}』")
        print("=" * 60)
        print(f"【应机经偈】《{res['sutra_title']}》")
        print(f"旨归：{res['theme']}")
        print(f"经云：\n    {res['key_verse']}")
        print("-" * 60)
        print(f"【导师开示】\n{res['counsel']}")
        print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
