"""Calendar / time progression system for どぅなん・ダッシュ！"""


class Calendar:
    """12 months × 4 weeks = 48 weeks per year."""

    # 月名
    MONTH_NAMES = [
        "1月", "2月", "3月", "4月", "5月", "6月",
        "7月", "8月", "9月", "10月", "11月", "12月",
    ]

    # 月別イベント (1-indexed month -> event name)
    EVENTS = {
        1: "セリ（競り市）",       # January: Auction
        3: "種付けシーズン",       # March: Breeding
        8: "豊年祭カップ",         # August: Hounen-sai Festival Cup
    }

    # レース定義 (month, week) -> [{name, req_prize, prize}]
    # 1週: ハナハナ級 (300G〜) と 未勝利 (0G)
    # 2〜3週: どぅなん級 (1000G〜) と 未勝利 (0G)
    # 4週: サンセットG1 (5000G〜) または特例重賞
    RACES = {}
    
    # 基本の定期レースを自動登録
    for m in range(1, 13):
        RACES[(m, 1)] = [{"name": "未勝利戦", "req_prize": 0, "prize": 300}, 
                         {"name": "ハナハナ賞", "req_prize": 300, "prize": 500}]
        RACES[(m, 2)] = [{"name": "未勝利戦", "req_prize": 0, "prize": 300},
                         {"name": "どぅなん特別", "req_prize": 1000, "prize": 1200}]
        RACES[(m, 3)] = [{"name": "どぅなん特別", "req_prize": 1000, "prize": 1200}]
        RACES[(m, 4)] = [{"name": "サンセット戦", "req_prize": 5000, "prize": 5000}]

    # 特殊重賞の上書き
    RACES[(8, 4)] = [{"name": "豊年祭カップ(G2)", "req_prize": 3000, "prize": 4000}]
    RACES[(12, 4)] = [{"name": "最西端サンセット記念", "req_prize": 5000, "prize": 10000}]


    def __init__(self, year=1, month=1, week=1):
        self.year = year
        self.month = month   # 1-12
        self.week = week     # 1-4

    def advance_week(self):
        """Advance by one week. Returns list of triggered events."""
        events = []
        self.week += 1
        if self.week > 4:
            self.week = 1
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1
                events.append("__NEW_YEAR__")
            # 月初イベント判定
            ev = self.EVENTS.get(self.month)
            if ev:
                events.append(ev)
        return events

    def get_current_event(self):
        """Return current month's event if week 1, else None."""
        if self.week == 1:
            return self.EVENTS.get(self.month)
        return None

    def get_races(self):
        """Return list of races for the current week."""
        return self.RACES.get((self.month, self.week), [])

    def get_upcoming_races(self, weeks=12):
        """Return races for the next `weeks` weeks. (list of dict with + offset info)"""
        upcoming = []
        m, w = self.month, self.week
        for offset in range(weeks):
            races = self.RACES.get((m, w), [])
            for r in races:
                rc = r.copy()
                rc["month"] = m
                rc["week"] = w
                rc["offset"] = offset
                upcoming.append(rc)
            w += 1
            if w > 4:
                w = 1
                m += 1
                if m > 12: m = 1
        return upcoming

    @property
    def month_name(self):
        return self.MONTH_NAMES[self.month - 1]

    def display(self):
        return f"{self.year}年目 {self.month_name} 第{self.week}週"

    def total_weeks(self):
        return (self.year - 1) * 48 + (self.month - 1) * 4 + self.week

    def __repr__(self):
        return f"Calendar({self.display()})"
