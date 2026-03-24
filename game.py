"""Game state manager for どぅなん・ダッシュ！"""

import random
from horse import Horse
from calendar_system import Calendar
from ranch import Ranch


class GameState:
    """Central game state that orchestrates all subsystems."""

    MAX_LOG = 30  # max log entries kept

    def __init__(self):
        self.calendar = Calendar()
        self.ranch = Ranch()
        self.log = []
        self.paddock = []
        self.selected_horse_index = 0
        self.actions_left = 2
        self.game_over = False
        self.paused = False

    def set_starter_horse(self, name):
        """Create the starter horse with the player-chosen name."""
        # 最初の1頭なので True (初期馬バフ)
        starter = Horse(name, is_initial=True)
        ok, msg = self.ranch.add_horse(starter)
        self._add_log(msg)
        self._add_log("ようこそ、どぅなん牧場へ！")

    # ---------- ログ ----------
    def _add_log(self, message):
        # 連続する重複メッセージは無視する (おじいのアドバイス重複対策)
        if self.log and self.log[-1] == message:
            return

        self.log.append(message)
        if len(self.log) > self.MAX_LOG:
            self.log = self.log[-self.MAX_LOG:]

    @property
    def recent_logs(self):
        """Return last 4 log entries for display."""
        return self.log[-4:]

    # ---------- 選択中の馬 ----------
    @property
    def selected_horse(self):
        horses = self.ranch.horses
        if not horses:
            return None
        idx = max(0, min(self.selected_horse_index, len(horses) - 1))
        self.selected_horse_index = idx
        return horses[idx]

    def select_next_horse(self):
        n = len(self.ranch.horses)
        if n > 0:
            self.selected_horse_index = (self.selected_horse_index + 1) % n

    # ---------- アクション ----------
    def do_train(self, location="sonai", intensity="normal"):
        h = self.selected_horse
        if h is None:
            self._add_log("馬がいません！")
            return
        msg = h.train(location, intensity)
        self._add_log(msg)

    def do_feed(self, feed_type="bagasse"):
        h = self.selected_horse
        if h is None:
            self._add_log("馬がいません！")
            return
        if feed_type == "choumeisou":
            cost = 300
            if self.ranch.balance < cost:
                self._add_log("資金不足！長命草は300G必要")
                return
            self.ranch.balance -= cost
        msg = h.feed(feed_type)
        self._add_log(msg)

    def do_rest(self, rest_type="normal"):
        h = self.selected_horse
        if h is None:
            self._add_log("馬がいません！")
            return
        
        if rest_type == "pasture":
            msg = h.pasture()
        elif rest_type == "sauna":
            msg = h.sauna()
        else:
            msg = h.rest()
            
        self._add_log(msg)

    def do_race(self):        
        h = self.selected_horse
        if h is None:
            self._add_log("馬がいません！")
            return False
        if h.fatigue > 70:
            self._add_log("疲労が高すぎます！ 休息させてください。")
            return False
        return True

    # ---------- 週送り ----------
    def advance_week(self):
        """Advance game by one week."""
        self.actions_left = 2
        events = self.calendar.advance_week()
        self._add_log(f"📅 {self.calendar.display()}")
        
        for h in self.ranch.horses:
            # 疲労自然回復
            h.fatigue = max(0, h.fatigue - 5)
            # ターゲット更新
            if h.target_race:
                h.target_weeks_left -= 1
                if h.target_weeks_left < 0:
                    h.target_race = None
            
            # 調子の波の更新 (1ヶ月〜2ヶ月周期)
            if not hasattr(h, 'condition_trend'): h.condition_trend = 1
            h.condition = max(0, min(100, h.condition + h.condition_trend * random.randint(2, 5)))
            
            # 反転判定 (0/100到達時、または確率)
            if h.condition >= 100: h.condition_trend = -1
            elif h.condition <= 0: h.condition_trend = 1
            elif random.random() < 0.1: # 10% で反転
                h.condition_trend *= -1
        
        # 老化・死亡判定 (18歳以上)
        dead_horses = []
        for h in self.ranch.horses:
            if h.age >= 18:
                # 18歳から毎週 5% + (年齢-18)*2% の確率で死亡判定
                death_chance = 0.05 + (h.age - 18) * 0.02
                if random.random() < death_chance:
                    dead_horses.append(h)
                else:
                    if random.random() < 0.3: # 時々警告
                        self._add_log(f"⚠ {h.name}は高齢さぁ。時の部屋への登録を考えてもいいかもね。")
        
        for dh in dead_horses:
            if dh in self.ranch.horses:
                self.ranch.horses.remove(dh)
                self._add_log(f"🕯 {dh.name}が天に召されました…（享年{dh.age}）")

        # 年越し処理
        if "__NEW_YEAR__" in events:
            for h in self.ranch.horses:
                h.age_one_year()
            for h in self.ranch.paddock:
                pass  # パドック内は加齢なし
            self._add_log(f"🎍 {self.calendar.year}年目が始まります！")

        # イベント通知
        for ev in events:
            if ev != "__NEW_YEAR__":
                self._add_log(f"📅 イベント: {ev}")

        # 牧場週次更新
        ranch_msgs = self.ranch.weekly_update()
        for m in ranch_msgs:
            self._add_log(m)

    # ---------- セリ（オークション）----------
    def auction_buy(self):
        """Buy a random horse at auction (January event)."""
        if self.calendar.month != 1:
            self._add_log("セリは1月だけです。")
            return
        cost = 1000
        if self.ranch.balance < cost:
            self._add_log(f"資金不足！（必要: {cost}G）")
            return
        if len(self.ranch.horses) >= self.ranch.max_horses:
            self._add_log("牧場に空きがありません。")
            return
        self.ranch.balance -= cost
        new_horse = Horse()
        self.ranch.add_horse(new_horse)
        self._add_log(f"🐴 {new_horse.name}を{cost}Gで購入！")
