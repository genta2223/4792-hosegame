"""Ojii's Advice AI - Logic for horse evaluation and comments."""
import random

def get_horse_advice(horse, calendar):
    """
    Generate dynamic advice from Ojii based on horse's age, stats, and potential (caps).
    """
    # Potential calculation (Speed/Stamina/Guts avg)
    selected_caps = [
        horse.caps.get("speed", 200),
        horse.caps.get("stamina", 200),
        horse.caps.get("guts", 200)
    ]
    avg_cap = sum(selected_caps) / len(selected_caps)
    
    is_raced = getattr(horse, 'wins', 0) > 0 or getattr(horse, 'prize_money', 0) > 0
    age = horse.age

    # --- 2 Years Old (Pre-race) ---
    if age == 2 and not is_raced:
        return random.choice([
            "まだ分からんさぁ。比川の軽めでもさせてみるさぁ。",
            "これからの馬だね。焦らず育てようねぇ。",
            "素質は眠っているかもしれん。楽しみさぁ。",
            "与那国の土が、この子を強くしてくれるさぁ。"
        ])

    # --- 2 Years Old (After-race) ---
    if age == 2 and is_raced:
        if avg_cap >= 235:
            return random.choice([
                "少し砂の味が分かってきたさぁ。この子は…化けるかもしれんよ！",
                "走る姿に力強さが出てきたさぁ。末恐ろしい素質を感じるねぇ。"
            ])
        elif avg_cap >= 210:
            return random.choice([
                "少し砂の味が分かってきたさぁ。潜在能力は…まずまずかねぇ。",
                "悪くない走りだ。これからが勝負さぁ。"
            ])
        else:
            return random.choice([
                "少し砂の味が分かってきたさぁ。潜在能力は…普通かねぇ。",
                "地道に鍛えれば、いつか花開くさぁ。"
            ])

    # --- 3 Years Old and Beyond (Serious Evaluation) ---
    if avg_cap >= 240:
        return random.choice([
            "この足腰は、風を追い越せるかもしれないさぁ！最強の素質を秘めているさぁ。",
            "与那国の王になれる器だ。歴史に名を残す馬になるはずさぁ！",
            "どぅなんの誇りさぁ。この馬の走りは、みんなに勇気をくれるよ。"
        ])
    elif avg_cap >= 220:
        return random.choice([
            "かなりの素質を感じるさぁ。大きなレースも狙えるねぇ。",
            "立派に育ったさぁ。この馬なら、どこへ出しても恥ずかしくないよ。",
            "スピードがあるねぇ。サンセットの風を感じる走りさぁ。"
        ])
    elif avg_cap >= 200:
        return random.choice([
            "だいぶ実力がついてきたさぁ。ここからが本当の始まりだね。",
            "いい馬になった。自分の力を信じて走るんだよ。",
            "粘り強い足腰だ。どんな苦境も跳ね返す根性があるさぁ。"
        ])
    else:
        return random.choice([
            "一歩ずつ、確実に。この馬のペースで頑張ればいいさぁ。",
            "心優しい馬だね。無事に走り続けることが一番大事さぁ。",
            "丈夫なのが一番さぁ。元気に走ってくれるだけで嬉しいよ。"
        ])
