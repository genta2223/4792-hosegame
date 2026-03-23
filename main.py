"""Main entry point for どぅなん・ダッシュ！ — DS3風操作"""

import sys
import pyxel
from game import GameState
from race import RaceEngine
from ui import (
    SCREEN_W, SCREEN_H, NAME_CANDIDATES,
    MAIN_COMMANDS, TRAIN_LOCATIONS, TRAIN_INTENSITY, FEED_ITEMS,
    init_font, draw_title, draw_main_screen,
    draw_prologue_scene, draw_naming_screen,
    draw_tutorial_overlay, draw_background, draw_horse,
    draw_message_window, draw_race_scene, draw_race_result,
    draw_password_input_screen, draw_password_show_screen,
    draw_reward_screen, draw_manual_naming_screen,
    draw_vs_password_input_screen, draw_slot_select_screen,
    draw_calendar_proceed_screen, draw_vs_ready_screen
)
from audio import (
    init_audio, play_se, play_fanfare, play_bgm, stop_bgm,
    SE_CURSOR, SE_CONFIRM, SE_CANCEL, SE_TRAIN, SE_WIN, SE_LOSE,
    BGM_RANCH, BGM_RACE, BGM_TITLE
)
from save_load import (
    generate_password, load_from_password,
    save_to_slot, load_from_slot, get_slot_info,
    generate_vs_password, load_horse_from_vs_password
)

# ゲーム状態
STATE_TITLE    = 0
STATE_PROLOGUE = 1
STATE_NAMING   = 2
STATE_TUTORIAL = 3
STATE_PLAY     = 4
STATE_RACE     = 5
STATE_RACE_RESULT = 6
STATE_TUTORIAL_RACE = 7
STATE_PASSWORD_INPUT = 8
STATE_PASSWORD_SHOW  = 9
STATE_REWARD         = 10
STATE_VS_INPUT_1P    = 11
STATE_VS_INPUT_2P    = 12
STATE_VS_RACE        = 13
STATE_VS_RESULT      = 14
STATE_MANUAL_NAMING  = 15
STATE_SAVE_SELECT    = 16
STATE_LOAD_SELECT    = 17
STATE_VS_LOAD_SELECT = 18
STATE_RANCH_MESSAGE  = 19
STATE_CALENDAR_PROCEED = 20
STATE_VS_READY       = 21
STATE_REST_SELECT    = 22

TYPEWRITER_SPEED = 2

# デバッグモード
DEBUG_MODE = "--debug" in sys.argv

# STATE名テーブル（デバッグ表示用）
STATE_NAMES = {
    0: "TITLE",
    1: "PROLOGUE",
    2: "NAMING",
    3: "TUTORIAL",
    4: "PLAY",
    5: "RACE",
    6: "RACE_RESULT",
    7: "TUTORIAL_RACE",
    8: "PASSWORD_INPUT",
    9: "PASSWORD_SHOW",
    10: "REWARD",
    11: "VS_INPUT_1P",
    12: "VS_INPUT_2P",
    13: "VS_RACE",
    14: "VS_RESULT",
    15: "MANUAL_NAMING",
    16: "SAVE_SELECT",
    17: "LOAD_SELECT",
    18: "VS_LOAD_SELECT",
    19: "RANCH_MESSAGE",
    20: "CALENDAR_PROCEED",
    21: "VS_READY",
    22: "REST_SELECT",
}

# おじぃセリフ
PROLOGUE_DIALOGUES = [
    "......",
    "お前さんが 新しく来た\n牧場主か。\n待ちかんてぃーしてたさぁ。",
    "わんは この島で 長いこと\n馬の世話をしている者さぁ。",
    "みんなからは「おじぃ」って\n呼ばれとるよ。よろしくな。",
    "ほれ、見てみぃ。\nこの子がお前さんの\n最初の相棒さぁ。",
    "さあ、まずは この子に\n名前をつけてやってくれ。",
]

TUTORIAL_DIALOGUES = [
    "牧場主の仕事は 1週間に\n2回まで行動できるさぁ。",
    "2回行動したら 次の週に進むよ。",
    "まずは「開墾」からさぁ。\nメニューで一番上の「開墾」を\n選んでみるさぁ。",
    "場所を選んで開墾するさぁ。\nどこでもいいから選んでみぃ。",
    "掘り方を選ぶさぁ。\n浅くか深くか 好きな方でよ。",
    "よくやったさぁ！\n次は「給餌」さぁ。",
    "「給餌」は体重を増やしたり\n軽い疲れを取るのにいいさぁ。\nバガスを食べさせてみぃ。",
    "うむ、いい感じさぁ！\n最後に「休養」さぁ。",
    "「休養」は疲れをしっかり\n癒やすためのものさぁ。",
    "よくやったさぁ！ これで基本の\n流れはバッチリさぁ。これからは\n自分の力で育ててみるさぁ！",
    "疲れが溜まった状態で\n無理に「開墾」すると、\n『故障』して能力がガタ落ち\nすることもあるから要注意さぁ！",
    "うむ、筋がいいさぁ！\nこれで基本は ばっちりよ。\nあとは自由にやってみぃ。\n↑↓とEnterで操作するさぁ。",
]

TUTORIAL_RACE_DIALOGUES = [
    "お前さん、馬をただ闇雲に\n走らせちゃ駄目さぁ。",
    "第1週は若駒むけ、\n第4週にはでっかい重賞があるさぁ。",
    "まずは3ヶ月先のカレンダーを見て\n『目標レース』を決めるんよ。",
    "そこに向けて、体重と疲れを\nピッタリ合わせるのが\n一流の牧場主さぁ！",
    "メニューの「レース」から\n先のレースを選んでみぃ。",
]

