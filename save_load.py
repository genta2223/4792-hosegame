import json
import zlib
import base64
import os
from calendar_system import Calendar
from horse import Horse
from ranch import Ranch

def _encode_base64_safe(data: bytes) -> str:
    # URL safe base64 without padding '='
    b64 = base64.urlsafe_b64encode(data).decode('ascii')
    return b64.rstrip('=')

def _decode_base64_safe(b64_str: str) -> bytes:
    # Add padding back
    b64_str += '=' * ((4 - len(b64_str) % 4) % 4)
    return base64.urlsafe_b64decode(b64_str)

def _serialize_horse(h: Horse) -> dict:
    if not h: return None
    return {
        "na": h.name, "ag": h.age, "ge": h.gender, "sp": h.speed,
        "st": h.stamina, "gu": h.guts, "lu": h.luck, "te": h.temper,
        "wt": h.weight, "bw": h.best_weight, "fa": h.fatigue,
        "co": h.contribution, "rt": h.retired, "ip": h.in_paddock,
        "ap": h.appearance,
        "pm": h.prize_money, "tr": h.target_race, "tw": h.target_weeks_left,
        "sr": h.sire, "dm": h.dam, "g1w": h.g1_wins
    }

def _deserialize_horse(d: dict) -> Horse:
    h = Horse()
    if d is None: return None
    h.name = d["na"]; h.age = d["ag"]; h.gender = d["ge"]
    h.speed = d["sp"]; h.stamina = d["st"]; h.guts = d["gu"]
    h.luck = d["lu"]; h.temper = d["te"]; h.weight = d["wt"]
    h.best_weight = d["bw"]; h.fatigue = d["fa"]
    h.contribution = d["co"]; h.retired = d["rt"]
    h.in_paddock = d["ip"]; h.prize_money = d["pm"]
    h.appearance = d.get("ap", {"base_color": 4, "face_marking": 0, "mane_tail_color": 0, "leg_marking": 0})
    h.target_race = d.get("tr"); h.target_weeks_left = d.get("tw", 0)
    h.sire = d.get("sr", "不明"); h.dam = d.get("dm", "不明")
    h.g1_wins = d.get("g1w", 0)
    return h

def generate_password(ranch: Ranch, calendar: Calendar) -> str:
    """Generate a compressed base64 password string from game state."""
    state = {
        "y": calendar.year, "m": calendar.month, "w": calendar.week,
        "bal": ranch.balance,
        "hs": [_serialize_horse(h) for h in ranch.horses],
        "pd": [_serialize_horse(h) for h in ranch.paddock],
        "st": [_serialize_horse(h) for h in ranch.stallions],
        "br": [_serialize_horse(h) for h in ranch.broodmares],
        "rc": ranch.reward_code
    }
    raw_json = json.dumps(state, ensure_ascii=False)
    compressed = zlib.compress(raw_json.encode('utf-8'))
    return _encode_base64_safe(compressed)

def load_from_password(pwd: str) -> tuple[Ranch, Calendar]:
    """Parse a password string and return updated Ranch and Calendar objects.
    Returns None, None if the password is invalid.
    """
    try:
        compressed = _decode_base64_safe(pwd)
        raw_json = zlib.decompress(compressed).decode('utf-8')
        state = json.loads(raw_json)
        
        cal = Calendar(state["y"], state["m"], state["w"])
        r = Ranch()
        r.balance = state["bal"]
        
        r.horses = [_deserialize_horse(hd) for hd in state["hs"]]
        r.paddock = [_deserialize_horse(hd) for hd in state["pd"]]
        r.stallions = [_deserialize_horse(hd) for hd in state["st"]]
        r.broodmares = [_deserialize_horse(hd) for hd in state["br"]]
        r.reward_code = state.get("rc", "")
        
        return True, (r, cal)
    except Exception:
        return False, "無効なパスワードです"

def get_slot_filename(slot_idx):
    return f"save_slot_{slot_idx}.json"

