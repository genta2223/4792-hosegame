"""Ranch management for どぅなん・ダッシュ！"""


class Ranch:
    """Manages horse slots, balance, and the Eternal Paddock."""

    INITIAL_BALANCE = 5000
    MAINTENANCE_FEE = 75       # per paddock horse per week (300G/month)
    MAX_HORSES = 2             # expandable to 3
    MAX_PADDOCK = 3

    def __init__(self):
        self.horses = []                # active horse list
        self.paddock = []               # Eternal Paddock list
        self.stallions = []             # 種牡馬 (max 8)
        self.broodmares = []            # 繁殖牝馬 (max 8)
        self.balance = self.INITIAL_BALANCE
        self.max_horses = self.MAX_HORSES
        self.contribution = 0
        self.reward_code = ""

    # ---------- 馬管理 ----------
    def add_horse(self, horse):
        if len(self.horses) >= self.max_horses:
            return False, "牧場の枠がいっぱいです。"
        self.horses.append(horse)
        return True, f"{horse.name}を牧場に迎えました！"

    def remove_horse(self, index):
        if 0 <= index < len(self.horses):
            h = self.horses.pop(index)
            return True, f"{h.name}が牧場を去りました。"
        return False, "無効なインデックスです。"

    # ---------- 引退・繁殖 ----------
    def retire_horse(self, index):
        if index < 0 or index >= len(self.horses):
            return False, "無効な馬です。"
        
        h = self.horses[index]
        if h.age < 5:
            return False, "5歳以上にならないと引退できません。"

        h = self.horses.pop(index)
        h.retired = True
        
        # 引退功労金
        bonus = h.contribution * 5
        self.balance += bonus

        # 繁殖へ
        if h.gender == "牝馬":
            # 牝馬は引退すれば自動で繁殖入り可能
            if len(self.broodmares) < 8:
                self.broodmares.append(h)
                return True, f"{h.name} 引退。(功労金{bonus}G)。繁殖牝馬となりました。"
            else:
                return True, f"{h.name} 引退。(功労金{bonus}G)。繁殖枠がいっぱいです。"
        else:
            # 牡馬はG1勝利経験がある場合のみ種牡馬入り
            if h.g1_wins > 0:
                if len(self.stallions) < 8:
                    self.stallions.append(h)
                    return True, f"{h.name} 引退。名馬として種牡馬入りしました！"
                else:
                    return True, f"{h.name} 引退。種牡馬枠が一杯です。"
            else:
                return True, f"{h.name} 引退。(功労金{bonus}G)。お疲れ様でした。"

    def breed_horse(self, stallion_idx, mare_idx, foal_name=None):
        if stallion_idx < 0 or stallion_idx >= len(self.stallions):
            return False, "無効な種牡馬です。"
        if mare_idx < 0 or mare_idx >= len(self.broodmares):
            return False, "無効な繁殖牝馬です。"
        if len(self.horses) >= self.max_horses:
            return False, "牧場に空きがありません。"
            
        stallion = self.stallions[stallion_idx]
        mare = self.broodmares[mare_idx]
        
        from horse import Horse
        foal = Horse.breed(stallion, mare, name=foal_name)
        self.horses.append(foal)
        return True, f"{foal.name} が誕生したさぁ！父:{stallion.name} 母:{mare.name}"

    # ---------- 時の部屋 (Eternal Paddock) ----------
    def add_to_paddock(self, horse_index):
        cost = 1500 # 登録料
        if self.balance < cost:
            return False, f"資金不足さぁ（登録料:{cost}G必要）"
        if len(self.paddock) >= self.MAX_PADDOCK:
            return False, "時の部屋がいっぱいです。"
        if horse_index < 0 or horse_index >= len(self.horses):
            return False, "無効な馬です。"
            
        horse = self.horses.pop(horse_index)
        self.balance -= cost
        horse.in_paddock = True
        self.paddock.append(horse)
        return True, f"{horse.name}を『時の部屋』へ！ (費用:{cost}G)" 

    def remove_from_paddock(self, paddock_index):
        if paddock_index < 0 or paddock_index >= len(self.paddock):
            return False, "無効な馬です。"
        horse = self.paddock.pop(paddock_index)
        horse.in_paddock = False
        ok, msg = self.add_horse(horse)
        if not ok:
            horse.in_paddock = True
            self.paddock.insert(paddock_index, horse)
            return False, "牧場に空きがないさぁ。"
        return True, f"{horse.name}が『時の部屋』から戻りました！"

    # ---------- 週次更新 ----------
    def weekly_update(self):
        """Deduct paddock maintenance fees. Force-release if bankrupt."""
        messages = []
        fee = len(self.paddock) * self.MAINTENANCE_FEE
        if fee > 0:
            self.balance -= fee
            messages.append(f"パドック維持費: -{fee}G (残高{self.balance}G)")

        # 資金不足 → パドックから強制解除
        while self.balance < 0 and self.paddock:
            horse = self.paddock.pop()
            horse.in_paddock = False
            if len(self.horses) < self.max_horses:
                self.horses.append(horse)
                messages.append(f"資金不足！ {horse.name}がパドックから解除")
            else:
                horse.retired = True
                messages.append(f"資金不足！ {horse.name}が引退を余儀なくされた…")
        return messages

    def expand(self):
        """Expand ranch to 3 horse slots."""
        cost = 3000
        if self.balance < cost:
            return False, f"資金不足です（必要: {cost}G）"
        self.balance -= cost
        self.max_horses = 3
        return True, "牧場を拡張しました！（最大3頭）"

    def __repr__(self):
        return (
            f"Ranch(horses={len(self.horses)}/{self.max_horses}, "
            f"paddock={len(self.paddock)}/{self.MAX_PADDOCK}, "
            f"balance={self.balance}G)"
        )
