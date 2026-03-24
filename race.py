"""Race engine for どぅなん・ダッシュ！"""

import random
import math
from horse import Horse


GOAL_DISTANCE = 1000
RACE_HORSE_COUNT = 5  # total horses including player


class RaceHorse:
    """A horse participating in a race with runtime state."""

    def __init__(self, horse, is_player=False, player_index=0):
        self.horse = horse
        self.name = horse.name
        self.is_player = is_player
        self.player_index = player_index  # 0=CPU, 1=1P, 2=2P, 3=3P, 4=4P

        # レース中パラメータ
        self.x = 0.0
        self.stamina_pool = horse.stamina * 3.5 + 200
        self.finished = False
        self.finish_order = 0

        # 出遅れ判定 (気性が高いほどリスク大)
        self.start_delay = 0
        if horse.temper > 50:
            delay_chance = (horse.temper - 50) / 200.0
            if random.random() < delay_chance:
                self.start_delay = random.randint(15, 45)  # frames

        # 掛かり（気性による無駄消費）
        self.kakari_rate = max(0, (horse.temper - 60)) * 0.01

        # Y座標（レーン位置）
        self.lane_y = 0

    def base_speed(self):
        """Base running speed per frame."""
        return 1.2 + self.horse.speed * 0.012

    def calc_speed(self, frame, all_horses):
        """Calculate current frame speed with all modifiers."""
        if frame < self.start_delay:
            return 0.3  # 出遅れ中

        spd = self.base_speed()

        # スタミナ消費
        progress = self.x / GOAL_DISTANCE
        stamina_drain = 1.0 + progress * 0.8
        if random.random() < self.kakari_rate:
            stamina_drain += 2.0  # 掛かり
        self.stamina_pool -= stamina_drain

        # スタミナ切れペナルティ
        if self.stamina_pool <= 0:
            spd *= 0.55
        elif progress > 0.7:
            # 後半: スタミナ依存
            sta_ratio = max(0, self.stamina_pool) / (self.horse.stamina * 3.5 + 200)
            spd *= (0.7 + sta_ratio * 0.5)

        # 競り合いブースト (guts)
        for other in all_horses:
            if other is self or other.finished:
                continue
            dist = abs(self.x - other.x)
            if dist < 30 and self.x > GOAL_DISTANCE * 0.3:
                guts_boost = self.horse.guts * 0.002
                spd += guts_boost
                break

        # 体重モディファイア
        spd *= self.horse.weight_modifier()

        # ランダムゆらぎ
        spd += random.gauss(0, 0.15)

        return max(0.2, spd)


RACE_TOTAL = 4  # レース常時4頭


# ====================================================================
#  レースエンジン
# ====================================================================