def save_to_slot(slot_idx, ranch, calendar):
    """Save full game state to a JSON file."""
    state = {
        "y": calendar.year, "m": calendar.month, "w": calendar.week,
        "bal": ranch.balance,
        "hs": [_serialize_horse(h) for h in ranch.horses],
        "pd": [_serialize_horse(h) for h in ranch.paddock],
        "st": [_serialize_horse(h) for h in ranch.stallions],
        "br": [_serialize_horse(h) for h in ranch.broodmares],
        "rc": ranch.reward_code
    }
    with open(get_slot_filename(slot_idx), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def load_from_slot(slot_idx):
    """Load full game state from a JSON file."""
    fname = get_slot_filename(slot_idx)
    if not os.path.exists(fname):
        return False, "ファイルが見つかりません"
    try:
        with open(fname, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        cal = Calendar(state["y"], state["m"], state["w"])
        r = Ranch()
        r.balance = state["bal"]
        r.horses = [_deserialize_horse(hd) for hd in state["hs"]]
        r.paddock = [_deserialize_horse(hd) for hd in state["pd"]]
        r.stallions = [_deserialize_horse(hd) for hd in state["st"]]
        r.broodmares = [_deserialize_horse(hd) for hd in state["br"]]
        r.reward_code = state.get("rc", "")
        return True, (r, cal)
    except Exception as e:
        return False, f"読込失敗: {str(e)}"

def get_slot_info(slot_idx):
    """Get summary info for a save slot."""
    fname = get_slot_filename(slot_idx)
    if not os.path.exists(fname):
        return None
    try:
        with open(fname, "r", encoding="utf-8") as f:
            state = json.load(f)
        main_horse = state["hs"][0]["na"] if state["hs"] else "なし"
        return f"{state['y']}年{state['m']}月{state['w']}週 - {main_horse}"
    except:
        return "データ破損"

# --- カスタム文字テーブル (256文字) ---
NAME_CHAR_TABLE = (
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんっー゛゜" # 53
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"   # 47
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" # 52
    "0123456789!?.- ()/ +*=@#$%&'\":%" # 32 (symbols)
    "　がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ" # 25
    "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ" # 25
    "ヴァヴィヴヴェヴォ" # 5
    "                                   " # padding to 256
) # 総計256文字 (実際には重複回避しつつ定義)

# Base-50 アルファベット (ひらがなのみで完結させるため)
VS_ALPHABET = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんっー゛゜"

# VS名用 64文字テーブル (18bit = 64^3)
VS_NAME_TABLE = (
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんっー" # 53
    "アイウエオカキク" # 8
    "　！？" # 3 (total 64)
)

HIRA_50 = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんっー゛゜"
KATA_50 = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフ+ホマミムメモヤユヨラ*ルレロワヲンッー゛゜"

def generate_vs_password(horse: Horse) -> str:
    """Generate an alternating 8-char VS password (45-bit)."""
    val = 0
    name_3 = horse.name[:3].ljust(3, "　")
    for char in name_3:
        idx = VS_NAME_TABLE.find(char)
        if idx == -1: idx = VS_NAME_TABLE.find("　")
        val = (val << 6) | (idx & 0x3F)
    
    stats = [horse.speed, horse.stamina, horse.guts, horse.wisdom, horse.luck, horse.temper]
    for s in stats:
        val = (val << 3) | ((s // 32) & 0x07)
        
    val = (val << 2) | ((horse.age - 2) & 0x03)
    val = (val << 1) | (1 if horse.gender == "牡" else 0)
    
    ap = horse.appearance
    val = (val << 2) | (ap.get("base_color", 4) & 0x03)
    val = (val << 1) | (ap.get("face_marking", 0) & 0x01)
    val = (val << 1) | (ap.get("leg_marking", 0) & 0x01)
    val = (val << 1) | (ap.get("mane_tail_color", 0) & 0x01)
    
    del ap
    chk = 0
    temp_val = val
    while temp_val > 0:
        chk ^= (temp_val & 0x01)
        temp_val >>= 1
    val = (val << 1) | (chk & 0x01)
    
    res = ""
    for i in range(8):
        rem = val % 50
        val //= 50
        idx_in_res = 7 - i
        res += HIRA_50[rem] if idx_in_res % 2 == 0 else KATA_50[rem]
    return res[::-1]

def load_horse_from_vs_password(pwd: str) -> Horse:
    """Extract horse data from an 8-char alternating VS password."""
    if len(pwd) != 8: return None
    try:
        val = 0
        for i, char in enumerate(pwd):
            idx = HIRA_50.find(char) if i % 2 == 0 else KATA_50.find(char)
            if idx == -1: return None
            val = val * 50 + idx
            
        chk = val & 0x01
        data_val = val >> 1
        calc_chk = 0
        temp_val = data_val
        while temp_val > 0:
            calc_chk ^= (temp_val & 0x01)
            temp_val >>= 1
        if chk != calc_chk: return None
        
        h = Horse()
        mane = data_val & 0x01; data_val >>= 1
        leg = data_val & 0x01; data_val >>= 1
        face = data_val & 0x01; data_val >>= 1
        color = data_val & 0x03; data_val >>= 2
        h.appearance = {"base_color": color, "face_marking": face, "leg_marking": leg, "mane_tail_color": mane}
        
        gender = data_val & 0x01; data_val >>= 1
        h.gender = "牡" if gender else "牝"
        h.age = (data_val & 0x03) + 2; data_val >>= 2
        
        h.temper = (data_val & 0x07) * 32 + 16; data_val >>= 3
        h.luck = (data_val & 0x07) * 32 + 16; data_val >>= 3
        h.wisdom = (data_val & 0x07) * 32 + 16; data_val >>= 3
        h.guts = (data_val & 0x07) * 32 + 16; data_val >>= 3
        h.stamina = (data_val & 0x07) * 32 + 16; data_val >>= 3
        h.speed = (data_val & 0x07) * 32 + 16; data_val >>= 3
        
        name = ""
        for _ in range(3):
            idx = data_val & 0x3F
            name = VS_NAME_TABLE[idx] + name
            data_val >>= 6
        h.name = name.strip("　")
        
        return h
    except:
        return None

def load_vs_horse_export():
    """Try to load VS horse data from vs_horse.txt."""
    if os.path.exists("vs_horse.txt"):
        try:
            with open("vs_horse.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return None
    return None
