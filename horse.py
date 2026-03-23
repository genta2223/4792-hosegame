"""Horse data model for どぅなん・ダッシュ！"""

import hashlib
import json
import random


def clamp(value, lo=0, hi=255):
    """Clamp an integer to [lo, hi]."""
    return max(lo, min(hi, int(value)))


class Horse:
    """Yonaguni horse with RPG-style parameters."""

    # ---------- 名前プール ----------
    NAMES = [
        "ハイビスカス", "サトウキビ", "ウミガメ", "ティンダバナ",
        "マーラン", "ナンタ", "クブラ", "アガリ",
        "ドナン", "サンニヌ台", "立神岩", "ダティグ",
    ]

    def __init__(self, name=None, randomise=True, is_initial=False):
        self.name = name or random.choice(self.NAMES)
        self.age = 2  # 2歳スタート
        self.gender = random.choice(["牡馬", "牝馬"])
        self.prize_money = 0
        
        # 血統 (Sire/Dam)
        self.sire = "不明"
        self.dam = "不明"

        # 基礎能力 (0-255)
        if randomise:
            # 初期馬なら少し高め (35-85)
            low = 35 if is_initial else 20
            self.speed = random.randint(low, 80)
            self.stamina = random.randint(low, 80)
            self.guts = random.randint(low, 80)
            self.wisdom = random.randint(low, 80)
            self.luck = random.randint(low, 80)
            self.temper = random.randint(30, 90)
            self.weight = random.randint(180, 220)
        else:
            self.speed = 50
            self.stamina = 50
            self.guts = 50
            self.wisdom = 50
            self.luck = 50
            self.temper = 60
            self.weight = 200
        
        # 潜在能力限界 (Potential Caps: 180-240)
        if randomise:
            # 初期馬はスピード・スタミナのCapを保証 (210以上)
            cap_low = 210 if is_initial else 180
            self.caps = {
                "speed": random.randint(cap_low, 245),
                "stamina": random.randint(cap_low, 245),
                "guts": random.randint(190 if is_initial else 180, 240),
                "wisdom": random.randint(190 if is_initial else 180, 240)
            }
        else:
            self.caps = {"speed": 220, "stamina": 220, "guts": 220, "wisdom": 220}
        
        self.last_training_msg = ""
        self.cap_warning_triggered = False
        
        # 調子の波 (Condition Wave: 0-100)
        self.condition = random.randint(30, 70)
        self.condition_trend = random.choice([1, -1]) # 1:上昇, -1:下降
        
        self.best_weight = self.weight
        self.fatigue = 0
        self.contribution = 0
        self.retired = False
        self.in_paddock = False  # エターナル・パドック内フラグ

        # グラフィック（外見）
        if randomise:
            self.appearance = {
                "base_color": random.choice([4, 9, 5, 13, 1]), # 4:鹿毛 9:栗毛 5:黒 13:芦 1:青
                "face_marking": random.randint(0, 3),        # 0:無し 1:星 2:流星 3:鼻白
                "mane_tail_color": random.choice([0, 4, 10, 7]), # 0:黒 4:茶 10:金 7:白
                "leg_marking": random.randint(0, 2)          # 0:無し 1:ソックス 2:ストッキング
            }
        else:
            self.appearance = {
                "base_color": 4, "face_marking": 0, "mane_tail_color": 0, "leg_marking": 0
            }

        # サブ目標
        self.target_race = None
        self.target_weeks_left = 0
        
        # 戦績・クラス用
        self.wins = 0
        self.stakes_wins = 0
        self.g1_wins = 0

    # ---------- クラス・番組表用 ----------
    def get_class_info(self):
        """現在のクラス名と昇級までのカウントダウンを返す。"""
        # 未勝利 (ハナハナ級)
        if self.wins == 0:
            return "未勝利", "あと1勝で一般へ"
        
        # 一般 (どぅなん級) -> 3勝 or 5000G
        if self.wins < 3 and self.prize_money < 5000:
            w_rem = 3 - self.wins
            p_rem = 5000 - self.prize_money
            return "一般", f"あと{w_rem}勝/賞金{p_rem}Gで重賞へ"
            
        # 重賞クラス (最西端級) -> 重賞1勝 or 5勝
        if self.stakes_wins < 1 and self.wins < 5:
            w_rem = 5 - self.wins
            return "重賞クラス", f"重賞1勝 or あと{w_rem}勝でG1へ"
            
        # G1級 (サンセット記念級)
        return "G1級", "最高クラス到達さぁ！"

    def get_class_name(self):
        """後方互換用。"""
        name, _ = self.get_class_info()
        return name

    @classmethod
    def breed(cls, stallion, broodmare, name=None):
        """Create a new foal from a stallion and broodmare (50% rule)."""
        foal = cls(name=name, randomise=False)
        foal.sire = stallion.name
        foal.dam = broodmare.name

        # 50% Inheritance Rule:
        # Parents contribute 50% of the average. 
        # The remaining 50% is a mix of gender bonus and randomness.
        # This keeps the bloodline strong but prevents immediate capping without refinement.
        for s in ["speed", "stamina", "guts", "wisdom", "luck"]:
            s_val = getattr(stallion, s)
            m_val = getattr(broodmare, s)
            parent_avg = (s_val + m_val) // 2
            
            # 50% based on parents, 50% on new potential (random + bonus)
            inherited_part = parent_avg * 0.5
            random_part = random.randint(20, 100) * 0.5 
            
            # Gender bonus: Stallion helps speed/guts, Mare helps stamina/wisdom
            bonus = 0
            if s == "speed" and stallion.speed > 180: bonus += 5
            if s == "stamina" and broodmare.stamina > 180: bonus += 5
            
            setattr(foal, s, clamp(inherited_part + random_part + bonus))
        
        # Temper and Weight
        foal.temper = clamp((stallion.temper + broodmare.temper) // 2 + random.randint(-15, 20))
        foal.weight = (stallion.best_weight + broodmare.best_weight) // 2 + random.randint(-8, 8)
        foal.best_weight = foal.weight

        # Potential Caps (Inherited from parents with bonus)
        foal.caps = {}
        for s in ["speed", "stamina", "guts", "wisdom"]:
            p_avg_cap = (stallion.caps[s] + broodmare.caps[s]) // 2
            # Caps inherit well, but need breeding to push further
            foal.caps[s] = clamp(p_avg_cap + random.randint(-5, 12), 170, 255)

        # 外見の遺伝
        p = stallion if random.random() < 0.5 else broodmare
        foal.appearance = p.appearance.copy()
        if random.random() < 0.2:
            foal.appearance["face_marking"] = random.randint(0, 3)

        return foal

    # ---------- パラメータ上限（加齢キャップ） ----------
    def _param_cap(self):
        """Age-based parameter cap. Peak at 4-5, decay afterwards."""
        if self.age <= 5:
            return 255
        decay_years = self.age - 5
        return max(80, 255 - decay_years * 20)

    def _apply_cap(self):
        cap = self._param_cap()
        self.speed = min(self.speed, cap)
        self.stamina = min(self.stamina, cap)
        self.guts = min(self.guts, cap)
        self.wisdom = min(self.wisdom, cap)
        self.luck = min(self.luck, cap)

    # ---------- 加齢 ----------
    def age_one_year(self):
        """Increment age by 1 year; apply decay if past peak."""
        if self.in_paddock:
            return  # パドック内は加齢停止
        self.age += 1
        if self.age > 5:
            # 各パラメータを少し自然減少
            decay = random.randint(2, 8)
            self.speed = clamp(self.speed - decay)
            self.stamina = clamp(self.stamina - decay)
            self.guts = clamp(self.guts - random.randint(1, 5))
            self.wisdom = clamp(self.wisdom - random.randint(0, 3))
        self._apply_cap()

    # ---------- アクション ----------
    def train(self, location="sonai", intensity="normal"):
        """場所別開墾トレーニング。
        location: 'higawa', 'kubura', 'sonai'
        intensity: 'normal' (軽め), 'deep' (強め)
        """
        if self.retired: return "引退した馬は調教できません。"
        
        self.cap_warning_triggered = False
        success = True
        if intensity == "normal":
            # 67% で成功 (+1以上)、33% で失敗 (+0)
            if random.random() > 0.67: success = False
        
        # 疲労計算
        fat_gain = 5 if intensity == "normal" else 10
        if location == "kubura": fat_gain += 3
        elif location == "higawa": fat_gain -= 2
        self.fatigue = clamp(self.fatigue + fat_gain, 0, 100)

        # 調子による倍率 (0.8x - 1.2x)
        cond_mult = 0.8 + (self.condition / 100.0) * 0.4
        
        # ステータス上昇値の決定
        gains = {"speed": 0, "stamina": 0, "guts": 0, "wisdom": 0}
        
        if success:
            if location == "kubura": # 久部良: スタミナ・根性
                gains["stamina"] += random.randint(1, 2)
                gains["guts"] += random.randint(1, 2)
            elif location == "sonai": # 祖納: スピード・賢さ
                gains["speed"] += random.randint(1, 2)
                gains["wisdom"] += random.randint(1, 2)
            else: # 比川: 全ステータスが「まんべんなく」伸びる
                # ヒガワ限定: 軽め(Light)ならステータス成否に関わらず「調子」が確実に +5〜10 上昇
                if intensity == "normal":
                    self.condition = clamp(self.condition + random.randint(5, 10), 0, 100)

                # 各ステータス個別に判定 (強めなら100%、軽めなら67%で+1)
                for s in ["speed", "stamina", "guts", "wisdom"]:
                    if intensity == "deep" or random.random() < 0.67:
                        gains[s] += 1
                self.temper = clamp(self.temper - 2) # 比川は気性改善

        # 調子への影響 (比川・軽め以外)
        if location != "higawa" or intensity != "normal":
            if intensity == "normal": self.condition = clamp(self.condition + 2, 0, 100)
            else: self.condition = clamp(self.condition - 3, 0, 100)

        # 潜在能力（Cap）による減衰適用
        final_gains = []
        for s, val in gains.items():
            if val <= 0: continue
            
            current = getattr(self, s)
            cap = self.caps.get(s, 220)
            
            if current >= cap + 20:
                val = 0 # ほぼストップ
            elif current >= cap:
                # 限界を超えると伸びが 50% にカット
                if random.random() < 0.5: val = max(0, val - 1)
                if val > 0: self.cap_warning_triggered = True # 限界示唆

            if val > 0:
                # 調子倍率適用 (確率的に +1 -> +1 or +0, +2 -> +2 or +1 or +3 等)
                actual_val = 0
                for _ in range(val):
                    if random.random() < cond_mult: actual_val += 1
                
                if actual_val > 0:
                    setattr(self, s, clamp(current + actual_val))
                    final_gains.append(f"{s.upper()}+{actual_val}")

        self.contribution += 1
        loc_name = {"higawa": "比川", "kubura": "久部良", "sonai": "祖納"}.get(location, "祖納")
        intensity_name = "軽め" if intensity == "normal" else "強め"
        
        gain_str = ", ".join(final_gains) if final_gains else "変化なし"
        res = f"{loc_name}で{intensity_name}に開墾した ({gain_str})"
        
        # 故障判定
        if self.fatigue > 80:
            injury_chance = (self.fatigue - 80) ** 2 / 400.0
            if random.random() < injury_chance:
                penalty = random.randint(5, 15)
                self.speed = clamp(self.speed - penalty)
                self.stamina = clamp(self.stamina - penalty)
                self.fatigue = 100
                return f"{loc_name}で故障発生！ 能力-{penalty}"
                
        return res

    def feed(self, feed_type="bagasse"):
        """給餌。feed_type: 'bagasse'(バガス) or 'choumeisou'(長命草)"""
        if self.retired:
            return "引退した馬には給餌できません。"
        
        if feed_type == "choumeisou":
            # 長命草: 高価、疲労大回復、調子アップ
            self.weight = min(300, self.weight + 2)
            self.fatigue = clamp(self.fatigue - 25, 0, 100)
            self.condition = clamp(self.condition + 8, 0, 100)
            return "長命草を与えた 疲労が取れ、調子も上がった"
        else:
            # バガス: 基本餌、体重維持、調子微増
            self.weight = min(300, self.weight + 3)
            self.fatigue = clamp(self.fatigue - 10, 0, 100)
            self.condition = clamp(self.condition + 3, 0, 100)
            return "バガスを与えた"

    def rest(self):
        """基本の休養: Fatigue-30, Weight+1, Condition+5"""
        if self.retired:
            return "引退した馬は休養できません。"
        self.fatigue = clamp(self.fatigue - 30, 0, 100)
        self.weight = min(300, self.weight + 1)
        self.condition = clamp(self.condition + 5, 0, 100)
        return "ゆっくりと休養させた"

    def pasture(self):
        """放牧: Fatigue-20, Condition+10 (調子上昇)"""
        if self.retired: return "引退した馬は放牧できません。"
        self.fatigue = clamp(self.fatigue - 20, 0, 100)
        self.condition = clamp(self.condition + 10, 0, 100)
        return "放牧でリフレッシュさせた 調子が上向いたさぁ"

    def sauna(self):
        """サウナ: Fatigue-50, Weight-2 (疲労大回復、体重減)"""
        if self.retired: return "引退した馬はサウナに入れません。"
        self.fatigue = clamp(self.fatigue - 50, 0, 100)
        self.weight = clamp(self.weight - 2, 150, 300)
        return "サウナで汗を流した 疲れがすっきり取れたさぁ"

    # ---------- 調子テキスト（ダビスタ風） ----------
    def condition_text(self):
        """Return condition wave text."""
        if self.condition >= 85: return "絶好調さぁ！"
        elif self.condition >= 65: return "調子は上向きよ"
        elif self.condition >= 35: return "普通だねぇ"
        elif self.condition >= 15: return "少し調子を落としとる"
        else: return "絶不調さぁ..."

    def fatigue_text(self):
        """Return DS3-style fatigue text."""
        if self.fatigue >= 80: return "かなり疲れています"
        elif self.fatigue >= 60: return "疲れているようです"
        elif self.fatigue >= 40: return "少し疲れています"
        elif self.fatigue >= 20: return "まあまあ元気です"
        else: return "元気いっぱいです"

    def weight_text(self):
        """Return DS3-style weight condition text."""
        diff = self.weight - self.best_weight
        if abs(diff) <= 2:
            return "ベスト体重です"
        elif diff > 8:
            return "かなり太めです"
        elif diff > 4:
            return "少し太めですね"
        elif diff < -8:
            return "かなり細いです"
        elif diff < -4:
            return "少し細いですね"
        return "ほぼベスト体重"

    # ---------- 体重ボーナス/ペナルティ ----------
    def weight_modifier(self):
        """ベスト体重±4kg以内なら1.0、外れるほど減衰"""
        diff = abs(self.weight - self.best_weight)
        if diff <= 4:
            return 1.0
        return max(0.7, 1.0 - (diff - 4) * 0.02)

    # ---------- レース用総合力 ----------
    def race_power(self):
        """Calculate overall race power with weight modifier."""
        base = (
            self.speed * 0.35
            + self.stamina * 0.25
            + self.guts * 0.15
            + self.wisdom * 0.10
            + self.luck * 0.05
        )
        temper_mod = 1.0 - (max(0, self.temper - 70)) * 0.003
        return base * self.weight_modifier() * temper_mod + random.gauss(0, 3)

    # ---------- ハッシュ ----------
    def generate_hash(self):
        """Serialize horse data to a shareable hash string."""
        data = {
            "n": self.name, "a": self.age, "g": self.gender, "pm": self.prize_money,
            "sr": self.sire, "dm": self.dam,
            "sp": self.speed, "st": self.stamina,
            "gu": self.guts, "wi": self.wisdom,
            "lu": self.luck, "te": self.temper,
            "wt": self.weight, "bw": self.best_weight,
            "co": self.contribution,
            "ap": self.appearance,
            "tr": self.target_race, "tw": self.target_weeks_left,
        }
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:16] + "|" + raw

    @classmethod
    def from_hash(cls, hash_str):
        """Deserialize a horse from a hash string."""
        _, raw = hash_str.split("|", 1)
        d = json.loads(raw)
        h = cls(name=d["n"], randomise=False)
        h.age = d["a"]
        h.gender = d.get("g", "牡馬")
        h.prize_money = d.get("pm", 0)
        h.sire = d.get("sr", "不明")
        h.dam = d.get("dm", "不明")
        h.speed = d["sp"]; h.stamina = d["st"]
        h.guts = d["gu"]; h.wisdom = d["wi"]
        h.luck = d["lu"]; h.temper = d["te"]
        h.weight = d["wt"]; h.best_weight = d["bw"]
        h.contribution = d["co"]
        h.appearance = d.get("ap", {"base_color": 4, "face_marking": 0, "mane_tail_color": 0, "leg_marking": 0})
        h.target_race = d.get("tr")
        h.target_weeks_left = d.get("tw", 0)
        return h

    # ---------- 表示 ----------
    def __repr__(self):
        return (
            f"Horse({self.name} {self.gender} age={self.age} cls={self.get_class_name()} "
            f"SPD={self.speed} STA={self.stamina} GUT={self.guts} "
            f"WT={self.weight} FAT={self.fatigue} CON={self.contribution})"
        )
