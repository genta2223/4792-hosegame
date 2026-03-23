import pyxel

SE_CURSOR = 0
SE_CONFIRM = 1
SE_CANCEL = 2
SE_TRAIN = 3
SE_HOOF = 4
SE_WIN = 5
SE_LOSE = 6

BGM_RANCH = 0
BGM_RACE = 1
BGM_TITLE = 2

def init_audio():
    """Define 8-bit sound effects and BGM inside Pyxel."""
    # --- Sound Effects ---
    # Cursor Move
    pyxel.sounds[SE_CURSOR].set("a3a2", "p", "7", "s", 5)
    # Confirm
    pyxel.sounds[SE_CONFIRM].set("c3e3g3", "p", "6", "f", 10)
    # Cancel / Error
    pyxel.sounds[SE_CANCEL].set("c2c2", "n", "7", "f", 15)
    # Cultivate (Dig)
    pyxel.sounds[SE_TRAIN].set("c1c0", "n", "6", "f", 10)
    # Race Hoofbeats
    pyxel.sounds[SE_HOOF].set("c2r c2c2 r c2", "n", "5", "f", 6)
    # Win Fanfare — 琉球音階の栄光のファンファーレ (C/E/F/G/B only)
    pyxel.sounds[SE_WIN].set(
        "c3 e3 f3 g3 b3 c4 r c4 b3 c4 e4 c4 g3 b3 c4 c4",
        "p", "7776665544", "n", 8
    )
    # Lose — 寂しげだが希望を感じる短いフレーズ (C/E/F/G/B only)
    pyxel.sounds[SE_LOSE].set(
        "g3 f3 e3 c3 r e3 c3 r c3 e3",
        "p", "6655443344", "n", 15
    )

    # --- BGM 0: Ranch (Dunan Sunkani Motif) ---
    # Ryukyu pentatonic: C E F G B only (no D, no A)
    melody1 = "c3 e3 f3 g3 b3 g3 f3 e3 c3 c3 r r"
    pyxel.sounds[10].set(melody1 * 4, "p", "6", "n", 15)
    bass1 = "c2 r c2 g1 r g1 c2 r c2 g1 r g1"
    pyxel.sounds[11].set(bass1 * 4, "t", "5", "n", 15)
    pyxel.musics[BGM_RANCH].set([10], [11], [], [])

    # --- BGM 1: Race (三線ロック — アップテンポ琉球音階) ---
    # Ryukyu pentatonic only: C E F G B — no D, no A
    # Driving, energetic sanshin-rock feel for the final stretch
    race_melody = (
        "g3 g3 b3 c4 "   # 力強い入り
        "b3 g3 f3 e3 "   # 下行フレーズ
        "f3 g3 b3 c4 "   # 再び上昇
        "b3 g3 e3 c3 "   # 解決
        "c4 b3 g3 f3 "   # 高音域の呼びかけ
        "e3 f3 g3 b3 "   # 駆け上がり
        "c4 c4 b3 g3 "   # 繰り返しの頂点
        "f3 e3 c3 r "    # 休符で息継ぎ
    )
    pyxel.sounds[20].set(race_melody * 2, "p", "76765454", "n", 8)

    race_bass = (
        "c2 c2 g2 c2 "
        "c2 c2 g2 c2 "
        "f1 f1 c2 f1 "
        "g1 g1 c2 g1 "
        "c2 c2 g2 c2 "
        "c2 c2 g2 c2 "
        "f1 f1 c2 f1 "
        "g1 g1 c2 g1 "
    )
    pyxel.sounds[21].set(race_bass * 2, "t", "5", "n", 8)

    # Percussion (noise channel for drive)
    race_perc = (
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
        "c2 r c2 c2 "
    )
    pyxel.sounds[22].set(race_perc * 2, "n", "43", "f", 8)
    pyxel.musics[BGM_RACE].set([20], [21], [22], [])

    # --- BGM 2: Title (魂の三線 — 琉球音階ゆったり) ---
    # Ryukyu pentatonic only: C E F G B — no D, no A
    # Slow, soulful sanshin melody evoking Yonaguni sunset
    title_melody = (
        "c3 r e3 r "     # 静かな始まり
        "f3 r g3 r "     # 穏やかな上昇
        "b3 r g3 r "     # シの余韻
        "f3 r e3 r "     # ゆるやかな下行
        "c3 r r r "       # 間を取る
        "e3 f3 g3 r "    # 少し動きをつけて
        "b3 r g3 f3 "    # 高音から降りてくる
        "e3 r c3 r "     # 落ち着きの解決
        "g3 r b3 r "     # 再び上昇
        "c4 r b3 r "     # 頂点
        "g3 r f3 r "     # 夕暮れの下降
        "e3 r c3 r "     # 静寂へ
    )
    # Pulse wave with sharp attack for sanshin pluck feel
    # Volume pattern: sharp attack then decay (7→5→3→2)
    pyxel.sounds[30].set(title_melody * 2, "p", "75327532", "n", 20)

    title_bass = (
        "c2 r r r "
        "c2 r r r "
        "g1 r r r "
        "c2 r r r "
        "c2 r r r "
        "f1 r r r "
        "g1 r r r "
        "c2 r r r "
        "g1 r r r "
        "c2 r r r "
        "g1 r r r "
        "c2 r r r "
    )
    pyxel.sounds[31].set(title_bass * 2, "p", "5321", "n", 20)

    pyxel.musics[BGM_TITLE].set([30], [31], [], [])

def play_se(idx):
    if 0 <= idx <= 6:
        pyxel.play(3, idx)

def play_bgm(idx):
    pyxel.playm(idx, loop=True)

def stop_bgm():
    pyxel.stop()