class RaceEngine:
    """Manages one full race."""

    def __init__(self, player_horse, vs_horses=None):
        self.horses = []
        self.frame = 0
        self.finished = False
        self.results = []  # 着順リスト
        self.is_vs_mode = vs_horses is not None and len(vs_horses) > 0

        # プレイヤー馬 (1P) - 万一Noneの場合のガード
        if player_horse is None:
            from horse import Horse
            player_horse = Horse("名無しの与那国馬(G)")
            player_horse.speed = 100; player_horse.stamina = 100; player_horse.guts = 100

        rh = RaceHorse(player_horse, is_player=True, player_index=1)
        rh.lane_y = 0
        self.horses.append(rh)

        if self.is_vs_mode:
            # 対戦馬 (2P, 3P, 4P...)
            for i, vh in enumerate(vs_horses):
                rh_vs = RaceHorse(vh, is_player=True, player_index=i + 2)
                rh_vs.lane_y = i + 1
                self.horses.append(rh_vs)

            # CPUで4頭に補完
            rival_names = ["ウミガメ号", "ティンダ号", "マーラン号"]
            cpu_idx = 0
            while len(self.horses) < RACE_TOTAL:
                rival = Horse(rival_names[cpu_idx] if cpu_idx < len(rival_names) else f"CPU馬{cpu_idx+1}")
                # CPU馬の強さはプレイヤー馬の平均に合わせる
                avg_speed = sum(h.horse.speed for h in self.horses) // len(self.horses)
                avg_stamina = sum(h.horse.stamina for h in self.horses) // len(self.horses)
                rival.speed = int(avg_speed * random.uniform(0.80, 1.0))
                rival.stamina = int(avg_stamina * random.uniform(0.80, 1.0))
                rr = RaceHorse(rival, is_player=False, player_index=0)
                rr.lane_y = len(self.horses)
                self.horses.append(rr)
                cpu_idx += 1
        else:
            # ライバル馬生成 (PVE) — always 4 total
            rival_names = ["ウミガメ号", "ティンダ号", "マーラン号", "クブラ号", "アガリ号"]
            p_class = player_horse.get_class_name()
            
            for i in range(RACE_TOTAL - 1):
                rival = Horse(rival_names[i] if i < len(rival_names) else f"馬{i+1}")
                
                if p_class == "未勝利":
                    # 序盤はライバルを弱体化 (プレイヤーの 75-90% 程度)
                    rival.speed = int(player_horse.speed * random.uniform(0.75, 0.90))
                    rival.stamina = int(player_horse.stamina * random.uniform(0.75, 0.90))
                    rival.guts = int(player_horse.guts * random.uniform(0.85, 1.0))
                elif p_class == "一般":
                    # 一般クラス: +15% 程度のブースト。しっかり育てないと勝てない
                    rival.speed = int(max(70, player_horse.speed) * random.uniform(1.05, 1.15))
                    rival.stamina = int(max(70, player_horse.stamina) * random.uniform(1.05, 1.15))
                    rival.guts = int(player_horse.guts * random.uniform(1.0, 1.2))
                else:
                    # 重賞・G1級: 「絶望的な壁」。180-230の高ステータスを設定
                    rival.speed = random.randint(190, 235)
                    rival.stamina = random.randint(190, 235)
                    rival.guts = random.randint(180, 220)
                    rival.wisdom = random.randint(180, 220)
                
                rr = RaceHorse(rival, is_player=False, player_index=0)
                rr.lane_y = i + 1
                self.horses.append(rr)

        # 実況ログ
        self.commentary = []
        self._add_commentary("レーススタート！")

        # 実況トリガー管理
        self._commented_30 = False
        self._commented_60 = False
        self._commented_90 = False

    def _add_commentary(self, text):
        self.commentary.append(text)
        if len(self.commentary) > 6:
            self.commentary = self.commentary[-6:]

    @property
    def player_horse(self):
        return self.horses[0]

    def skip_to_final(self):
        """Skip race until leader reaches final stretch (approx 5s from goal)."""
        stretch = GOAL_DISTANCE - 150
        while not self.finished and self._get_leader().x < stretch:
            self._step()

    def update(self):
        """Advance race by one frame. Returns True while still running."""
        if self.finished:
            return False

        # Determine number of ticks to run
        ticks = 1
        if not self.is_vs_mode:
            # PVE: Fast-forward if player horse finished
            if self.player_horse.finished:
                ticks = 10
        else:
            # VS: Fast-forward if ALL player horses finished
            all_players_done = all(rh.finished for rh in self.horses if rh.is_player)
            if all_players_done:
                ticks = 10

        for _ in range(ticks):
            if self.finished:
                break
            self._step()

        return not self.finished

    def _step(self):
        """Single simulation tick."""
        self.frame += 1

        # 各馬の速度計算と移動
        for rh in self.horses:
            if rh.finished:
                continue
            spd = rh.calc_speed(self.frame, self.horses)
            rh.x += spd

            # ゴール判定
            if rh.x >= GOAL_DISTANCE:
                rh.x = GOAL_DISTANCE
                rh.finished = True
                rh.finish_order = len(self.results) + 1
                self.results.append(rh)

                if rh.finish_order == 1:
                    self._add_commentary(f"{rh.name}、1着でゴール！")
                elif rh.is_player:
                    self._add_commentary(f"{rh.name}、{rh.finish_order}着！")

        # 実況（進行度）
        # プレイヤーがゴールした後は実況を抑制（スキップ）するか、そのまま流す。
        # ここではプレイヤーの進行度ベースなので、ゴール後は更新されない。
        if not self.player_horse.finished:
            player_progress = self.player_horse.x / GOAL_DISTANCE
            if player_progress > 0.3 and not self._commented_30:
                self._commented_30 = True
                leader = self._get_leader()
                if leader.is_player:
                    self._add_commentary(f"{leader.name}、先頭で快調！")
                else:
                    self._add_commentary(f"{leader.name}が先頭、追え！")

            if player_progress > 0.6 and not self._commented_60:
                self._commented_60 = True
                pos = self._player_position()
                if pos <= 2:
                    self._add_commentary("いい脚で上がってきた！")
                else:
                    self._add_commentary("まだまだこれから！")

            if player_progress > 0.9 and not self._commented_90:
                self._commented_90 = True
                pos = self._player_position()
                if pos == 1:
                    self._add_commentary("そのまま！ そのまま！")
                elif pos <= 3:
                    self._add_commentary("ゴール前の叩き合い！")
                else:
                    self._add_commentary("追い込めるか！？")

        # 全馬フィニッシュ
        if all(rh.finished for rh in self.horses):
            self.finished = True
            self._final_commentary()

    def _get_leader(self):
        return max(self.horses, key=lambda rh: rh.x)

    def _player_position(self):
        sorted_h = sorted(self.horses, key=lambda rh: -rh.x)
        for i, rh in enumerate(sorted_h):
            if rh is self.player_horse:
                return i + 1
        return len(self.horses)

    def _final_commentary(self):
        player = self.player_horse
        order = player.finish_order
        if order == 1:
            self._add_commentary(f"1着！ {player.name}の勝利！")
        elif order <= 3:
            self._add_commentary(f"惜しい！ {order}着でした")
        else:
            self._add_commentary(f"{order}着… 次こそ頑張ろう")

    def get_player_rank(self):
        return self.player_horse.finish_order

    def get_prize(self):
        rank = self.get_player_rank()
        if rank == 1:
            return 500
        elif rank == 2:
            return 300
        elif rank == 3:
            return 200
        return 0

    def scroll_offset(self):
        """Camera follows the leader pack."""
        leader_x = max(rh.x for rh in self.horses)
        return max(0, leader_x - 80)
