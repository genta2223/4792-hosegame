"""UI rendering for どぅなん・ダッシュ！ — DS3風ウィンドウシステム"""

import os
import pyxel
import math
from race import GOAL_DISTANCE

# ---------- レイアウト定数 ----------
SCREEN_W = 256
GAME_H = 224
PAD_H = 64
SCREEN_H = GAME_H + PAD_H

# 背景（上部エリア）
BG_H = 75

# Pyxel colors
COL_BG      = 1   # dark blue
COL_GRASS   = 3   # dark green
COL_LGRASS  = 11  # light green
COL_SEA     = 12  # blue
COL_SUNSET  = 9   # orange
COL_SUN     = 10  # yellow
COL_RED     = 8   # red
COL_WHITE   = 7   # white
COL_BLACK   = 0   # black
COL_GRAY    = 13  # gray
COL_DKGRAY  = 5   # dark gray

# ---------- 日本語フォント ----------
_jp_font = None
FONT_CHAR_W = 8


def init_font():
    """Initialize Japanese BDF font. Must be called AFTER pyxel.init()."""
    global _jp_font
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "misaki_gothic.bdf")
    if os.path.exists(font_path):
        _jp_font = pyxel.Font(font_path)
    else:
        print(f"[WARN] Font not found: {font_path}")
        print("       Run 'python download_font.py' first.")


def jp_text(x, y, text, col):
    if _jp_font:
        pyxel.text(x, y, text, col, _jp_font)
    else:
        pyxel.text(x, y, text, col)


def text_width(text):
    if _jp_font:
        return len(text) * FONT_CHAR_W
    return len(text) * 4


def _wrap_text(text, line_len):
    """Simple text wrapper for Japanese characters."""
    lines = []
    for i in range(0, len(text), line_len):
        lines.append(text[i:i+line_len])
    return lines


def draw_parameter_gauge(x, y, label, val, cap, max_val=255):
    """Draw a dot-style parameter gauge with a cap marker. Hardened against freezes."""
    jp_text(x, y, label, COL_WHITE)
    
    # 物理的な数値保証 (Noneや文字列対策)
    try:
        val = int(val or 0)
        cap = int(cap or 0)
        max_val = max(1, int(max_val or 255)) # 0除算防止
    except (ValueError, TypeError):
        val = 0
        cap = 0
        max_val = 255
        
    gx = int(x) + 38
    gy = int(y)
    gw = 60
    gh = 4
    
    # クランプ処理
    val = max(0, min(val, max_val))
    cap = max(0, min(cap, max_val))
    
    # Base
    pyxel.rect(gx, gy + 1, gw, gh, COL_DKGRAY)
    
    # Segments (dot-style)
    # 描画幅を整数で計算
    fill_w = int((val / max_val) * gw)
    for i in range(0, fill_w, 2):
        # 座標とサイズを必ず int() に
        pyxel.rect(int(gx + i), gy + 1, 1, gh, COL_LGRASS)
    
    # Cap Marker
    cx = gx + int((cap / max_val) * gw)
    pyxel.line(int(cx), gy, int(cx), gy + gh + 1, COL_SUN)


# ====================================================================
#  DS3風ウィンドウ描画
# ====================================================================

def draw_window(x, y, w, h, title=None):
    """Draw a DS3-style window: black bg with white border."""
    pyxel.rect(x, y, w, h, COL_BLACK)
    pyxel.rectb(x, y, w, h, COL_WHITE)
    pyxel.rectb(x + 1, y + 1, w - 2, h - 2, COL_DKGRAY)
    if title:
        tw = text_width(title) + 8
        pyxel.rect(x + 4, y - 1, tw, 10, COL_BLACK)
        pyxel.rectb(x + 4, y - 1, tw, 10, COL_WHITE)
        jp_text(x + 8, y + 1, title, COL_SUN)


