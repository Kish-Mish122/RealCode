#!/usr/bin/env python3
# crashpad.py - RealCode CrashPad
# Отдельное приложение, следит за состоянием RealCode.
# Работает кроссплатформенно (Windows / Linux / macOS).

import os
import sys
import json
import time
import signal
import subprocess
import threading
import tkinter as tk
import argparse
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

from config_public import VERSION_CRASHPAD
from config_public import VERSION_REALCODE


# =====================================================================
# ПЛАТФОРМЕННЫЕ ХЕЛПЕРЫ
# =====================================================================

def is_windows() -> bool:
    return sys.platform == 'win32'


def is_linux() -> bool:
    return sys.platform.startswith('linux')


def get_app_dir() -> str:
    """Директория, где лежит crashpad.py / crashpad.exe."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_default_ui_font() -> str:
    if is_windows():
        return "Segoe UI"
    elif sys.platform == 'darwin':
        return "SF Pro Text"
    return "DejaVu Sans"


def get_default_mono_font() -> str:
    if is_windows():
        return "Consolas"
    elif sys.platform == 'darwin':
        return "Menlo"
    return "DejaVu Sans Mono"


def is_process_alive(pid: int) -> bool:
    """Проверяет, жив ли процесс по PID."""
    if pid <= 0:
        return False
    try:
        if is_windows():
            # tasklist не всегда быстрый — используем OpenProcess
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            # Проверяем, что процесс ещё не завершился
            exit_code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(
                h, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(h)
            return ok and exit_code.value == 259  # STILL_ACTIVE
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False


def kill_process(pid: int):
    """Жёстко убивает процесс."""
    try:
        if is_windows():
            subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                           capture_output=True, shell=False)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass


# =====================================================================
# CRASHPAD APP
# =====================================================================

# Цвета (в стиле RealCode)
class C:
    BG        = "#1e1e1e"
    BG_MED    = "#252526"
    BG_LIGHT  = "#2d2d2d"
    FG        = "#d4d4d4"
    FG_DIM    = "#858585"
    ACCENT    = "#2e7d32"
    ACCENT_H  = "#1b5e20"
    DANGER    = "#d9534f"
    WARN      = "#a05a00"
    OK        = "#1b5e20"
    BORDER    = "#3e3e42"


class CrashPadApp:
    # Как часто проверять состояние (сек)
    POLL_INTERVAL = 2

    # Через сколько секунд "протухает" heartbeat
    HEARTBEAT_STALE_AFTER = 15

    # Сколько строк лога показывать
    LOG_TAIL_LINES = 200

    def __init__(self, root: tk.Tk, visible: bool = False,
                 watch_pid: int = None, auto_start_realcode: bool = True):
        self.root = root
        self.app_dir = get_app_dir()
        self.visible_on_start = visible
        self.external_pid = watch_pid           # если задан — следим за чужим RealCode
        self.auto_start_realcode = auto_start_realcode

        # Пути
        self.rlcode_exe = self._detect_realcode_path()
        self.work_dir = self._detect_work_dir()

        # Процесс RealCode
        self.process: subprocess.Popen | None = None
        self.last_pid: int | None = None
        self.started_at: float | None = None

        # Состояние наблюдателя
        self.watchdog_running = False
        self.crash_reports_dir = os.path.join(self.app_dir, "crash_reports")
        os.makedirs(self.crash_reports_dir, exist_ok=True)

        # Пути к heartbeat и логу
        self.heartbeat_path = os.path.join(self.work_dir, ".RLCode", "heartbeat.json")
        self.log_path = os.path.join(self.work_dir, ".RLCode", "realcode.log")

        # UI
        self._setup_window()
        self._create_widgets()

        # ─── Скрываем окно сразу после создания ──────────────────────
        if not self.visible_on_start:
            self.root.withdraw()  # окно невидимо, но процесс жив

        # ─── Если передан чужой PID — сразу цепляемся за него ────────
        if self.external_pid:
            self._attach_to_pid(self.external_pid)
        elif self.auto_start_realcode:
            # Иначе сами запускаем RealCode
            self.root.after(500, self._auto_start)

    # ------------------------------------------------------------------
    # ИНИЦИАЛИЗАЦИЯ
    # ------------------------------------------------------------------
    def _detect_realcode_path(self) -> str | None:
        """Ищет RealCode.exe / main.py рядом с crashpad."""
        # 1. Рядом с crashpad.exe есть RealCode.exe / RealCode
        candidates = [
            os.path.join(self.app_dir, "RealCode.exe"),
            os.path.join(self.app_dir, "RealCode"),
            os.path.join(self.app_dir, "main.py"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _detect_work_dir(self) -> str:
        """Папка рядом с RealCode.exe — там же, где пишет heartbeat сам RealCode."""
        if self.rlcode_exe:
            return os.path.dirname(os.path.abspath(self.rlcode_exe))
        return self.app_dir

    def _setup_window(self):
        ui = get_default_ui_font()
        self.root.title(f"RealCode v.{VERSION_CRASHPAD} CrashPad - Запуск...")
        self.root.geometry("720x520")
        self.root.minsize(600, 400)
        self.root.configure(bg=C.BG)

        # Иконка, если есть
        try:
            if os.path.exists("icon.ico") and is_windows():
                self.root.iconbitmap("icon.ico")
            elif os.path.exists("icon.png"):
                from PIL import Image, ImageTk
                img = Image.open("icon.png")
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
                self.root._icon_ref = photo
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        ui = get_default_ui_font()
        mono = get_default_mono_font()

        # ─── Header ──────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=C.BG_MED, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🛡️  CrashPad", bg=C.BG_MED, fg=C.FG,
                 font=(ui, 14, "bold"), padx=15).pack(side=tk.LEFT)
        self.version_label = tk.Label(
            header, text="Наблюдатель за RealCode",
            bg=C.BG_MED, fg=C.FG_DIM, font=(ui, 9), padx=10)
        self.version_label.pack(side=tk.LEFT)

        # ─── Статус-панель ──────────────────────────────────────────
        status_frame = tk.Frame(self.root, bg=C.BG_LIGHT, height=80)
        status_frame.pack(fill=tk.X, pady=(1, 0))
        status_frame.pack_propagate(False)

        self.status_icon = tk.Label(status_frame, text="⚪", bg=C.BG_LIGHT,
                                    fg=C.FG, font=(ui, 28))
        self.status_icon.pack(side=tk.LEFT, padx=(15, 5))

        status_texts = tk.Frame(status_frame, bg=C.BG_LIGHT)
        status_texts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)

        self.status_label = tk.Label(status_texts, text="Готов к запуску",
                                     bg=C.BG_LIGHT, fg=C.FG,
                                     font=(ui, 12, "bold"), anchor="w")
        self.status_label.pack(fill=tk.X)

        self.status_detail = tk.Label(status_texts, text="RealCode не запущен",
                                      bg=C.BG_LIGHT, fg=C.FG_DIM,
                                      font=(ui, 9), anchor="w")
        self.status_detail.pack(fill=tk.X)

        # ─── Кнопки управления ──────────────────────────────────────
        btn_bar = tk.Frame(self.root, bg=C.BG, pady=10)
        btn_bar.pack(fill=tk.X, padx=15)

        self.start_btn = self._make_button(
            btn_bar, "▶  Запустить RealCode", self.start_realcode, C.ACCENT)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = self._make_button(
            btn_bar, "⏹  Остановить", self.stop_realcode, C.BG_LIGHT)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.restart_btn = self._make_button(
            btn_bar, "🔄  Перезапустить", self.restart_realcode, C.BG_LIGHT)
        self.restart_btn.pack(side=tk.LEFT, padx=5)

        self.open_logs_btn = self._make_button(
            btn_bar, "📁  Открыть логи", self.open_crash_reports, C.BG_LIGHT)
        self.open_logs_btn.pack(side=tk.RIGHT, padx=5)

        # ─── Лог ────────────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg=C.BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        tk.Label(log_frame, text="Последние события RealCode:",
                 bg=C.BG, fg=C.FG_DIM, font=(ui, 9), anchor="w"
                 ).pack(fill=tk.X, pady=(0, 3))

        text_frame = tk.Frame(log_frame, bg=C.BORDER)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            text_frame, wrap=tk.WORD,
            bg="#0c0c0c", fg="#e0e0e0",
            font=(mono, 9),
            relief=tk.FLAT, borderwidth=0,
            padx=8, pady=8,
            state=tk.DISABLED,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(text_frame, orient=tk.VERTICAL,
                          command=self.log_text.yview,
                          bg=C.BG_MED, troughcolor=C.BG,
                          width=12)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

        # Тег для ошибок
        self.log_text.tag_configure("error", foreground="#ff6b6b")
        self.log_text.tag_configure("warn",  foreground="#e5c07b")
        self.log_text.tag_configure("info",  foreground="#61afef")
        self.log_text.tag_configure("crash", foreground="#ff6b6b",
                                    font=(mono, 9, "bold"))

        # ─── Нижняя строка ──────────────────────────────────────────
        bottom = tk.Frame(self.root, bg=C.BG_MED, height=24)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)
        bottom.pack_propagate(False)

        self.bottom_label = tk.Label(
            bottom, text="", bg=C.BG_MED, fg=C.FG_DIM,
            font=(ui, 8), padx=10, anchor="w")
        self.bottom_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._set_bottom(f"RealCode: {self.rlcode_exe or 'НЕ НАЙДЕН'}")

    def _make_button(self, parent, text, command, bg=C.BG_LIGHT):
        ui = get_default_ui_font()
        btn = tk.Label(parent, text=text, bg=bg, fg="white",
                       font=(ui, 10), padx=15, pady=8, cursor="hand2")
        btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self._hover_color(bg)))
        btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=bg))
        btn.bind('<Button-1>', lambda e: command())
        return btn

    def _hover_color(self, bg):
        mapping = {
            C.ACCENT:   C.ACCENT_H,
            C.BG_LIGHT: "#3d3d3d",
            C.DANGER:   "#b03a36",
        }
        return mapping.get(bg, "#3d3d3d")

    def _set_bottom(self, text: str):
        try:
            self.bottom_label.config(text=text)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # ЛОГ
    # ------------------------------------------------------------------
    def _append_log(self, text: str, tag: str = None):
        """Добавляет строку в лог-виджет."""
        try:
            self.log_text.config(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            if tag:
                self.log_text.insert(tk.END, f"[{ts}] ", "info")
                self.log_text.insert(tk.END, text + "\n", tag)
            else:
                self.log_text.insert(tk.END, f"[{ts}] {text}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception:
            pass

    def _load_tail_from_log(self):
        """Загружает последние строки realcode.log в лог-виджет."""
        try:
            if not os.path.exists(self.log_path):
                return
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            tail = lines[-self.LOG_TAIL_LINES:]
            self.log_text.config(state=tk.NORMAL)
            for line in tail:
                self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # УПРАВЛЕНИЕ ПРОЦЕССОМ
    # ------------------------------------------------------------------
    def _attach_to_pid(self, pid: int):
        """Подключается к уже запущенному RealCode по PID.
        Не запускает его снова — только наблюдает."""
        if not is_process_alive(pid):
            self._append_log(f"⚠️ PID {pid} не существует — RealCode уже закрыт",
                             "warn")
            # Он уже мёртв — тихо выходим
            self.root.after(100, self._on_close_silent)
            return

        self.last_pid = pid
        self.started_at = time.time()
        self.process = None  # не мы его запускали

        self._append_log(f"Следим за RealCode (PID {pid})", "info")
        self._update_status("running", "RealCode работает",
                            f"PID {pid} · подключились к запущенному")

        # Watchdog по PID (без subprocess.poll())
        self.watchdog_running = True
        threading.Thread(target=self._watchdog_external, daemon=True).start()

    def _watchdog_external(self):
        """Следит за чужим процессом через is_process_alive."""
        # Таймаут: если RealCode не запускается 60 сек — выходим
        started_waiting = time.time()
        first_seen_alive = False

        while self.watchdog_running:
            try:
                # Ждём появления процесса (до 60 сек)
                if not first_seen_alive:
                    if is_process_alive(self.last_pid):
                        first_seen_alive = True
                        self._append_log(
                            f"✅ RealCode (PID {self.last_pid}) обнаружен",
                            "info")
                    elif time.time() - started_waiting > 60:
                        # Процесс так и не появился — выходим
                        self._append_log(
                            "⚠️ RealCode не появился за 60 сек — выхожу",
                            "warn")
                        self.watchdog_running = False
                        self.root.after(200, self._on_close_silent)
                        return
                    else:
                        time.sleep(0.5)
                        continue

                # Проверяем, жив ли процесс
                if not is_process_alive(self.last_pid):
                    # RealCode умирает — даём 3 секунды на финальную запись heartbeat
                    # (без этого бывает гонка: процесс уже мёртв, а clean_shutdown
                    #  ещё не дописан на диск)
                    state = None
                    for _ in range(6):
                        time.sleep(0.5)
                        state = self._read_heartbeat_state()
                        if state == "clean_shutdown":
                            break
                    if state == "clean_shutdown":
                        self._append_log(
                            "✅ RealCode закрыт нормально", "info")
                        self.watchdog_running = False
                        self.root.after(300, self._on_close_silent)
                        return
                    else:
                        # Крах
                        self.watchdog_running = False
                        self._handle_crash_external()
                        return

                self._check_heartbeat()
                time.sleep(self.POLL_INTERVAL)
            except Exception as e:
                print(f"external watchdog error: {e}")
                time.sleep(1)

    def _handle_crash_external(self):
        """Обработка краха для внешнего процесса (без exit_code)."""
        duration = time.time() - self.started_at if self.started_at else 0

        self._append_log("💥 RealCode УПАЛ! (внешний процесс)", "crash")
        self._update_status("crashed", "💥 RealCode упал!",
                            "Heartbeat не был clean_shutdown")

        report_path = self._write_crash_report(-1, duration)
        self._append_log(f"📄 Отчёт: {report_path}", "info")
        self._load_tail_from_log()

        self.root.after(0, lambda: self._show_crash_dialog(-1, report_path))

    def _auto_start(self):
        if self.rlcode_exe and not self.process:
            self.start_realcode()

    def start_realcode(self):
        if self.process and self.process.poll() is None:
            self._append_log("RealCode уже запущен", "warn")
            return

        if not self.rlcode_exe:
            messagebox.showerror(
                "CrashPad",
                "Не найден RealCode.\n\n"
                "Положи crashpad.py рядом с main.py, или собери\n"
                "RealCode.exe и положи рядом с crashpad.exe.")
            return

        try:
            # Как запускать — .exe или python-скрипт?
            if self.rlcode_exe.endswith(".py"):
                cmd = [sys.executable, self.rlcode_exe]
            else:
                cmd = [self.rlcode_exe]

            creationflags = 0
            if is_windows():
                creationflags = 0x08000000  # CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                cmd,
                cwd=self.work_dir,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.last_pid = self.process.pid
            self.started_at = time.time()

            self._append_log(f"▶ RealCode запущен (PID {self.last_pid})", "info")
            self._update_status("running", "RealCode работает",
                                f"PID {self.last_pid}")
            self._set_bottom(f"PID: {self.last_pid} · запущен {datetime.now().strftime('%H:%M:%S')}")

            # Запускаем watchdog
            self.watchdog_running = True
            threading.Thread(target=self._watchdog_loop, daemon=True).start()

        except Exception as e:
            messagebox.showerror("CrashPad", f"Не удалось запустить RealCode:\n{e}")

    def stop_realcode(self):
        if not self.process:
            self._append_log("RealCode не запущен", "warn")
            return
        self.watchdog_running = False
        try:
            kill_process(self.process.pid)
            self._append_log("⏹ RealCode остановлен вручную", "info")
            self._update_status("stopped", "Остановлен вручную",
                                "Нажмите ▶ для запуска")
        except Exception as e:
            self._append_log(f"Ошибка остановки: {e}", "error")
        self.process = None
        self.last_pid = None

    def restart_realcode(self):
        self.watchdog_running = False
        if self.process and self.process.poll() is None:
            try:
                kill_process(self.process.pid)
            except Exception:
                pass
        self.process = None
        time.sleep(0.5)
        self.start_realcode()

    def open_crash_reports(self):
        """Открывает папку с crash-отчётами и логами."""
        try:
            if is_windows():
                os.startfile(self.crash_reports_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.crash_reports_dir])
            else:
                subprocess.Popen(['xdg-open', self.crash_reports_dir],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception as e:
            messagebox.showerror("CrashPad", f"Не удалось открыть папку:\n{e}")

    # ------------------------------------------------------------------
    # WATCHDOG
    # ------------------------------------------------------------------
    def _watchdog_loop(self):
        """Следит за процессом, пока он жив."""
        while self.watchdog_running:
            try:
                self._check_process()
                self._check_heartbeat()
                # Проверяем каждые POLL_INTERVAL секунд, но мелким шагом
                for _ in range(self.POLL_INTERVAL * 10):
                    if not self.watchdog_running:
                        return
                    time.sleep(0.1)
            except Exception as e:
                print(f"watchdog error: {e}")
                time.sleep(1)

    def _check_process(self):
        """Проверяет, жив ли процесс и с каким кодом вышел."""
        if not self.process:
            return

        code = self.process.poll()
        if code is None:
            return  # ещё работает

        # Процесс завершился
        self.watchdog_running = False
        exited_after = time.time() - self.started_at if self.started_at else 0

        if code == 0:
            state = self._read_heartbeat_state()
            if state == "clean_shutdown":
                # Обычное закрытие — тихо выходим, не мешаем пользователю
                self._append_log("✅ RealCode закрыт нормально", "info")
                self.watchdog_running = False
                self.root.after(300, self._on_close_silent)
            else:
                # Код 0 без clean_shutdown — необычно, но не краш.
                # Тихо выходим, чтобы не мешать.
                self._append_log(
                    "ℹ️ RealCode завершён (без clean_shutdown)", "info")
                self.watchdog_running = False
                self.root.after(300, self._on_close_silent)
        else:
            # КРАШ — вот тут показываем окно
            self._handle_crash(code, exited_after)

        self.process = None

    def _read_heartbeat_state(self) -> str | None:
        try:
            if not os.path.exists(self.heartbeat_path):
                return None
            with open(self.heartbeat_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("state")
        except Exception:
            return None

    def _check_heartbeat(self):
        """Проверяет, не устарел ли heartbeat — если да, процесс завис."""
        if not self.process or self.process.poll() is not None:
            return
        if not os.path.exists(self.heartbeat_path):
            return
        try:
            mtime = os.path.getmtime(self.heartbeat_path)
            age = time.time() - mtime
            if age > self.HEARTBEAT_STALE_AFTER:
                # Heartbeat устарел
                self._append_log(
                    f"⚠️ Heartbeat устарел на {int(age)} сек — RealCode завис?",
                    "warn")
                self._update_status("hung", "RealCode не отвечает",
                                    f"Heartbeat не обновлялся {int(age)} сек")
        except Exception:
            pass

    def _handle_crash(self, exit_code: int, duration: float):
        """Обрабатывает краш — показывает окно, пишет отчёт."""
        # 1. Сначала показываем окно
        self._show_window()

        # 2. Пишем в лог и статус
        self._append_log(
            f"💥 RealCode УПАЛ! Код выхода: {exit_code}",
            "crash")
        self._update_status("crashed", "💥 RealCode упал!",
                            f"Код выхода: {exit_code}")

    def _show_window(self):
        """Показывает окно, если оно скрыто (при краше)."""
        def _apply():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.attributes('-topmost', True)
                # Через секунду снять topmost, чтобы не бесило
                self.root.after(1000,
                    lambda: self.root.attributes('-topmost', False))
            except Exception:
                pass
        self.root.after(0, _apply)

        # Сохраняем crash-отчёт
        report_path = self._write_crash_report(exit_code, duration)
        self._append_log(f"📄 Отчёт: {report_path}", "info")

        # Перезагружаем хвост лога из realcode.log
        self._load_tail_from_log()

        # Показываем диалог
        self.root.after(0, lambda: self._show_crash_dialog(exit_code, report_path))

    def _write_crash_report(self, exit_code: int, duration: float) -> str:
        """Пишет crash-отчёт в crash_reports/."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(
            self.crash_reports_dir, f"crash_{ts}_exit{exit_code}.txt")

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write(f"RealCode Crash Report (v.{VERSION_CRASHPAD})\n")
                f.write(f"Время: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")

                f.write(f"Код выхода:   {exit_code}\n")
                f.write(f"Длительность: {self._format_duration(duration)}\n")
                f.write(f"PID:          {self.last_pid}\n")
                f.write(f"RealCode:     {self.rlcode_exe}\n")
                f.write(f"Рабочая папка: {self.work_dir}\n")
                f.write(f"Python:       {sys.version}\n")
                f.write(f"Платформа:    {sys.platform}\n\n")
                f.write("== Если RealCode крашнулся, то отправьте этот лог на help.k1shm1sh@gmail.com ==")

                # Heartbeat
                f.write("-" * 70 + "\n")
                f.write("Heartbeat:\n")
                f.write("-" * 70 + "\n")
                if os.path.exists(self.heartbeat_path):
                    try:
                        with open(self.heartbeat_path, "r", encoding="utf-8") as hb:
                            f.write(hb.read() + "\n")
                    except Exception as e:
                        f.write(f"(не удалось прочитать: {e})\n")
                else:
                    f.write("(heartbeat не найден)\n")
                f.write("\n")

                # Хвост лога
                f.write("-" * 70 + "\n")
                f.write(f"Последние {self.LOG_TAIL_LINES} строк лога:\n")
                f.write("-" * 70 + "\n")
                if os.path.exists(self.log_path):
                    try:
                        with open(self.log_path, "r",
                                  encoding="utf-8", errors="replace") as lg:
                            lines = lg.readlines()
                        tail = lines[-self.LOG_TAIL_LINES:]
                        for line in tail:
                            f.write(line)
                    except Exception as e:
                        f.write(f"(не удалось прочитать лог: {e})\n")
                else:
                    f.write("(лог не найден)\n")
        except Exception as e:
            print(f"Ошибка записи отчёта: {e}")

        return report_path

    def _show_crash_dialog(self, exit_code: int, report_path: str):
        """Показывает диалог с предложениями."""
        result = messagebox.askyesno(
            f"RealCode v.{VERSION_REALCODE} не удачно закрылся!",
            f"RealCode завершился с кодом {exit_code}.\n\n"
            f"Отчёт сохранён:\n{report_path}\n\n"
            f"Перезапустить RealCode?")
        if result:
            self.root.after(200, self.start_realcode)
        else:
            # Не перезапускаем — закрываемся сами
            self._on_close_silent()

    # ------------------------------------------------------------------
    # UI HELPERS
    # ------------------------------------------------------------------
    def _update_status(self, state: str, title: str, detail: str):
        """state: running / stopped / crashed / hung"""
        icons = {
            "running": ("🟢", C.OK,     "RealCode работает"),
            "stopped": ("⚪", C.FG_DIM, "RealCode остановлен"),
            "crashed": ("💥", C.DANGER, "RealCode упал!"),
            "hung":    ("🟡", C.WARN,   "RealCode не отвечает"),
        }
        icon, color, _ = icons.get(state, ("⚪", C.FG_DIM, ""))

        def _apply():
            try:
                self.status_icon.config(text=icon)
                self.status_label.config(text=title, fg=color)
                self.status_detail.config(text=detail)
            except Exception:
                pass

        self.root.after(0, _apply)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds} сек"
        elif seconds < 3600:
            return f"{seconds // 60} мин {seconds % 60} сек"
        else:
            return f"{seconds // 3600} ч {(seconds % 3600) // 60} мин"

    # ------------------------------------------------------------------
    # ЗАКРЫТИЕ
    # ------------------------------------------------------------------
    def _on_close_silent(self):
        """Закрывает CrashPad без диалогов и вопросов."""
        self.watchdog_running = False
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def _on_close(self):
        # Не даём закрыть, если RealCode работает
        if self.process and self.process.poll() is None:
            res = messagebox.askyesnocancel(
                "CrashPad",
                "RealCode ещё работает. Закрыть CrashPad и остановить RealCode?")
            if res is None:
                return
            if res:
                self.watchdog_running = False
                try:
                    kill_process(self.process.pid)
                except Exception:
                    pass
            else:
                return
        self.watchdog_running = False
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass


# =====================================================================
# ТОЧКА ВХОДА
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RealCode CrashPad — тихий наблюдатель за RealCode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  crashpad.py                   # тихий режим: сам запустит RealCode, скроется
  crashpad.py --visible         # показать окно сразу (для отладки)
  crashpad.py --watch-pid 12345 # следить за уже запущенным RealCode
  crashpad.py --no-auto-start   # не запускать RealCode, только наблюдать
        """
    )
    parser.add_argument("--visible", action="store_true",
                        help="Показать окно сразу (режим отладки)")
    parser.add_argument("--watch-pid", type=int, default=None,
                        help="PID уже запущенного RealCode")
    parser.add_argument("--no-auto-start", action="store_true",
                        help="Не запускать RealCode, только наблюдать")

    args = parser.parse_args()

    root = tk.Tk()
    app = CrashPadApp(
        root,
        visible=args.visible,
        watch_pid=args.watch_pid,
        auto_start_realcode=not args.no_auto_start,
    )
    root.mainloop()