class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="DUNAN DASH!", fps=30)
        pyxel.mouse(True)
        init_font()
        init_audio()
        # play_bgm(BGM_RANCH)  # 初期状態は無音（忙しさを避けるため）

        self.state = STATE_TITLE
        self._title_bgm_started = False
        self.game = GameState()
        self.frame = 0
        self.fanfare_played = False

        # プロローグ
        self.dialogue_index = 0
        self.typewriter_counter = 0
        self.chars_shown = 0

        # 命名
        self.name_selected_index = 0

        # チュートリアル
        self.tutorial_step = 0
        self.tutorial_sub_phase = 0  # 0: メッセージ待機, 1: アクション待機
        self.tutorial_input_cooldown = 0

        # DS3メニュー
        self.menu_cursor = 0
        self.sub_menu = None       # None, 'train_loc', 'train_int', 'feed'
        self.sub_cursor = 0
        self.train_location = None  # 選択された場所
        # レース
        self.race_engine = None
        self.current_race_prize = 0
        self.selected_stallion = 0
        
        # パスワード
        self.password_input = ""
        self.password_error = "" # パスワード発行用
        self.current_password_display = ""
        self.title_cursor = 0
        
        self.current_race_name = ""
        self.vs_horses = []  # 対戦馬リスト (最大4頭)

        # ソフトウェアキーボード状態
        self.naming_cursor_row = 0
        self.naming_cursor_col = 0
        self.naming_mode = 0  # 0:ひらがな, 1:カタカナ, 2:英数

        # 牧場メッセージ用
        self.ranch_msg_text = ""
        self.ranch_msg_callback = None

        # カレンダー遷移用
        self.cal_frame = 0
        self.cal_old_year = 1
        self.cal_old_month = 1
        self.cal_old_week = 1
        self.cal_new_year = 1
        self.cal_new_month = 1
        self.cal_new_week = 1
        self.cal_next_state = STATE_PLAY

        # デバッグモード
        self.debug_mode = DEBUG_MODE
        self.debug_panel_open = False

        pyxel.run(self.update, self.draw)

    # ---------- タイプライター ----------
    def _current_text(self):
        if self.state == STATE_PROLOGUE:
            if self.dialogue_index < len(PROLOGUE_DIALOGUES):
                return PROLOGUE_DIALOGUES[self.dialogue_index]
        elif self.state == STATE_NAMING:
            return "この子の名前を\n選んでくれさぁ。"
        elif self.state == STATE_TUTORIAL:
            if self.tutorial_step < len(TUTORIAL_DIALOGUES):
                return TUTORIAL_DIALOGUES[self.tutorial_step]
        elif self.state == STATE_TUTORIAL_RACE:
            if self.tutorial_step < len(TUTORIAL_RACE_DIALOGUES):
                return TUTORIAL_RACE_DIALOGUES[self.tutorial_step]
        return ""

    def _advance_typewriter(self):
        self.typewriter_counter += 1
        if self.typewriter_counter >= TYPEWRITER_SPEED:
            self.typewriter_counter = 0
            self.chars_shown += 1

    def _is_text_complete(self):
        return self.chars_shown >= len(self._current_text())

    def _skip_or_advance(self):
        if not self._is_text_complete():
            self.chars_shown = len(self._current_text())
            return False
        return True

    def _reset_typewriter(self):
        self.chars_shown = 0
        self.typewriter_counter = 0

    # ---------- UPDATE ----------
    def update(self):
        self.frame += 1

        # デバッグ: F12でデバッグモード切り替え
        if pyxel.btnp(pyxel.KEY_F12):
            self.debug_mode = not self.debug_mode

        # デバッグパネル表示切り替え
        if self.debug_mode and pyxel.btnp(pyxel.KEY_F1):
            self.debug_panel_open = not self.debug_panel_open

        # デバッグ: 数字キーで各ステートにジャンプ
        if self.debug_mode and self.debug_panel_open:
            self._handle_debug_jump()

        if self.state == STATE_TITLE:
            self._update_title()
        elif self.state == STATE_PROLOGUE:
            self._update_prologue()
        elif self.state == STATE_NAMING:
            self._update_naming()
        elif self.state == STATE_TUTORIAL:
            self._update_tutorial()
        elif self.state == STATE_TUTORIAL_RACE:
            self._update_tutorial_race()
        elif self.state == STATE_PLAY:
            self._update_play()
        elif self.state == STATE_RACE:
            if self.frame == 1:
                self.race_engine.skip_to_final()
            self._update_race()
        elif self.state == STATE_RACE_RESULT:
            self._update_race_result()
        elif self.state == STATE_PASSWORD_INPUT:
            self._update_password_input()
        elif self.state == STATE_PASSWORD_SHOW:
            self._update_password_show()
        elif self.state == STATE_REWARD:
            self._update_reward()
        elif self.state == STATE_VS_READY:
            self._update_vs_ready()
        elif self.state == STATE_REST_SELECT:
            self._update_rest_select()
        elif self.state == STATE_VS_INPUT_2P:
            self._update_vs_input_2p()
        elif self.state == STATE_VS_RACE:
            if self.frame == 1:
                self.race_engine.skip_to_final()
            self._update_vs_race()
        elif self.state == STATE_VS_RESULT:
            self._update_vs_result()
        elif self.state == STATE_MANUAL_NAMING:
            self._update_manual_naming()
        elif self.state == STATE_SAVE_SELECT:
            self._update_save_select()
        elif self.state == STATE_LOAD_SELECT:
            self._update_load_select()
        elif self.state == STATE_VS_LOAD_SELECT:
            self._update_vs_load_select()
        elif self.state == STATE_RANCH_MESSAGE:
            self._update_ranch_message()
        elif self.state == STATE_CALENDAR_PROCEED:
            self._update_calendar_proceed()

    def _update_title(self):
        # タイトルBGM再生（初回のみ）
        if not self._title_bgm_started:
            play_bgm(BGM_TITLE)
            self._title_bgm_started = True

        if pyxel.btnp(pyxel.KEY_UP):
            self.title_cursor = (self.title_cursor - 1) % 3
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.title_cursor = (self.title_cursor + 1) % 3
            play_se(SE_CURSOR)
            
        if pyxel.btnp(pyxel.KEY_RETURN):
            play_se(SE_CONFIRM)
            stop_bgm()
            self._title_bgm_started = False
            if self.title_cursor == 0:
                self.state = STATE_PROLOGUE
                self._reset_typewriter()
                self.dialogue_index = 0
            elif self.title_cursor == 1:
                self.state = STATE_LOAD_SELECT
                self.sub_cursor = 0
            elif self.title_cursor == 2:
                self.state = STATE_VS_LOAD_SELECT
                self.sub_cursor = 0
                self.password_input = ""
                self.password_error = ""

    def _update_prologue(self):
        self._advance_typewriter()
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self._skip_or_advance():
                self.dialogue_index += 1
                self._reset_typewriter()
                if self.dialogue_index < len(PROLOGUE_DIALOGUES):
                    play_se(SE_CURSOR) # 台詞送りSE
                if self.dialogue_index >= len(PROLOGUE_DIALOGUES):
                    play_se(SE_CONFIRM)
                    self.state = STATE_NAMING
                    self._reset_typewriter()

    def _update_naming(self):
        self._advance_typewriter()
        n = len(NAME_CANDIDATES)

        if pyxel.btnp(pyxel.KEY_RIGHT):
            play_se(SE_CURSOR)
            self.name_selected_index = (self.name_selected_index + 1) % n
        if pyxel.btnp(pyxel.KEY_LEFT):
            play_se(SE_CURSOR)
            self.name_selected_index = (self.name_selected_index - 1) % n
        if pyxel.btnp(pyxel.KEY_DOWN):
            play_se(SE_CURSOR)
            self.name_selected_index = (self.name_selected_index + 2) % n
        if pyxel.btnp(pyxel.KEY_UP):
            play_se(SE_CURSOR)
            self.name_selected_index = (self.name_selected_index - 2) % n

        if pyxel.btnp(pyxel.KEY_RETURN):
            chosen_name = NAME_CANDIDATES[self.name_selected_index]
            if chosen_name == "自分で決める":
                self.state = STATE_MANUAL_NAMING
                self.password_input = "" # リユース
                self.password_error = ""
            else:
                self.game.set_starter_horse(chosen_name)
                self.state = STATE_TUTORIAL
                self.tutorial_step = 0
                self.menu_cursor = 0
                self.sub_menu = None
                self._reset_typewriter()

    def _update_manual_naming(self):
        from ui import HIRAGANA_GRID, KATAKANA_GRID, ALPHA_GRID
        grid = [HIRAGANA_GRID, KATAKANA_GRID, ALPHA_GRID][self.naming_mode]
        
        # ソフトウェアキーボードの操作
        if pyxel.btnp(pyxel.KEY_UP):
            limit = 6 if self.naming_cursor_row == 11 else 5
            self.naming_cursor_col = (self.naming_cursor_col - 1) % limit
            if self.naming_cursor_row < 11:
                while grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                    self.naming_cursor_col = (self.naming_cursor_col - 1) % 5
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            limit = 6 if self.naming_cursor_row == 11 else 5
            self.naming_cursor_col = (self.naming_cursor_col + 1) % limit
            if self.naming_cursor_row < 11:
                while grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                    self.naming_cursor_col = (self.naming_cursor_col + 1) % 5
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.naming_cursor_row = (self.naming_cursor_row - 1) % 12
            while self.naming_cursor_row < 11 and grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                self.naming_cursor_row = (self.naming_cursor_row - 1) % 12
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.naming_cursor_row = (self.naming_cursor_row + 1) % 12
            while self.naming_cursor_row < 11 and grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                self.naming_cursor_row = (self.naming_cursor_row + 1) % 12
            play_se(SE_CURSOR)

        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.naming_cursor_row == 11:
                # 右側のアクションボタン
                idx = self.naming_cursor_col
                if idx <= 2: # モード切り替え
                    self.naming_mode = idx
                    play_se(SE_CURSOR)
                elif idx == 3: # 消す
                    if self.password_input:
                        self.password_input = self.password_input[:-1]
                        play_se(SE_CANCEL)
                elif idx == 4: # 決定
                    if self.password_input:
                        play_se(SE_CONFIRM)
                        self.game.set_starter_horse(self.password_input)
                        self.state = STATE_TUTORIAL
                        self.tutorial_step = 0
                        self.menu_cursor = 0
                        self.sub_menu = None
                        self._reset_typewriter()
                    else:
                        self.password_error = "名前を入力してくれさぁ"
                elif idx == 5: # 戻る
                    play_se(SE_CANCEL)
                    self.state = STATE_NAMING
            else:
                # 文字入力
                from ui import HIRAGANA_GRID, KATAKANA_GRID, ALPHA_GRID
                grid = [HIRAGANA_GRID, KATAKANA_GRID, ALPHA_GRID][self.naming_mode]
                char = grid[self.naming_cursor_row][self.naming_cursor_col]
                if char != "　" and len(self.password_input) < 10:
                    self.password_input += char
                    play_se(SE_CONFIRM)

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            if self.password_input:
                self.password_input = self.password_input[:-1]
                play_se(SE_CANCEL)
        
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            play_se(SE_CANCEL)
            self.state = STATE_NAMING

    def _update_save_select(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.sub_cursor = (self.sub_cursor - 1) % 4
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.sub_cursor = (self.sub_cursor + 1) % 4
            play_se(SE_CURSOR)
        
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.sub_cursor < 3:
                save_to_slot(self.sub_cursor, self.game.ranch, self.game.calendar)
                play_se(SE_CONFIRM)
                self.game._add_log(f"スロット{self.sub_cursor}に記録したさぁ。")
            self.state = STATE_PLAY
            self.sub_menu = None
            
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.state = STATE_PLAY
            self.sub_menu = None
            play_se(SE_CANCEL)

    def _update_load_select(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.sub_cursor = (self.sub_cursor - 1) % 4
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.sub_cursor = (self.sub_cursor + 1) % 4
            play_se(SE_CURSOR)
        
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.sub_cursor < 3:
                ok, res = load_from_slot(self.sub_cursor)
                if ok:
                    self.game.ranch, self.game.calendar = res
                    self.state = STATE_PLAY
                    play_se(SE_CONFIRM)
                    return
            self.state = STATE_TITLE
            play_se(SE_CANCEL)

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.state = STATE_TITLE
            play_se(SE_CANCEL)

    def _update_vs_load_select(self):
        """Pick a horse from save slot for VS 1P."""
        if pyxel.btnp(pyxel.KEY_UP):
            self.sub_cursor = (self.sub_cursor - 1) % 4
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.sub_cursor = (self.sub_cursor + 1) % 4
            play_se(SE_CURSOR)
        
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.sub_cursor < 3:
                ok, res = load_from_slot(self.sub_cursor)
                if ok:
                    ranch, _ = res
                    if ranch.horses:
                        self.vs_horses = [ranch.horses[0]]
                        self.state = STATE_VS_READY
                        self.sub_cursor = 0
                        play_se(SE_CONFIRM)
                        return
                    else:
                        play_se(SE_CANCEL)
                        return
            self.state = STATE_TITLE
            play_se(SE_CANCEL)

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            self.state = STATE_TITLE
            play_se(SE_CANCEL)

    def _update_vs_ready(self):
        """VS preparation screen — add horses or start race."""
        items = []
        if len(self.vs_horses) < 4:
            items.append("add")
        items.append("start")
        items.append("back")

        if pyxel.btnp(pyxel.KEY_UP):
            self.sub_cursor = (self.sub_cursor - 1) % len(items)
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.sub_cursor = (self.sub_cursor + 1) % len(items)
            play_se(SE_CURSOR)

        if pyxel.btnp(pyxel.KEY_RETURN):
            action = items[self.sub_cursor]
            if action == "add":
                play_se(SE_CONFIRM)
                self.state = STATE_VS_INPUT_2P
                self.password_input = ""
                self.password_error = ""
                self.naming_cursor_row = 0
                self.naming_cursor_col = 0
            elif action == "start":
                if len(self.vs_horses) >= 2:
                    play_se(SE_CONFIRM)
                    self.race_engine = RaceEngine(self.vs_horses[0], vs_horses=self.vs_horses[1:])
                    self.state = STATE_VS_RACE
                    self.frame = 1
                    play_bgm(BGM_RACE)
                else:
                    self.password_error = "最低2頭必要さぁ"
            elif action == "back":
                play_se(SE_CANCEL)
                self.vs_horses = []
                self.state = STATE_TITLE

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            play_se(SE_CANCEL)
            self.vs_horses = []
            self.state = STATE_TITLE

    def _enter_train_menu(self):
        """Helper to enter training menu (after warning if needed)."""
        self.state = STATE_PLAY # 戻す
        self.sub_menu = "train_loc"
        self.sub_cursor = 0


    def _trigger_calendar_proceed(self, next_state):
        self.cal_old_year = self.game.calendar.year
        self.cal_old_month = self.game.calendar.month
        self.cal_old_week = self.game.calendar.week
        
        self.game.advance_week()
        
        self.cal_new_year = self.game.calendar.year
        self.cal_new_month = self.game.calendar.month
        self.cal_new_week = self.game.calendar.week
        
        self.cal_next_state = next_state
        self.cal_frame = 0
        self.state = STATE_CALENDAR_PROCEED

    def _update_calendar_proceed(self):
        self.cal_frame += 1
        if self.cal_frame >= 35:
            if pyxel.btnp(pyxel.KEY_RETURN):
                play_se(SE_CONFIRM)
                self.state = self.cal_next_state

    def _update_ranch_message(self):
        """Show a message window in ranch context (Ojii advice)."""
        self._advance_typewriter()
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self._skip_or_advance():
                if self.ranch_msg_callback:
                    callback = self.ranch_msg_callback
                    self.ranch_msg_callback = None
                    callback()
                else:
                    self.state = STATE_PLAY

    def _update_tutorial(self):
        step = self.tutorial_step
        self._advance_typewriter()
        
        if self.tutorial_input_cooldown > 0:
            self.tutorial_input_cooldown -= 1

        # サブフェーズ0: メッセージ表示中
        if self.tutorial_sub_phase == 0:
            if pyxel.btnp(pyxel.KEY_RETURN):
                if not self._is_text_complete():
                    self._skip_or_advance()
                else:
                    self.tutorial_sub_phase = 1
                    self.tutorial_input_cooldown = 12 # 強制的に遊び（クールダウン）を作る
                    play_se(SE_CONFIRM)
            return

        # サブフェーズ1: アクション待機 (クールダウン中は入力を受け付けない)
        if step == 0:
            # 「牧場主の仕事は...」
            self.tutorial_step = 1
            self.tutorial_sub_phase = 0
            self._reset_typewriter()
        elif step == 1:
            # 「2回行動したら...」
            self.tutorial_step = 2
            self.tutorial_sub_phase = 0
            self._reset_typewriter()
        elif step == 2:
            # 「開墾を選んで」
            self.menu_cursor = 0
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                play_se(SE_CONFIRM)
                self.tutorial_step = 3
                self.tutorial_sub_phase = 0
                self.sub_cursor = 0
                self._reset_typewriter()
        elif step == 3:
            # 場所選択
            if pyxel.btnp(pyxel.KEY_UP): 
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor - 1) % len(TRAIN_LOCATIONS)
            if pyxel.btnp(pyxel.KEY_DOWN):
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor + 1) % len(TRAIN_LOCATIONS)
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                play_se(SE_CONFIRM)
                locs = ["higawa", "kubura", "sonai"]
                self.train_location = locs[self.sub_cursor]
                self.tutorial_step = 4
                self.tutorial_sub_phase = 0
                self.sub_cursor = 0
                self._reset_typewriter()
        elif step == 4:
            # 掘り方選択
            if pyxel.btnp(pyxel.KEY_UP):
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor - 1) % len(TRAIN_INTENSITY)
            if pyxel.btnp(pyxel.KEY_DOWN):
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor + 1) % len(TRAIN_INTENSITY)
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                intensity = "normal" if self.sub_cursor == 0 else "deep"
                play_se(SE_TRAIN)
                self.game.do_train(self.train_location, intensity)
                self.tutorial_step = 5
                self.tutorial_sub_phase = 0
                self.sub_cursor = 0
                self._reset_typewriter()
        elif step == 5:
            # 「次は給餌さぁ」
            self.tutorial_step = 6
            self.tutorial_sub_phase = 0
            self._reset_typewriter()
        elif step == 6:
            # 給餌選択 (説明含む)
            self.menu_cursor = 1
            if pyxel.btnp(pyxel.KEY_UP):
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor - 1) % len(FEED_ITEMS)
            if pyxel.btnp(pyxel.KEY_DOWN):
                play_se(SE_CURSOR)
                self.sub_cursor = (self.sub_cursor + 1) % len(FEED_ITEMS)
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                play_se(SE_CONFIRM)
                feed = "bagasse" if self.sub_cursor == 0 else "choumeisou"
                self.game.do_feed(feed)
                self.tutorial_step = 7
                self.tutorial_sub_phase = 0
                self.sub_cursor = 0
                self._reset_typewriter()
        elif step == 7:
            # 「最後に休養さぁ」
            self.tutorial_step = 8
            self.tutorial_sub_phase = 0
            self._reset_typewriter()
        elif step == 8:
            # 休養選択 (説明含む)
            self.menu_cursor = 2
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                play_se(SE_CONFIRM)
                self.game.do_rest()
                self.tutorial_step = 9
                self.tutorial_sub_phase = 0
                self._reset_typewriter()
        elif step == 9:
            # 「よくやったさぁ」などの完了メッセージ
            if pyxel.btnp(pyxel.KEY_RETURN) and self.tutorial_input_cooldown == 0:
                play_se(SE_CONFIRM)
                self._trigger_calendar_proceed(STATE_PLAY)
                self._reset_typewriter()

    def _update_tutorial_race(self):
        self._advance_typewriter()

        if pyxel.btnp(pyxel.KEY_RETURN):
            if self._skip_or_advance():
                if self.tutorial_step >= len(TUTORIAL_RACE_DIALOGUES) - 1:
                    play_se(SE_CONFIRM)
                    self.state = STATE_PLAY
                    self.menu_cursor = 3
                    self.sub_menu = "race_calendar"
                    self.sub_cursor = 0
                    stop_bgm()
                else:
                    self.tutorial_step += 1
                    play_se(SE_CURSOR)
                    self._reset_typewriter()


    def _update_race(self):
        is_running = self.race_engine.update()
        if not is_running:
            stop_bgm()
            order = self.race_engine.player_horse.finish_order
            if order == 1: 
                play_fanfare(SE_WIN)
            else: 
                play_fanfare(SE_LOSE)
            
            self.state = STATE_RACE_RESULT
            self.frame = 0
            self.fanfare_played = True

    def _update_race_result(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            play_se(SE_CONFIRM)
            rank = self.race_engine.get_player_rank()
            prize = 0
            if rank == 1: 
                prize = self.current_race_prize
            elif rank <= 3: 
                prize = self.current_race_prize // 3
            
            h = self.game.selected_horse
            self.game.ranch.balance += prize
            
            # クラス昇級用カウント
            if rank == 1:
                h.wins += 1
                # 重賞判定
                if any(kw in self.current_race_name for kw in ["G1", "G2", "G3", "重賞", "記念", "カップ"]):
                    h.stakes_wins += 1
                # G1判定 (種牡馬制限用)
                if "G1" in self.current_race_name:
                    h.g1_wins += 1
                
            if prize > 0:
                h.prize_money += prize
                
            h.fatigue = max(0, min(100, h.fatigue + 30))
            self.game.ranch.contribution += prize
            self.game._add_log(f"レース終了！ {rank}着 賞金{prize}G")
            
            won_sunset = (rank == 1 and "サンセット" in self.current_race_name)
            if not self.game.ranch.reward_code and (self.game.ranch.contribution >= 10000 or won_sunset):
                import random
                chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # Exclude confusing chars
                suffix = "".join(random.choices(chars, k=4))
                code = f"YONA-2026-{suffix}"
                self.game.ranch.reward_code = code
                self._reset_typewriter()
                stop_bgm()
                self._trigger_calendar_proceed(STATE_REWARD)
                return

            stop_bgm()
            self._trigger_calendar_proceed(STATE_PLAY)

    def _handle_password_typing(self):
        # Alphabet and numbers for password
        for char_code in range(32, 127):
            if pyxel.btnp(char_code):
                char = chr(char_code).upper()
                if len(self.password_input) < 100:
                    self.password_input += char
        
        if pyxel.btnp(pyxel.KEY_BACKSPACE) and len(self.password_input) > 0:
            self.password_input = self.password_input[:-1]

    def _update_password_input(self):
        self._handle_password_typing()
        if pyxel.btnp(pyxel.KEY_RETURN) and self.password_input:
            play_se(SE_CONFIRM)
            success, result = load_from_password(self.password_input)
            if success:
                ranch, cal = result
                self.game.ranch = ranch
                self.game.calendar = cal
                self.state = STATE_PLAY
                stop_bgm()
                self.game._add_log("牧場データをロードしました！")
            else:
                self.password_error = result
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            play_se(SE_CANCEL)
            self.state = STATE_TITLE

    def _update_password_show(self):
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_ESCAPE):
            play_se(SE_CONFIRM)
            self.state = STATE_PLAY

    def _update_reward(self):
        self._advance_typewriter()
        if pyxel.btnp(pyxel.KEY_RETURN):
            if self._is_text_complete():
                play_se(SE_CONFIRM)
                self.state = STATE_PLAY
                stop_bgm()
            else:
                self.chars_shown = 999 # Skip to end

    def _update_vs_pass_input(self):
        # オート・トグル: 文字数に応じてひらがな/カタカナを自動切り替え
        self.naming_mode = len(self.password_input) % 2
        from ui import HIRAGANA_GRID, KATAKANA_GRID
        grid = [HIRAGANA_GRID, KATAKANA_GRID][self.naming_mode]

        # ソフトウェアキーボードの操作
        if pyxel.btnp(pyxel.KEY_UP):
            limit = 6 if self.naming_cursor_row == 11 else 5
            self.naming_cursor_col = (self.naming_cursor_col - 1) % limit
            if self.naming_cursor_row < 11:
                while grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                    self.naming_cursor_col = (self.naming_cursor_col - 1) % 5
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_DOWN):
            limit = 6 if self.naming_cursor_row == 11 else 5
            self.naming_cursor_col = (self.naming_cursor_col + 1) % limit
            if self.naming_cursor_row < 11:
                while grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                    self.naming_cursor_col = (self.naming_cursor_col + 1) % 5
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.naming_cursor_row = (self.naming_cursor_row - 1) % 12
            while self.naming_cursor_row < 11 and grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                self.naming_cursor_row = (self.naming_cursor_row - 1) % 12
            play_se(SE_CURSOR)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.naming_cursor_row = (self.naming_cursor_row + 1) % 12
            while self.naming_cursor_row < 11 and grid[self.naming_cursor_row][self.naming_cursor_col] == "　":
                self.naming_cursor_row = (self.naming_cursor_row + 1) % 12
            play_se(SE_CURSOR)

        if pyxel.btnp(pyxel.KEY_RETURN):
            if self.naming_cursor_row == 11:
                # アクションボタン
                idx = self.naming_cursor_col
                if idx <= 1: # モード切り替え (かな/カナ)
                    # 自動切り替えのため手動切り替えは無視
                    play_se(SE_CURSOR)
                elif idx == 2: # 「ー」
                    if len(self.password_input) < 8:
                        self.password_input += "ー"
                        play_se(SE_CONFIRM)
                elif idx == 3: # 消す
                    if self.password_input:
                        self.password_input = self.password_input[:-1]
                        play_se(SE_CANCEL)
                elif idx == 4: # 決定
                    if len(self.password_input) == 8:
                        h = load_horse_from_vs_password(self.password_input)
                        if h:
                            play_se(SE_CONFIRM)
                            self.vs_horses.append(h)
                            self.password_input = ""
                            self.password_error = ""
                            self.state = STATE_VS_READY
                            self.sub_cursor = 0
                            return
                        else:
                            self.password_error = "呪文が違うさぁ"
                    else:
                        self.password_error = "8文字必要さぁ"
                elif idx == 5: # 戻る
                    play_se(SE_CANCEL)
                    self.state = STATE_VS_READY
                    self.sub_cursor = 0
            else:
                # 文字入力
                from ui import HIRAGANA_GRID, KATAKANA_GRID
                grid = [HIRAGANA_GRID, KATAKANA_GRID][self.naming_mode % 2]
                char = grid[self.naming_cursor_row][self.naming_cursor_col % 5]
                if char != "　" and len(self.password_input) < 8:
                    self.password_input += char
                    play_se(SE_CONFIRM)

        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            if self.password_input:
                self.password_input = self.password_input[:-1]
                play_se(SE_CANCEL)
        
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            play_se(SE_CANCEL)
            self.state = STATE_VS_READY
            self.sub_cursor = 0

    def _update_vs_input_2p(self):
        self._update_vs_pass_input()

    def _update_vs_race(self):
        is_running = self.race_engine.update()
        if not is_running:
            stop_bgm()
            # 1Pの着順をチェック
            order = next((h.finish_order for h in self.race_engine.results if h.player_index == 1), 99)
            if order == 1: 
                play_fanfare(SE_WIN)
            else: 
                play_fanfare(SE_LOSE)

            self.state = STATE_VS_RESULT
            self.frame = 0
            self.fanfare_played = True

    def _update_vs_result(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            play_se(SE_CONFIRM)
            self.vs_horses = []
            self.state = STATE_TITLE


    def _get_current_menu(self):
        h = self.game.selected_horse
        if self.state == STATE_REST_SELECT:
            items = ["ほうぼく", "サウナ", "もどる"]
            return "休養", items, self.sub_cursor

        if self.sub_menu is None:
            items = ["開墾", "給餌", "休養", "レース", "牧場", "対戦パス発行", "記録する"]
            if h and h.age >= 5:
                items.append("引退")
            return "コマンド", items, self.menu_cursor
            
        elif self.sub_menu == "train_loc":
            return "開墾(場所)", TRAIN_LOCATIONS + ["もどる"], self.sub_cursor
            
        elif self.sub_menu == "train_int":
            return "開墾(深さ)", TRAIN_INTENSITY + ["もどる"], self.sub_cursor
            
        elif self.sub_menu == "feed":
            return "給餌", FEED_ITEMS + ["もどる"], self.sub_cursor


        elif self.sub_menu == "ranch":
            items = []
            if len(self.game.ranch.horses) > 1:
                items.append("馬 切替")
            items.append("時の部屋")
            if self.game.calendar.month in [1, 2, 3]:
                items.append("種付け")
            items.append("おじぃに聞く")
            items.append("戻る")
            return "牧場", items, self.sub_cursor
            
        elif self.sub_menu == "paddock":
            return "時の部屋", ["預ける", "引き出す", "戻る"], self.sub_cursor
            
        elif self.sub_menu == "breed_stallion":
            items = [f"{s.name}({s.speed})" for s in self.game.ranch.stallions]
            items.append("戻る")
            return "種牡馬", items, self.sub_cursor
            
        elif self.sub_menu == "breed_mare":
            items = [f"{m.name}({m.speed})" for m in self.game.ranch.broodmares]
            items.append("戻る")
            return "繁殖牝馬", items, self.sub_cursor

        elif self.sub_menu == "paddock_select":
            items = [f"{h.name}" for h in self.game.ranch.horses]
            items.append("戻る")
            return "預ける馬を選択", items, self.sub_cursor
            
        elif self.sub_menu == "race_calendar":
            races = self.game.calendar.get_upcoming_races()
            if not races:
                return "番組表", ["開催なし"], self.sub_cursor
            items = []
            for r in races:
                prefix = "" if r['offset'] == 0 else f"(あと{r['offset']}週) "
                
                # クラスラベルの決定
                r_cls = "未勝利"
                if r["req_prize"] >= 5000: r_cls = "G1"
                elif r["req_prize"] >= 1000: r_cls = "重賞"
                elif r["req_prize"] > 0: r_cls = "一般"
                
                # 出走可能判定
                can_enter = h and h.prize_money >= r["req_prize"]
                color_tag = "#B#" if can_enter else "#R#"
                
                # ラベル生成
                label = f"[{r_cls}]{prefix}{r['name']}({r['prize']}G)"
                items.append(f"{color_tag}{label}")
                
            items.append("戻る")
            return "番組表", items, self.sub_cursor

        return "", [], 0

    def _get_preview_text(self):
        """Return preview text for the current menu selection."""
        if self.sub_menu == "train_loc":
            if self.sub_cursor == 0: return "【比川】\n各能力がバランス良く\n上昇し、気性も改善さぁ"
            if self.sub_cursor == 1: return "【久部良】\nスタミナと根性を\n重点的に鍛えるさぁ"
            if self.sub_cursor == 2: return "【祖納】\nスピードと賢さが\nグンと伸びるさぁ"
            return "前のメニューに戻るさぁ"
        
        elif self.sub_menu == "train_int":
            if self.sub_cursor == 0: return "【浅く】\n疲労が少なく、\n調子も少し上がるさぁ"
            if self.sub_cursor == 1: return "【深く】\n疲労が溜まるが、\n確実に成長できるさぁ"
            return "前のメニューに戻るさぁ"
            
        elif self.sub_menu == "feed":
            if self.sub_cursor == 0: return "【バガス】\n無料の基本餌さぁ。\n体重維持と疲労回復に"
            if self.sub_cursor == 1: return "【長命草】\n300G必要さぁ。\n疲労と調子が劇的に回復"
            return "前のメニューに戻るさぁ"
            
        elif self.state == STATE_REST_SELECT:
            if self.sub_cursor == 0: return "【ほうぼく】\n疲労を中程度回復し、馬の\n『気分』を上向かせる。\n与那国の自然でリフレッシュさぁ！"
            if self.sub_cursor == 1: return "【サウナ】\n疲労を大幅に回復するが、\n少し体重が減る。一気に\n疲れを取るならこれさぁ！"
            return "前のメニューに戻るさぁ"

        elif self.sub_menu == "ranch":
            sel = items[self.sub_cursor] if items else ""
            if sel == "馬 切替": return "【馬 切替】\n操作する馬を切り替えるさぁ"
            if sel == "時の部屋": return "【時の部屋】\n馬を時の部屋へ送るさぁ。\n加齢が止まる便利な場所だぞ。\n（登録料: 1500G）"
            if sel == "種付け": return "【種付け】\n引退した馬を掛け合わせ、\n新しい子を誕生させるさぁ！"
            if sel == "おじぃに聞く": return "【おじぃに聞く】\nおじぃから馬の状態や\n血統について助言をもらうさぁ"
            return "前のメニューに戻るさぁ"

        elif self.sub_menu == "paddock":
            if self.sub_cursor == 0: return "【預ける】\n今いる馬を時の部屋へ送るさぁ。\n(最大3頭まで)"
            if self.sub_cursor == 1: return "【引き出す】\n時の部屋の馬を戻すさぁ。\n(牧場の空きが必要)"
            return "前のメニューに戻るさぁ"

        return None

    def _handle_rest_select(self, sel):
        """Handle selection in the STATE_REST_SELECT."""
        if sel == "もどる":
            play_se(SE_CANCEL)
            self.state = STATE_PLAY
            return
            
        play_se(SE_CONFIRM)
        rest_type = "pasture" if sel == "ほうぼく" else "sauna"
        self.game.do_rest(rest_type=rest_type)
        
        # おじぃのメッセージを表示
        if self.game.recent_logs:
            self.ranch_msg_text = self.game.recent_logs[-1]
        else:
            self.ranch_msg_text = "ゆっくり休ませたさぁ。また明日から頑張ろうねぇ。"
            
        self.ranch_msg_callback = lambda: self._post_action_event_check()
        self.state = STATE_RANCH_MESSAGE
        self._reset_typewriter()

    def _update_rest_select(self):
        """Update logic for the rest select screen."""
        title, items, cursor = self._get_current_menu()
        
        if pyxel.btnp(pyxel.KEY_UP):
            play_se(SE_CURSOR)
            self.sub_cursor = (self.sub_cursor - 1) % len(items)
        if pyxel.btnp(pyxel.KEY_DOWN):
            play_se(SE_CURSOR)
            self.sub_cursor = (self.sub_cursor + 1) % len(items)
            
        if pyxel.btnp(pyxel.KEY_RETURN):
            sel = items[self.sub_cursor]
            self._handle_rest_select(sel)
            
        if pyxel.btnp(pyxel.KEY_BACKSPACE) or pyxel.btnp(pyxel.KEY_ESCAPE):
            play_se(SE_CANCEL)
            self.state = STATE_PLAY
            self.sub_menu = None

    def _update_play(self):
        h = self.game.selected_horse
        
        # 昇級間近のアドバイス (Countdownが1勝の時など)
        if h and not self.sub_menu:
            _, c_cnt = h.get_class_info()
            if "あと1勝" in c_cnt or "次走で昇級" in c_cnt:
                if self.frame % 300 == 0: # 時々喋る
                    self.game._add_log("おじぃ「次勝てば、もっと上のレースに出られるさぁ！」")

        # --- DS3風キーボード操作 ---
        title, items, cursor = self._get_current_menu()
        
        if pyxel.btnp(pyxel.KEY_UP):
            play_se(SE_CURSOR)
            cursor = (cursor - 1) % len(items)
            if self.sub_menu is None: self.menu_cursor = cursor
            else: self.sub_cursor = cursor
            
        if pyxel.btnp(pyxel.KEY_DOWN):
            play_se(SE_CURSOR)
            cursor = (cursor + 1) % len(items)
            if self.sub_menu is None: self.menu_cursor = cursor
            else: self.sub_cursor = cursor
            
        if pyxel.btnp(pyxel.KEY_RETURN):
            play_se(SE_CONFIRM)
            sel = items[cursor]
            self._handle_menu_select(sel, cursor)
            
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            play_se(SE_CANCEL)
            if self.sub_menu == "train_int":
                self.sub_menu = "train_loc"
                self.sub_cursor = 0
            elif self.sub_menu == "breed_mare":
                self.sub_menu = "breed_stallion"
                self.sub_cursor = 0
            elif self.sub_menu is not None:
                self.sub_menu = None
                self.sub_cursor = 0

    def _handle_menu_select(self, sel, cursor):
        h = self.game.selected_horse
        
        if self.sub_menu is None:
            if sel == "開墾":
                if h.fatigue >= 70:
                    self.ranch_msg_text = "かなり疲れが溜まっておるさぁ。無理に開墾すると『故障』して取り返しがつかなくなるぞ。本当にやるか？"
                    self.ranch_msg_callback = lambda: self._enter_train_menu()
                    self.state = STATE_RANCH_MESSAGE
                    self._reset_typewriter()
                else:
                    self._enter_train_menu()
            elif sel == "給餌":
                self.sub_menu = "feed"
                self.sub_cursor = 0
            elif sel == "休養":
                # 即時実行せずメニューへ
                self.state = STATE_REST_SELECT
                self.sub_cursor = 0
                play_se(SE_CONFIRM)
            elif sel == "レース":
                if self.game.do_race():
                    self.sub_menu = "race_calendar"
                    self.sub_cursor = 0
            elif sel == "牧場":
                self.sub_menu = "ranch"
                self.sub_cursor = 0
            elif sel == "対戦パス発行":
                # 対戦用パスワード(短縮)発行
                pwd = generate_vs_password(h)
                self.current_password_display = pwd
                self.state = STATE_PASSWORD_SHOW
                play_se(SE_CONFIRM)
            elif sel == "記録する":
                self.state = STATE_SAVE_SELECT
                self.sub_cursor = 0
                play_se(SE_CONFIRM)
            elif sel == "引退":
                idx = self.game.ranch.horses.index(h)
                ok, msg = self.game.ranch.retire_horse(idx)
                self.game._add_log(msg)
                if ok: 
                    self.game.select_next_horse()
                
        elif self.sub_menu == "train_loc":
            if sel == "もどる":
                self.sub_menu = None
                self.sub_cursor = 0
            else:
                locs = ["higawa", "kubura", "sonai"]
                self.train_location = locs[cursor]
                self.sub_menu = "train_int"
                self.sub_cursor = 0
            
        elif self.sub_menu == "train_int":
            if sel == "もどる":
                self.sub_menu = "train_loc"
                self.sub_cursor = 0
            else:
                intensity = "normal" if cursor == 0 else "deep"
                play_se(SE_TRAIN)
                self.game.do_train(self.train_location, intensity)
                self.sub_menu = None
                self.sub_cursor = 0
            
            # 潜在能力キャップの警告チェック
            if h.cap_warning_triggered:
                warning_msgs = [
                    "この子の限界が見えてきたかもしれんさぁ。\nこれ以上は相当な根気がいるぞ。",
                    "かなり仕上がってきたさぁ！\nだが、ここから先は一筋縄じゃいかんさぁ。"
                ]
                self.ranch_msg_text = random.choice(warning_msgs)
                self.ranch_msg_callback = lambda: self._post_action_event_check()
                self.state = STATE_RANCH_MESSAGE
                self._reset_typewriter()
                return

            self._post_action_event_check()
            
        elif self.sub_menu == "feed":
            if sel == "もどる":
                self.sub_menu = None
                self.sub_cursor = 0
            else:
                feed = "bagasse" if cursor == 0 else "choumeisou"
                self.game.do_feed(feed)
                self.sub_menu = None
                self._post_action_event_check()
                
        elif self.sub_menu == "ranch":
            if sel == "馬 切替":
                self.game.select_next_horse()
                self.sub_menu = None
            elif sel == "時の部屋":
                self.sub_menu = "paddock"
                self.sub_cursor = 0
            elif sel == "戻る":
                self.sub_menu = None
            elif sel == "種付け":
                self.sub_menu = "breed_stallion"
                self.sub_cursor = 0
            elif sel == "おじぃに聞く":
                self._show_ojii_advice()
                
        elif self.sub_menu == "paddock":
            if sel == "預ける":
                if len(self.game.ranch.horses) > 1:
                    # 預ける馬を選択するサブメニューへ
                    self.sub_menu = "paddock_select"
                    self.sub_cursor = 0
                elif self.game.ranch.horses:
                    # 1頭しかいない場合はその馬を預ける
                    idx = 0
                    ok, msg = self.game.ranch.add_to_paddock(idx)
                    self.game._add_log(msg)
                    if ok: self.game.select_next_horse()
                    self.sub_menu = None
                else:
                    self.game._add_log("馬がいません。")
            elif sel == "引き出す":
                if self.game.ranch.paddock:
                    # 引き出す馬を選択 (現在は最後の一頭を自動引き出し)
                    idx = len(self.game.ranch.paddock) - 1
                    ok, msg = self.game.ranch.remove_from_paddock(idx)
                    self.game._add_log(msg)
                else:
                    self.game._add_log("パドックに馬がいません。")
                self.sub_menu = None
            elif sel == "戻る":
                self.sub_menu = "ranch"
                self.sub_cursor = 0
                
        elif self.sub_menu == "paddock_select":
            if sel == "戻る":
                self.sub_menu = "paddock"
                self.sub_cursor = 0
            else:
                ok, msg = self.game.ranch.add_to_paddock(cursor)
                self.game._add_log(msg)
                if ok: self.game.select_next_horse()
                self.sub_menu = None

        elif self.sub_menu == "breed_stallion":
            if sel == "戻る":
                self.sub_menu = "ranch"
                self.sub_cursor = 0
                return
            self.selected_stallion = cursor
            self.sub_menu = "breed_mare"
            self.sub_cursor = 0
            
        elif self.sub_menu == "breed_mare":
            if sel == "戻る":
                self.sub_menu = "breed_stallion"
                self.sub_cursor = 0
                return
            ok, msg = self.game.ranch.breed_horse(self.selected_stallion, cursor, "新星号")
            self.game._add_log(msg)
            self.sub_menu = None
            
        elif self.sub_menu == "race_calendar":
            if sel == "戻る" or sel == "開催なし":
                self.sub_menu = None
                return
                
            races = self.game.calendar.get_upcoming_races()
            selected_race = races[cursor]
            
            # クラス制限チェック
            h_class, _ = h.get_class_info()
            # 未勝利馬は未勝利戦のみ
            if h_class == "未勝利" and "未勝利" not in selected_race["name"]:
                self.game._add_log("未勝利馬は一般レースに出られません！")
                return
            # 一般以上の馬は未勝利戦に出られない
            if h_class != "未勝利" and "未勝利" in selected_race["name"]:
                self.game._add_log("既勝利馬は未勝利戦に出られません！")
                return
            # G1は重賞クラス以上
            if "G1" in selected_race["name"] and h_class not in ["重賞クラス", "G1級"]:
                self.game._add_log("G1は重賞を勝たないと出られません！")
                return
            
            if selected_race["offset"] == 0:
                # 当週のレースなら出走準備（おじぃの助言を挟む）
                self._prepare_race(selected_race)
            else:
                # 目標レースとして登録
                h.target_race = selected_race["name"]
                h.target_weeks_left = selected_race["offset"]
                self.game._add_log(f"目標を「{h.target_race}」に設定しました！")
                self.sub_menu = None

    def _start_race(self, race_obj):
        """Transition to race scene."""
        self.race_engine = RaceEngine(self.game.selected_horse)
        self.current_race_prize = race_obj["prize"]
        self.current_race_name = race_obj["name"]
        self.state = STATE_RACE
        self.frame = 1 # リセット
        stop_bgm()
        play_bgm(BGM_RACE)

    def _show_ojii_advice(self):
        """Sage Ojii provides context-aware advice about the horse and bloodline."""
        h = self.game.selected_horse
        if not h: return

        advice = ""
        # 1. 血統の傾向
        if h.sire != "不明" or h.dam != "不明":
            if h.speed > 180:
                advice = f"おぉ、{h.name}のこの脚の速さ！まさに父：{h.sire}からの贈り物さぁ。素晴らしい血筋だねぇ。"
            elif h.stamina > 180:
                advice = f"この子の粘り強さは母：{h.dam}譲りだねぇ。長い距離でもバテない良い血筋さぁ。"
            else:
                advice = f"父：{h.sire}、母：{h.dam}。二人の良さをしっかり引き継いで、これからが楽しみさぁ。"
        else:
            advice = "この子はまだ独自の道を歩んでおる。ここから伝説を作っていこうさぁ。"

        # 2. 成長限界とキャップ
        for s, cap in h.caps.items():
            val = getattr(h, s)
            if val >= cap - 10:
                advice += f"\n\n…おっと、{s}の成長が鈍くなっておるねぇ。「今の血筋」での限界が近いかもしれん。次は時の部屋で、もっと強い血と混ぜる時かもしれんさぁ。"
                break
        
        # 3. 引退/時の部屋/モードの誘導
        if h.age >= 6:
            advice += "\n\nそろそろ この子もベテランさぁ。全盛期のうちに『時の部屋』へ登録して、次世代に夢を託すのも一つの手だぞ。"
        elif h.get_class_name() == "G1級":
            advice += "\n\nG1を勝つなんて大したもんさぁ！友人対戦パスを発行して、島一番の馬であることを証明しにいこうさぁ！"

        self.ranch_msg_text = advice
        self.ranch_msg_callback = None
        self.state = STATE_RANCH_MESSAGE
        self._reset_typewriter()

    def _prepare_race(self, race_obj):
        """Show Ojii advice before race start."""
        # ダミーエンジンで相対的な強さを判定
        dummy_engine = RaceEngine(self.game.selected_horse)
        
        p_pwr = self.game.selected_horse.race_power()
        rivals = [rh.horse for rh in dummy_engine.horses if not rh.is_player]
        r_avg = sum(rh.race_power() for rh in rivals) / len(rivals) if rivals else 0
        
        if p_pwr > r_avg + 5:
            self.ranch_msg_text = "ほほう。今回の相手なら、普通に走れるはずさぁ。\n「開墾・給餌・休養」など、悔いのないよう\n最後の仕上げをしてから出走するよ！"
        elif p_pwr > r_avg - 2:
            self.ranch_msg_text = "なかなか 手強い相手もいるが、\nこの子なら きっとやってくれるさぁ。\n「開墾・給餌・休養」で最後の仕上げさぁ！"
        else:
            self.ranch_msg_text = "格上の相手が 揃っておるねぇ。\nまずは 無事に走ってくることを考えようさぁ。\n「開墾・給餌・休養」で最後の仕上げさぁ！"
            
        # 目標に登録
        self.game.selected_horse.target_race = race_obj["name"]
        self.game.selected_horse.target_weeks_left = 0
        self.game._add_log(f"目標を「{race_obj['name']}」に設定しました！")

        self.ranch_msg_callback = None
        self.state = STATE_RANCH_MESSAGE
        self.sub_menu = None
        self._reset_typewriter()

    def _jump_to_race_state(self):
        """Called after Ojii advice text finishes."""
        self.state = STATE_RACE
        self.frame = 1
        stop_bgm()
        play_bgm(BGM_RACE)

    def _post_action_event_check(self):
        """Decrement actions_left, check for races, or advance week."""
        h = self.game.selected_horse
        self.game.actions_left -= 1

        if self.game.actions_left <= 0:
            if h and h.target_race and h.target_weeks_left == 0:
                # Race day! Race ALWAYS ends the week after it's done.
                races = self.game.calendar.get_races()
                match = next((r for r in races if r["name"] == h.target_race), None)
                if match:
                    self.game._add_log(f"⏰ レース「{h.target_race}」の時間です！")
                    self._start_race(match)
                    return

            # End of week
            self._trigger_calendar_proceed(STATE_PLAY)
            return
        
        self.state = STATE_PLAY

    # ---------- DRAW ----------
    def draw(self):
        pyxel.cls(0)

        if self.state == STATE_TITLE:
            draw_title(self.frame, self.title_cursor)
        elif self.state == STATE_PROLOGUE:
            self._draw_prologue()
        elif self.state == STATE_NAMING:
            self._draw_naming()
        elif self.state == STATE_TUTORIAL:
            self._draw_tutorial()
        elif self.state == STATE_TUTORIAL_RACE:
            self._draw_tutorial_race()
        elif self.state == STATE_PLAY or self.state == STATE_REST_SELECT:
            self._draw_play()
        elif self.state == STATE_RACE:
            self._draw_race()
        elif self.state == STATE_RACE_RESULT:
            self._draw_race_result()
        elif self.state == STATE_LOAD_SELECT:
            draw_slot_select_screen(self.frame, "データをロード", [get_slot_info(i) for i in range(3)], self.sub_cursor)
        elif self.state == STATE_SAVE_SELECT:
            draw_slot_select_screen(self.frame, "どこに記録する？", [get_slot_info(i) for i in range(3)], self.sub_cursor)
        elif self.state == STATE_VS_LOAD_SELECT:
            draw_slot_select_screen(self.frame, "自分の馬を選ぶさぁ", [get_slot_info(i) for i in range(3)], self.sub_cursor)
        elif self.state == STATE_RANCH_MESSAGE:
            # 牧場画面を背景におじぃのメッセージを表示
            draw_main_screen(self.frame, self.game, "おじぃ", [], 0)
            draw_message_window(self.ranch_msg_text, self.chars_shown, "おじぃ")
        elif self.state == STATE_CALENDAR_PROCEED:
            draw_calendar_proceed_screen(self.frame, self.game, self.cal_frame,
                                         self.cal_old_year, self.cal_old_month, self.cal_old_week,
                                         self.cal_new_year, self.cal_new_month, self.cal_new_week)
        elif self.state == STATE_PASSWORD_SHOW:
            draw_password_show_screen(self.frame, self.current_password_display)
        elif self.state == STATE_REWARD:
            draw_reward_screen(self.frame, self.chars_shown, self.game.ranch.reward_code)
        elif self.state == STATE_VS_READY:
            draw_vs_ready_screen(self.frame, self.vs_horses, self.sub_cursor)
        elif self.state == STATE_VS_INPUT_2P:
            p_num = len(self.vs_horses) + 1
            draw_vs_password_input_screen(self.frame, self.password_input, self.naming_cursor_row, self.naming_cursor_col, self.naming_mode, self.password_error, f"{p_num}Pの呪文入力")
        elif self.state == STATE_VS_RACE:
            draw_race_scene(self.frame, self.race_engine)
        elif self.state == STATE_VS_RESULT:
            draw_race_scene(self.frame, self.race_engine)
            draw_race_result(self.race_engine)
        elif self.state == STATE_MANUAL_NAMING:
            draw_manual_naming_screen(self.frame, self.password_input, 
                                       self.naming_cursor_row, self.naming_cursor_col, 
                                       self.naming_mode, self.password_error)

        # デバッグオーバーレイ（全画面の上に描画）
        if self.debug_mode:
            self._draw_debug_overlay()

    def _draw_prologue(self):
        text = self._current_text()
        draw_prologue_scene(self.frame, text, self.chars_shown)

    def _draw_naming(self):
        text = self._current_text()
        draw_naming_screen(self.frame, self.name_selected_index,
                           text, self.chars_shown)

    def _draw_tutorial(self):
        step = self.tutorial_step
        # サブメニュー状態をチュートリアルステップに合わせる (10段階版)
        if step == 3:
            sub = "train_loc"
        elif step == 4:
            sub = "train_int"
        elif step == 6:
            sub = "feed"
        else:
            sub = None

        if sub == "train_loc":
            title, items, cursor = "開墾(場所)", TRAIN_LOCATIONS, self.sub_cursor
        elif sub == "train_int":
            title, items, cursor = "開墾(深さ)", TRAIN_INTENSITY, self.sub_cursor
        elif sub == "feed":
            title, items, cursor = "給餌", FEED_ITEMS, self.sub_cursor
        else:
            title, items, cursor = "チュートリアル", MAIN_COMMANDS, self.menu_cursor

        draw_main_screen(self.frame, self.game, title, items, cursor)
        # チュートリアルメッセージ
        text = self._current_text()
        draw_message_window(text, self.chars_shown)

    def _draw_tutorial_race(self):
        draw_main_screen(self.frame, self.game, "チュートリアル", MAIN_COMMANDS, 3)
        text = self._current_text()
        draw_message_window(text, self.chars_shown)

    def _draw_play(self):
        title, items, cursor = self._get_current_menu()
        is_wide = (title in ["番組表", "種牡馬", "繁殖牝馬"])
        preview = self._get_preview_text()
        draw_main_screen(self.frame, self.game, title, items, cursor, wide_menu=is_wide, preview_text=preview)

    def _draw_race(self):
        draw_race_scene(self.frame, self.race_engine)

    def _draw_race_result(self):
        draw_race_scene(self.frame, self.race_engine)
        draw_race_result(self.race_engine)

    # ---------- デバッグモード ----------
    def _handle_debug_jump(self):
        """デバッグパネル表示中: 数字キーでステートジャンプ。"""
        jump_map = {
            pyxel.KEY_0: STATE_TITLE,
            pyxel.KEY_1: STATE_PROLOGUE,
            pyxel.KEY_2: STATE_NAMING,
            pyxel.KEY_3: STATE_TUTORIAL,
            pyxel.KEY_4: STATE_PLAY,
            pyxel.KEY_5: STATE_RACE,
            pyxel.KEY_6: STATE_RACE_RESULT,
            pyxel.KEY_7: STATE_TUTORIAL_RACE,
            pyxel.KEY_8: STATE_MANUAL_NAMING,
            pyxel.KEY_9: STATE_REWARD,
        }
        for key, target_state in jump_map.items():
            if pyxel.btnp(key):
                self._debug_jump_to(target_state)
                break

        # F2: 馬を即座に作成（馬がいない場合テスト不可なので）
        if pyxel.btnp(pyxel.KEY_F2):
            if not self.game.ranch.horses:
                self.game.set_starter_horse("デバッグ号")
                self.game._add_log("[DEBUG] デバッグ馬を作成")
            else:
                self.game._add_log("[DEBUG] 馬はすでにいます")

        # F3: 資金追加
        if pyxel.btnp(pyxel.KEY_F3):
            self.game.ranch.balance += 10000
            self.game._add_log("[DEBUG] 資金+10000G")

        # F4: 疲労リセット
        if pyxel.btnp(pyxel.KEY_F4):
            h = self.game.selected_horse
            if h:
                h.fatigue = 0
                self.game._add_log("[DEBUG] 疲労リセット")

        # F5: 週を進める
        if pyxel.btnp(pyxel.KEY_F5):
            self._trigger_calendar_proceed(STATE_PLAY)
            self.game._add_log("[DEBUG] 1週進めました")

    def _debug_jump_to(self, target):
        """指定ステートに安全にジャンプする。"""
        self.game._add_log(f"[DEBUG] → {STATE_NAMES.get(target, '?')}")
        
        # 必要な前提条件を自動セットアップ
        if target in (STATE_TUTORIAL, STATE_PLAY, STATE_TUTORIAL_RACE):
            if not self.game.ranch.horses:
                self.game.set_starter_horse("デバッグ号")
            self.menu_cursor = 0
            self.sub_menu = None
            self.sub_cursor = 0
            
        if target == STATE_PROLOGUE:
            self.dialogue_index = 0
            self._reset_typewriter()

        if target == STATE_NAMING:
            self.name_selected_index = 0
            self._reset_typewriter()

        if target == STATE_TUTORIAL:
            self.tutorial_step = 0
            self._reset_typewriter()

        if target == STATE_TUTORIAL_RACE:
            self.tutorial_step = 0
            self._reset_typewriter()

        if target == STATE_MANUAL_NAMING:
            self.password_input = ""
            self.password_error = ""
            self.naming_cursor_row = 0
            self.naming_cursor_col = 0
            self.naming_mode = 0

        if target in (STATE_RACE, STATE_RACE_RESULT):
            if not self.game.ranch.horses:
                self.game.set_starter_horse("デバッグ号")
            self.race_engine = RaceEngine(self.game.selected_horse)
            self.current_race_prize = 500
            self.current_race_name = "デバッグレース"
            if target == STATE_RACE_RESULT:
                # レースを即終了させる
                for _ in range(500):
                    if not self.race_engine.update():
                        break

        if target == STATE_REWARD:
            self._reset_typewriter()
            if not self.game.ranch.reward_code:
                self.game.ranch.reward_code = "YONA-DEBUG-0000"

        self.state = target

    def _draw_debug_overlay(self):
        """デバッグ情報のオーバーレイ描画。"""
        from ui import jp_text, COL_SUN, COL_WHITE, COL_BLACK, COL_RED, COL_GRAY, SCREEN_W
        
        # 右上にミニインジケーター（常時）
        pyxel.text(SCREEN_W - 38, 1, "[DEBUG]", 8)
        pyxel.text(SCREEN_W - 80, 1, f"F:{self.frame:06d}", 13)

        if not self.debug_panel_open:
            pyxel.text(2, 1, "F1:Panel", 13)
            return

        # パネルを描画
        pw, ph = 200, 120
        px, py = (SCREEN_W - pw) // 2, 20
        pyxel.rect(px, py, pw, ph, 0)
        pyxel.rectb(px, py, pw, ph, 8)
        pyxel.rectb(px + 1, py + 1, pw - 2, ph - 2, 5)

        y = py + 4
        pyxel.text(px + 4, y, "=== DEBUG PANEL ===", 8)
        y += 10
        state_name = STATE_NAMES.get(self.state, "?")
        pyxel.text(px + 4, y, f"State: {self.state} ({state_name})", 7)
        y += 8
        pyxel.text(px + 4, y, f"Frame: {self.frame}  FPS: {pyxel.frame_count // max(1, self.frame // 30)}" if self.frame > 30 else f"Frame: {self.frame}", 7)
        y += 8

        h = self.game.selected_horse
        if h:
            pyxel.text(px + 4, y, f"Horse: {h.name} age={h.age}", 10)
            y += 8
            pyxel.text(px + 4, y, f"SPD={h.speed} STA={h.stamina} GUT={h.guts}", 7)
            y += 8
            pyxel.text(px + 4, y, f"WIS={h.wisdom} LCK={h.luck} TMP={h.temper}", 7)
            y += 8
            pyxel.text(px + 4, y, f"WT={h.weight}/{h.best_weight} FAT={h.fatigue} PM={h.prize_money}", 7)
            y += 8
        else:
            pyxel.text(px + 4, y, "Horse: (none)", 13)
            y += 8

        pyxel.text(px + 4, y, f"Balance: {self.game.ranch.balance}G", 10)
        y += 8
        pyxel.text(px + 4, y, f"Calendar: {self.game.calendar.display()}", 7)
        y += 10

        # ジャンプキー一覧
        pyxel.text(px + 4, y, "0:TITLE 1:PRO 2:NAME 3:TUT 4:PLAY", 13)
        y += 8
        pyxel.text(px + 4, y, "5:RACE 6:RESULT 7:TUTRACE 8:MNAME 9:REWARD", 13)
        y += 8
        pyxel.text(px + 4, y, "F2:Horse F3:+10kG F4:FAT=0 F5:Week++", 13)


if __name__ == "__main__":
    if DEBUG_MODE:
        print("[DEBUG] デバッグモード ON")
        print("[DEBUG] F12: デバッグ表示切替  F1: パネル表示")
        print("[DEBUG] パネル表示中の数字キーで各画面にジャンプ")
    App()