def draw_menu_list(x, y, items, cursor, w=None, max_visible=None):
    """Draw a vertical menu list with cursor arrow and simple scrolling."""
    if not items:
        return

    if w is None:
        # Strip color tags for width calculation
        stripped_items = [i[3:] if i.startswith(("#R#", "#B#")) else i for i in items]
        w = max(text_width(item) for item in stripped_items) + 24
        
    # Scrolling logic
    n = len(items)
    if max_visible is None:
        max_visible = n
        
    start_idx = 0
    if n > max_visible:
        # Keep cursor in view
        if cursor >= max_visible // 2:
            start_idx = min(n - max_visible, cursor - max_visible // 2)
            
    end_idx = min(n, start_idx + max_visible)
    
    for i in range(start_idx, end_idx):
        item = items[i]
        iy = y + (i - start_idx) * 14
        
        # Color tag support
        d_col = COL_GRAY
        display_text = item
        if item.startswith("#R#"):
            d_col = COL_RED
            display_text = item[3:]
        elif item.startswith("#B#"):
            d_col = COL_SEA
            display_text = item[3:]
            
        if i == cursor:
            jp_text(x + 4, iy, "▶", COL_SUN)
            jp_text(x + 16, iy, display_text, COL_WHITE)
        else:
            jp_text(x + 16, iy, display_text, d_col)
            
    # Scroll indicators
    if start_idx > 0:
        pyxel.tri(x + w - 8, y - 2, x + w - 12, y + 2, x + w - 4, y + 2, COL_GRAY)
    if end_idx < n:
        ey = y + max_visible * 14 - 8
        pyxel.tri(x + w - 8, ey + 4, x + w - 12, ey, x + w - 4, ey, COL_GRAY)


# ====================================================================
#  背景描画（上部2/3）
# ====================================================================

def draw_background(frame):
    """Draw Yonaguni landscape in the top portion."""
    # 空
    for y in range(0, 25):
        col = COL_BG if y < 8 else COL_SUNSET if y < 16 else COL_SUN
        pyxel.line(0, y, SCREEN_W, y, col)

    # 太陽
    # 経過週によって色や位置を少し変える（夕方演出など）
    sun_y = 12 + int(math.sin(frame * 0.02) * 2)
    pyxel.circ(200, sun_y, 10, COL_SUN)
    pyxel.circ(200, sun_y, 7, 10)

    # 海
    for y in range(20, 43):
        wave = int(math.sin(frame * 0.05 + y * 0.3) * 2)
        pyxel.line(0, y, SCREEN_W, y, COL_SEA)
        if (y + frame // 8) % 6 == 0:
            pyxel.line(wave + 20, y, wave + 40, y, COL_WHITE)

    # 牧草地
    for y in range(43, BG_H):
        col = COL_GRASS if (y % 4 < 2) else COL_LGRASS
        pyxel.line(0, y, SCREEN_W, y, col)

    # 柵
    for fx in range(10, SCREEN_W, 35):
        pyxel.rect(fx, 45, 2, 10, COL_DKGRAY)
        pyxel.line(fx, 48, fx + 33, 48, COL_DKGRAY)
        pyxel.line(fx, 52, fx + 33, 52, COL_DKGRAY)

    # 草
    for gx in range(8, SCREEN_W, 20):
        gy = 55 + (gx * 7) % 25
        if gy < BG_H:
            sway = int(math.sin(frame * 0.03 + gx) * 2)
            pyxel.line(gx, gy, gx + sway, gy - 5, COL_LGRASS)


# ====================================================================
#  馬ドット絵
# ====================================================================

def draw_horse(x, y, horse, frame):
    """Draw an 8-bit horse with variations and fatigue cues."""
    # Handle Horse object or None
    if horse and hasattr(horse, 'appearance'):
        ap = horse.appearance
        fatigue = horse.fatigue
    else:
        # Default appearance for title/naming screens
        ap = {"base_color": 4, "face_marking": 0, "mane_tail_color": 0, "leg_marking": 0}
        fatigue = 0

    bob = int(math.sin(frame * 0.1) * 2)
    leg_phase = frame % 30
    
    # Fatigue effect: drooping head and sweat
    head_y_off = 0
    if fatigue > 60:
        head_y_off = 2
        bob = int(math.sin(frame * 0.05) * 1) # Slower bobbing
        
    base_col = ap["base_color"]
    mane_col = ap["mane_tail_color"]
    
    # Body
    pyxel.rect(x + 4, y + bob + 4, 20, 10, base_col)
    
    # Neck and Head
    neck_x, neck_y = x + 20, y + bob - 2 + head_y_off
    pyxel.rect(neck_x, neck_y, 5, 10, base_col)
    
    head_x, head_y = x + 22, y + bob - 5 + head_y_off
    pyxel.rect(head_x, head_y, 10, 7, base_col)
    
    # Eye
    pyxel.pset(head_x + 7, head_y + 2, COL_BLACK)
    
    # Ears
    pyxel.rect(x + 25, head_y - 3, 2, 4, base_col)
    pyxel.rect(x + 28, head_y - 3, 2, 4, base_col)
    
    # Face Markings (White)
    fm = ap["face_marking"]
    if fm == 1: # Star
        pyxel.pset(head_x + 4, head_y + 1, COL_WHITE)
    elif fm == 2: # Blaze
        pyxel.line(head_x + 4, head_y + 1, head_x + 9, head_y + 4, COL_WHITE)
    elif fm == 3: # Snip
        pyxel.pset(head_x + 9, head_y + 4, COL_WHITE)

    # Mane
    pyxel.line(neck_x + 1, neck_y, neck_x + 1, neck_y + 6, mane_col)
    pyxel.line(neck_x + 2, neck_y - 1, neck_x + 2, neck_y + 5, mane_col)

    # Tail
    tail_sway = int(math.sin(frame * 0.06) * 3)
    if fatigue > 80: tail_sway = 0 # Tail doesn't move when exhausted
    pyxel.line(x + 4, y + bob + 6, x + 1 + tail_sway, y + bob + 10, mane_col)
    pyxel.line(x + 4, y + bob + 7, x + tail_sway, y + bob + 11, mane_col)

    # Legs and Leg Markings
    lo = [0, 0, 0, 0]
    if leg_phase < 10:
        lo[0] = 1; lo[3] = -1
    elif leg_phase < 20:
        lo[1] = 1; lo[2] = -1
        
    leg_marking = ap["leg_marking"]
    for i, lx in enumerate([7, 13, 18, 22]):
        off = lo[i]
        ly = y + bob + 14
        pyxel.rect(x + lx + off, ly, 2, 8, base_col)
        
        # Markings
        if leg_marking == 1: # Socks
            pyxel.rect(x + lx + off, ly + 5, 2, 3, COL_WHITE)
        elif leg_marking == 2: # Stockings
            pyxel.rect(x + lx + off, ly + 2, 2, 6, COL_WHITE)
            
        # Hooves
        pyxel.rect(x + lx + off, ly + 7, 3, 2, COL_BLACK)

    # Sweat particles
    if fatigue > 50:
        if (frame + x) % 15 < 5:
            pyxel.pset(x + 10 + (frame % 5), y + bob + 8, COL_WHITE)


# ====================================================================
#  おじぃキャラクター
# ====================================================================

def draw_ojii(x, y, frame):
    bob = int(math.sin(frame * 0.06) * 1)
    pyxel.rect(x + 2, y + bob - 3, 14, 3, COL_SUN)
    pyxel.rect(x + 4, y + bob - 7, 10, 5, COL_SUN)
    pyxel.rect(x + 5, y + bob - 6, 8, 3, 10)
    pyxel.rect(x + 5, y + bob, 8, 7, 15)
    pyxel.line(x + 6, y + bob + 2, x + 7, y + bob + 2, COL_BLACK)
    pyxel.line(x + 10, y + bob + 2, x + 11, y + bob + 2, COL_BLACK)
    pyxel.pset(x + 7, y + bob + 5, COL_BLACK)
    pyxel.line(x + 8, y + bob + 6, x + 9, y + bob + 6, COL_BLACK)
    pyxel.pset(x + 10, y + bob + 5, COL_BLACK)
    pyxel.rect(x + 4, y + bob + 7, 10, 10, COL_GRASS)
    pyxel.rect(x + 1, y + bob + 8, 4, 6, COL_GRASS)
    pyxel.rect(x + 13, y + bob + 8, 4, 6, COL_GRASS)
    pyxel.rect(x + 1, y + bob + 14, 3, 2, 15)
    pyxel.rect(x + 14, y + bob + 14, 3, 2, 15)
    pyxel.rect(x + 5, y + bob + 17, 3, 4, COL_DKGRAY)
    pyxel.rect(x + 10, y + bob + 17, 3, 4, COL_DKGRAY)


# ====================================================================
#  DS3風メイン画面
# ====================================================================

# メインコマンド
MAIN_COMMANDS = ["開墾", "給餌", "休養", "レース", "牧場"]

# 開墾サブメニュー
TRAIN_LOCATIONS = ["比川(穏やか)", "久部良(ハード)", "祖納(バランス)"]
TRAIN_INTENSITY = ["浅く耕す", "深く耕す"]

# 給餌サブメニュー
FEED_ITEMS = ["バガス(無料)", "長命草(300G)"]


def draw_main_screen(frame, game, left_title, left_items, cursor_idx, wide_menu=False, force_date_str=None, preview_text=None):
    """Draw the full DS3-style main game screen with dynamic menu."""
    pyxel.cls(COL_BLACK)

    # --- 上部: 牧場風景 + 馬 ---
    draw_background(frame)
    horse = game.selected_horse
    draw_horse(100, 45, horse, frame)

    # --- メインコマンドウィンドウ ---
    cmd_x, cmd_y = 2, BG_H + 2
    cmd_w, cmd_h = (SCREEN_W - 4), 85
    if not wide_menu:
        cmd_w = 100

    draw_window(cmd_x, cmd_y, cmd_w, cmd_h, left_title)
    draw_menu_list(cmd_x + 4, cmd_y + 10, left_items, cursor_idx, w=cmd_w-8, max_visible=5)

    # --- 情報ウィンドウ (右上/オーバーレイ) ---
    if not wide_menu:
        info_x, info_y = 106, BG_H + 2
        info_w, info_h = 148, 85
    else:
        info_x, info_y = 132, BG_H + 2
        info_w, info_h = 122, 85
        
    draw_window(info_x, info_y, info_w, info_h, "情報")

    if preview_text and not wide_menu:
        # プレビュー表示（情報欄を上書き）
        py = info_y + 12
        lines = preview_text.split("\n")
        for line in lines:
            jp_text(info_x + 8, py, line, COL_WHITE)
            py += 12
    else:
        sy = info_y + 11
        date_str = force_date_str if force_date_str else game.calendar.display()
        jp_text(info_x + 6, sy, date_str, COL_WHITE)
        jp_text(info_x + 85, sy, f"残:{game.actions_left}", COL_LGRASS)
        sy += 12
        jp_text(info_x + 6, sy, f"所持金 {game.ranch.balance}G", COL_SUN)
        sy += 16 # Spacing

        if horse:
            # 1. 馬名、年齢、体重
            jp_text(info_x + 6, sy, horse.name, COL_WHITE)
            aw_text = f"{horse.age}才 {horse.weight}kg"
            aw_x = info_x + info_w - text_width(aw_text) - 4
            jp_text(aw_x, sy, aw_text, COL_GRAY)
            sy += 12
            
            # 2. 体調
            jp_text(info_x + 6, sy, f"体調: {horse.fatigue_text()}", _cond_color(horse.fatigue))
            sy += 12
            # 3. 気分
            jp_text(info_x + 6, sy, f"気分: {horse.condition_text()}", COL_WHITE)
            sy += 12

            # 4. 目標レース
            if horse.target_race:
                name = horse.target_race
                if len(name) > 8: name = name[:7] + ".."
                jp_text(info_x + 6, sy, f"目標:{name}", COL_SUNSET)
                w_text = f"あと{horse.target_weeks_left}週"
                w_x = info_x + info_w - text_width(w_text) - 4
                jp_text(w_x, sy, w_text, COL_WHITE)
            else:
                jp_text(info_x + 6, sy, "目標: 登録なし", COL_DKGRAY)
        else:
            jp_text(info_x + 6, sy, "馬がいません", COL_GRAY)

    # --- 下部ログウィンドウ ---
    log_y = 164
    log_h = 46
    draw_window(2, log_y, SCREEN_W - 4, log_h)

    ly = log_y + 4
    for msg in game.recent_logs[-4:]: # 直近4件
        col = COL_WHITE
        if "故障" in msg: col = COL_RED
        elif "1着" in msg: col = COL_SUN
        
        clean = msg.replace("⚠", "!").replace("🏆", "*")
        jp_text(8, ly, clean[:30], col)
        ly += 10

def draw_ranch_screen(frame, game, horse_list, selected_idx, advice_text):
    """Deeply overhauled Ranch menu: Pedigree, Gauges, and Ojii."""
    pyxel.cls(COL_BLACK)
    draw_background(frame)
    
    # 選択中の馬
    horse = None
    if selected_idx < len(game.ranch.horses):
        horse = game.ranch.horses[selected_idx]
    
    # --- 左: 所有馬リスト ---
    list_w = 80
    draw_window(2, BG_H + 2, list_w, 85, "所有馬")
    draw_menu_list(6, BG_H + 12, horse_list, selected_idx, w=list_w-8)
    
    # --- 右: 個別詳細 ---
    det_x, det_y = list_w + 4, BG_H + 2
    det_w = SCREEN_W - det_x - 2
    draw_window(det_x, det_y, det_w, 85, "詳細")
    
    if horse:
        # 右側に馬を描画
        draw_horse(det_x + det_w - 45, det_y + 35, horse, frame)

        # 1. 名前、年齢、体重
        name_text = horse.name
        if text_width(name_text) > 75:
            name_text = name_text[:8] + ".."
        jp_text(det_x + 6, sy, name_text, COL_WHITE)
        
        status_text = f"{horse.age}才 {horse.weight}kg"
        # 名前から最低16px空ける。ただし窓枠に収まるように stats_x を調整
        stats_x = max(det_x + 95 - text_width(status_text), det_x + 6 + text_width(name_text) + 16)
        jp_text(stats_x, sy, status_text, COL_GRAY)
        sy += 14
        
        # 2. 血統 (1行に圧縮 & トリミング)
        jp_text(det_x + 6, sy, "血統:", COL_DKGRAY)
        ped = f"{horse.sire} x {horse.dam}"
        if len(ped) > 18: ped = ped[:17] + ".."
        jp_text(det_x + 35, sy, ped, COL_WHITE)
        sy += 14
        
        # 3. パラメーター・ゲージ (少し上に詰める)
        draw_parameter_gauge(det_x + 6, sy, "速さ", horse.speed, horse.caps.get("speed", 220))
        sy += 10
        draw_parameter_gauge(det_x + 6, sy, "体力", horse.stamina, horse.caps.get("stamina", 220))
        sy += 10
        draw_parameter_gauge(det_x + 6, sy, "根性", horse.guts, horse.caps.get("guts", 220))
        sy += 12 # 余裕を持たせる
        
        # 4. 昇級ヒント (枠線への干渉回避)
        _, c_hint = horse.get_class_info()
        jp_text(det_x + 6, sy, c_hint, COL_LGRASS)
    else:
        jp_text(det_x + 10, det_y + 35, "馬を選択してさぁ", COL_GRAY)

    # --- 下部: おじぃの鑑定 ---
    msg_y = 164
    draw_window(2, msg_y, SCREEN_W - 4, 46, "おじぃの鑑定")
    
    draw_ojii(8, msg_y + 12, frame)
    
    adv_lines = _wrap_text(advice_text, 22)
    ay = msg_y + 10
    for line in adv_lines[:3]:
        jp_text(35, ay, line, COL_WHITE)
        ay += 12
        
    jp_text(4, 216, "↑↓:移動 Enter:決定 BS:戻る", COL_DKGRAY)

def _cond_color(fatigue):
    if fatigue >= 80:
        return COL_RED
    elif fatigue >= 50:
        return COL_SUNSET
    elif fatigue >= 30:
        return COL_SUN
    return COL_LGRASS


def _wt_color(horse):
    diff = abs(horse.weight - horse.best_weight)
    if diff <= 2:
        return COL_LGRASS
    elif diff <= 4:
        return COL_SUN
    return COL_RED


# ====================================================================
#  タイトル画面
# ====================================================================

def draw_title(frame, cursor, has_data=True):
    """Draw title screen with dynamic menu colors."""
    pyxel.cls(COL_BG)

    for y in range(60, 100):
        wave = int(math.sin(frame * 0.04 + y * 0.2) * 3)
        pyxel.line(0, y, SCREEN_W, y, COL_SEA)
        if y % 5 == 0:
            pyxel.line(wave + 30, y, wave + 50, y, COL_WHITE)

    title = "DUNAN DASH!"
    tw = text_width(title)
    tx = (SCREEN_W - tw) // 2
    jp_text(tx + 1, 36, title, COL_BLACK)
    jp_text(tx, 35, title, COL_SUN)

    sub = "- どぅなん・ダッシュ！ -"
    sw = text_width(sub)
    sx = (SCREEN_W - sw) // 2
    jp_text(sx, 50, sub, COL_SUNSET)

    draw_horse(100, 110, None, frame)

    items = ["はじめから", "つづきから", "パスワード対戦"]
    y = 160
    for i, item in enumerate(items):
        is_disabled = (i == 2 and not has_data)
        
        if i == cursor:
            col = COL_SUN
            pyxel.tri(80, y + 2, 80, y + 8, 84, y + 5, COL_SUN)
        else:
            col = COL_DKGRAY if is_disabled else COL_GRAY
            
        jp_text(90, y, item, col)
        y += 15


# ====================================================================
#  プロローグ / 命名 / チュートリアル（Phase 2 preserved）
# ====================================================================

def draw_message_window(text, chars_shown, speaker="おじぃ"):
    win_h = 52
    win_y = GAME_H - win_h - 2
    win_x = 2
    win_w = SCREEN_W - 4

    pyxel.rect(win_x, win_y, win_w, win_h, COL_BLACK)
    pyxel.rectb(win_x, win_y, win_w, win_h, COL_SUN)
    pyxel.rectb(win_x + 1, win_y + 1, win_w - 2, win_h - 2, COL_DKGRAY)

    name_w = text_width(speaker) + 8
    pyxel.rect(win_x + 6, win_y - 5, name_w, 10, COL_BLACK)
    pyxel.rectb(win_x + 6, win_y - 5, name_w, 10, COL_SUN)
    jp_text(win_x + 10, win_y - 3, speaker, COL_SUN)

    visible = text[:chars_shown]
    lines = _wrap_text(visible, 28)
    ty = win_y + 8
    for line in lines[:4]:
        jp_text(win_x + 8, ty, line, COL_WHITE)
        ty += 10

    if chars_shown >= len(text):
        if (pyxel.frame_count // 15) % 2 == 0:
            tx2 = win_x + win_w - 12
            ty2 = win_y + win_h - 8
            pyxel.tri(tx2, ty2, tx2 + 4, ty2 + 4, tx2 + 8, ty2, COL_SUN)


def _wrap_text(text, max_chars):
    lines = []
    while text:
        if len(text) <= max_chars:
            lines.append(text)
            break
        nl = text.find("\n")
        if nl != -1 and nl <= max_chars:
            lines.append(text[:nl])
            text = text[nl + 1:]
            continue
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines


def draw_prologue_scene(frame, text, chars_shown):
    pyxel.cls(COL_BG)

    for y in range(0, 60):
        t = y / 60.0
        col = COL_BG if t < 0.3 else COL_SUNSET if t < 0.7 else COL_SUN
        pyxel.line(0, y, SCREEN_W, y, col)

    sun_y = 45 + int(math.sin(frame * 0.015) * 2)
    pyxel.circ(SCREEN_W // 2, sun_y, 18, COL_SUN)
    pyxel.circ(SCREEN_W // 2, sun_y, 14, 10)
    for ry in range(3):
        rx = int(math.sin(frame * 0.03 + ry) * 8)
        pyxel.line(SCREEN_W // 2 - 15 + rx, 60 + ry * 3,
                   SCREEN_W // 2 + 15 + rx, 60 + ry * 3, COL_SUN)

    for y in range(55, 95):
        wave = int(math.sin(frame * 0.04 + y * 0.25) * 3)
        pyxel.line(0, y, SCREEN_W, y, COL_SEA)
        if (y + frame // 10) % 7 == 0:
            pyxel.line(wave + 20, y, wave + 40, y, COL_WHITE)

    for y in range(95, 160):
        col = COL_GRASS if (y % 5 < 3) else COL_LGRASS
        pyxel.line(0, y, SCREEN_W, y, col)

    for fx in range(10, SCREEN_W, 30):
        pyxel.rect(fx, 98, 2, 12, COL_DKGRAY)
        pyxel.line(fx, 102, fx + 28, 102, COL_DKGRAY)
        pyxel.line(fx, 107, fx + 28, 107, COL_DKGRAY)

    for gx in range(8, SCREEN_W, 15):
        gy = 115 + (gx * 11) % 40
        if gy < 155:
            sway = int(math.sin(frame * 0.025 + gx * 0.5) * 2)
            pyxel.line(gx, gy, gx + sway, gy - 6, COL_LGRASS)

    draw_horse(170, 115, None, frame)
    draw_ojii(70, 120, frame)
    draw_message_window(text, chars_shown)


NAME_CANDIDATES = [
    "ハーリー", "サンニヌ", "ティンダ", "ドゥナン",
    "ナンタ", "アガリ", "ドゥンタ", "自分で決める"
]

# --- ソフトウェアキーボード用文字セット ---
HIRAGANA_GRID = [
    ["あ", "い", "う", "え", "お"],
    ["か", "き", "く", "け", "こ"],
    ["さ", "し", "す", "せ", "そ"],
    ["た", "ち", "つ", "て", "と"],
    ["な", "に", "ぬ", "ね", "の"],
    ["は", "ひ", "ふ", "へ", "ほ"],
    ["ま", "み", "む", "め", "も"],
    ["や", "　", "ゆ", "　", "よ"],
    ["ら", "り", "る", "れ", "ろ"],
    ["わ", "　", "　", "　", "を"],
    ["ん", "っ", "ー", "゛", "゜"],
]

KATAKANA_GRID = [
    ["ア", "イ", "ウ", "エ", "オ"],
    ["カ", "キ", "ク", "ケ", "コ"],
    ["サ", "シ", "ス", "セ", "ソ"],
    ["タ", "チ", "ツ", "テ", "ト"],
    ["ナ", "ニ", "ヌ", "ネ", "ノ"],
    ["ハ", "ヒ", "フ", "+", "ホ"],
    ["マ", "ミ", "ム", "メ", "モ"],
    ["ヤ", "　", "ユ", "　", "ヨ"],
    ["ラ", "*", "ル", "レ", "ロ"],
    ["ワ", "　", "　", "　", "ヲ"],
    ["ン", "ッ", "ー", "゛", "゜"],
]

ALPHA_GRID = [
    ["A", "B", "C", "D", "E"],
    ["F", "G", "H", "I", "J"],
    ["K", "L", "M", "N", "O"],
    ["P", "Q", "R", "S", "T"],
    ["U", "V", "W", "X", "Y"],
    ["Z", "0", "1", "2", "3"],
    ["4", "5", "6", "7", "8"],
    ["9", "!", "?", ".", "-"],
    [" ", "(", ")", "/", "+"],
    ["*", "=", "@", "#", "$"],
    ["%", "&", "'", "\"", ":"],
]


def draw_naming_screen(frame, selected_index, text, chars_shown):
    pyxel.cls(COL_BG)

    for y in range(0, 50):
        pyxel.line(0, y, SCREEN_W, y, COL_BG)
    for y in range(50, 160):
        col = COL_GRASS if (y % 4 < 2) else COL_LGRASS
        pyxel.line(0, y, SCREEN_W, y, col)

    # Use default appearance for naming (no horse object yet)
    draw_horse(110, 65, None, frame)

    title = "名前をつけよう"
    tw = text_width(title)
    tx = (SCREEN_W - tw) // 2
    jp_text(tx + 1, 10, title, COL_BLACK)
    jp_text(tx, 9, title, COL_SUN)

    cols = 2
    rows = (len(NAME_CANDIDATES) + cols - 1) // cols
    box_w = 90
    box_h = 14
    start_x = (SCREEN_W - cols * box_w - 8) // 2
    start_y = 80

    for i, name in enumerate(NAME_CANDIDATES):
        col_idx = i % cols
        row_idx = i // cols
        bx = start_x + col_idx * (box_w + 8)
        by = start_y + row_idx * (box_h + 4)

        if i == selected_index:
            pyxel.rect(bx - 1, by - 1, box_w + 2, box_h + 2, COL_SUN)
            pyxel.rect(bx, by, box_w, box_h, COL_DKGRAY)
            tcol = COL_SUN
        else:
            pyxel.rect(bx, by, box_w, box_h, COL_BLACK)
            pyxel.rectb(bx, by, box_w, box_h, COL_GRAY)
            tcol = COL_WHITE

        nw = text_width(name)
        ntx = bx + (box_w - nw) // 2
        nty = by + (box_h - 8) // 2
        jp_text(ntx, nty, name, tcol)

    draw_ojii(20, 75, frame)

    hint = "↑↓←→:選択  ENTER:決定"
    hw = text_width(hint)
    hx = (SCREEN_W - hw) // 2
    jp_text(hx, 70, hint, COL_DKGRAY)

    draw_message_window(text, chars_shown)


def draw_manual_naming_screen(frame, input_text, cursor_row, cursor_col, input_mode, error_msg=""):
    """Screen for manual naming with software keyboard."""
    pyxel.cls(COL_BG)
    draw_background(frame)
    
    # プレビュー表示
    draw_window(4, 2, SCREEN_W - 8, 30, "現在の名前")
    jp_text(16, 12, input_text, COL_SUN)
    if frame % 30 < 15:
        cx = 16 + text_width(input_text)
        pyxel.line(cx, 12, cx, 20, COL_WHITE)

    # キーボードウィンドウ
    draw_window(4, 34, SCREEN_W - 8, GAME_H - 120, "文字選択")
    
    # 文字グリッド
    if input_mode == 0: grid = HIRAGANA_GRID
    elif input_mode == 1: grid = KATAKANA_GRID
    else: grid = ALPHA_GRID

    start_x = 10
    start_y = 62
    bw, bh = 18, 14
    
    # グリッド描画
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if char == "　": continue
            bx = start_x + r * (bw + 2) # 11列
            by = start_y + c * (bh + 2) # 5行
            
            is_cursor = (r == cursor_row and c == cursor_col)
            bg = COL_SUN if is_cursor else COL_BLACK
            tcol = COL_BLACK if is_cursor else COL_WHITE
            
            pyxel.rect(bx, by, bw, bh, bg)
            pyxel.rectb(bx, by, bw, bh, COL_DKGRAY)
            jp_text(bx + (bw - 8)//2, by + (bh - 8)//2, char, tcol)

    # アクションボタン（右サイドバー）
    side_items = ["かな", "カナ", "英数", "消す", "決定", "戻る"]
    for i, item in enumerate(side_items):
        bx = start_x + 11 * (bw + 2) + 4
        by = start_y + i * (bh + 2)
        
        is_cursor = (cursor_row == 11 and cursor_col == i)
        
        # モード選択中なら強調
        is_current_mode = (i == input_mode)
        
        bg = COL_SUN if is_cursor else (COL_DKGRAY if is_current_mode else COL_BLACK)
        tcol = COL_BLACK if is_cursor else COL_WHITE
        if not is_cursor and i == 5: tcol = COL_RED # 戻るは赤
        
        pyxel.rect(bx, by, bw + 14, bh, bg)
        pyxel.rectb(bx, by, bw + 14, bh, COL_GRAY)
        jp_text(bx + 2, by + 3, item, tcol)

    if error_msg:
        jp_text(130, SCREEN_H - 72, error_msg, COL_RED)

    # おじぃ (わ=9列0行 と を=9列4行 の間の空白セル(9,2)付近に配置)
    draw_ojii(194, 94, frame)
    
    hint = "↑↓←→:移動  Enter:入力/決定"
    jp_text(10, SCREEN_H - 10, hint, COL_DKGRAY)


def draw_vs_password_input_screen(frame, input_text, cursor_row, cursor_col, input_mode, error_msg="", title="対戦パス入力"):
    """Visual grid input for VS password (19 chars)."""
    pyxel.cls(COL_BG)
    draw_background(frame)
    
    # プレビュー表示
    draw_window(4, 2, SCREEN_W - 8, 30, f"{title} [{len(input_text)}/8]")
    
    # パスワードを1行で表示 (8文字 * 16px = 128px)
    px = (SCREEN_W - len(input_text)*16) // 2
    # 文字間を空けて表示 (高コントラストの白)
    jp_text(px, 12, " ".join(input_text), COL_WHITE)
    if frame % 30 < 15 and len(input_text) < 8:
        cx = px + len(input_text) * 16
        pyxel.line(cx, 12, cx, 20, COL_WHITE)

    # キーボードウィンドウ
    draw_window(4, 34, SCREEN_W - 8, GAME_H - 120, "ふっかつのじゅもん選択")
    
    # 文字グリッド (HIRAGANA/KATAKANAのみ)
    if input_mode == 0: grid = HIRAGANA_GRID
    else: grid = KATAKANA_GRID

    start_x = 10
    start_y = 62
    bw, bh = 18, 14
    
    # グリッド描画 (11x5)
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if char == "　": continue
            bx = start_x + r * (bw + 2)
            by = start_y + c * (bh + 2)
            
            is_cursor = (r == cursor_row and c == cursor_col)
            bg = COL_SUN if is_cursor else COL_BLACK
            tcol = COL_BLACK if is_cursor else COL_WHITE
            
            pyxel.rect(bx, by, bw, bh, bg)
            pyxel.rectb(bx, by, bw, bh, COL_DKGRAY)
            jp_text(bx + (bw - 8)//2, by + (bh - 8)//2, char, tcol)

    # アクションボタン
    side_items = ["かな", "カナ", "ー", "消す", "決定", "戻る"]
    for i, item in enumerate(side_items):
        bx = start_x + 11 * (bw + 2) + 4
        by = start_y + i * (bh + 2)
        
        is_cursor = (cursor_row == 11 and cursor_col == i)
        is_current_mode = (i == input_mode)
        
        bg = COL_SUN if is_cursor else (COL_DKGRAY if is_current_mode else COL_BLACK)
        tcol = COL_BLACK if is_cursor else COL_WHITE
        if not is_cursor and i == 5: tcol = COL_RED
        
        pyxel.rect(bx, by, bw + 14, bh, bg)
        pyxel.rectb(bx, by, bw + 14, bh, COL_GRAY)
        jp_text(bx + 2, by + 3, item, tcol)

    if error_msg:
        jp_text(130, GAME_H - 72, error_msg, COL_RED)

    draw_ojii(194, 94, frame)
    hint = "↑↓←→:移動  Enter:入力/決定"
    jp_text(10, GAME_H - 10, hint, COL_DKGRAY)


def draw_vs_ready_screen(frame, vs_horses, cursor):
    """Draw VS preparation screen showing registered horses."""
    _player_colors = {1: COL_SUN, 2: COL_RED, 3: 12, 4: COL_LGRASS}
    pyxel.cls(COL_BG)
    draw_background(frame)

    # タイトル
    draw_window(4, 2, SCREEN_W - 8, 20, "対戦準備")
    jp_text(16, 8, f"登録: {len(vs_horses)}頭 / 最大4頭", COL_WHITE)

    # 馬リスト
    draw_window(4, 26, SCREEN_W - 8, 100, "出走馬")
    sy = 38
    for i, h in enumerate(vs_horses):
        if not h: continue
        p_idx = i + 1
        col = _player_colors.get(p_idx, COL_WHITE)
        # getattrを用いて属性参照を安全に (NullPointer/AttributeError防止)
        name = getattr(h, 'name', '名無し')
        spd = getattr(h, 'speed', 0)
        sta = getattr(h, 'stamina', 0)
        gut = getattr(h, 'guts', 0)
        
        label = f"{p_idx}P: {name}"
        jp_text(12, sy, label, col)
        stats = f"SPD{spd} STA{sta} GUT{gut}"
        jp_text(130, sy, stats, COL_GRAY)
        sy += 16

    for i in range(len(vs_horses), 4):
        jp_text(12, sy, f"{i+1}P: ---", COL_DKGRAY)
        sy += 16

    # メニューボタン
    menu_y = 136
    items = []
    if len(vs_horses) < 4:
        items.append("次の馬を追加")
    items.append("出走！")
    items.append("戻る")

    draw_window(4, menu_y, SCREEN_W - 8, len(items) * 14 + 10, "アクション")
    for i, item in enumerate(items):
        iy = menu_y + 10 + i * 14
        if i == cursor:
            pyxel.tri(12, iy + 2, 12, iy + 8, 16, iy + 5, COL_SUN)
            jp_text(20, iy, item, COL_SUN)
        else:
            col = COL_RED if item == "戻る" else COL_WHITE
            jp_text(20, iy, item, col)

    draw_ojii(200, 50, frame)
    jp_text(4, GAME_H - 10, "↑↓:選択  Enter:決定", COL_DKGRAY)


def draw_tutorial_overlay(frame, tutorial_step, text, chars_shown):
    """Draw tutorial message over the main screen."""
    jp_text(4, GAME_H - 10, "↑↓:選択  Enter:決定", COL_DKGRAY)
    # BG_Hは 160 (GAME_H - 64) に調整
    draw_ojii(SCREEN_W - 24, GAME_H - 64, frame)
    draw_message_window(text, chars_shown)

# ====================================================================
#  レース画面
# ====================================================================

def draw_race_scene(frame, engine):
    """Draw the horizontal scrolling race scene."""
    pyxel.cls(COL_BG)

    # カメラ位置
    cam_x = int(engine.scroll_offset())

    # --- 背景（夕日の海と灯台） ---
    for y in range(0, 40):
        t = y / 40.0
        col = COL_BG if t < 0.2 else COL_SUNSET if t < 0.8 else COL_SUN
        pyxel.line(0, y, SCREEN_W, y, col)

    # オリジナル夕日
    sun_y = 25 + int(math.sin(frame * 0.02) * 2)
    pyxel.circ(SCREEN_W - 60 - (cam_x // 10 % SCREEN_W), sun_y, 12, COL_SUN)

    # 海
    for y in range(35, 60):
        wave = int(math.sin(frame * 0.05 + y * 0.3) * 2)
        pyxel.line(0, y, SCREEN_W, y, COL_SEA)
        if (y + (cam_x // 4)) % 8 == 0:
            pyxel.line(wave + 20, y, wave + 40, y, COL_WHITE)

    # 遠景の陸地（灯台）
    land_x = 200 - (cam_x // 6)
    pyxel.rect(land_x, 30, 40, 6, COL_DKGRAY)
    pyxel.rect(land_x + 15, 10, 8, 20, COL_WHITE)
    pyxel.rect(land_x + 14, 8, 10, 4, COL_SUNSET)

    # --- トラック ---
    for y in range(60, 160):
        col = COL_GRASS if (y + cam_x//2) % 10 < 5 else COL_LGRASS
        pyxel.line(0, y, SCREEN_W, y, col)

    # ハロン棒 / マーカー
    for mx in range(0, GOAL_DISTANCE + 500, 200):
        sc_x = mx - cam_x
        if -20 < sc_x < SCREEN_W + 20:
            pyxel.rect(sc_x, 60, 4, 100, COL_WHITE)
            pyxel.rect(sc_x, 60, 4, 20, COL_RED)
    # ゴールライン
    goal_x = GOAL_DISTANCE - cam_x
    if -50 < goal_x < SCREEN_W + 50:
        for gy in range(60, 160, 8):
            pyxel.rect(goal_x, gy, 8, 4, COL_WHITE)
            pyxel.rect(goal_x + 8, gy + 4, 8, 4, COL_WHITE)

    # --- プログレスバー（上部） ---
    bar_y = 4
    bar_w = SCREEN_W - 40
    bar_x = 20
    pyxel.line(bar_x, bar_y, bar_x + bar_w, bar_y, COL_WHITE)
    pyxel.rect(bar_x, bar_y - 2, 2, 5, COL_RED)
    pyxel.rect(bar_x + bar_w, bar_y - 2, 2, 5, COL_RED)

    # --- 馬の描画 ---
    # 奥から手前（lane_y順）に描画
    # プレイヤー毎の色 (1P=黄, 2P=赤, 3P=青, 4P=緑, CPU=灰)
    _player_colors = {1: COL_SUN, 2: COL_RED, 3: 12, 4: COL_LGRASS}

    sorted_horses = sorted(engine.horses, key=lambda h: h.lane_y)
    for rh in sorted_horses:
        hx = int(rh.x) - cam_x
        hy = 65 + rh.lane_y * 14

        if hx < -30 or hx > SCREEN_W + 30:
            pass
        else:
            draw_horse(hx, hy, rh.horse, frame)
            
            if rh.is_player and rh.player_index > 0:
                # プレイヤーマーカー (色分け + 番号)
                p_col = _player_colors.get(rh.player_index, COL_SUN)
                pyxel.tri(hx + 14, hy - 6, hx + 18, hy - 6, hx + 16, hy - 2, p_col)
                pyxel.text(hx + 12, hy - 12, f"{rh.player_index}P", p_col)

        # プログレスバー上のアイコン
        prog_x = bar_x + int((rh.x / GOAL_DISTANCE) * bar_w)
        if rh.player_index > 0:
            prog_col = _player_colors.get(rh.player_index, COL_SUN)
        else:
            prog_col = COL_DKGRAY
        pyxel.rect(prog_x - 1, bar_y - 2, 3, 5, prog_col)

    # --- 実況ウィンドウ ---
    draw_window(2, 162, SCREEN_W - 4, 60)
    jp_text(8, 166, "[ レース実況 ]", COL_SUNSET)
    
    ly = 178
    # 最新の5行のみ表示してはみ出しを防止（スクロール風）
    for text in engine.commentary[-5:]:
        jp_text(8, ly, text, COL_WHITE)
        ly += 8


def draw_race_result(engine):
    """Draw the race result overlay."""
    _player_colors = {1: COL_SUN, 2: COL_RED, 3: 12, 4: COL_LGRASS}
    win_w, win_h = 160, 110
    win_x = (SCREEN_W - win_w) // 2
    win_y = (GAME_H - win_h) // 2
    
    draw_window(win_x, win_y, win_w, win_h, "レース結果")
    
    sy = win_y + 16
    for rh in sorted(engine.results, key=lambda h: h.finish_order):
        # プレイヤーは色分け、CPUは白
        if rh.player_index > 0:
            col = _player_colors.get(rh.player_index, COL_SUN)
            prefix = f"[{rh.player_index}P] "
        else:
            col = COL_WHITE
            prefix = ""
        
        text = f"{rh.finish_order}着: {prefix}{rh.name}"
        jp_text(win_x + 10, sy, text, col)
        sy += 12
        if sy > win_y + win_h - 30:
            break
            
    if not engine.is_vs_mode:
        prize = engine.get_prize()
        if prize > 0:
            jp_text(win_x + 10, sy + 4, f"賞金 {prize}G 獲得！", COL_SUN)
        else:
            jp_text(win_x + 10, sy + 4, "賞金なし...", COL_GRAY)
    else:
        # VS Mode — winner is first in results
        winner = engine.results[0]
        if winner.player_index > 0:
            jp_text(win_x + 10, sy + 4, f"{winner.player_index}Pの勝利さぁ！", COL_SUN)
        else:
            jp_text(win_x + 10, sy + 4, "CPUの勝利...", COL_GRAY)
        
    jp_text(win_x + 10, win_y + win_h - 12, "Enterで進む", COL_DKGRAY)



# ====================================================================
#  カレンダー演出
# ====================================================================

def _draw_calendar_card(x, y, w, h, year, month, week, is_special, is_new_year):
    # Shadow
    pyxel.rect(x + 4, y + 4, w, h, COL_BLACK)
    
    bg_col = COL_WHITE
    b_col = COL_GRAY
    t_col = COL_BLACK
    rw_col = COL_RED
    
    if is_new_year:
        bg_col = COL_SUN
        b_col = COL_RED
        t_col = COL_BLACK
        rw_col = COL_WHITE
    elif is_special:
        bg_col = COL_SUN
        b_col = COL_SUNSET
        t_col = COL_BLACK
        rw_col = COL_RED
        
    pyxel.rect(x, y, w, h, bg_col)
    
    # Thick border
    pyxel.rectb(x, y, w, h, b_col)
    pyxel.rectb(x + 1, y + 1, w - 2, h - 2, b_col)
    pyxel.rectb(x + 3, y + 3, w - 6, h - 6, b_col)
    
    y_str = f"{year}年目"
    m_str = f"{month}月"
    w_str = f"第{week}週"
    
    # Card top bar like a real calendar
    pyxel.rect(x + 4, y + 4, w - 8, 12, COL_RED if not is_new_year else COL_WHITE)
    jp_text(x + w//2 - text_width(m_str)//2, y + 6, m_str, COL_WHITE if not is_new_year else COL_RED)
    
    jp_text(x + w//2 - text_width(y_str)//2, y + 25, y_str, t_col)
    jp_text(x + w//2 - text_width(w_str)//2, y + 40, w_str, rw_col if is_special else t_col)


def draw_calendar_proceed_screen(frame, game, anim_frame, old_y, old_m, old_w, new_y, new_m, new_w):
    is_new_month = (old_m != new_m)
    is_new_year = (old_y != new_y)
    is_special = is_new_month or is_new_year

    # Sync top right text
    date_str = f"{old_y}年 {old_m}月 {old_w}週" if anim_frame < 15 else f"{new_y}年 {new_m}月 {new_w}週"
    draw_main_screen(frame, game, "コマンド", [], 0, force_date_str=date_str)
    
    cw, ch = 100, 60
    if is_new_year:
        cw, ch = 120, 70
    elif is_new_month:
        cw, ch = 110, 64

    cx = (SCREEN_W - cw) // 2
    cy = (GAME_H - ch) // 2

    # Old card slides down and left slightly to simulate falling
    if anim_frame < 30:
        drop = (anim_frame / 30.0)**2
        old_cx = (SCREEN_W - 100) // 2 - int(drop * 20)
        old_cy = (SCREEN_H - 60) // 2 + int(drop * 150)
        _draw_calendar_card(old_cx, old_cy, 100, 60, old_y, old_m, old_w, False, False)

    # New card drops in
    if anim_frame >= 5:
        progress = min(1.0, (anim_frame - 5) / 15.0)
        t = progress - 1.0
        ease_out = t*t*t + 1.0
        
        new_cy = cy - 100 + int(ease_out * 100)
        _draw_calendar_card(cx, new_cy, cw, ch, new_y, new_m, new_w, is_special, is_new_year)
        
    # Particle effect for new year
    if is_new_year and anim_frame >= 15:
        for i in range(20):
            px = cx + cw//2 + int(math.sin(i * 7.1) * 60)
            py = cy + ch//2 + int(math.cos(i * 3.3) * 60) + (anim_frame-15)*3
            col = [COL_RED, COL_SUN, COL_WHITE, COL_LGRASS][i % 4]
            pyxel.rect(px, py, 2, 2, col)

    if anim_frame >= 35:
        # 視認性向上のための半透明バナー (全幅)
        hint_text = "Enterで進むさぁ"
        hw = text_width(hint_text)
        jx = (SCREEN_W - hw) // 2
        jy = 198
        
        # テキストの背景に全幅の黒い帯を敷く
        pyxel.rect(0, 195, SCREEN_W, 14, COL_BLACK)
        pyxel.rectb(0, 195, SCREEN_W, 14, COL_DKGRAY)
        
        jp_text(jx, jy, hint_text, COL_WHITE)
        if frame % 30 < 15:
            pyxel.tri(jx + hw + 4, jy + 2, jx + hw + 8, jy + 6, jx + hw + 12, jy + 2, COL_SUN)

# ====================================================================
#  パスワード画面 (Phase 6)
# ====================================================================

def draw_password_show_screen(frame, password, title="対戦用パスワード"):
    """Draw a screen showing the short VS horse password."""
    pyxel.cls(COL_BLACK)
    draw_background(frame)
    draw_window(30, 60, 196, 100, title)
    
    jp_text(40, 80, "以下のパスワードをメモして、", COL_WHITE)
    jp_text(40, 92, "友達と対戦しよう！", COL_WHITE)
    
    # 中央寄せ表示 (8文字 * 16px = 128px)
    # 文字の間隔を広げ、高コントラストの白で表示
    spaced_pass = " ".join(password)
    px = 30 + (196 - 128) // 2
    jp_text(px, 115, spaced_pass, COL_WHITE)
    # 少し影をつけて袋文字風に
    jp_text(px + 1, 115, spaced_pass, COL_WHITE) 
    
    jp_text(30, 172, "[Enter] で戻る", COL_GRAY)

def draw_slot_select_screen(frame, title, slot_infos, cursor_idx):
    """Draw a screen for selecting a save/load slot."""
    pyxel.cls(COL_BLACK)
    draw_background(frame)
    draw_window(30, 40, 196, 120, title)
    
    for i in range(3):
        y = 60 + i * 25
        color = COL_SUN if i == cursor_idx else COL_WHITE
        slot_text = slot_infos[i] if slot_infos[i] else "--- なし ---"
        if i == cursor_idx:
            pyxel.tri(40, y+2, 40, y+6, 44, y+4, COL_SUN)
        jp_text(50, y, f"Slot {i}: {slot_text}", color)
        
    # 戻るボタン
    y = 60 + 3 * 25
    color = COL_SUN if cursor_idx == 3 else COL_WHITE
    if cursor_idx == 3:
        pyxel.tri(40, y+2, 40, y+6, 44, y+4, COL_SUN)
    jp_text(50, y, "やめる / 戻る", color)

    jp_text(30, 170, "↑↓: 選択 ENTER: 決定", COL_GRAY)

def draw_password_input_screen(frame, input_text, error_msg="", title="パスワード入力"):
    """Draw a screen for inputting a short password."""
    pyxel.cls(COL_BLACK)
    draw_background(frame)
    draw_window(10, 40, SCREEN_W - 20, 130, title)
    jp_text(16, 56, "パスワードを入力してください。", COL_WHITE)
    
    # 入力文字表示 (中央寄せ)
    px = 10 + (SCREEN_W - 20 - 152) // 2
    y = 90
    jp_text(px, y, input_text, COL_SUN)
    
    if frame % 30 < 15: # カーソル点滅
        cx = px + len(input_text) * 8
        pyxel.rect(cx, y, 6, 8, COL_GRAY)
        
    if error_msg:
        jp_text(16, 140, error_msg, COL_RED)
    
    jp_text(16, 172, "キーボード入力  [Enter]決定 [Esc]戻る", COL_GRAY)

# ====================================================================
#  クリア報酬画面 (Phase 7)
# ====================================================================

def draw_reward_screen(frame, chars_shown, code):
    pyxel.cls(COL_BLACK)
    
    # Sunset background
    for y in range(0, SCREEN_H):
        col = COL_BG if y < 40 else COL_SUNSET if y < 100 else COL_BLACK
        pyxel.line(0, y, SCREEN_W, y, col)
        
    draw_horse(100, 80, None, frame)
    
    win_h = 52
    win_y = SCREEN_H - win_h - 4
    draw_window(4, win_y, SCREEN_W - 8, win_h, "おじぃ")

    text = "島のためによう頑張って\nくれたさぁ！\nこのコードを使うといいさぁ！"
    display_text = text[:chars_shown]
    lines = display_text.split('\n')
    for i, line in enumerate(lines):
        jp_text(16, win_y + 16 + i * 10, line, COL_WHITE)
        
    if chars_shown >= len(text):
        jp_text(16, win_y - 20, "特産品コード:", COL_SUN)
        pyxel.text(16, win_y - 10, code, COL_WHITE)
        jp_text(SCREEN_W - 60, win_y + win_h - 12, "Enterで進む", COL_DKGRAY)

def draw_virtual_controller():
    """ゲーム画面と完全に分離した暗闇エリア(y >= 224)にコントローラーを描画。"""
    con_y = GAME_H
    # 専用の暗闇エリア
    pyxel.rect(0, con_y, SCREEN_W, PAD_H, COL_BLACK)
    # 物理的分離線
    pyxel.line(0, con_y, SCREEN_W, con_y, COL_DKGRAY)

    # 十字キー (左側) - 暗闇エリアの中央付近(y=256)に配置
    # 上(25, 230), 下(25, 260), 左(10, 245), 右(40, 245)
    base_cy = con_y + 32
    pyxel.rectb(24, base_cy - 20, 12, 12, COL_GRAY) # U
    pyxel.rectb(24, base_cy + 8, 12, 12, COL_GRAY) # D
    pyxel.rectb(8, base_cy - 6, 12, 12, COL_GRAY)  # L
    pyxel.rectb(40, base_cy - 6, 12, 12, COL_GRAY) # R
    
    jp_text(26, base_cy - 18, "^", COL_WHITE)
    jp_text(26, base_cy + 10, "v", COL_WHITE)
    jp_text(10, base_cy - 4, "<", COL_WHITE)
    jp_text(42, base_cy - 4, ">", COL_WHITE)

    # A/B ボタン (右側)
    # B(195, base_cy), A(235, base_cy)
    pyxel.circb(195, base_cy, 12, COL_RED) # B
    pyxel.circb(235, base_cy, 12, COL_SUN) # A
    jp_text(192, base_cy - 4, "B", COL_WHITE)
    jp_text(232, base_cy - 4, "A", COL_WHITE)

    # 操作ガイド（中央）
    jp_text(85, base_cy - 4, "DUNAN PAD", COL_DKGRAY)
