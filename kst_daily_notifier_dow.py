
# -*- coding: utf-8 -*-
"""
KST Daily Notifier (요일 지정 기능 추가 버전)
- 매일이 아니라, 사용자가 체크한 요일(월~일)에만 지정한 시간에 팝업 알림을 띄웁니다.
- 기존 기능(팝업 확인 시 닫히고, 삭제 전까지 반복/확인 주기/5분+주기 보정/로컬 JSON 저장)은 그대로 유지합니다.
"""
import json
import os
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "schedules.json"
DEFAULT_INTERVAL_SEC = 30
KST_TZNAME = "Asia/Seoul"
# Python weekday(): Monday=0 ... Sunday=6
KOR_WD = ["월", "화", "수", "목", "금", "토", "일"]


@dataclass
class Schedule:
    title: str                 # 일정 제목
    time_str: str              # "HH:MM" 또는 "HH:MM:SS"
    days: list = field(default_factory=lambda: [0,1,2,3,4,5,6])  # 알림 요일(기본: 매일)
    active: bool = True
    last_fired_date: str = ""  # "YYYY-MM-DD" (KST 기준 마지막 팝업 확인 날짜 저장)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        # days가 없는 기존 데이터도 호환 (기본: 매일)
        days = d.get("days", [0,1,2,3,4,5,6])
        return Schedule(
            title=d["title"],
            time_str=d["time_str"],
            days=days,
            active=d.get("active", True),
            last_fired_date=d.get("last_fired_date", ""),
        )


class NotifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KST Daily Notifier (요일/시간 알림)")
        self.root.geometry("900x620")

        # KST Timezone
        if ZoneInfo is None:
            messagebox.showwarning(
                "경고",
                "이 파이썬에는 zoneinfo 모듈이 없습니다 (Python 3.9+ 권장). "
                "KST 계산이 OS 로캘에 의존할 수 있습니다."
            )
            self.tz = None
        else:
            self.tz = ZoneInfo(KST_TZNAME)

        # State
        self.schedules = self.load_schedules()
        self.interval_sec = DEFAULT_INTERVAL_SEC
        self.stop_event = threading.Event()
        self.thread = None

        # UI
        self.build_ui()

        # 백그라운드 알림 스레드 시작
        self.start_thread()

    # ---------- Persistence ----------
    def load_schedules(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Schedule.from_dict(x) for x in data.get("schedules", [])]
        except Exception:
            return []

    def save_schedules(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"schedules": [s.to_dict() for s in self.schedules]}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("저장 오류", f"일정 저장 중 오류가 발생했습니다:\n{e}")

    # ---------- UI ----------
    def build_ui(self):
        # 상단 입력 프레임
        frm_top = ttk.Frame(self.root, padding=10)
        frm_top.pack(fill="x")

        ttk.Label(frm_top, text="일정 제목").grid(row=0, column=0, sticky="w")
        self.title_var = tk.StringVar()
        ttk.Entry(frm_top, textvariable=self.title_var, width=30).grid(row=0, column=1, padx=6)

        ttk.Label(frm_top, text="알림 시간 (HH:MM 또는 HH:MM:SS)").grid(row=0, column=2, sticky="w")
        self.time_var = tk.StringVar()
        ttk.Entry(frm_top, textvariable=self.time_var, width=18).grid(row=0, column=3, padx=6)

        ttk.Button(frm_top, text="추가", command=self.add_schedule).grid(row=0, column=4, padx=6)

        # 요일 체크박스
        frm_days = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frm_days.pack(fill="x")
        ttk.Label(frm_days, text="알림 요일").pack(side="left", padx=(0, 10))

        self.day_vars = []
        for i, name in enumerate(KOR_WD):
            var = tk.BooleanVar(value=True)  # 기본 모두 체크(매일)
            chk = ttk.Checkbutton(frm_days, text=name, variable=var)
            chk.pack(side="left", padx=(0, 6))
            self.day_vars.append(var)

        # 중간 리스트 프레임
        frm_mid = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frm_mid.pack(fill="both", expand=True)

        columns = ("title", "days", "time", "active", "last")
        self.tree = ttk.Treeview(frm_mid, columns=columns, show="headings", height=10)
        self.tree.heading("title", text="제목")
        self.tree.heading("days", text="요일")
        self.tree.heading("time", text="알림 지정시간")
        self.tree.heading("active", text="토글 사용")
        self.tree.heading("last", text="마지막 확인(KST)")

        self.tree.column("title", width=240)
        self.tree.column("days", width=120, anchor="center")
        self.tree.column("time", width=120, anchor="center")
        self.tree.column("active", width=80, anchor="center")
        self.tree.column("last", width=160, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frm_mid, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.refresh_tree()

        # 하단 제어 프레임
        frm_bot = ttk.Frame(self.root, padding=10)
        frm_bot.pack(fill="x")

        ttk.Button(frm_bot, text="삭제 (선택)", command=self.delete_selected).pack(side="left")
        ttk.Button(frm_bot, text="토글 활성/비활성 (선택)", command=self.toggle_selected).pack(side="left", padx=6)

        ttk.Label(frm_bot, text="확인 주기(초)").pack(side="left", padx=(20, 4))
        self.interval_var = tk.IntVar(value=self.interval_sec)
        sp = ttk.Spinbox(frm_bot, from_=5, to=600, textvariable=self.interval_var, width=8, command=self.update_interval)
        sp.pack(side="left")
        ttk.Button(frm_bot, text="주기 적용", command=self.update_interval).pack(side="left", padx=6)

        hint = (
            "주의: 팝업은 [설정한 알림시간 - (5분 + 주기)]에 시작합니다.\n"
            "예) 09:00, 주기 30초 → 08:54:30~08:55:00 팝업 표시\n"
            "시간 확인 주기(초)를 너무 짧게 설정하면, 프로그램 CPU 사용량이 증가할 수 있습니다."
        )
        ttk.Label(self.root, text=hint, foreground="#555").pack(anchor="w", padx=12, pady=(0, 8))

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, s in enumerate(self.schedules):
            days_str = ",".join(KOR_WD[d] for d in sorted(s.days))
            self.tree.insert("", "end", iid=str(idx),
                             values=(s.title, days_str, s.time_str, "예" if s.active else "아니오", s.last_fired_date or "-"))

    def add_schedule(self):
        title = self.title_var.get().strip()
        tstr = self.time_var.get().strip()
        if not title or not tstr:
            messagebox.showwarning("입력 필요", "제목과 시간을 모두 입력해 주세요.")
            return
        if not self._validate_time(tstr):
            messagebox.showerror("형식 오류", "시간 형식은 HH:MM 또는 HH:MM:SS 입니다.")
            return
        selected_days = [i for i, v in enumerate(self.day_vars) if v.get()]
        if not selected_days:
            messagebox.showerror("요일 선택", "알림 받을 요일을 최소 1개 이상 선택해 주세요.")
            return

        self.schedules.append(Schedule(title=title, time_str=tstr, days=selected_days))
        self.save_schedules()
        self.refresh_tree()
        self.title_var.set("")
        self.time_var.set("")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("선택 필요", "삭제할 일정을 선택해 주세요.")
            return
        idx = int(sel[0])
        del self.schedules[idx]
        self.save_schedules()
        self.refresh_tree()

    def toggle_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("선택 필요", "토글할 일정을 선택해 주세요.")
            return
        idx = int(sel[0])
        self.schedules[idx].active = not self.schedules[idx].active
        self.save_schedules()
        self.refresh_tree()

    def update_interval(self):
        try:
            val = int(self.interval_var.get())
            if val < 5 or val > 600:
                raise ValueError
            self.interval_sec = val
        except Exception:
            messagebox.showerror("입력 오류", "확인 주기는 5초~600초 사이의 정수로 입력해 주세요.")
            self.interval_var.set(self.interval_sec)

    # ---------- Thread / Alert ----------
    def start_thread(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop_thread(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _run_loop(self):
        while not self.stop_event.is_set():
            try:
                self._check_and_alert()
            except Exception as e:
                # 안전하게 계속 동작
                print("알림 루프 오류:", e)
            # 확인 주기만큼 대기
            time.sleep(self.interval_sec)

    def _check_and_alert(self):
        # 현재 시각 (KST)
        now = self._now_kst()
        today_str = now.strftime("%Y-%m-%d")
        today_wd = now.weekday()  # 0=Mon ... 6=Sun

        for s in self.schedules:
            if not s.active:
                continue
            # 오늘 요일에 해당하지 않으면 건너뛰기
            if today_wd not in s.days:
                continue
            # 오늘 이미 알림 처리했는지 확인
            if s.last_fired_date == today_str:
                continue

            # 원래 알림 목표 시간 (오늘 KST 기준)
            target_dt = self._combine_today_time(now, s.time_str)

            # 보정: 5분 + 확인주기 초 앞당겨 알림
            lead = timedelta(minutes=5, seconds=self.interval_sec)
            alert_dt = target_dt - lead

            # 만약 alert_dt가 현재보다 과거이고 target_dt는 아직 지나지 않은 경우,
            # 지금 팝업을 띄워보자.
            if alert_dt <= now < target_dt:
                self._show_alert(s, target_dt)  # 팝업 표시
                # 사용자가 확인을 누른 뒤 날짜 갱신
                s.last_fired_date = today_str
                self.save_schedules()
                self.refresh_tree()

    def _show_alert(self, schedule: Schedule, target_dt: datetime):
        # 메인 쓰레드에서 안전하게 팝업 띄우기
        def popup():
            alert = tk.Toplevel(self.root)
            alert.title("일정 알림")
            alert.attributes("-topmost", True)
            w, h = 360, 180
            alert.geometry(f"{w}x{h}")
            alert.resizable(False, False)

            # 중앙 배치
            alert.update_idletasks()
            sw = alert.winfo_screenwidth()
            sh = alert.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            alert.geometry(f"{w}x{h}+{x}+{y}")

            frm = ttk.Frame(alert, padding=16)
            frm.pack(fill="both", expand=True)

            ttk.Label(frm, text="일정 알림", font=("Segoe UI", 14, "bold")).pack(anchor="center", pady=(0, 10))
            ttk.Label(frm, text=schedule.title, font=("Segoe UI", 12)).pack(anchor="center", pady=(0, 6))

            # 원래 알림 시간 안내
            tstr = target_dt.strftime("%Y-%m-%d %H:%M")
            ttk.Label(frm, text=f"(원래 알림 시각: {tstr} KST)", foreground="#555").pack(anchor="center", pady=(0, 10))

            ttk.Button(frm, text="확인", command=alert.destroy).pack(pady=(8, 0))

            # 포커스
            alert.transient(self.root)
            alert.grab_set()
            alert.focus_force()
            self.root.wait_window(alert)

        # tkinter는 메인 스레드에서 UI를 다뤄야 하므로 이벤트 큐에 넣는다.
        self.root.after(0, popup)

    # ---------- Helpers ----------
    def _now_kst(self) -> datetime:
        if self.tz is not None:
            return datetime.now(self.tz)
        # Fallback: naive localtime (KST 가정)
        return datetime.now()

    def _combine_today_time(self, now_kst: datetime, time_str: str) -> datetime:
        parts = time_str.split(":")
        if len(parts) == 2:
            hh, mm = int(parts[0]), int(parts[1])
            ss = 0
        elif len(parts) == 3:
            hh, mm, ss = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            raise ValueError("시간 형식은 HH:MM 또는 HH:MM:SS")
        dt = datetime(now_kst.year, now_kst.month, now_kst.day, hh, mm, ss)
        if self.tz is not None:
            dt = dt.replace(tzinfo=self.tz)
        return dt

    def _validate_time(self, time_str: str) -> bool:
        try:
            parts = time_str.split(":")
            if len(parts) not in (2, 3):
                return False
            hh = int(parts[0]); mm = int(parts[1])
            ss = int(parts[2]) if len(parts) == 3 else 0
            if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
                return False
            return True
        except Exception:
            return False

    # ---------- Cleanup ----------
    def on_close(self):
        self.stop_thread()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = NotifierApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
