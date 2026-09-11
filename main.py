#!/usr/bin/env python3
# main.py - RealCode
# Кроссплатформенная версия (Windows + Linux + macOS (coming soon))

import site
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import sys
from pathlib import Path
import threading
import re
from datetime import datetime
import webbrowser
import time
from PIL import Image, ImageTk
import pyflakes.api
import pycodestyle
import tempfile
import queue
from dataclasses import dataclass
from typing import List, Dict, Set
import requests
import zipfile
import io
import shutil
import glob
import importlib.util

from pyflakes import reporter
from pyflakes.api import check
from io import StringIO
from packaging import version
from git_integration import GitManager, GitFileStatus

try:
    if sys.platform == "win32" and sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, ValueError):
    pass

old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()


# =====================================================================
# ПЛАТФОРМЕННЫЕ ХЕЛПЕРЫ
# =====================================================================

def get_os_type():
    if sys.platform == 'win32':
        return 'windows'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform == 'darwin':
        return 'macos'
    return 'unknown'


def is_windows() -> bool:
    return sys.platform == 'win32'
    print("Платформа: Windows")


def is_linux() -> bool:
    return sys.platform.startswith('linux')
    print("Платформа: Linux")


def is_macos() -> bool:
    return sys.platform == 'darwin'
    print("Платформа: MacOS. Поддержка не гарантируется")


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_default_mono_font() -> str:
    if is_windows():
        return "Consolas"
    elif is_macos():
        return "Menlo"
    return "DejaVu Sans Mono"


def get_default_ui_font() -> str:
    if is_windows():
        return "Segoe UI"
    elif is_macos():
        return "SF Pro Text"
    return "DejaVu Sans"


def open_in_os(path: str) -> bool:
    try:
        if is_windows():
            os.startfile(path)  # type: ignore[attr-defined]
        elif is_macos():
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"⚠️ Не удалось открыть {path}: {e}")
        return False


def hide_folder(path: str) -> None:
    try:
        if is_windows():
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
    except Exception as e:
        print(f"⚠️ Не удалось скрыть папку: {e}")


def get_icon_path() -> str | None:
    app_dir = get_app_dir()
    candidates = ["icon.ico", "icon.png"] if is_windows() else ["icon.png", "icon.svg", "icon.ico"]
    for name in candidates:
        p = os.path.join(app_dir, name)
        if os.path.exists(p):
            return p
    return None


def set_window_icon(root: tk.Tk) -> None:
    icon_path = get_icon_path()
    if not icon_path:
        return
    try:
        if is_windows() and icon_path.lower().endswith('.ico'):
            root.iconbitmap(icon_path)
            return
        img = Image.open(icon_path)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        root._icon_ref = photo  # type: ignore[attr-defined]
    except Exception as e:
        print(f"⚠️ Не удалось установить иконку: {e}")


def maximize_window(root: tk.Tk) -> None:
    try:
        if is_windows():
            root.state('zoomed')
        elif is_linux():
            try:
                root.attributes('-zoomed', True)
            except tk.TclError:
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                root.geometry(f"{sw}x{sh}+0+0")
        elif is_macos():
            try:
                root.state('zoomed')
            except tk.TclError:
                root.attributes('-zoomed', True)
    except Exception as e:
        print(f"⚠️ Не удалось максимизировать окно: {e}")


def is_window_maximized(root: tk.Tk) -> bool:
    try:
        if is_windows():
            return root.state() == 'zoomed'
        if is_linux():
            try:
                return bool(root.attributes('-zoomed'))
            except tk.TclError:
                return False
        if is_macos():
            try:
                return root.state() == 'zoomed'
            except tk.TclError:
                return False
    except Exception:
        pass
    return False


def pick_ttk_theme() -> str:
    style = ttk.Style()
    available = style.theme_names()
    for preferred in ('clam', 'alt', 'default', 'classic'):
        if preferred in available:
            return preferred
    return available[0] if available else 'default'


# =====================================================================
# PYTHON PATHS
# =====================================================================

def setup_python_paths():
    added_paths = []
    try:
        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path and os.path.exists(user_site):
            sys.path.insert(0, user_site)
            added_paths.append(f"Пользовательский: {user_site}")
    except Exception:
        pass
    try:
        for path in site.getsitepackages():
            if path not in sys.path and os.path.exists(path):
                sys.path.insert(0, path)
                added_paths.append(f"Системный: {path}")
    except Exception:
        pass

    if is_windows():
        common_paths = [
            os.path.expanduser("~\\AppData\\Local\\Python\\Python39\\Lib\\site-packages"),
            os.path.expanduser("~\\AppData\\Local\\Python\\Python310\\Lib\\site-packages"),
            os.path.expanduser("~\\AppData\\Local\\Python\\Python311\\Lib\\site-packages"),
            os.path.expanduser("~\\AppData\\Local\\Python\\Python312\\Lib\\site-packages"),
            "C:\\Python39\\Lib\\site-packages",
            "C:\\Python310\\Lib\\site-packages",
            "C:\\Python311\\Lib\\site-packages",
            "C:\\Python312\\Lib\\site-packages",
        ]
    else:
        common_paths = []
        for path in (os.path.expanduser("~/.local/lib/python3.*/site-packages"),
                     "/usr/local/lib/python3.*/dist-packages",
                     "/usr/lib/python3.*/dist-packages"):
            common_paths.extend(glob.glob(path))

    for path in common_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            added_paths.append(f"Найденный: {path}")

    if added_paths:
        print(f"✅ Добавлено путей: {len(added_paths)}")


# =====================================================================
# КОНФИГ
# =====================================================================

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "font_family": get_default_mono_font(),
    "ui_font_family": get_default_ui_font(),
    "show_hidden_files": True,
    "font_size": 11,
    "project_path": ".",
    "sidebar_width": 250,
    "console_height": 200,
    "window_x": 100,
    "window_y": 100,
    "window_width": 1300,
    "window_height": 800,
    "window_maximized": False,
    "auto_save": False,
    "word_wrap": False,
    "tab_size": 4,
    "show_line_numbers": True,
    "syntax_highlight": True,
    "last_opened_folder": ".",
    "minimap_enabled": True,
    "save_scroll_position": True,
    "sidebar_visible": True,
    "console_visible": True,
    "explorer_position": "left",
    "console_position": "bottom",
    "recent_projects": []
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения конфига: {e}")


def check_and_import(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        module = __import__(module_name)
        print(f"✅ {package_name} успешно загружен")
        return True, module
    except ImportError as e:
        print(f"⚠️ {package_name} не загружен: {e}")
        print(f"   Установите: pip install {package_name}")
        return False, None
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке {package_name}: {e}")
        return False, None


setup_python_paths()

discord_ok, discord_module = check_and_import("pypresence", "pypresence")
DISCORD_AVAILABLE = discord_ok
if DISCORD_AVAILABLE:
    from pypresence import Presence
else:
    Presence = None

packaging_ok, packaging_module = check_and_import("packaging", "packaging")
PACKAGING_AVAILABLE = packaging_ok


# =====================================================================
# КОНФИГ ПРОЕКТА
# =====================================================================

from config import DISCORD_ID_CONFIG
from config import VERSION_REALCODE
from config import DOWNLOAD_URL
from config import GITHUB_VERSION_URL_CONFIG
from config import GITHUB_TOKEN
from config import FORMSPREE_ID
from config import MIN_REALCODE_VERSION
from config import GITHUB_VERSION_MIN
from config import PLUGIN_URL_CONF

DISCORD_ID = DISCORD_ID_CONFIG
GITHUB_VERSION_URL = GITHUB_VERSION_URL_CONFIG

APP_NAME = "RealCode"
VERSION = VERSION_REALCODE
DISCORD_CLIENT_ID = DISCORD_ID
MIN_REALCODE = MIN_REALCODE_VERSION


def ensure_directories(app_dir):
    for dir_name in ('plugins',):
        dir_path = os.path.join(app_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Создана папка: {dir_path}")


# =====================================================================
# ЦВЕТА
# =====================================================================

class VSColorScheme:
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2d2d2d"
    FG = "#d4d4d4"
    FG_LIGHT = "#cccccc"
    ACCENT = "#2e7d32"
    ACCENT_HOVER = "#1b5e20"
    STATUS_BG = "#2e7d32"
    SELECTION = "#1b5e20"
    LINE_NUMBERS = "#858585"
    BORDER = "#3e3e42"
    SCROLLBAR = "#3e3e42"
    TAB_ACTIVE = "#1e1e1e"
    TAB_INACTIVE = "#2d2d2d"
    CONSOLE_BG = "#1e1e1e"
    BUTTON_BG = "#2e7d32"
    PINNED = "#ff6b6b"
    KEYWORD = "#81c784"
    STRING = "#ce9178"
    COMMENT = "#6a9955"
    NUMBER = "#b5cea8"
    FUNCTION = "#dcdcaa"
    CLASS = "#4ec9b0"
    DECORATOR = "#c586c0"
    BUILTIN = "#4ec9b0"


def load_icon(filename, size=(16, 16)):
    path = os.path.join(get_app_dir(), "icons", filename)
    if os.path.exists(path):
        try:
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
    return None


# =====================================================================
# МОДЕЛЬ
# =====================================================================

@dataclass
class LintMessage:
    line: int
    column: int
    message: str
    code: str
    level: str
    source: str


class StringIOReporter(reporter.Reporter):
    def __init__(self, output):
        self.output = output

    def flake(self, message):
        self.output.write(str(message) + "\n")

    def unexpectedError(self, filename, msg):
        self.output.write(f"{filename}: {msg}\n")


class Project:
    STATE_FILE = "project_state.json"
    PINS_FILE = "pinned_items.json"
    RECENT_FILE = "recent_files.json"

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path) or "Unknown_Project"
        self.rlcode_path = os.path.join(path, ".RLCode")
        self._ensure_rlcode_folder()

        self.tabs = []
        self.pinned_tabs = []
        self.files = {}
        self.file_contents = {}
        self.current_tab = None

        self.state = {}
        self.pins = {"pinned_files": []}
        self.recent_files = []
        self._load_state()

    def _ensure_rlcode_folder(self):
        if not os.path.exists(self.rlcode_path):
            try:
                os.makedirs(self.rlcode_path, exist_ok=True)
                hide_folder(self.rlcode_path)
            except Exception as e:
                print(f"Не удалось создать .RLCode: {e}")

    def _get_file_path(self, filename):
        return os.path.join(self.rlcode_path, filename)

    def _load_state(self):
        try:
            state_path = self._get_file_path(self.STATE_FILE)
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
            else:
                self.state = {"last_opened_files": [], "expanded_folders": [],
                              "last_active_tab": None, "window_state": {}}

            pins_path = self._get_file_path(self.PINS_FILE)
            if os.path.exists(pins_path):
                with open(pins_path, 'r', encoding='utf-8') as f:
                    self.pins = json.load(f)
            else:
                self.pins = {"pinned_files": []}

            recent_path = self._get_file_path(self.RECENT_FILE)
            if os.path.exists(recent_path):
                with open(recent_path, 'r', encoding='utf-8') as f:
                    self.recent_files = json.load(f)
            else:
                self.recent_files = []
        except Exception as e:
            print(f"Ошибка загрузки состояния проекта: {e}")
            self.state = {"last_opened_files": [], "expanded_folders": [],
                          "last_active_tab": None, "window_state": {}}
            self.pins = {"pinned_files": []}
            self.recent_files = []

    def save_state(self):
        try:
            opened_files, pinned_files = [], []
            for tab in self.tabs:
                fp = self.files.get(tab)
                if fp:
                    opened_files.append(fp)
                    if tab.pinned:
                        pinned_files.append(fp)
            last_active = self.files.get(self.current_tab) if self.current_tab else None
            self.state["last_opened_files"] = opened_files
            self.state["last_active_tab"] = last_active

            with open(self._get_file_path(self.STATE_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
            self.pins["pinned_files"] = pinned_files
            with open(self._get_file_path(self.PINS_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.pins, f, indent=4, ensure_ascii=False)
            self.recent_files = self.recent_files[:20]
            with open(self._get_file_path(self.RECENT_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.recent_files, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения состояния проекта: {e}")

    def add_to_recent(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.save_state()

    def set_expanded_folders(self, expanded_folders):
        self.state["expanded_folders"] = expanded_folders
        self.save_state()

    def get_expanded_folders(self):
        return self.state.get("expanded_folders", [])

    def get_last_opened_files(self):
        return self.state.get("last_opened_files", [])

    def get_last_active_tab(self):
        return self.state.get("last_active_tab")

    def get_pinned_files(self):
        return self.pins.get("pinned_files", [])

    def is_file_pinned(self, file_path):
        return file_path in self.pins.get("pinned_files", [])

    def clear(self):
        self.tabs.clear()
        self.pinned_tabs.clear()
        self.files.clear()
        self.file_contents.clear()
        self.current_tab = None


# =====================================================================
# ВИДЖЕТЫ
# =====================================================================

class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, app=None, *args, **kwargs):
        self.app = app
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.configure(bg=VSColorScheme.BG_MEDIUM, highlightthickness=0, width=50)
        if self.text_widget:
            self._bind_events()
            self.update_numbers()

    def _bind_events(self):
        self.text_widget.bind('<KeyRelease>', lambda e: self.update_numbers(), add='+')
        self.text_widget.bind('<MouseWheel>', lambda e: self.update_numbers(), add='+')
        self.text_widget.bind('<Button-4>', lambda e: self.update_numbers(), add='+')
        self.text_widget.bind('<Button-5>', lambda e: self.update_numbers(), add='+')
        self.text_widget.bind('<Configure>', lambda e: self.update_numbers(), add='+')
        self.text_widget.bind('<<Modified>>', lambda e: self.update_numbers(), add='+')

    def update_numbers(self, event=None):
        self.delete("all")
        if not self.text_widget or not self.text_widget.winfo_exists():
            return
        try:
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            first_line = int(self.text_widget.index("@0,0").split('.')[0])
            last_line = int(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            for line_num in range(first_line, min(last_line + 1, total_lines + 1)):
                dline_info = self.text_widget.dlineinfo(f"{line_num}.0")
                if dline_info:
                    x, y, width, height, baseline = dline_info
                    self.create_text(45, y + height // 2, text=str(line_num),
                                     anchor="e", fill=VSColorScheme.LINE_NUMBERS,
                                     font=(get_default_mono_font(), 9))
                    if self.app and hasattr(self.app, 'linter') and self.app.linter:
                        msgs = self.app.linter.get_messages_at_line(line_num)
                        if msgs:
                            color = "red" if any(m.level == 'error' for m in msgs) else "orange"
                            self.create_oval(5, y + height // 2 - 4, 13, y + height // 2 + 4,
                                             fill=color, outline=color)
        except Exception as e:
            print(f"Ошибка обновления номеров строк: {e}")


class Minimap(tk.Canvas):
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.configure(bg=VSColorScheme.BG_MEDIUM, highlightthickness=1,
                       highlightcolor=VSColorScheme.BORDER, width=100)
        self.dragging = False
        self.content_lines = []
        self.scale_factor = 1.0
        self.update_after_id = None
        self.scroll_after_id = None
        self._bind_events()
        if self.text_widget:
            self._bind_text_events()
            self.update_minimap()

    def _bind_events(self):
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<MouseWheel>', self._on_minimap_scroll)
        self.bind('<Button-4>', self._on_minimap_scroll)
        self.bind('<Button-5>', self._on_minimap_scroll)

    def _bind_text_events(self):
        self.text_widget.bind('<KeyRelease>', self._schedule_update, add='+')
        self.text_widget.bind('<MouseWheel>', self._on_editor_scroll, add='+')
        self.text_widget.bind('<Button-4>', self._on_editor_scroll, add='+')
        self.text_widget.bind('<Button-5>', self._on_editor_scroll, add='+')
        self.text_widget.bind('<Configure>', self._schedule_update, add='+')
        self.text_widget.bind('<<Modified>>', self._schedule_update, add='+')

    def _schedule_update(self, event=None):
        if self.update_after_id:
            self.after_cancel(self.update_after_id)
        self.update_after_id = self.after(200, self.update_minimap)

    def update_minimap(self, event=None):
        if not self._check_widgets():
            return
        self.delete("all")
        try:
            text = self.text_widget.get("1.0", tk.END)
            self.content_lines = text.split('\n')
            total_lines = len(self.content_lines)
            if total_lines == 0:
                return
            minimap_height = self.winfo_height()
            if minimap_height <= 1:
                return
            self.scale_factor = minimap_height / total_lines
            self._draw_minimap_lines(total_lines, minimap_height)
            self._draw_visible_area()
        except Exception as e:
            print(f"Minimap error: {e}")

    def _check_widgets(self):
        return (self.text_widget and self.text_widget.winfo_exists()
                and self.winfo_exists())

    def _draw_minimap_lines(self, total_lines, minimap_height):
        y = 0
        max_display_lines = min(total_lines, 2000)
        for i in range(max_display_lines):
            if y > minimap_height:
                break
            line = self.content_lines[i]
            line_h = max(2, self.scale_factor)
            color = self._get_line_color(line)
            self.create_rectangle(0, y, self.winfo_width(), y + line_h,
                                  fill=color, outline="", tags=f"line_{i}")
            y += line_h

    def _get_line_color(self, line):
        if not line.strip():
            return VSColorScheme.BG_LIGHT
        if line.strip().startswith(('#', '//', '/*')):
            return VSColorScheme.COMMENT
        elif line.strip().startswith(('def ', 'class ')):
            return VSColorScheme.FUNCTION
        elif any(kw in line for kw in ['import ', 'from ', 'return ']):
            return VSColorScheme.KEYWORD
        elif re.match(r'^\s*$', line):
            return VSColorScheme.BG_LIGHT
        else:
            indent = len(line) - len(line.lstrip())
            return VSColorScheme.FG_LIGHT if indent > 0 else VSColorScheme.FG

    def _draw_visible_area(self):
        try:
            if not hasattr(self, 'scale_factor') or not self.content_lines:
                return
            first_line = float(self.text_widget.index("@0,0").split('.')[0])
            last_line = float(self.text_widget.index(
                f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            y1 = max(0, (first_line - 1) * self.scale_factor)
            y2 = min(self.winfo_height(), last_line * self.scale_factor)
            self.delete("visible_area")
            self.create_rectangle(0, y1, self.winfo_width(), y2,
                                  fill="#264f78", stipple="gray50",
                                  outline=VSColorScheme.ACCENT, width=1,
                                  tags="visible_area")
        except Exception as e:
            print(f"Ошибка отрисовки области видимости: {e}")

    def _on_editor_scroll(self, event):
        if self.scroll_after_id:
            self.after_cancel(self.scroll_after_id)
        self.scroll_after_id = self.after(50, self._draw_visible_area)

    def _on_minimap_scroll(self, event):
        if not (hasattr(self, 'scale_factor') and self.content_lines):
            return
        if hasattr(event, 'num') and event.num in (4, 5):
            delta = -5 if event.num == 4 else 5
        else:
            delta = -5 if event.delta > 0 else 5
        self.text_widget.yview_scroll(delta, "units")
        self._draw_visible_area()

    def _on_click(self, event):
        self.dragging = True
        self._scroll_to_position(event.y)

    def _on_drag(self, event):
        if self.dragging:
            self._scroll_to_position(event.y)

    def _on_release(self, event):
        self.dragging = False

    def _scroll_to_position(self, y):
        try:
            if not (hasattr(self, 'scale_factor') and self.content_lines):
                return
            total_lines = len(self.content_lines)
            if total_lines == 0:
                return
            fraction = y / self.winfo_height()
            target_line = max(1, min(total_lines, int(fraction * total_lines) + 1))
            self.text_widget.see(f"{target_line}.0")
            self.text_widget.focus_set()
            self._draw_visible_area()
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")


class SyntaxHighlighter:
    FULL_HIGHLIGHT_LIMIT = 1 * 1024 * 1024

    def __init__(self, text_widget):
        self.text = text_widget
        self.highlight_enabled = True
        self.current_language = 'python'
        self.update_after_id = None
        self.last_content = ""
        self.compiled_patterns = {}
        self._setup_tags()
        self._load_language_patterns('python')

    def _setup_tags(self):
        self.text.tag_configure("keyword", foreground=VSColorScheme.KEYWORD)
        self.text.tag_configure("builtin", foreground=VSColorScheme.BUILTIN)
        self.text.tag_configure("decorator", foreground=VSColorScheme.DECORATOR)
        self.text.tag_configure("function", foreground=VSColorScheme.FUNCTION)
        self.text.tag_configure("class", foreground=VSColorScheme.CLASS)
        self.text.tag_configure("comment", foreground=VSColorScheme.COMMENT,
                                font=(get_default_mono_font(), 10, "italic"))
        self.text.tag_configure("string", foreground=VSColorScheme.STRING)
        self.text.tag_configure("number", foreground=VSColorScheme.NUMBER)

    def _load_language_patterns(self, language='python'):
        base_patterns = {
            'number': r'\b\d+\.?\d*\b',
            'function': r'\b\w+(?=\s*\()',
        }
        lang_patterns = {
            'python': {
                'keyword': r'\b(def|class|if|else|elif|for|while|import|from|return|try|except|finally|with|as|in|is|not|and|or|True|False|None|break|continue|pass|lambda|yield|async|await)\b',
                'builtin': r'\b(print|len|range|input|str|int|float|list|dict|set|tuple|open|file|type|isinstance|issubclass|super|staticmethod|classmethod|property|abs|all|any|bin|bool|chr|complex|enumerate|filter|format|hex|id|max|min|next|oct|ord|pow|repr|reversed|round|sorted|sum|vars|zip)\b',
                'decorator': r'@\w+',
                'comment': r'#.*$',
                'class': r'(?<=class\s)\w+',
            },
            'cpp': {
                'keyword': r'\b(if|else|for|while|do|switch|case|break|continue|return|goto|void|int|float|#include|double|char|bool|long|short|unsigned|signed|const|static|virtual|override|final|class|struct|enum|typedef|using|namespace|template|typename|public|private|protected|friend|explicit|inline|new|delete|this|throw|try|catch|auto|decltype|nullptr|sizeof|alignof|noexcept)\b',
                'builtin': r'\b(cout|cin|endl|string|vector|array|map|set|pair|make_pair|shared_ptr|unique_ptr|weak_ptr|move|forward)\b',
                'decorator': r'__\w+__',
                'comment': r'//.*$',
                'block_comment': r'/\*.*?\*/',
                'class': r'(?<=class\s)\w+|(?<=struct\s)\w+',
            },
            'csharp': {
                'keyword': r'\b(if|else|for|while|do|switch|case|break|continue|return|using|goto|void|int|float|double|char|bool|long|short|uint|ulong|ushort|byte|sbyte|decimal|string|object|dynamic|var|const|static|readonly|class|struct|enum|interface|delegate|event|namespace|public|private|protected|internal|abstract|sealed|override|virtual|new|async|await|throw|try|catch|finally|lock|unsafe|fixed|sizeof|typeof|nameof|is|as|base|this)\b',
                'builtin': r'\b(Console|WriteLine|Write|ReadLine|Read|StringBuilder|List|Dictionary|Tuple|DateTime|Task)\b',
                'decorator': r'\[.*?\]',
                'comment': r'//.*$',
                'block_comment': r'/\*.*?\*/',
                'class': r'(?<=class\s)\w+|(?<=struct\s)\w+',
            },
            'c': {
                'keyword': r'\b(if|else|for|while|do|switch|case|break|continue|return|goto|void|int|float|double|char|long|short|unsigned|signed|const|static|volatile|extern|register|typedef|struct|union|enum|sizeof|auto|inline|restrict|_Bool|_Complex|_Imaginary)\b',
                'builtin': r'\b(printf|scanf|fopen|fclose|fread|fwrite|malloc|calloc|realloc|free|memcpy|strlen|strcpy|strcat|strcmp|exit|system|getchar|putchar)\b',
                'decorator': r'__attribute__\s*\(\(.*?\)\)',
                'comment': r'//.*$',
                'block_comment': r'/\*.*?\*/',
                'class': r'(?<=struct\s)\w+',
            },
            'go': {
                'keyword': r'\b(if|else|for|switch|case|break|continue|return|goto|func|go|select|defer|import|package|type|interface|struct|map|chan|var|const|range|fallthrough|default|append|cap|close|complex|copy|delete|imag|len|make|new|panic|print|println|real|recover)\b',
                'builtin': r'\b(make|new|append|copy|delete|len|cap|close|complex|imag|real|panic|recover|print|println)\b',
                'decorator': r'//go:.*$',
                'comment': r'//.*$',
                'block_comment': r'/\*.*?\*/',
                'class': r'(?<=type\s)\w+',
            },
            'holyc': {
                'keyword': r'\b(if|else|for|while|do|switch|case|break|continue|return|goto|void|int|float|double|char|long|short|unsigned|signed|const|static|volatile|typedef|struct|union|enum|sizeof|auto|register|extern|public|private|import|class|new|delete|this|base|using|namespace)\b',
                'builtin': r'\b(Print|PrintF|PrintLn|Input|PutChar|GetChar|Open|Close|Read|Write|Seek|Malloc|Free|MemSet|MemCopy|StrLen|StrCpy|StrCat|StrCmp|Exit|System|Yield|Sleep)\b',
                'decorator': r'\[.*?\]',
                'comment': r'//.*$',
                'block_comment': r'/\*.*?\*/',
                'class': r'(?<=class\s)\w+|(?<=struct\s)\w+',
            }
        }
        lang_data = lang_patterns.get(language, lang_patterns['python'])
        self.patterns = {**base_patterns}
        self.block_patterns = {}
        for key, pattern in lang_data.items():
            if key == 'block_comment':
                self.block_patterns['comment'] = pattern
            else:
                self.patterns[key] = pattern

        self.compiled_patterns = {}
        for tag, pat in self.patterns.items():
            try:
                self.compiled_patterns[tag] = re.compile(pat, re.MULTILINE)
            except Exception:
                pass
        for tag, pat in self.block_patterns.items():
            try:
                self.compiled_patterns[tag] = re.compile(pat, re.DOTALL | re.MULTILINE)
            except Exception:
                pass
        self.current_language = language

    def set_language(self, extension):
        ext_map = {
            '.py': 'python', '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp',
            '.c': 'c', '.cs': 'csharp', '.go': 'go',
            '.hc': 'holyc', '.holyc': 'holyc',
        }
        self._load_language_patterns(ext_map.get(extension.lower(), 'python'))

    def should_highlight(self):
        return self.highlight_enabled

    def get_file_size(self):
        try:
            return len(self.text.get("1.0", tk.END).encode('utf-8'))
        except Exception:
            return 0

    def highlight(self, force=False):
        if not self.should_highlight():
            return
        if self.get_file_size() > self.FULL_HIGHLIGHT_LIMIT:
            self.highlight_visible()
            return
        try:
            current_content = self.text.get("1.0", tk.END)
            if not force and current_content == self.last_content:
                return
            self.last_content = current_content
            for tag in ('keyword', 'builtin', 'decorator', 'function',
                        'class', 'comment', 'string', 'number'):
                self.text.tag_remove(tag, "1.0", tk.END)
            for tag_name, compiled in self.compiled_patterns.items():
                try:
                    for match in compiled.finditer(current_content):
                        self.text.tag_add(tag_name,
                                          f"1.0+{match.start()}c",
                                          f"1.0+{match.end()}c")
                except Exception as e:
                    print(f"Ошибка применения паттерна {tag_name}: {e}")
        except Exception as e:
            print(f"Ошибка подсветки: {e}")

    def incremental_highlight(self, start_line=1, end_line=None):
        if not self.should_highlight():
            return
        if end_line is None:
            end_line = start_line
        for tag in ('keyword', 'builtin', 'decorator', 'function',
                    'class', 'comment', 'string', 'number'):
            self.text.tag_remove(tag, f"{start_line}.0", f"{end_line + 1}.0")
        text_range = self.text.get(f"{start_line}.0", f"{end_line + 1}.0")
        if not text_range:
            return
        base_offset = 0
        try:
            for i in range(1, start_line):
                base_offset += len(self.text.get(f"{i}.0", f"{i}.end")) + 1
        except Exception:
            base_offset = 0
        for tag_name, compiled in self.compiled_patterns.items():
            if tag_name == 'comment' and 'comment' in self.block_patterns:
                continue
            try:
                for match in compiled.finditer(text_range):
                    abs_s = base_offset + match.start()
                    abs_e = base_offset + match.end()
                    self.text.tag_add(tag_name, f"1.0+{abs_s}c", f"1.0+{abs_e}c")
            except Exception:
                pass

    def highlight_visible(self):
        if not self.should_highlight():
            return
        try:
            first = int(self.text.index("@0,0").split('.')[0])
            last = int(self.text.index(f"@0,{self.text.winfo_height()}").split('.')[0])
            if last <= first:
                last = first + 50
            first = max(1, first - 2)
            last = min(int(self.text.index('end-1c').split('.')[0]), last + 2)
            if last - first > 100:
                last = first + 100
            self.incremental_highlight(first, last)
        except Exception as e:
            print(f"Ошибка подсветки видимой области: {e}")


class ModernTab(tk.Frame):
    def __init__(self, parent, title, close_callback, select_callback, pin_callback, *args, **kwargs):
        super().__init__(parent, bg=VSColorScheme.TAB_INACTIVE, height=45, width=180)
        self.pack_propagate(False)
        self.close_callback = close_callback
        self.select_callback = select_callback
        self.pin_callback = pin_callback
        self.title = title
        self.is_active = False
        self.modified = False
        self.pinned = False
        self.scroll_position = 0.0
        self.file_path = None
        self.configure(cursor="hand2")
        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        ui = get_default_ui_font()
        self.pin_btn = tk.Label(self, text="📌", bg=VSColorScheme.TAB_INACTIVE,
                                fg=VSColorScheme.FG_LIGHT, font=(ui, 10), cursor="hand2")
        self.pin_btn.place(x=5, y=12, width=20, height=20)
        self.title_label = tk.Label(self, text=self.title, bg=VSColorScheme.TAB_INACTIVE,
                                    fg=VSColorScheme.FG, font=(ui, 11),
                                    cursor="hand2", padx=10, pady=12)
        self.title_label.place(x=30, y=0, width=120, height=45)
        self.close_btn = tk.Label(self, text="✕", bg=VSColorScheme.TAB_INACTIVE,
                                  fg=VSColorScheme.FG, font=(ui, 12, "bold"), cursor="hand2")
        self.close_btn.place(x=155, y=10, width=20, height=25)

    def _bind_events(self):
        self.bind('<Button-1>', self._on_select)
        self.title_label.bind('<Button-1>', self._on_select)
        self.pin_btn.bind('<Button-1>', self._on_pin)
        self.close_btn.bind('<Button-1>', self._on_close)
        self.pin_btn.bind('<Enter>', self._on_pin_enter)
        self.pin_btn.bind('<Leave>', self._on_pin_leave)
        self.close_btn.bind('<Enter>', self._on_close_enter)
        self.close_btn.bind('<Leave>', self._on_close_leave)
        self.bind('<Enter>', self._on_enter)
        self.title_label.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.title_label.bind('<Leave>', self._on_leave)

    def _on_enter(self, e):
        if not self.is_active:
            self._set_bg_color(VSColorScheme.BG_LIGHT)

    def _on_leave(self, e):
        if not self.is_active:
            self._set_bg_color(VSColorScheme.TAB_INACTIVE)

    def _set_bg_color(self, color):
        self.configure(bg=color)
        self.title_label.configure(bg=color)
        self.pin_btn.configure(bg=color)
        self.close_btn.configure(bg=color)

    def _on_pin_enter(self, e):
        self.pin_btn.configure(fg=VSColorScheme.PINNED if self.pinned else VSColorScheme.ACCENT)

    def _on_pin_leave(self, e):
        self.pin_btn.configure(fg=VSColorScheme.PINNED if self.pinned else VSColorScheme.FG_LIGHT)

    def _on_close_enter(self, e):
        self.close_btn.configure(fg=VSColorScheme.ACCENT, bg=VSColorScheme.ACCENT_HOVER)

    def _on_close_leave(self, e):
        bg = VSColorScheme.TAB_ACTIVE if self.is_active else VSColorScheme.TAB_INACTIVE
        self.close_btn.configure(fg=VSColorScheme.FG, bg=bg)

    def _on_select(self, e):
        self.select_callback(self)

    def _on_pin(self, e):
        self.pinned = not self.pinned
        if self.pinned:
            self.pin_btn.configure(fg=VSColorScheme.PINNED, text="📍")
        else:
            self.pin_btn.configure(fg=VSColorScheme.FG_LIGHT, text="📌")
        if self.pin_callback:
            self.pin_callback(self)

    def _on_close(self, e):
        if not self.pinned and self.close_callback:
            self.close_callback(self)

    def set_active(self, active):
        self.is_active = active
        bg = VSColorScheme.TAB_ACTIVE if active else VSColorScheme.TAB_INACTIVE
        self._set_bg_color(bg)

    def set_modified(self, modified):
        self.modified = modified
        text = self.title + (" ●" if modified else "")
        self.title_label.config(text=text)

    def save_scroll_position(self, position):
        self.scroll_position = position

    def get_scroll_position(self):
        return self.scroll_position


class WelcomeScreen:
    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.frame = None
        self._create_welcome_screen()

    def _create_welcome_screen(self):
        ui = get_default_ui_font()
        self.frame = tk.Frame(self.parent, bg=VSColorScheme.BG_DARK)
        center = tk.Frame(self.frame, bg=VSColorScheme.BG_DARK)
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        tk.Label(center, text=APP_NAME, bg=VSColorScheme.BG_DARK,
                 fg=VSColorScheme.FG, font=(ui, 48, "bold")).pack(pady=(0, 10))
        tk.Label(center, text=f"Версия {VERSION}", bg=VSColorScheme.BG_DARK,
                 fg=VSColorScheme.FG_LIGHT, font=(ui, 14)).pack(pady=(0, 40))

        actions = tk.Frame(center, bg=VSColorScheme.BG_DARK)
        actions.pack(pady=20)
        for text, cmd in (("📄  Новый файл", lambda e: self.app.add_new_tab()),
                          ("📂  Открыть файл", lambda e: self.app.open_file()),
                          ("📁  Открыть папку", lambda e: self.app.open_folder())):
            btn = tk.Label(actions, text=text, bg=VSColorScheme.BG_LIGHT,
                           fg=VSColorScheme.FG, font=(ui, 11), padx=30,
                           pady=10, cursor="hand2")
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=VSColorScheme.ACCENT))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=VSColorScheme.BG_LIGHT))
            btn.bind('<Button-1>', cmd)
            btn.pack(side=tk.LEFT, padx=10)

        shortcuts = tk.Frame(center, bg=VSColorScheme.BG_DARK)
        shortcuts.pack(pady=30)
        data = [("Ctrl+N", "Новый файл"), ("Ctrl+O", "Открыть файл"),
                ("Ctrl+K", "Открыть папку"), ("Ctrl+S", "Сохранить"),
                ("Ctrl+F", "Поиск"), ("Ctrl+G", "Перейти к строке"),
                ("F5", "Запустить код"), ("F1", "Настройки")]
        left = tk.Frame(shortcuts, bg=VSColorScheme.BG_DARK)
        left.pack(side=tk.LEFT, padx=20)
        right = tk.Frame(shortcuts, bg=VSColorScheme.BG_DARK)
        right.pack(side=tk.LEFT, padx=20)
        for key, desc in data[:4]:
            self._shortcut_item(left, key, desc, ui)
        for key, desc in data[4:]:
            self._shortcut_item(right, key, desc, ui)

    def _shortcut_item(self, parent, key, desc, ui):
        f = tk.Frame(parent, bg=VSColorScheme.BG_DARK)
        f.pack(pady=5)
        tk.Label(f, text=key, bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.ACCENT,
                 font=(ui, 10, "bold"), padx=10, pady=2).pack(side=tk.LEFT, padx=5)
        tk.Label(f, text=desc, bg=VSColorScheme.BG_DARK, fg=VSColorScheme.FG_LIGHT,
                 font=(ui, 10)).pack(side=tk.LEFT, padx=5)

    def hide(self):
        if self.frame and self.frame.winfo_ismapped():
            self.frame.pack_forget()

    def show(self):
        if self.frame and not self.frame.winfo_ismapped():
            self.frame.pack(fill=tk.BOTH, expand=True)


# =====================================================================
# НАСТРОЙКИ
# =====================================================================

class SettingsDialog:
    def __init__(self, parent, config, callback):
        self.parent = parent
        self.config = config.copy()
        self.callback = callback
        self.window = None
        self._show()

    def _show(self):
        ui = get_default_ui_font()
        self.window = tk.Toplevel(self.parent)
        self.window.title("Настройки")
        self.window.geometry("600x600")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        tk.Label(self.window, text="НАСТРОЙКИ", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(ui, 12, "bold"), pady=10).pack()
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ef = tk.Frame(notebook, bg=VSColorScheme.BG_MEDIUM)
        notebook.add(ef, text="Редактор")
        self._create_editor_settings(ef)
        wf = tk.Frame(notebook, bg=VSColorScheme.BG_MEDIUM)
        notebook.add(wf, text="Окна")
        self._create_window_settings(wf)
        self._create_buttons()

    def _create_editor_settings(self, parent):
        row = 0
        tk.Label(parent, text="Шрифт:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.font_var = tk.StringVar(value=self.config["font_family"])
        ttk.Combobox(parent, textvariable=self.font_var,
                     values=["Consolas", "Courier New", "Monaco", "Lucida Console",
                             "DejaVu Sans Mono", "Ubuntu Mono", "Menlo", "Fira Code"],
                     width=20).grid(row=row, column=1, pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Размер шрифта:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.size_var = tk.IntVar(value=self.config["font_size"])
        tk.Spinbox(parent, from_=8, to=24, textvariable=self.size_var, width=10
                   ).grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Размер табуляции:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.tab_var = tk.IntVar(value=self.config["tab_size"])
        tk.Spinbox(parent, from_=2, to=8, textvariable=self.tab_var, width=10
                   ).grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2,
                                                        sticky="ew", pady=10, padx=10)
        row += 1
        for vn, key, default, lbl in [
            ("save_scroll_var", "save_scroll_position", True, "Сохранять позицию прокрутки"),
            ("auto_save_var", "auto_save", False, "Автосохранение"),
            ("wrap_var", "word_wrap", False, "Перенос строк"),
            ("highlight_var", "syntax_highlight", True, "Подсветка синтаксиса"),
            ("minimap_var", "minimap_enabled", True, "Показывать миникарту"),
            ("hidden_var", "show_hidden_files", False, "Показывать скрытые файлы (Например: .git, .env и подобные)"),
        ]:
            var = tk.BooleanVar(value=self.config.get(key, default))
            setattr(self, vn, var)
            tk.Checkbutton(parent, text=lbl, variable=var,
                           bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                           selectcolor=VSColorScheme.BG_MEDIUM,
                           activebackground=VSColorScheme.BG_MEDIUM
                           ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
            row += 1

    def _create_window_settings(self, parent):
        row = 0
        tk.Label(parent, text="Ширина проводника:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.sidebar_width_var = tk.IntVar(value=self.config.get("sidebar_width", 250))
        tk.Spinbox(parent, from_=150, to=500, textvariable=self.sidebar_width_var, width=10
                   ).grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Высота консоли:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.console_height_var = tk.IntVar(value=self.config.get("console_height", 200))
        tk.Spinbox(parent, from_=100, to=500, textvariable=self.console_height_var, width=10
                   ).grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2,
                                                        sticky="ew", pady=10, padx=10)
        row += 1
        tk.Label(parent, text="Позиция проводника:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.explorer_pos_var = tk.StringVar(value=self.config.get("explorer_position", "left"))
        pf = tk.Frame(parent, bg=VSColorScheme.BG_MEDIUM)
        pf.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        for v, t in (("left", "Слева"), ("right", "Справа")):
            tk.Radiobutton(pf, text=t, variable=self.explorer_pos_var, value=v,
                           bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                           selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)
        row += 1
        tk.Label(parent, text="Позиция консоли:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG
                 ).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.console_pos_var = tk.StringVar(value=self.config.get("console_position", "bottom"))
        pf2 = tk.Frame(parent, bg=VSColorScheme.BG_MEDIUM)
        pf2.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        for v, t in (("bottom", "Снизу"), ("top", "Сверху")):
            tk.Radiobutton(pf2, text=t, variable=self.console_pos_var, value=v,
                           bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                           selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)

    def _create_buttons(self):
        f = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        f.pack(fill=tk.X, padx=20, pady=20)
        tk.Button(f, text="Сохранить", command=self._save, bg=VSColorScheme.BUTTON_BG,
                  fg="white", relief=tk.FLAT, padx=20, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT, padx=5)
        tk.Button(f, text="Отмена", command=self.window.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                  relief=tk.FLAT, padx=20, pady=5,
                  cursor="hand2").pack(side=tk.RIGHT)

    def _save(self):
        self.config["font_family"] = self.font_var.get()
        self.config["font_size"] = self.size_var.get()
        self.config["tab_size"] = self.tab_var.get()
        self.config["sidebar_width"] = self.sidebar_width_var.get()
        self.config["console_height"] = self.console_height_var.get()
        self.config["explorer_position"] = self.explorer_pos_var.get()
        self.config["console_position"] = self.console_pos_var.get()
        self.config["save_scroll_position"] = self.save_scroll_var.get()
        self.config["auto_save"] = self.auto_save_var.get()
        self.config["word_wrap"] = self.wrap_var.get()
        self.config["syntax_highlight"] = self.highlight_var.get()
        self.config["minimap_enabled"] = self.minimap_var.get()
        self.config["show_hidden_files"] = self.hidden_var.get()
        self.callback(self.config)
        self.window.destroy()


# =====================================================================
# DISCORD
# =====================================================================

class DiscordPresence:
    def __init__(self, app):
        self.app = app
        self.client_id = DISCORD_CLIENT_ID
        self.rpc = None
        self.connected = False
        self.thread_running = False
        self.update_thread = None
        self.start_time = time.time()
        self.current_state = "editing"
        if DISCORD_AVAILABLE and Presence is not None:
            try:
                self._connect()
            except Exception as e:
                print(f"❌ Ошибка инициализации Discord: {e}")
                self.connected = False
        else:
            print("ℹ️ Discord функции отключены")

    def _connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            print("✅ Discord Rich Presence подключён")
            self.thread_running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
        except Exception as e:
            print(f"❌ Ошибка подключения к Discord: {e}")
            self.connected = False

    def disconnect(self):
        self.thread_running = False
        if self.rpc:
            try:
                self.rpc.clear()
                time.sleep(0.1)
                self.rpc.close()
            except Exception:
                pass
        self.connected = False
        print("👋 Discord Rich Presence отключён")

    def _update_loop(self):
        while self.thread_running and self.connected:
            try:
                self._update_presence()
                time.sleep(15)
            except Exception as e:
                print(f"Ошибка в update_loop: {e}")
                break
        self.connected = False

    def set_state(self, state):
        self.current_state = state
        self._update_presence()

    def _get_file_info(self):
        if not self.app.current_project or not self.app.current_project.current_tab:
            return "Безымянный", "unknown"
        filename = self.app.current_project.files.get(self.app.current_project.current_tab)
        if not filename:
            return "Безымянный", "unknown"
        name = os.path.basename(filename)
        ext = os.path.splitext(name)[1].lower()
        ext_map = {'.py': 'python', '.js': 'javascript', '.jsx': 'javascript',
                   '.ts': 'javascript', '.tsx': 'javascript', '.html': 'html',
                   '.htm': 'html', '.css': 'css', '.json': 'json',
                   '.md': 'text', '.txt': 'text', '.cpp': 'cpp',
                   '.cs': 'cs', '.c': 'c', '.h': 'holdc'}
        return name, ext_map.get(ext, 'unknown')

    def _update_presence(self):
        if not self.connected or not self.rpc:
            return
        try:
            filename, file_type = self._get_file_info()
            project_name = "Безымянный проект" if not self.app.current_project else self.app.current_project.name
            files_count = len(self.app.current_project.tabs) if self.app.current_project else 0
            state_text = {"editing": "Пишет код...",
                          "running": "Выполняет код",
                          "idle": "Не за компьютером"}.get(self.current_state, "Пишет код...")
            details = f"{filename} • {project_name}"
            buttons = [
                {"label": "RealCode in GitLab", "url": "https://gitlab.com/K1sh-M1sh/RealCode"},
                {"label": "Download RealCode", "url": "https://gitlab.com/K1sh-M1sh/RealCode/-/releases/"}
            ]
            self.rpc.update(state=state_text, details=details, start=self.start_time,
                            large_image="realcode_logo",
                            large_text=f"RealCode v{VERSION}",
                            small_image=file_type if file_type != "unknown" else "file",
                            small_text=file_type.upper() if file_type != "unknown" else "Файл",
                            buttons=buttons, party_size=[files_count, 10])
        except Exception as e:
            print(f"Ошибка обновления Discord: {e}")
            self.connected = False


# =====================================================================
# ОБНОВЛЕНИЯ
# =====================================================================

class UpdateChecker:
    def __init__(self, app):
        self.app = app
        self.current_version = VERSION
        self.update_url = GITHUB_VERSION_URL
        self.update_info = None
        self.update_available = False
        self.update_dialog = None
        self.progress_bar = None
        self.status_label = None
        self.progress_frame = None

    def check_for_updates(self, silent=False):
        try:
            import urllib.request
            import ssl
            import json as _json
            from packaging import version as vparse

            api_url = "https://api.github.com/repos/Kish-Mish122/RealCode/releases/latest"
            context = ssl._create_unverified_context()
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'RealCode Updater',
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {GITHUB_TOKEN}'
            })
            print("🔍 Просмотр обновлений...")
            with urllib.request.urlopen(req, context=context, timeout=8) as response:
                data = response.read().decode('utf-8')
                release_info = _json.loads(data)

            latest_tag = release_info.get('tag_name', '')
            match = re.search(r'(\d+(?:\.\d+)+)', latest_tag)
            if match:
                latest_version_str = match.group(1)
            else:
                latest_version_str = latest_tag.lstrip('v').lstrip('.')
                if not latest_version_str:
                    raise ValueError("Не удалось извлечь версию из тега")

            download_url = None
            os_type = get_os_type()
            print(f"🔍 Поиск файла для {os_type}...")
            for asset in release_info.get('assets', []):
                an = asset['name'].lower()
                if os_type == 'windows' and an.endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
                elif os_type == 'linux':
                    if an.endswith('.appimage') or 'linux' in an:
                        download_url = asset['browser_download_url']
                        break
                    elif not an.endswith(('.exe', '.dmg', '.appimage')):
                        download_url = asset['browser_download_url']
                        break
                elif os_type == 'macos':
                    if an.endswith(('.dmg', '.app')):
                        download_url = asset['browser_download_url']
                        break
            if not download_url:
                for asset in release_info.get('assets', []):
                    n = asset['name'].lower()
                    if 'source' not in n and 'src' not in n:
                        download_url = asset['browser_download_url']
                        break
            if not download_url:
                raise ValueError(f"Не найден файл для {os_type} в релизе")

            latest = vparse.parse(latest_version_str)
            current = vparse.parse(str(self.current_version))
            self.update_available = latest > current
            self.update_info = {
                'latest_version': latest_version_str,
                'download_url': download_url,
                'update_message': release_info.get('name', f'Доступна новая версия {latest_version_str}'),
                'release_notes': release_info.get('body', '')
            }
            if self.update_available:
                print(f"✅ Доступно обновление! {current} -> {latest}")
                if not silent:
                    self.app.root.after(0, self._show_update_dialog)
                return True
            else:
                if not silent:
                    self.app.log("✅ Установлена последняя версия RealCode")
                return False
        except Exception as e:
            print(f"❌ Ошибка проверки обновлений: {e}")
            if not silent:
                self.app.log(f"⚠️ Не удалось проверить обновления: {e}")
            return False

    def _show_update_dialog(self):
        if not isinstance(self.update_info, dict):
            return
        ui = get_default_ui_font()
        self.update_dialog = tk.Toplevel(self.app.root)
        self.update_dialog.title("Доступно обновление RealCode")
        self.update_dialog.geometry("650x540")
        self.update_dialog.configure(bg=VSColorScheme.BG_MEDIUM)
        self.update_dialog.transient(self.app.root)
        self.update_dialog.resizable(False, False)
        self.update_dialog.update_idletasks()
        x = (self.update_dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.update_dialog.winfo_screenheight() // 2) - (540 // 2)
        self.update_dialog.geometry(f'+{x}+{y}')

        latest = self.update_info.get('latest_version', 'неизвестна')
        tf = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        tf.pack(pady=(30, 10))
        tk.Label(tf, text="🔄", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.ACCENT,
                 font=(ui, 48)).pack(side=tk.LEFT, padx=10)
        tk.Label(tf, text=f"Пора обновляться! Новая версия RealCode {latest}",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 14, "bold"), wraplength=400,
                 justify="center").pack(side=tk.LEFT, padx=10)

        vf = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_LIGHT, padx=20, pady=15)
        vf.pack(fill=tk.X, padx=30, pady=10)
        cf = tk.Frame(vf, bg=VSColorScheme.BG_LIGHT)
        cf.pack(fill=tk.X, pady=2)
        tk.Label(cf, text="Текущая версия:", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.FG_LIGHT, font=(ui, 10)).pack(side=tk.LEFT)
        tk.Label(cf, text=f"  {self.current_version}", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.FG, font=(ui, 10, "bold")).pack(side=tk.LEFT)
        nf = tk.Frame(vf, bg=VSColorScheme.BG_LIGHT)
        nf.pack(fill=tk.X, pady=2)
        tk.Label(nf, text="Новая версия:  ", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.ACCENT, font=(ui, 10)).pack(side=tk.LEFT)
        tk.Label(nf, text=f"{latest}", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.ACCENT, font=(ui, 12, "bold")).pack(side=tk.LEFT)

        msg = self.update_info.get('update_message',
                                   f"Новая версия RealCode {latest} с улучшениями!")
        tk.Label(self.update_dialog, text=msg, bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(ui, 11), wraplength=500,
                 justify="center").pack(pady=15, padx=30)

        if 'release_notes' in self.update_info:
            notes_f = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_LIGHT,
                               padx=15, pady=15)
            notes_f.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
            tk.Label(notes_f, text="Что обновилось:", bg=VSColorScheme.BG_LIGHT,
                     fg=VSColorScheme.FG, font=(ui, 11, "bold")).pack(anchor="w", pady=(0, 5))
            notes_t = tk.Text(notes_f, height=6, bg=VSColorScheme.BG_LIGHT,
                              fg=VSColorScheme.FG_LIGHT, font=(ui, 10),
                              wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
            notes_t.pack(fill=tk.BOTH, expand=True)
            notes_t.insert("1.0", self.update_info['release_notes'])
            notes_t.config(state=tk.DISABLED)

        self.progress_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        self.progress_frame.pack(fill=tk.X, padx=30, pady=10)
        self.progress_frame.pack_forget()
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        self.status_label = tk.Label(self.progress_frame, text="",
                                     bg=VSColorScheme.BG_MEDIUM,
                                     fg=VSColorScheme.FG_LIGHT, font=(ui, 9))
        self.status_label.pack()

        bf = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(pady=20)
        tk.Button(bf, text="Обновиться", command=self._start_update,
                  bg=VSColorScheme.ACCENT, fg="white", relief=tk.FLAT,
                  padx=25, pady=8, font=(ui, 11, "bold"),
                  cursor="hand2").pack(side=tk.LEFT, padx=10)
        tk.Button(bf, text="Напомнить позже", command=self.update_dialog.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                  relief=tk.FLAT, padx=25, pady=8, font=(ui, 11),
                  cursor="hand2").pack(side=tk.LEFT, padx=10)
        tk.Label(self.update_dialog, text="При завершении работы RealCode будет обновлён",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.PINNED,
                 font=(ui, 9, "italic")).pack(pady=(10, 5))

    def _start_update(self):
        if not isinstance(self.update_info, dict):
            return
        for w in self.update_dialog.winfo_children():
            if w == self.progress_frame:
                continue
            try:
                w.pack_forget()
            except Exception:
                pass
        self.progress_frame.pack(fill=tk.X, padx=30, pady=20)
        self.status_label.config(text="Подготовка...")
        threading.Thread(target=self._download_and_install, daemon=True).start()

    def _download_and_install(self):
        try:
            download_url = self.update_info.get('download_url')
            if not download_url:
                self._show_error("Ссылка для скачивания не найдена")
                return
            os_type = get_os_type()
            print(f"📥 Скачивание для {os_type}...")
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                download_path = (current_exe.replace('.exe', '.new.exe')
                                 if os_type == 'windows' else current_exe + '.new')
            else:
                download_path = os.path.join(os.getcwd(), f'RealCode-{os_type}.new')

            self._update_status("Загрузка обновления...", 10)
            import urllib.request
            import ssl
            ctx = ssl._create_unverified_context()

            def report(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(int(block_num * block_size * 100 / total_size), 99)
                    if self.update_dialog and self.update_dialog.winfo_exists():
                        self.update_dialog.after(0, lambda: self._update_progress(percent))

            urllib.request.urlretrieve(download_url, download_path, reporthook=report)
            if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
                self._show_error("Скачанный файл повреждён или пустой")
                return
            self._update_status("Установка обновления...", 100)
            time.sleep(0.5)
            if os_type == 'windows':
                self._install_windows_update(download_path)
            elif os_type in ('linux', 'macos'):
                self._install_unix_update(download_path, macos=(os_type == 'macos'))
        except Exception as e:
            self._show_error(f"Ошибка обновления:\n{e}")

    def _update_progress(self, value):
        if self.progress_bar:
            self.progress_bar['value'] = value

    def _update_status(self, text, progress=None):
        if self.status_label and self.status_label.winfo_exists():
            self.status_label.config(text=text)
        if progress is not None:
            self._update_progress(progress)

    def _show_error(self, message):
        if self.update_dialog and self.update_dialog.winfo_exists():
            self.update_dialog.after(0, self.update_dialog.destroy)
        self.app.root.after(0, lambda: messagebox.showerror("Ошибка обновления", message))

    def _install_windows_update(self, download_path):
        current_exe = sys.executable
        bat_path = os.path.join(os.path.dirname(current_exe), "update.bat")
        dl_name = os.path.basename(download_path)
        exe_name = os.path.basename(current_exe)
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f"""@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Обновление RealCode...
timeout /t 2 /nobreak >nul
:loop
taskkill /f /im RealCode.exe 2>nul
timeout /t 1 /nobreak >nul
copy /y "{dl_name}" "{exe_name}" >nul
if %errorlevel% neq 0 goto loop
del /f /q "{dl_name}"
start "" "{exe_name}"
del /f /q "%~f0"
""")
        if self.update_dialog and self.update_dialog.winfo_exists():
            self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление загружено на диск!",
                                       "Обновление загружено успешно! Установить сейчас?")
        if response:
            try:
                os.startfile(bat_path)  # type: ignore[attr-defined]
            except Exception:
                subprocess.Popen(['cmd', '/c', 'start', '', bat_path])
            self.app.root.after(100, self.app.on_closing)

    def _install_unix_update(self, download_path, macos=False):
        current_exe = sys.executable
        try:
            os.chmod(download_path, 0o755)
        except Exception as e:
            print(f"⚠️ Не удалось установить права: {e}")
        script_path = os.path.join(os.path.dirname(current_exe), "update.sh")
        dl_name = os.path.basename(download_path)
        exe_name = os.path.basename(current_exe)
        launch = f'open "./{exe_name}"' if macos else f'"./{exe_name}" &'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
cd "$(dirname "$0")"
echo "Обновление RealCode..."
sleep 2
pkill -f "{exe_name}" 2>/dev/null || true
sleep 1
cp "{dl_name}" "{exe_name}"
chmod +x "{exe_name}"
rm -f "{dl_name}"
{launch}
rm -f "$0"
""")
        try:
            os.chmod(script_path, 0o755)
        except Exception as e:
            print(f"⚠️ Не удалось сделать скрипт исполняемым: {e}")
        if self.update_dialog and self.update_dialog.winfo_exists():
            self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление загружено!",
                                       "Обновление загружено успешно! Установить сейчас?")
        if response:
            try:
                subprocess.Popen(['bash', script_path],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            except Exception as e:
                messagebox.showerror("Ошибка",
                                     f"Не удалось запустить скрипт обновления:\n{e}")
                return
            self.app.root.after(100, self.app.on_closing)


# =====================================================================
# ЛИНТЕР
# =====================================================================

class Linter:
    def __init__(self, text_widget, app):
        self.text = text_widget
        self.app = app
        self.messages = []
        self.ignored_messages = set()
        self.running = False
        self.after_id = None
        self._load_ignored()

    def _load_ignored(self):
        if self.app.current_project:
            ignored = self.app.current_project.state.get('ignored_lint', [])
            self.ignored_messages = set(tuple(x) for x in ignored)

    def _save_ignored(self):
        if self.app.current_project:
            self.app.current_project.state['ignored_lint'] = [list(x) for x in self.ignored_messages]
            self.app.current_project.save_state()

    def schedule_lint(self, delay=800):
        if self.after_id:
            self.app.root.after_cancel(self.after_id)
        self.after_id = self.app.root.after(delay, self._start_lint)

    def _start_lint(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._lint_thread, daemon=True).start()

    def _lint_thread(self):
        try:
            code = self.text.get("1.0", tk.END)
            messages = []
            lang = 'python'
            if self.app.current_project and self.app.current_project.current_tab:
                filename = self.app.current_project.files.get(self.app.current_project.current_tab)
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    ext_map = {'.py': 'python', '.c': 'c', '.cpp': 'cpp', '.cxx': 'cpp',
                               '.cc': 'cpp', '.cs': 'csharp', '.hc': 'holyc', '.holyc': 'holyc'}
                    lang = ext_map.get(ext, 'python')
            if lang == 'python':
                messages = self._lint_python(code)
            elif lang in ('c', 'cpp'):
                messages = self._lint_with_clang(code, lang)
            elif lang == 'csharp':
                messages = self._lint_with_csc(code)
            elif lang == 'holyc':
                messages = self._lint_holyc_basic(code)
            filtered = [m for m in messages if (m.code, m.line, m.message) not in self.ignored_messages]
            self.app.root.after(0, self._apply_lint_results, filtered)
        except Exception as e:
            print(f"Lint thread error: {e}")
        finally:
            self.running = False

    def _lint_python(self, code):
        messages = []
        if pyflakes is not None:
            try:
                import contextlib
                with contextlib.redirect_stdout(StringIO()) as out:
                    pyflakes.api.check(code, filename='<string>')
                    out_text = out.getvalue()
                for line in out_text.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            ln, col = int(parts[1]), int(parts[2])
                            msg = parts[3].strip()
                            cm = re.search(r'([A-Z]\d+)\s+(.*)', msg)
                            code_str = cm.group(1) if cm else 'F?'
                            msg_text = cm.group(2) if cm else msg
                            messages.append(LintMessage(ln, col, msg_text, code_str,
                                                        'warning', 'pyflakes'))
                        except Exception:
                            pass
            except Exception:
                pass
        if pycodestyle is not None:
            try:
                import contextlib
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                                 delete=False, encoding='utf-8') as f:
                    f.write(code)
                    tmp = f.name
                with contextlib.redirect_stdout(StringIO()) as out:
                    pycodestyle.StyleGuide().check_files([tmp])
                    out_text = out.getvalue()
                os.unlink(tmp)
                ignored_codes = {'E501', 'E225', 'E302', 'E303'}
                for line in out_text.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            ln, col = int(parts[1]), int(parts[2])
                            rest = parts[3].strip()
                            cm = re.match(r'([A-Z]\d+)\s+(.*)', rest)
                            code_str = cm.group(1) if cm else 'E?'
                            msg_text = cm.group(2) if cm else rest
                            if code_str in ignored_codes:
                                continue
                            messages.append(LintMessage(ln, col, msg_text, code_str,
                                                        'warning', 'pep8'))
                        except Exception:
                            pass
            except Exception:
                pass
        return messages

    def _lint_with_clang(self, code, lang):
        messages = []
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp',
                                             delete=False, encoding='utf-8') as f:
                f.write(code)
                tmp = f.name
            clang = shutil.which('clang')
            if not clang:
                return messages
            cmd = [clang, '-fsyntax-only', '-fno-caret-diagnostics',
                   '-x', 'c' if lang == 'c' else 'c++', tmp]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            for line in result.stderr.splitlines():
                m = re.match(r'.+?:(\d+):(\d+):\s*(error|warning):\s*(.*)', line)
                if m:
                    cm = re.search(r'\[(.*?)\]', m.group(4))
                    messages.append(LintMessage(
                        int(m.group(1)), int(m.group(2)), m.group(4).strip(),
                        cm.group(1) if cm else 'C?',
                        'error' if m.group(3) == 'error' else 'warning', 'clang'))
        except Exception as e:
            self.app.log(f"⚠️ Clang ошибка: {e}")
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
        return messages

    def _lint_with_csc(self, code):
        messages = []
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cs',
                                             delete=False, encoding='utf-8') as f:
                f.write(code)
                tmp = f.name
            csc = self._find_csc()
            if not csc:
                self.app.log("⚠️ C# компилятор не найден.")
                return []
            cmd = [csc, '/nologo', '/target:module', '/nowarn:1701,1702', tmp]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    encoding='cp866', errors='ignore')
            out = result.stderr or result.stdout
            for line in out.splitlines():
                m = re.match(r'.+?\((\d+),(\d+)\):\s*(error|warning)\s+(\w+):\s*(.*)', line)
                if m:
                    messages.append(LintMessage(
                        int(m.group(1)), int(m.group(2)), m.group(5).strip(),
                        m.group(4), 'error' if m.group(3) == 'error' else 'warning', 'csc'))
        except Exception as e:
            self.app.log(f"⚠️ C# ошибка: {e}")
        finally:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
        return messages

    def _find_csc(self):
        csc = shutil.which('csc.exe') or shutil.which('csc')
        if csc:
            return csc
        if not is_windows():
            return None
        for p in (r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319",
                  r"C:\Windows\Microsoft.NET\Framework\v4.0.30319"):
            c = os.path.join(p, 'csc.exe')
            if os.path.exists(c):
                return c
        root = os.environ.get('DOTNET_ROOT')
        if root:
            sdk = os.path.join(root, 'sdk')
            if os.path.exists(sdk):
                for sd in glob.glob(os.path.join(sdk, '*')):
                    for sub in ('Roslyn/bincore', 'Roslyn/bin'):
                        c = os.path.join(sd, sub, 'csc.exe')
                        if os.path.exists(c):
                            return c
        return None

    def _lint_holyc_basic(self, code):
        messages = []
        lines = code.splitlines()
        ob = op = obr = 0
        in_str = in_cmt = False
        for i, line in enumerate(lines, start=1):
            j = 0
            while j < len(line):
                ch = line[j]
                if in_cmt:
                    if ch == '*' and j + 1 < len(line) and line[j + 1] == '/':
                        in_cmt = False
                        j += 2
                        continue
                    j += 1
                    continue
                if ch == '/' and j + 1 < len(line):
                    if line[j + 1] == '/':
                        break
                    if line[j + 1] == '*':
                        in_cmt = True
                        j += 2
                        continue
                if in_str:
                    if ch == '"' and (j == 0 or line[j - 1] != '\\'):
                        in_str = False
                    j += 1
                    continue
                if ch == '"':
                    in_str = True
                    j += 1
                    continue
                if ch == '{':
                    ob += 1
                elif ch == '}':
                    ob -= 1
                elif ch == '(':
                    op += 1
                elif ch == ')':
                    op -= 1
                elif ch == '[':
                    obr += 1
                elif ch == ']':
                    obr -= 1
                j += 1
            s = line.strip()
            if (s and not s.endswith(';') and not s.endswith('{') and not s.endswith('}')
                    and not (s.startswith('//') or s.startswith('/*')
                             or s.startswith('*') or s.startswith('#'))):
                messages.append(LintMessage(i, len(line) + 1,
                                            "Возможно, отсутствует точка с запятой",
                                            'H004', 'warning', 'holyc'))
        if ob != 0:
            messages.append(LintMessage(1, 1, f"Несбалансированные фигурные скобки: {ob}",
                                        'H001', 'error', 'holyc'))
        if op != 0:
            messages.append(LintMessage(1, 1, f"Несбалансированные круглые скобки: {op}",
                                        'H002', 'error', 'holyc'))
        if obr != 0:
            messages.append(LintMessage(1, 1, f"Несбалансированные квадратные скобки: {obr}",
                                        'H003', 'error', 'holyc'))
        return messages

    def _apply_lint_results(self, messages):
        self.text.tag_remove("lint_error", "1.0", tk.END)
        self.text.tag_remove("lint_warning", "1.0", tk.END)
        self.messages = messages
        for msg in messages:
            tag = "lint_error" if msg.level == 'error' else "lint_warning"
            self.text.tag_add(tag, f"{msg.line}.0", f"{msg.line}.end")
        self.text.tag_config("lint_error", underline=True, foreground="red")
        self.text.tag_config("lint_warning", underline=True, foreground="orange")
        if self.app.line_numbers:
            self.app.line_numbers.update_numbers()
        errors = len([m for m in messages if m.level == 'error'])
        warnings = len([m for m in messages if m.level == 'warning'])
        self.app.status_label.config(text=f"Ошибок: {errors}, Предупреждений: {warnings}")

    def get_messages_at_line(self, line):
        return [m for m in self.messages if m.line == line]

    def ignore_message(self, msg):
        self.ignored_messages.add((msg.code, msg.line, msg.message))
        self._save_ignored()
        self._start_lint()


# =====================================================================
# GIT ДИАЛОГИ
# =====================================================================

class GitCommitDialog:
    """Окно коммита: выбор файлов + сообщение."""
    def __init__(self, parent, app, git, files):
        self.parent = parent
        self.app = app
        self.git = git
        self.files = files
        self.checked = {f.path: True for f in files}
        self._show()

    def _status_label(self, s: str) -> str:
        return {
            'M': 'Редактирован', 'MM': 'Редактирован', 'A': 'Новый',
            'AM': 'Новый+', 'D': 'Удалён', 'R': 'Переимен.',
            '??': 'Не отслеж.', 'C': 'Копия',
        }.get(s, s)

    def _show(self):
        ui = get_default_ui_font()
        self.window = tk.Toplevel(self.parent)
        self.window.title("Git: Коммит")
        self.window.geometry("640x620")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)

        tk.Label(self.window, text="Файлы для коммита:",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 11, "bold")).pack(anchor="w", padx=15, pady=(15, 5))

        tree_frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        cols = ("check", "status", "file")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        self.tree.heading("check", text="✓")
        self.tree.heading("status", text="Статус")
        self.tree.heading("file", text="Файл")
        self.tree.column("check", width=40, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("file", width=430)
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for f in self.files:
            self.tree.insert("", "end",
                             values=("☑", self._status_label(f.status), f.path),
                             tags=(f.path,))
        self.tree.bind("<Button-1>", self._on_click)

        tk.Label(self.window, text="Сообщение коммита:",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 10)).pack(anchor="w", padx=15, pady=(15, 5))
        self.msg = tk.Text(self.window, height=4, bg=VSColorScheme.BG_LIGHT,
                           fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG,
                           font=(ui, 10), relief=tk.FLAT, padx=5, pady=5)
        self.msg.pack(fill=tk.X, padx=15)
        self.msg.focus_set()

        bf = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(pady=15)
        tk.Button(bf, text="Закоммитить", command=self._commit,
                  bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT,
                  padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Отмена", command=self.window.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT,
                  padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def _on_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = list(self.tree.item(item, "values"))
        path = values[2]
        self.checked[path] = not self.checked.get(path, True)
        values[0] = "☑" if self.checked[path] else "☐"
        self.tree.item(item, values=values)
        return "break"

    def _commit(self):
        message = self.msg.get("1.0", tk.END).strip()
        if not message:
            messagebox.showwarning("Git", "Поле для сообщения о коммите - обязательна!")
            return
        selected = [p for p, c in self.checked.items() if c]
        if not selected:
            messagebox.showwarning("Git", "Выберите хотя бы один файл.")
            return
        self.window.destroy()
        app = self.app
        git = self.git

        def _work():
            return git.commit(message, paths=selected)

        threading.Thread(target=app._git_bg,
                         args=("Commit", _work), daemon=True).start()


class GitLogDialog:
    def __init__(self, parent, commits):
        ui = get_default_ui_font()
        self.window = tk.Toplevel(parent)
        self.window.title("Git: История коммитов")
        self.window.geometry("760x480")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(parent)

        tk.Label(self.window, text="Последние коммиты",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 12, "bold")).pack(pady=10)

        f = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cols = ("hash", "date", "author", "subject")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=18)
        for c, t, w in (("hash", "Хэш", 80), ("date", "Когда", 120),
                        ("author", "Автор", 140), ("subject", "Сообщение", 380)):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for c in commits:
            tree.insert("", "end",
                        values=(c['hash'], c['date'], c['author'], c['subject']))

        tk.Button(self.window, text="Закрыть", command=self.window.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                  relief=tk.FLAT, padx=20, pady=5).pack(pady=10)


# =====================================================================
# BUG REPORT
# =====================================================================

class BugReportDialog:
    def __init__(self, parent, app):
        self._ui = get_default_ui_font()
        self.parent = parent
        self.app = app
        self.window = None
        self._show()

    def _set_grab(self):
        try:
            if self.window and self.window.winfo_exists():
                self.window.grab_set()
                self.window.focus_force()
        except Exception as e:
            print(f"⚠️ Ошибка захвата фокуса: {e}")

    def _show(self):
        ui = self._ui
        self.window = tk.Toplevel(self.parent)
        self.window.title("Создание баг-репорта...")
        self.window.geometry("530x400")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        self.window.resizable(False, False)
        self.window.update_idletasks()
        self.window.after(100, self._set_grab)

        tk.Label(self.window, text="Создать баг-репорт:", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(ui, 14, "bold"), pady=10).pack()
        tk.Label(self.window, text="Ваше имя (необязательно):",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 10)).pack(anchor="w", padx=30, pady=(10, 0))
        self.name_var = tk.StringVar()
        ne = tk.Entry(self.window, textvariable=self.name_var, bg=VSColorScheme.BG_LIGHT,
                      fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG,
                      font=(ui, 10), width=40)
        ne.pack(padx=30, pady=5)
        ne.focus()

        tk.Label(self.window, text="Email (для связи с вами, обязательно):",
                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                 font=(ui, 10)).pack(anchor="w", padx=30, pady=(10, 0))
        self.email_var = tk.StringVar()
        tk.Entry(self.window, textvariable=self.email_var, bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG,
                 font=(ui, 10), width=40).pack(padx=30, pady=5)

        tk.Label(self.window, text="Описание проблемы (как воспроизвести, что не так):", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(ui, 10)).pack(anchor="w", padx=30, pady=(10, 0))
        self.message_text = tk.Text(self.window, bg=VSColorScheme.BG_LIGHT,
                                    fg=VSColorScheme.FG,
                                    insertbackground=VSColorScheme.FG,
                                    font=(ui, 10), height=6, width=40,
                                    relief=tk.FLAT, borderwidth=0, padx=5, pady=5)
        self.message_text.pack(padx=30, pady=5)

        bf = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(pady=20)
        tk.Button(bf, text="Отправить", command=self._on_send_click,
                  bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT,
                  padx=20, pady=5, font=(ui, 10, "bold"),
                  cursor="hand2").pack(side=tk.LEFT, padx=10)
        tk.Button(bf, text="Отмена", command=self.window.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                  relief=tk.FLAT, padx=20, pady=5, font=(ui, 10),
                  cursor="hand2").pack(side=tk.LEFT, padx=10)

    def _on_send_click(self):
        msg = self.message_text.get("1.0", tk.END).strip()
        self._send_report(msg)

    def _send_report(self, message):
        if not message:
            messagebox.showwarning("Описание проблемы", "Опишите вашу проблему подробнее")
            return
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        if email and not self._is_valid_email(email):
            messagebox.showwarning("Невалидный email", "Пожалуйста, введите корректный email.")
            return
        if not email:
            messagebox.showwarning("Требуется email", "Для связи с вами необходим email.")
            return

        data = {"name": name, "email": email, "message": message,
                "_subject": f"Баг-репорт от {name} (RealCode {VERSION})"}

        self.window.config(cursor="watch")
        for ch in self.window.winfo_children():
            if isinstance(ch, tk.Button):
                ch.config(state=tk.DISABLED)
        try:
            r = requests.get(GITHUB_VERSION_MIN, timeout=8)
            r.raise_for_status()
            min_v = r.json()['min_version']
            if version.parse(VERSION_REALCODE) < version.parse(min_v):
                messagebox.showwarning(
                    f"Ваша версия RealCode ({VERSION_REALCODE}) больше не поддерживается!",
                    "Пожалуйста, обновитесь — возможно, этот баг уже исправлен.")
                self._unblock_interface()
            else:
                threading.Thread(target=self._send_thread, args=(data,), daemon=True).start()
        except Exception as e:
            print(f"Ошибка: {e}")
            messagebox.showerror("Ошибка сети", "Не удалось проверить актуальность версии.")
            self._unblock_interface()

    def _unblock_interface(self):
        self.window.config(cursor="")
        for ch in self.window.winfo_children():
            if isinstance(ch, tk.Button):
                ch.config(state=tk.NORMAL)

    def _is_valid_email(self, email):
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

    def _send_thread(self, data):
        try:
            r = requests.post(FORMSPREE_ID, data=data, timeout=10)
            if r.status_code == 200:
                self.window.after(0, self._on_success)
            else:
                self.window.after(0, lambda: self._on_error(
                    f"Ошибка: {r.status_code}: {r.text[:200]}..."))
        except Exception as e:
            self.window.after(0, lambda: self._on_error(str(e)))

    def _on_success(self):
        self.window.destroy()
        messagebox.showinfo("Благодарим за ваш вклад!",
                            "Ваш баг-репорт отправлен! Мы рассмотрим его в ближайшее время.")

    def _on_error(self, error_msg):
        self.window.config(cursor="")
        for ch in self.window.winfo_children():
            if isinstance(ch, tk.Button):
                ch.config(state=tk.NORMAL)
        messagebox.showerror("Ошибка отправки",
                             f"Не удалось отправить сообщение:\n{error_msg}")


# =====================================================================
# ПЛАГИНЫ
# =====================================================================

class PluginManager:
    PLUGINS_URL = PLUGIN_URL_CONF

    def __init__(self, app):
        self.app = app
        self.PLUGINS_DIR = os.path.join(self.app.app_dir, 'plugins')
        self.plugins = []
        self.installed_plugins = self._get_installed()
        os.makedirs(self.PLUGINS_DIR, exist_ok=True)

    def uninstall_plugin(self, plugin_id):
        d = os.path.join(self.PLUGINS_DIR, plugin_id)
        if os.path.exists(d):
            shutil.rmtree(d)
            return True
        return False

    def _get_installed(self):
        if not os.path.exists(self.PLUGINS_DIR):
            return []
        return [d for d in os.listdir(self.PLUGINS_DIR)
                if os.path.isdir(os.path.join(self.PLUGINS_DIR, d))]

    def fetch_plugins(self, callback):
        def _fetch():
            try:
                r = requests.get(self.PLUGINS_URL, timeout=8)
                if r.status_code == 200:
                    plugins = json.loads(r.text)
                    self.plugins = plugins
                    self.app.root.after(0, lambda: callback(plugins, None))
                else:
                    self.app.root.after(0, lambda: callback(None, f"HTTP {r.status_code}"))
            except Exception as e:
                self.app.root.after(0, lambda: callback(None, str(e)))
        threading.Thread(target=_fetch, daemon=True).start()

    def install_plugin(self, plugin, callback):
        def _install():
            try:
                r = requests.get(plugin['download_url'], timeout=30)
                if r.status_code != 200:
                    self.app.root.after(0, lambda: callback(False, f"HTTP {r.status_code}"))
                    return
                plugin_id = plugin['id']
                plugin_dir = os.path.join(self.PLUGINS_DIR, plugin_id)
                with tempfile.TemporaryDirectory() as tmp:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        for n in z.namelist():
                            if '..' in n or os.path.isabs(n):
                                self.app.root.after(0, lambda: callback(False, "Недопустимые пути"))
                                return
                        z.extractall(tmp)
                    main_file = None
                    for root, dirs, files in os.walk(tmp):
                        if 'main.py' in files:
                            main_file = os.path.join(root, 'main.py')
                            break
                    if not main_file:
                        self.app.root.after(0, lambda: callback(False, "Не найден main.py"))
                        return
                    if os.path.exists(plugin_dir):
                        shutil.rmtree(plugin_dir)
                    shutil.copytree(os.path.dirname(main_file), plugin_dir)
                self.app.root.after(0, lambda: callback(True, None))
            except Exception as e:
                self.app.root.after(0, lambda: callback(False, str(e)))
        threading.Thread(target=_install, daemon=True).start()

    def load_plugins(self):
        for plugin_id in self._get_installed():
            path = os.path.join(self.PLUGINS_DIR, plugin_id)
            if not os.path.isdir(path):
                continue
            if path not in sys.path:
                sys.path.insert(0, path)
            try:
                spec = importlib.util.spec_from_file_location(
                    f"{plugin_id}.main", os.path.join(path, "main.py"))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, 'init'):
                        mod.init(self.app)
                        self.app.log(f"✅ Плагин '{plugin_id}' загружен")
                    else:
                        self.app.log(f"⚠️ Плагин '{plugin_id}' без init()")
                else:
                    self.app.log(f"⚠️ Не найден main.py в '{plugin_id}'")
            except Exception as e:
                self.app.log(f"⚠️ Ошибка загрузки '{plugin_id}': {e}")


class PluginMarketplaceDialog:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.plugin_manager = PluginManager(app)
        self.window = None
        self.tree = None
        self.tooltip_window = None
        self._show()

    def _show(self):
        ui = get_default_ui_font()
        self.window = tk.Toplevel(self.parent)
        self.window.title("Маркетплейс плагинов")
        self.window.geometry("700x550")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        self.window.focus_force()
        self.window.lift()
        self.window.resizable(True, True)

        tk.Label(self.window, text="Маркетплейс плагинов", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(ui, 14, "bold"), pady=10).pack()

        f = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(f, columns=("name", "version", "author", "category"),
                                 show="headings", height=15)
        for col, txt, w in (("name", "Название", 200), ("version", "Версия", 70),
                            ("author", "Автор", 150), ("category", "Категория", 100)):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)

        sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        bf = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(fill=tk.X, padx=10, pady=10)
        self.install_btn = tk.Button(bf, text="Установить выбранный",
                                     command=self._install_selected,
                                     bg=VSColorScheme.BUTTON_BG, fg="white",
                                     relief=tk.FLAT, padx=15, pady=5, cursor="hand2")
        self.install_btn.pack(side=tk.LEFT, padx=5)
        self.uninstall_btn = tk.Button(bf, text="Удалить", command=self._uninstall_selected,
                                       bg="#d9534f", fg="white", relief=tk.FLAT,
                                       padx=15, pady=5, cursor="hand2")
        self.uninstall_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Обновить список", command=self._refresh,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT,
                  padx=15, pady=5, cursor="hand2").pack(side=tk.RIGHT, padx=5)
        tk.Button(bf, text="Закрыть", command=self.window.destroy,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT,
                  padx=15, pady=5, cursor="hand2").pack(side=tk.RIGHT, padx=5)

        self.status_label = tk.Label(self.window, text="Загрузка...",
                                     bg=VSColorScheme.STATUS_BG, fg="white",
                                     font=(ui, 9), anchor="w", padx=10)
        self.status_label.pack(fill=tk.X)

        self._refresh()

    def _refresh(self):
        self.status_label.config(text="Загрузка...")
        self.install_btn.config(state=tk.DISABLED)
        self.uninstall_btn.config(state=tk.DISABLED)
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.plugin_manager.fetch_plugins(self._on_plugins_loaded)

    def _on_tree_motion(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self._hide_tooltip()
            return
        tags = self.tree.item(item, "tags")
        if not tags:
            self._hide_tooltip()
            return
        plugin = next((p for p in self.plugin_manager.plugins if p['id'] == tags[0]), None)
        if not plugin or not plugin.get('description'):
            self._hide_tooltip()
            return
        x, y, _, _ = self.tree.bbox(item)
        x += self.tree.winfo_rootx() + 50
        y += self.tree.winfo_rooty() + 20
        self._show_tooltip(plugin['description'], x, y)

    def _on_tree_leave(self, event):
        self._hide_tooltip()

    def _show_tooltip(self, text, x, y):
        self._hide_tooltip()
        self.tooltip_window = tk.Toplevel(self.window)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip_window, text=text, justify=tk.LEFT,
                 background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                 font=(get_default_ui_font(), 9), padx=5, pady=3).pack()

    def _hide_tooltip(self):
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None

    def _on_plugins_loaded(self, plugins, error):
        if error:
            self.status_label.config(text=f"❌ Ошибка: {error}")
            return
        installed = self.plugin_manager._get_installed()
        self.status_label.config(text=f"✅ Загружено {len(plugins)} плагинов")
        for p in plugins:
            mark = " ✅" if p['id'] in installed else ""
            self.tree.insert("", tk.END,
                             values=(p['name'] + mark, p['version'], p['author'], p['category']),
                             tags=(p['id'],))
        self.tree.bind('<Motion>', self._on_tree_motion)
        self.tree.bind('<Leave>', self._on_tree_leave)
        self.install_btn.config(state=tk.NORMAL)
        self.uninstall_btn.config(state=tk.NORMAL)

    def _install_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выберите плагин", "Пожалуйста, выберите плагин.")
            return
        pid = self.tree.item(sel[0], "tags")[0]
        plugin = next((p for p in self.plugin_manager.plugins if p['id'] == pid), None)
        if not plugin:
            return
        if pid in self.plugin_manager._get_installed():
            messagebox.showinfo("Уже установлен", "Этот плагин уже установлен.")
            return
        self.status_label.config(text=f"Установка {plugin['name']}...")
        self.install_btn.config(state=tk.DISABLED)
        self.plugin_manager.install_plugin(plugin, self._on_install_done)

    def _on_install_done(self, success, error):
        self.install_btn.config(state=tk.NORMAL)
        if success:
            self.status_label.config(text="Установлено")
            self._refresh()
            messagebox.showinfo("Плагин установлен!",
                                "Плагин установлен! Перезапустите RealCode.")
        else:
            self.status_label.config(text=f"Ошибка: {error}")
            messagebox.showerror("Ошибка", f"Не удалось установить:\n{error}")

    def _uninstall_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = self.tree.item(sel[0], "tags")[0]
        if pid not in self.plugin_manager._get_installed():
            messagebox.showinfo("Не установлен", "Плагин не установлен.")
            return
        if messagebox.askyesno(f"Удаление {pid}", f"Удалить плагин '{pid}'?"):
            self.plugin_manager.uninstall_plugin(pid)
            self.status_label.config(text=f"Плагин {pid} удалён")
            self._refresh()


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind('<Enter>', self.show_tip)
        self.widget.bind('<Leave>', self.hide_tip)
        self.widget.bind('<Motion>', self.move_tip)

    def show_tip(self, event):
        if self.tip_window or not self.text:
            return
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            x, y = 0, 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                 background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                 font=(get_default_ui_font(), 9)).pack()

    def hide_tip(self, event):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

    def move_tip(self, event):
        if self.tip_window:
            try:
                x, y, _, _ = self.widget.bbox("insert")
            except Exception:
                x, y = 0, 0
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
            self.tip_window.wm_geometry(f"+{x}+{y}")


# =====================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# =====================================================================

class CodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.root.title(APP_NAME)
        set_window_icon(self.root)

        self.current_project = None
        self.projects = {}
        self.discord = None
        self.updater = UpdateChecker(self)
        self.highlighter = None
        self.linter = None
        self._dialog_open = False
        self.git = None

        self.app_dir = get_app_dir()
        ensure_directories(self.app_dir)

        try:
            ttk.Style().theme_use(pick_ttk_theme())
        except Exception:
            pass

        self._highlight_after_id = None
        self._line_numbers_after_id = None
        self._minimap_after_id = None
        self._minimap_scroll_id = None
        self.auto_save_timer = None

        # Флаги для авто-скрытия скроллбара вкладок
        self._tabs_update_scheduled = False
        self._tabs_scrollbar_visible = False

        self.line_numbers = None
        self.minimap = None
        self.editor = None
        self.console = None
        self.welcome_screen = None
        self.editor_scrollbar = None
        self.file_tree = None
        self.folder_label = None
        self.explorer_frame = None
        self.main_paned = None
        self.center_paned = None
        self.editor_area = None
        self.console_area = None
        self.tabs_container = None
        self.tabs_canvas = None
        self.tabs_container_id = None
        self.tabs_scrollbar = None
        self.tab_bar = None
        self.status_label = None
        self.pos_label = None
        self.git_label = None
        self.console_scrollbar = None
        self.editor_container = None
        self.toolbar = None

        self.explorer_visible = self.config.get("sidebar_visible", True)
        self.console_visible = self.config.get("console_visible", True)

        self._setup_window()
        self._create_menu()
        self._create_widgets()
        self._bind_global_shortcuts()

        self._init_discord()

        last_folder = self.config.get("last_opened_folder", ".")
        if os.path.exists(last_folder):
            self.load_project(last_folder)
        else:
            self.load_project_tree()
            self.show_welcome_screen()

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_plugins()

        # Применяем сохранённые размеры панелей после отрисовки окна
        self.root.after(150, self._apply_saved_pane_sizes)
        threading.Thread(target=self._check_updates_thread, daemon=True).start()
        # Автосохранение размеров панелей при движении саша
        self.main_paned.bind("<ButtonRelease-1>", self._autosave_pane_sizes)
        self.center_paned.bind("<ButtonRelease-1>", self._autosave_pane_sizes)
        print("Привет, Юзер! Удачного кодинга!")

    def _is_dialog_focused(self) -> bool:
        try:
            focused = self.root.focus_get()
            if focused is None:
                for w in self.root.winfo_children():
                    if isinstance(w, tk.Toplevel) and w.winfo_viewable():
                        return True
                return False
            return focused.winfo_toplevel() is not self.root
        except Exception:
            return False

    # ------------------------------------------------------------------
    # GIT
    # ------------------------------------------------------------------
    def _init_git_for_project(self):
        if not self.current_project:
            self.git = None
            self._update_git_label()
            return
        self.git = GitManager(self.current_project.path)
        self._refresh_git_status()

    def _refresh_git_status(self):
        self._update_git_label()
        self._apply_git_indicators_to_tree()

    def _update_git_label(self):
        if not hasattr(self, 'git_label') or not self.git_label:
            return
        if not self.git:
            self.git_label.config(text="", bg=VSColorScheme.STATUS_BG)
            return
        if not self.git.is_git_installed():
            self.git_label.config(text="⎇ git не установлен",
                                  bg="#8a2a2a", fg="white")
            return
        if not self.git.is_repo():
            self.git_label.config(text="⎇ не репозиторий",
                                  bg=VSColorScheme.STATUS_BG, fg="white")
            return
        branch = self.git.current_branch() or "?"
        files = self.git.status()
        if not files:
            bg, mark = "#1b5e20", "✓"
        else:
            bg, mark = "#a05a00", f"±{len(files)}"
        self.git_label.config(text=f"⎇ {branch}  {mark}", bg=bg, fg="white")

    def _apply_git_indicators_to_tree(self):
        if not self.file_tree or not self.git or not self.git.is_repo():
            return
        statuses = {s.path.replace('/', os.sep): s for s in self.git.status()}

        def walk(parent=""):
            for item in self.file_tree.get_children(parent):
                values = self.file_tree.item(item, "values")
                if not values:
                    walk(item)
                    continue
                full_path, kind = (values[0], values[1] if len(values) > 1 else "")
                if kind == "file" and self.current_project:
                    try:
                        rel = os.path.relpath(full_path, self.current_project.path)
                    except Exception:
                        rel = full_path
                    gs = statuses.get(rel) or statuses.get(rel.replace(os.sep, '/'))
                    base = os.path.basename(full_path)
                    ext = os.path.splitext(base)[1].lower()
                    icons = {".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨",
                             ".json": "📦", ".md": "📘", ".txt": "📝"}
                    prefix = f"{icons.get(ext, '📄')} "
                    if gs:
                        new_text = f"{prefix}[{gs.marker}] {base}"
                        tag = {
                            'M': 'git_modified', 'A': 'git_added',
                            'U': 'git_untracked', 'D': 'git_deleted',
                            'R': 'git_renamed', 'C': 'git_added',
                        }.get(gs.marker, 'git_modified')
                        self.file_tree.item(item, text=new_text, tags=(tag,))
                    else:
                        self.file_tree.item(item, text=f"{prefix}{base}", tags=())
                walk(item)

        walk()

    def git_init(self):
        self._ensure_project()
        if not self.git:
            self.git = GitManager(self.current_project.path)
        out, err = self.git.init()
        if out is None:
            messagebox.showerror("git init", err)
            return
        self.log("✅ Git-репозиторий инициализирован, теперь можете пользоваться функциями Git!")
        self._refresh_git_status()

    def git_commit(self):
        if not self._require_git_repo():
            return
        files = self.git.status()
        if not files:
            messagebox.showinfo("Git", "Нет изменений для коммита.")
            return
        GitCommitDialog(self.root, self, self.git, files)

    def git_push(self):
        if not self._require_git_repo():
            return
        if not self.git.has_remote():
            url = simpledialog.askstring(
                "Git push",
                "У репозитория нет remote 'origin'.\nВведите URL (или оставьте пустым для отмены):",
                parent=self.root
            )
            if not url:
                return
            out, err = self.git._run(['remote', 'add', 'origin', url])
            if out is None:
                messagebox.showerror("git remote add", err)
                return
        branch = self.git.current_branch() or ""

        def _work():
            out, err = self.git.push(set_upstream=True)
            if out is None:
                out2, err2 = self.git.push(set_upstream=False)
                if out2 is None:
                    return None, err2 or err
            return out, err
        threading.Thread(
            target=self._git_bg,
            args=("Отправка (push)...", _work),
            daemon=True
        ).start()

    def git_pull(self):
        if not self._require_git_repo():
            return
        threading.Thread(
            target=self._git_bg,
            args=("Получение (pull)...", self.git.pull),
            daemon=True
        ).start()

    def git_fetch(self):
        if not self._require_git_repo():
            return
        threading.Thread(
            target=self._git_bg,
            args=("Fetch...", self.git.fetch),
            daemon=True
        ).start()

    def git_log(self):
        if not self._require_git_repo():
            return
        commits = self.git.log(30)
        if not commits:
            messagebox.showinfo("Git", "Пока нет коммитов.")
            return
        GitLogDialog(self.root, commits)

    def git_open_remote(self):
        if not self._require_git_repo():
            return
        url = self.git.remote_url()
        if not url:
            messagebox.showinfo("Git", "У репозитория нет remote 'origin'.")
            return
        if url.startswith("git@") and ":" in url:
            host_part, path = url.split(":", 1)
            host = host_part.replace("git@", "")
            url = f"https://{host}/{path}"
        if url.endswith(".git"):
            url = url[:-4]
        webbrowser.open(url)

    def _require_git_repo(self) -> bool:
        if not self.git or not self.git.is_git_installed():
            messagebox.showerror("Git", "Git не установлен. Установите Git и добавьте в PATH.")
            return False
        if not self.git.is_repo():
            r = messagebox.askyesno("Git", "Папка не является Git-репозиторием.\nИнициализировать?")
            if r:
                self.git_init()
            return False
        return True

    def _git_bg(self, title, func):
        self.log(f"⏳ {title}")
        out, err = func()
        if out is None:
            self.log(f"❌ {title} — {err}")
            self.root.after(0, lambda: messagebox.showerror("Git", f"{title}\n{err}"))
        else:
            self.log(f"✅ {title} — готово")
            if out.strip():
                self.log(out.strip()[:2000])
        self.root.after(0, self._refresh_git_status)

    # ------------------------------------------------------------------
    # ГАРАНТИЯ НАЛИЧИЯ ПРОЕКТА
    # ------------------------------------------------------------------
    def _ensure_project(self):
        if self.current_project is not None:
            return self.current_project
        temp_path = os.path.join(os.path.expanduser("~"), "RealCode_temp")
        os.makedirs(temp_path, exist_ok=True)
        self.load_project(temp_path)
        return self.current_project

    # ------------------------------------------------------------------
    # ПРОКРУТКА ВКЛАДОК (авто-скрытие слайдера)
    # ------------------------------------------------------------------
    def _update_tabs_scrollregion(self, event=None):
        """Планирует проверку переполнения вкладок (debounce)."""
        if getattr(self, '_tabs_update_scheduled', False):
            return
        self._tabs_update_scheduled = True
        self.root.after(30, self._do_update_tabs_scrollregion)

    def _do_update_tabs_scrollregion(self):
        """Проверяет переполнение и показывает/прячет скроллбар."""
        self._tabs_update_scheduled = False
        if not getattr(self, 'tabs_canvas', None) or not self.tabs_canvas.winfo_exists():
            return

        try:
            self.tabs_canvas.update_idletasks()
            self.tabs_canvas.configure(scrollregion=self.tabs_canvas.bbox("all"))
        except Exception:
            return

        try:
            content_w = self.tabs_container.winfo_reqwidth()
            canvas_w = self.tabs_canvas.winfo_width()
        except Exception:
            return

        if canvas_w <= 1:
            self.root.after(50, self._update_tabs_scrollregion)
            return

        need = content_w > canvas_w + 1

        if need == getattr(self, '_tabs_scrollbar_visible', False):
            return

        self._tabs_scrollbar_visible = need

        if need:
            self.tab_bar.configure(height=72)
            self.tabs_canvas.pack_forget()
            self.tabs_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            self.tabs_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.tabs_scrollbar.pack_forget()
            self.tab_bar.configure(height=55)
            try:
                self.tabs_canvas.xview_moveto(0.0)
            except Exception:
                pass

        self._update_tabs_scrollregion()

    def _on_tabs_canvas_configure(self, event):
        try:
            self.tabs_canvas.itemconfigure(self.tabs_container_id, height=50)
        except Exception:
            pass
        self._update_tabs_scrollregion()

    def _scroll_tabs(self, event):
        if getattr(event, 'num', None) == 4:
            delta = -3
        elif getattr(event, 'num', None) == 5:
            delta = 3
        else:
            delta = -3 if getattr(event, 'delta', 0) > 0 else 3
        try:
            self.tabs_canvas.xview_scroll(delta, "units")
        except Exception:
            pass
        return "break"

    def _scroll_active_tab_into_view(self):
        if not getattr(self, 'tabs_canvas', None) or not self.tabs_canvas.winfo_exists():
            return
        if not getattr(self, '_tabs_scrollbar_visible', False):
            return
        if not self.current_project or not self.current_project.current_tab:
            return
        try:
            self.tabs_canvas.update_idletasks()
            tab = self.current_project.current_tab
            if not tab.winfo_exists():
                return
            x = tab.winfo_x()
            w = tab.winfo_width()
            total_w = max(1, self.tabs_container.winfo_reqwidth())
            canvas_w = self.tabs_canvas.winfo_width()
            if canvas_w <= 1 or w <= 1:
                return
            cur_left = self.tabs_canvas.canvasx(0)
            cur_right = cur_left + canvas_w
            if x < cur_left:
                self.tabs_canvas.xview_moveto(x / total_w)
            elif x + w > cur_right:
                new_left = x + w - canvas_w
                self.tabs_canvas.xview_moveto(max(0, new_left) / total_w)
        except Exception as e:
            print(f"Ошибка прокрутки вкладок: {e}")

    # ------------------------------------------------------------------
    # ПАНЕЛИ / ФОКУС
    # ------------------------------------------------------------------
    def _apply_saved_pane_sizes(self):
        try:
            if self.explorer_visible:
                w = self.config.get("sidebar_width", 250)
                self.main_paned.paneconfig(self.explorer_frame, width=w)
            if self.console_visible:
                h = self.config.get("console_height", 200)
                self.center_paned.paneconfig(self.console_area, height=h)
        except Exception as e:
            print(f"⚠️ Не удалось применить размеры панелей: {e}")
        try:
            if self.editor:
                self.editor.focus_set()
        except Exception:
            pass

    def open_marketplace(self):
        PluginMarketplaceDialog(self.root, self)

    def _get_explorer_width(self) -> int:
        """Реальная ширина проводника (без учёта sash)."""
        try:
            if not self.explorer_visible or len(self.main_paned.panes()) < 2:
                return self.config.get("sidebar_width", 250)
            self.main_paned.update_idletasks()
            total = self.main_paned.winfo_width()
            sash_x = self.main_paned.sash_coord(0)[0]
            pos = self.config.get("explorer_position", "left")
            if pos == "left":
                w = sash_x
            else:
                w = total - sash_x
            return w if w > 50 else self.config.get("sidebar_width", 250)
        except Exception:
            return self.config.get("sidebar_width", 250)

    def _autosave_pane_sizes(self, event=None):
        """Автосохранение размеров панелей при движении саша."""
        try:
            self.config["sidebar_width"] = self._get_explorer_width()
            self.config["console_height"] = self._get_console_height()
            # Не пишем конфиг на каждый чих — только после остановки движения
            if getattr(self, '_pane_save_after_id', None):
                self.root.after_cancel(self._pane_save_after_id)
            self._pane_save_after_id = self.root.after(500, save_config, self.config)
        except Exception:
            pass

    def _get_console_height(self) -> int:
        """Реальная высота консоли (без учёта sash)."""
        try:
            if not self.console_visible or len(self.center_paned.panes()) < 2:
                return self.config.get("console_height", 200)
            self.center_paned.update_idletasks()
            total = self.center_paned.winfo_height()
            sash_y = self.center_paned.sash_coord(0)[1]
            pos = self.config.get("console_position", "bottom")
            if pos == "bottom":
                h = total - sash_y
            else:
                h = sash_y
            return h if h > 30 else self.config.get("console_height", 200)
        except Exception:
            return self.config.get("console_height", 200)
        """Реальная ширина проводника (без учёта sash)."""
        try:
            if not self.explorer_visible or len(self.main_paned.panes()) < 2:
                return self.config.get("sidebar_width", 250)
            self.main_paned.update_idletasks()
            total = self.main_paned.winfo_width()
            sash_x = self.main_paned.sash_coord(0)[0]
            pos = self.config.get("explorer_position", "left")
            if pos == "left":
                w = sash_x
            else:
                w = total - sash_x
            return w if w > 50 else self.config.get("sidebar_width", 250)
        except Exception:
            return self.config.get("sidebar_width", 250)
    
    def _get_console_height(self) -> int:
        """Реальная высота консоли (без учёта sash)."""
        try:
            if not self.console_visible or len(self.center_paned.panes()) < 2:
                return self.config.get("console_height", 200)
            self.center_paned.update_idletasks()
            total = self.center_paned.winfo_height()
            sash_y = self.center_paned.sash_coord(0)[1]
            pos = self.config.get("console_position", "bottom")
            if pos == "bottom":
                h = total - sash_y
            else:
                h = sash_y
            return h if h > 30 else self.config.get("console_height", 200)
        except Exception:
            return self.config.get("console_height", 200)

    # ------------------------------------------------------------------
    # СОХРАНЕНИЕ ПОЗИЦИИ ПРОКРУТКИ
    # ------------------------------------------------------------------
    def _save_scroll_position(self):
        if not (self.config.get("save_scroll_position", True)
                and self.current_project and self.current_project.current_tab
                and self.editor):
            return
        try:
            pos = self.editor.yview()[0]
            self.current_project.current_tab.save_scroll_position(pos)
        except Exception:
            pass

    def _safe_yview_moveto(self, pos):
        try:
            if self.editor and self.editor.winfo_exists():
                self.editor.yview_moveto(pos)
        except Exception:
            pass

    def _setup_window(self):
        x = self.config.get("window_x", 100)
        y = self.config.get("window_y", 100)
        width = self.config.get("window_width", 1300)
        height = self.config.get("window_height", 800)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)
        self.root.configure(bg=VSColorScheme.BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        if self.config.get("window_maximized", False):
            self.root.after(50, lambda: maximize_window(self.root))

    def _init_discord(self):
        try:
            self.discord = DiscordPresence(self)
        except Exception as e:
            print(f"Ошибка инициализации Discord: {e}")
            self.discord = None

    def _is_python_file(self, tab):
        if not self.current_project or not tab:
            return False
        fn = self.current_project.files.get(tab)
        return bool(fn and fn.endswith('.py'))

    def _check_updates_thread(self):
        time.sleep(2)
        self.updater.check_for_updates(silent=False)

    def manual_check_updates(self):
        self.updater.check_for_updates(silent=False)

    # ------------------------------------------------------------------
    # ПРОЕКТЫ
    # ------------------------------------------------------------------
    def load_project(self, path):
        if self.current_project:
            self.save_project_state()
            for tab in self.current_project.tabs[:]:
                self._remove_tab_from_ui(tab)
        if path not in self.projects:
            self.projects[path] = Project(path)
        self.current_project = self.projects[path]
        self.config["project_path"] = path
        self.config["last_opened_folder"] = path
        recent = self.config.get("recent_projects", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.config["recent_projects"] = recent[:10]
        save_config(self.config)
        self.folder_label.config(text=os.path.basename(path))
        self.load_project_tree()
        self._restore_project_state()
        self._init_git_for_project()

    def save_project_state(self):
        if not self.current_project:
            return
        if self.editor and self.current_project.current_tab:
            self.current_project.file_contents[self.current_project.current_tab] = \
                self.editor.get("1.0", tk.END)
        self._save_scroll_position()
        self.current_project.save_state()

    def _restore_project_state(self):
        if not self.current_project:
            self.show_welcome_screen()
            return
        last_files = self.current_project.get_last_opened_files()
        pinned = self.current_project.get_pinned_files()
        if last_files:
            for fp in last_files:
                if os.path.exists(fp):
                    try:
                        with open(fp, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.add_new_tab(filename=fp, content=content,
                                         restore=True, pinned=(fp in pinned))
                    except Exception as e:
                        print(f"Ошибка загрузки файла {fp}: {e}")
            self._reorder_tabs()
            last_tab = self.current_project.get_last_active_tab()
            if last_tab:
                for t in self.current_project.tabs:
                    if self.current_project.files.get(t) == last_tab:
                        self.select_tab(t)
                        break
            elif self.current_project.tabs:
                self.select_tab(self.current_project.tabs[0])
            self.hide_welcome_screen()
        else:
            self.show_welcome_screen()

    def _remove_tab_from_ui(self, tab):
        if tab in self.current_project.pinned_tabs:
            self.current_project.pinned_tabs.remove(tab)
        if tab in self.current_project.tabs:
            self.current_project.tabs.remove(tab)
        self.current_project.files.pop(tab, None)
        self.current_project.file_contents.pop(tab, None)
        tab.destroy()

    def _reorder_tabs(self):
        if not self.current_project:
            return
        pinned = [t for t in self.current_project.tabs if t.pinned]
        unpinned = [t for t in self.current_project.tabs if not t.pinned]
        new_order = pinned + unpinned
        if new_order != self.current_project.tabs:
            for t in self.current_project.tabs:
                t.pack_forget()
            for t in new_order:
                t.pack(side=tk.LEFT, padx=2, pady=3)
            self.current_project.tabs = new_order
        self._update_tabs_scrollregion()

    # ------------------------------------------------------------------
    # ВКЛАДКИ
    # ------------------------------------------------------------------
    def add_new_tab(self, filename=None, content="", restore=False, pinned=False):
        self._ensure_project()
        tab_title = Path(filename).name if filename else \
            f"Безымянный {len(self.current_project.tabs) + 1}"
        tab = ModernTab(self.tabs_container, tab_title,
                        self._close_tab, self.select_tab, self._toggle_pin)
        if pinned:
            tab.pinned = True
            tab.pin_btn.configure(fg=VSColorScheme.PINNED, text="📍")
            self.current_project.pinned_tabs.append(tab)
        tab.pack(side=tk.LEFT, padx=2, pady=3)
        self.current_project.tabs.append(tab)
        self.current_project.files[tab] = filename
        self.current_project.file_contents[tab] = content
        if len(self.current_project.tabs) == 1:
            self.hide_welcome_screen()
        if filename and not restore:
            self.current_project.add_to_recent(filename)
        self.select_tab(tab)

        # Привязываем прокрутку колёсиком к самой вкладке
        tab.bind("<MouseWheel>", self._scroll_tabs)
        tab.bind("<Button-4>", self._scroll_tabs)
        tab.bind("<Button-5>", self._scroll_tabs)

        # Обновляем область прокрутки и показываем новую вкладку
        self._update_tabs_scrollregion()
        self.root.after(10, self._scroll_active_tab_into_view)

        if filename:
            self.status_label.config(text=f"Открыт: {filename}")
        return tab

    def select_tab(self, tab):
        if not self.current_project or tab not in self.current_project.tabs:
            return
        # Сохраняем позицию прокрутки старой вкладки
        if (self.current_project.current_tab
                and self.current_project.current_tab in self.current_project.file_contents
                and self.editor):
            self.current_project.file_contents[self.current_project.current_tab] = \
                self.editor.get("1.0", tk.END)
            if self.config.get("save_scroll_position", True):
                self.current_project.current_tab.save_scroll_position(self.editor.yview()[0])

        for t in self.current_project.tabs:
            t.set_active(t == tab)
        self.current_project.current_tab = tab

        if tab in self.current_project.file_contents:
            content = self.current_project.file_contents[tab]
        else:
            fn = self.current_project.files.get(tab)
            if fn and os.path.exists(fn):
                try:
                    with open(fn, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.current_project.file_contents[tab] = content
                except Exception as e:
                    content = ""
                    self.log(f"Ошибка загрузки: {e}")
            else:
                content = ""
                self.current_project.file_contents[tab] = ""

        saved_scroll = 0.0
        if self.config.get("save_scroll_position", True):
            saved_scroll = tab.get_scroll_position() or 0.0

        if self.editor:
            self.editor.edit_modified(False)
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", content.rstrip('\n'))
            self.editor.edit_modified(False)
            tab.set_modified(False)
            self.editor.mark_set(tk.INSERT, "1.0")

            if saved_scroll > 0.0:
                self.editor.after_idle(lambda p=saved_scroll: self._safe_yview_moveto(p))
            else:
                self.editor.see("1.0")

        if self.config.get("syntax_highlight", True) and self.highlighter:
            fn = self.current_project.files.get(tab)
            if fn:
                self.highlighter.set_language(os.path.splitext(fn)[1].lower())
            self.highlighter.highlight_enabled = True
            self.editor.update_idletasks()
            fsize = self.highlighter.get_file_size()
            if fsize <= self.highlighter.FULL_HIGHLIGHT_LIMIT:
                self.highlighter.highlight(force=True)
            else:
                self.highlighter.highlight_visible()
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap.update_minimap()

        # Возвращаем фокус редактору
        try:
            self.editor.focus_set()
        except Exception:
            pass

        if self.discord:
            self.discord._update_presence()
        self._update_tabs_scrollregion()
        self.current_project.save_state()
        if self.linter is not None:
            self.linter.schedule_lint(500)

        self.root.after(10, self._scroll_active_tab_into_view)

    def _close_tab(self, tab):
        if not self.current_project or tab not in self.current_project.tabs:
            return
        if tab.pinned:
            messagebox.showinfo("Закреплённая вкладка",
                                "Эта вкладка закреплена. Открепите её, чтобы закрыть.")
            return
        if tab.modified:
            r = messagebox.askyesnocancel("Сохранение", f"Сохранить изменения в '{tab.title}'?")
            if r is None:
                return
            elif r:
                self.select_tab(tab)
                self.save_file()
        try:
            idx = self.current_project.tabs.index(tab)
        except ValueError:
            idx = 0
        self._remove_tab_from_ui(tab)
        if self.current_project.tabs:
            if idx >= len(self.current_project.tabs):
                idx = len(self.current_project.tabs) - 1
            self.select_tab(self.current_project.tabs[idx])
        else:
            self.current_project.current_tab = None
            self.show_welcome_screen()
            if self.editor:
                self.editor.delete("1.0", tk.END)
        self._update_tabs_scrollregion()
        self.current_project.save_state()

    def _toggle_pin(self, tab):
        if not self.current_project:
            return
        if tab.pinned:
            if tab not in self.current_project.pinned_tabs:
                self.current_project.pinned_tabs.append(tab)
        else:
            if tab in self.current_project.pinned_tabs:
                self.current_project.pinned_tabs.remove(tab)
        self._reorder_tabs()
        self.current_project.save_state()

    def close_current_tab(self, event=None):
        if self.current_project and self.current_project.current_tab:
            self._close_tab(self.current_project.current_tab)
        return "break"

    # ------------------------------------------------------------------
    # ФАЙЛЫ
    # ------------------------------------------------------------------
    def open_file(self):
        self._ensure_project()
        fp = filedialog.askopenfilename(
            initialdir=self.config.get("project_path", "."),
            filetypes=[
                ("Python", "*.py"), ("JavaScript", "*.js"),
                ("HTML", "*.html"), ("CSS", "*.css"),
                ("JSON", "*.json"), ("C++", "*.cpp"),
                ("C#", "*.cs"), ("C", "*.c"),
                ("Shell", "*.sh"), ("Все файлы", "*.*")
            ])
        if fp:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                for t, fn in self.current_project.files.items():
                    if fn == fp:
                        self.select_tab(t)
                        return
                self.add_new_tab(filename=fp, content=content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def save_file(self):
        if not self.current_project or not self.current_project.current_tab:
            return
        fn = self.current_project.files.get(self.current_project.current_tab)
        if not fn:
            self.save_file_as()
            return
        try:
            content = self.editor.get("1.0", tk.END)
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(content)
            self.current_project.file_contents[self.current_project.current_tab] = content
            self.current_project.current_tab.set_modified(False)
            self.status_label.config(text=f"Сохранено: {fn}")
            self.log(f"✅ Сохранено: {Path(fn).name}")
            self.current_project.add_to_recent(fn)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def save_file_as(self):
        if not self.current_project or not self.current_project.current_tab:
            return
        fp = filedialog.asksaveasfilename(
            initialdir=self.config.get("project_path", "."),
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Все файлы", "*.*")])
        if fp:
            self.current_project.files[self.current_project.current_tab] = fp
            self.current_project.current_tab.title_label.config(text=Path(fp).name)
            self.save_file()

    def open_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.config.get("last_opened_folder", "."),
            title="Выберите папку проекта")
        if folder:
            self.load_project(folder)
            self.status_label.config(text=f"Открыта папка: {folder}")

    def load_project_tree(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        root_path = self.config.get("project_path", ".")
        if not os.path.exists(root_path):
            root_path = "."
        self.folder_label.config(text=os.path.basename(root_path))
        root_name = os.path.basename(os.path.abspath(root_path)) or "Проект"
        root_node = self.file_tree.insert("", "end", text=f"📁 {root_name}",
                                          open=True, values=("",))
        self._process_directory(root_path, root_node)
        self._apply_git_indicators_to_tree()

    def _process_directory(self, path, parent):
        try:
            items = os.listdir(path)
            dirs, files = [], []
            show_hidden = self.config.get("show_hidden_files", False)
            for it in items:
                if not show_hidden and it.startswith('.'):
                    continue
                if it in ["__pycache__", ".git", ".idea", "venv", "node_modules"]:
                    continue
                fp = os.path.join(path, it)
                (dirs if os.path.isdir(fp) else files).append(it)
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)
            for it in dirs:
                fp = os.path.join(path, it)
                node = self.file_tree.insert(parent, "end", text=f"📁 {it}",
                                             open=False, values=(fp, "dir"))
                self._process_directory(fp, node)
            icons = {".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨",
                     ".json": "📦", ".md": "📘", ".txt": "📝", ".exe": "⚙️",
                     ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️",
                     ".svg": "🖼️", ".ico": "🖼️", ".gitignore": "🙈", ".env": "🔑",
                     ".pyc": "🐍", ".pyo": "🐍", ".so": "📦", ".dll": "📦",
                     ".dylib": "📦", ".sh": "📜"}
            for it in files:
                fp = os.path.join(path, it)
                ext = os.path.splitext(it)[1].lower()
                self.file_tree.insert(parent, "end",
                                      text=f"{icons.get(ext, '📄')} {it}",
                                      values=(fp, "file"))
        except Exception as e:
            print(f"Ошибка обхода директории {path}: {e}")

    def on_file_double_click(self, event):
        sel = self.file_tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.file_tree.item(item, "values")
        if not vals:
            return
        fp = vals[0]
        if os.path.isdir(fp):
            self.file_tree.item(item, open=not self.file_tree.item(item, "open"))
            return
        if os.path.isfile(fp):
            try:
                self._ensure_project()
                for t, fn in self.current_project.files.items():
                    if fn == fp:
                        self.select_tab(t)
                        return
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.add_new_tab(filename=fp, content=content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def on_tree_open(self, event):
        if not self.current_project:
            return
        expanded = []
        for item in self.file_tree.get_children():
            if self.file_tree.item(item, "open"):
                v = self.file_tree.item(item, "values")
                if v:
                    expanded.append(v[0])
        self.current_project.set_expanded_folders(expanded)

    # ------------------------------------------------------------------
    # РЕДАКТОР
    # ------------------------------------------------------------------
    def on_key_release(self, event):
        if not (self.current_project and self.current_project.current_tab and self.editor):
            return
        self.update_cursor_position()
        if self._line_numbers_after_id:
            self.root.after_cancel(self._line_numbers_after_id)
        self._line_numbers_after_id = self.root.after(200, self._update_line_numbers_delayed)

        if self.config.get("syntax_highlight", True) and self.highlighter:
            fsize = self.highlighter.get_file_size()
            if fsize > 50 * 1024:
                if self._highlight_after_id:
                    self.root.after_cancel(self._highlight_after_id)
                self._highlight_after_id = self.root.after(500, self._delayed_highlight_visible)
            else:
                try:
                    cl = int(self.editor.index(tk.INSERT).split('.')[0])
                except Exception:
                    cl = 1
                self.highlighter.incremental_highlight(cl, cl)
                if self._highlight_after_id:
                    self.root.after_cancel(self._highlight_after_id)
                self._highlight_after_id = self.root.after(600, self._delayed_full_highlight)

        if self.config.get("auto_save", False) and self.current_project.current_tab:
            if self.auto_save_timer:
                self.root.after_cancel(self.auto_save_timer)
            self.auto_save_timer = self.root.after(2000, self._auto_save)

        if self.minimap:
            if self._minimap_after_id:
                self.root.after_cancel(self._minimap_after_id)
            self._minimap_after_id = self.root.after(500, self._update_minimap_delayed)

        if self.config.get("syntax_highlight", True) and self.linter is not None:
            self.linter.schedule_lint(800)

    def _update_line_numbers_delayed(self):
        if self.line_numbers and self.line_numbers.winfo_exists():
            self.line_numbers.update_numbers()
        self._line_numbers_after_id = None

    def _delayed_full_highlight(self):
        if self.highlighter and self.current_project and self.current_project.current_tab:
            if self.highlighter.get_file_size() > self.highlighter.FULL_HIGHLIGHT_LIMIT:
                self.highlighter.highlight_visible()
            else:
                self.highlighter.highlight(force=False)
        self._highlight_after_id = None

    def _delayed_highlight_visible(self):
        if self.highlighter and self.current_project and self.current_project.current_tab:
            self.highlighter.highlight_visible()
        self._highlight_after_id = None

    def _update_minimap_delayed(self):
        if self.minimap:
            self.minimap._schedule_update()
        self._minimap_after_id = None

    def on_text_modified(self, event):
        if not (self.current_project and self.current_project.current_tab and self.editor):
            return
        if self.editor.edit_modified() and self.current_project.current_tab:
            self.current_project.current_tab.set_modified(True)
            self.editor.edit_modified(False)

    def _auto_save(self):
        if (self.current_project and self.current_project.current_tab
                and self.current_project.current_tab.modified):
            self.save_file()

    def update_cursor_position(self, event=None):
        if not self.editor:
            return
        try:
            pos = self.editor.index(tk.INSERT)
            line, col = pos.split('.')
            self.pos_label.config(text=f"Стр {line}, Кол {int(col) + 1}")
        except Exception:
            pass

    def on_editor_scroll(self, *args):
        if self.editor:
            self.editor.yview(*args)
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
            if (self.highlighter and self.config.get("syntax_highlight", True)
                    and self.highlighter.highlight_enabled):
                self.highlighter.highlight_visible()
            self._save_scroll_position()

    def on_editor_scrollbar_move(self, *args):
        if self.editor_scrollbar:
            self.editor_scrollbar.set(*args)
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
            self._save_scroll_position()

    def on_editor_wheel(self, event):
        if self.editor:
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
            self.editor.after_idle(self._save_scroll_position)

    def on_scroll(self, event=None):
        self.line_numbers.update_numbers()
        if self.minimap:
            if self._minimap_scroll_id:
                self.root.after_cancel(self._minimap_scroll_id)
            self._minimap_scroll_id = self.root.after(100, self._update_minimap_after_scroll)
        self._save_scroll_position()

    def _update_minimap_after_scroll(self):
        if self.minimap:
            self.minimap._draw_visible_area()
        self._minimap_scroll_id = None

    # ------------------------------------------------------------------
    # КОНТЕКСТНОЕ МЕНЮ
    # ------------------------------------------------------------------
    def show_editor_context_menu(self, event):
        if not (self.current_project and self.current_project.current_tab):
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Вырезать", command=self.cut)
        menu.add_command(label="Копировать", command=self.copy)
        menu.add_command(label="Вставить", command=self.paste)
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=self.select_all)
        menu.add_separator()
        menu.add_command(label="Найти", command=self.open_find)
        menu.add_command(label="Перейти к строке", command=self.go_to_line)
        if self.linter and self._is_python_file(self.current_project.current_tab):
            try:
                line = int(self.editor.index(f"@{event.x},{event.y}").split('.')[0])
                msgs = self.linter.get_messages_at_line(line)
                if msgs:
                    menu.add_separator()
                    sub = tk.Menu(menu, tearoff=0)
                    menu.add_cascade(label="Предупреждения", menu=sub)
                    for m in msgs[:5]:
                        sub.add_command(label=f"{m.code}: {m.message[:50]}",
                                        command=lambda mm=m: self._ignore_lint_message(mm))
                    if len(msgs) > 1:
                        menu.add_command(label="Игнорировать все в этой строке",
                                         command=lambda ms=msgs: self._ignore_all_in_line(ms))
            except Exception:
                pass
        menu.post(event.x_root, event.y_root)

    def cut(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            self.editor.event_generate("<<Cut>>")
        return "break"

    def copy(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            self.editor.event_generate("<<Copy>>")
        return "break"

    def paste(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            self.editor.event_generate("<<Paste>>")
        return "break"

    def select_all(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            self.editor.tag_add("sel", "1.0", tk.END)
        return "break"

    def _ignore_lint_message(self, msg):
        if self.linter is not None:
            self.linter.ignore_message(msg)

    def _ignore_all_in_line(self, messages):
        for m in messages:
            if self.linter is not None:
                self.linter.ignore_message(m)

    # ------------------------------------------------------------------
    # ЗАПУСК
    # ------------------------------------------------------------------
    def run_code(self):
        if not (self.current_project and self.current_project.current_tab):
            messagebox.showinfo("Информация", "Сначала откройте или создайте файл")
            return
        fn = self.current_project.files.get(self.current_project.current_tab)
        if not fn:
            self.save_file_as()
            fn = self.current_project.files.get(self.current_project.current_tab)
        if fn and os.path.exists(fn):
            self.save_file()
            if self.discord:
                self.discord.set_state("running")
            self.log(f"\n{'=' * 50}")
            self.log(f"▶ Запуск: {Path(fn).name}")
            self.log(f"📅 {datetime.now().strftime('%H:%M:%S')}")
            self.log('=' * 50)
            threading.Thread(target=self._run_thread, args=(fn,), daemon=True).start()

    def _run_thread(self, filename):
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            r = subprocess.run([sys.executable, filename], capture_output=True,
                               text=True, encoding='utf-8', env=env)
            if r.stdout:
                self.log(r.stdout)
            if r.stderr:
                self.log("❌ ОШИБКА:")
                self.log(r.stderr)
            self.log("=" * 50)
            self.log("✅ Завершено")
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
        finally:
            if self.discord:
                self.discord.set_state("editing")

    # ------------------------------------------------------------------
    # ПОИСК
    # ------------------------------------------------------------------
    def open_find(self, event=None):
        if not (self.editor and self.current_project and self.current_project.current_tab):
            return "break"
        d = tk.Toplevel(self.root)
        d.title("Найти")
        d.geometry("400x150")
        d.configure(bg=VSColorScheme.BG_MEDIUM)
        d.transient(self.root)
        d.grab_set()
        d.resizable(False, False)
        tk.Label(d, text="Найти:", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG).pack(pady=(10, 0))
        sv = tk.StringVar()
        e = tk.Entry(d, textvariable=sv, bg=VSColorScheme.BG_LIGHT,
                     fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG, width=40)
        e.pack(pady=5, padx=20)
        e.focus()
        e.bind('<Return>', lambda ev: self._find_text(sv.get()))
        e.bind('<Escape>', lambda ev: d.destroy())
        bf = tk.Frame(d, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(pady=10)
        tk.Button(bf, text="Найти далее", command=lambda: self._find_text(sv.get()),
                  bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT,
                  padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Закрыть", command=d.destroy, bg=VSColorScheme.BG_LIGHT,
                  fg=VSColorScheme.FG, relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        return "break"

    def _find_text(self, text):
        if not text:
            return
        self.editor.tag_remove("search", "1.0", tk.END)
        start = self.editor.index(tk.INSERT)
        pos = self.editor.search(text, start, tk.END)
        if not pos:
            pos = self.editor.search(text, "1.0", tk.END)
        if pos:
            end = f"{pos}+{len(text)}c"
            self.editor.tag_add("search", pos, end)
            self.editor.tag_config("search", background=VSColorScheme.SELECTION)
            self.editor.mark_set(tk.INSERT, end)
            self.editor.see(tk.INSERT)

    def go_to_line(self, event=None):
        if not (self.editor and self.current_project and self.current_project.current_tab):
            return "break"
        try:
            total = int(self.editor.index('end-1c').split('.')[0])
            d = tk.Toplevel(self.root)
            d.title("Перейти к строке")
            d.geometry("300x120")
            d.configure(bg=VSColorScheme.BG_MEDIUM)
            d.transient(self.root)
            d.grab_set()
            d.resizable(False, False)
            tk.Label(d, text=f"Номер строки (1-{total}):",
                     bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG).pack(pady=(10, 5))
            v = tk.StringVar()
            e = tk.Entry(d, textvariable=v, bg=VSColorScheme.BG_LIGHT,
                         fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG, width=10)
            e.pack(pady=5)
            e.focus()

            def on_close():
                try:
                    ln = int(v.get())
                    if 1 <= ln <= total:
                        self.editor.mark_set(tk.INSERT, f"{ln}.0")
                        self.editor.see(tk.INSERT)
                        self.update_cursor_position()
                except ValueError:
                    pass
                d.destroy()

            e.bind('<Return>', lambda ev: on_close())
            e.bind('<Escape>', lambda ev: d.destroy())
            d.protocol("WM_DELETE_WINDOW", on_close)
            tk.Button(d, text="Перейти", command=on_close, bg=VSColorScheme.BUTTON_BG,
                      fg="white", relief=tk.FLAT, padx=15).pack(pady=10)
        except Exception as e:
            print(f"Ошибка перехода к строке: {e}")
        return "break"

    # ------------------------------------------------------------------
    # КОНСОЛЬ / STDOUT
    # ------------------------------------------------------------------
    def log(self, text):
        if not self.console or not self.console.winfo_exists():
            return
        try:
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, text + "\n")
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
            self.console.yview_moveto(1.0)
        except Exception:
            pass

    def write(self, text):
        self.log(text.rstrip())
        return len(text)

    def flush(self):
        pass

    def clear_console(self):
        if self.console and self.console.winfo_exists():
            self.console.config(state=tk.NORMAL)
            self.console.delete("1.0", tk.END)
            self.console.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # ЭКРАН ПРИВЕТСТВИЯ
    # ------------------------------------------------------------------
    def show_welcome_screen(self):
        if self.welcome_screen and self.editor_container:
            self.editor_container.pack_forget()
            self.welcome_screen.show()
            if self.editor:
                self.editor.delete("1.0", tk.END)

    def hide_welcome_screen(self):
        if self.welcome_screen and self.editor_container:
            self.welcome_screen.hide()
            self.editor_container.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # ПАНЕЛИ
    # ------------------------------------------------------------------
    def toggle_explorer(self):
        if self.explorer_visible:
            self.main_paned.forget(self.explorer_frame)
            self.explorer_visible = False
        else:
            pos = self.config.get("explorer_position", "left")
            if pos == "left":
                self.main_paned.insert(0, self.explorer_frame,
                                       width=self.config.get("sidebar_width", 250))
            else:
                self.main_paned.add(self.explorer_frame,
                                    width=self.config.get("sidebar_width", 250))
            self.explorer_visible = True
        self.show_explorer_var.set(self.explorer_visible)
        self.config["sidebar_visible"] = self.explorer_visible

    def toggle_console(self):
        if self.console_visible:
            self.center_paned.forget(self.console_area)
            self.console_visible = False
        else:
            pos = self.config.get("console_position", "bottom")
            if pos == "bottom":
                self.center_paned.add(self.console_area,
                                      height=self.config.get("console_height", 200))
            else:
                self.center_paned.insert(0, self.console_area,
                                         height=self.config.get("console_height", 200))
            self.console_visible = True
        self.show_console_var.set(self.console_visible)
        self.config["console_visible"] = self.console_visible

    def move_explorer(self):
        new_pos = self.explorer_pos_var.get()
        if self.config.get("explorer_position") == new_pos:
            return
        self.config["explorer_position"] = new_pos
        if self.explorer_visible:
            try:
                cw = self.main_paned.sash_coord(0)[0]
            except Exception:
                cw = self.config.get("sidebar_width", 250)
            self.main_paned.forget(self.explorer_frame)
            self.main_paned.forget(self.center_paned)
            if new_pos == "left":
                self.main_paned.add(self.explorer_frame, width=cw)
                self.main_paned.add(self.center_paned)
            else:
                self.main_paned.add(self.center_paned)
                self.main_paned.add(self.explorer_frame, width=cw)

    def move_console(self):
        new_pos = self.console_pos_var.get()
        if self.config.get("console_position") == new_pos:
            return
        self.config["console_position"] = new_pos
        if self.console_visible:
            try:
                ch = self.center_paned.sash_coord(0)[1]
            except Exception:
                ch = self.config.get("console_height", 200)
            self.center_paned.forget(self.editor_area)
            self.center_paned.forget(self.console_area)
            if new_pos == "bottom":
                self.center_paned.add(self.editor_area)
                self.center_paned.add(self.console_area, height=ch)
            else:
                self.center_paned.add(self.console_area, height=ch)
                self.center_paned.add(self.editor_area)

    # ------------------------------------------------------------------
    # НАСТРОЙКИ
    # ------------------------------------------------------------------
    def zoom_in(self):
        self.config["font_size"] = min(24, self.config["font_size"] + 1)
        if self.editor:
            self.editor.config(font=(self.config["font_family"], self.config["font_size"]))

    def zoom_out(self):
        self.config["font_size"] = max(8, self.config["font_size"] - 1)
        if self.editor:
            self.editor.config(font=(self.config["font_family"], self.config["font_size"]))

    def open_settings(self):
        SettingsDialog(self.root, self.config, self.apply_settings)

    def apply_settings(self, new_config):
        old_pos = self.config.get("explorer_position")
        old_cpos = self.config.get("console_position")
        self.config = new_config
        save_config(self.config)

        if self.editor:
            self.editor.config(
                font=(self.config["font_family"], self.config["font_size"]),
                wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
                tabs=(self.config["tab_size"] * 10,))

        if self.config.get("syntax_highlight", True) and self.highlighter:
            tab = self.current_project.current_tab if self.current_project else None
            if tab:
                fn = self.current_project.files.get(tab)
                if fn:
                    self.highlighter.set_language(os.path.splitext(fn)[1].lower())
                self.highlighter.highlight_enabled = True
                self.editor.update_idletasks()
                fsize = self.highlighter.get_file_size()
                if fsize <= self.highlighter.FULL_HIGHLIGHT_LIMIT:
                    self.highlighter.highlight(force=True)
                else:
                    self.highlighter.highlight_visible()

        if self.explorer_visible:
            self.main_paned.paneconfig(self.explorer_frame,
                                       width=self.config.get("sidebar_width", 250))
        if self.console_visible:
            self.center_paned.paneconfig(self.console_area,
                                         height=self.config.get("console_height", 200))

        if old_pos != self.config.get("explorer_position"):
            self.move_explorer()
        if old_cpos != self.config.get("console_position"):
            self.move_console()

        if self.config.get("minimap_enabled", True):
            if self.highlighter and self.highlighter.get_file_size() > 50 * 1024 * 1024:
                if self.minimap:
                    self.minimap.destroy()
                    self.minimap = None
            else:
                if not self.minimap and self.editor:
                    self.minimap = Minimap(self.editor_container, self.editor)
                    self.minimap.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            if self.minimap:
                self.minimap.destroy()
                self.minimap = None

        if self.line_numbers:
            self.line_numbers.update_numbers()
        self.status_label.config(text="Настройки применены")
        self.load_project_tree()

    # ------------------------------------------------------------------
    # TAB / SHIFT+TAB
    # ------------------------------------------------------------------
    def _bind_tab_shortcuts(self):
        if not self.editor:
            return
        try:
            self.editor.bind('<Tab>', self._on_tab_pressed)
            self.editor.bind('<Shift-Tab>', self._on_shift_tab_pressed)
            self.editor.bind('<ISO_Left_Tab>', self._on_shift_tab_pressed)
        except Exception as e:
            print(f"⚠️ Ошибка привязки Tab: {e}")

    def _on_tab_pressed(self, event):
        try:
            if self.editor.tag_ranges('sel'):
                ss = self.editor.index(tk.SEL_FIRST)
                se = self.editor.index(tk.SEL_LAST)
                sl = int(ss.split('.')[0])
                el = int(se.split('.')[0])
                if int(se.split('.')[1]) == 0 and el > sl:
                    el -= 1
                for ln in range(sl, el + 1):
                    self.editor.insert(f"{ln}.0", '    ')
                self.editor.tag_remove(tk.SEL, "1.0", tk.END)
                self.editor.tag_add(tk.SEL, f"{sl}.0", f"{el + 1}.0")
                return "break"
            else:
                self.editor.insert(tk.INSERT, '    ')
                return "break"
        except Exception as e:
            print(f"Tab error: {e}")
            return "break"

    def _on_shift_tab_pressed(self, event):
        try:
            if self.editor.tag_ranges('sel'):
                ss = self.editor.index(tk.SEL_FIRST)
                se = self.editor.index(tk.SEL_LAST)
                sl = int(ss.split('.')[0])
                el = int(se.split('.')[0])
                if int(se.split('.')[1]) == 0 and el > sl:
                    el -= 1
                for ln in range(sl, el + 1):
                    if self.editor.get(f"{ln}.0", f"{ln}.0+4c") == '    ':
                        self.editor.delete(f"{ln}.0", f"{ln}.0+4c")
                self.editor.tag_remove(tk.SEL, "1.0", tk.END)
                self.editor.tag_add(tk.SEL, f"{sl}.0", f"{el + 1}.0")
                return "break"
            else:
                ln = self.editor.index(tk.INSERT).split('.')[0]
                if self.editor.get(f"{ln}.0", f"{ln}.0+4c") == '    ':
                    self.editor.delete(f"{ln}.0", f"{ln}.0+4c")
                return "break"
        except Exception as e:
            print(f"Shift+Tab error: {e}")
            return "break"

    # ------------------------------------------------------------------
    # МЕНЮ
    # ------------------------------------------------------------------
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        fm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=fm)
        fm.add_command(label="Новый (Ctrl+N)", command=self.add_new_tab)
        fm.add_command(label="Открыть (Ctrl+O)", command=self.open_file)
        fm.add_command(label="Открыть папку (Ctrl+K)", command=self.open_folder)
        fm.add_separator()
        fm.add_command(label="Сохранить (Ctrl+S)", command=self.save_file)
        fm.add_command(label="Сохранить как... (Ctrl+Shift+S)", command=self.save_file_as)
        fm.add_separator()
        fm.add_command(label="Выход", command=self.on_closing)

        em = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=em)
        em.add_command(label="Вырезать (Ctrl+X)", command=self.cut)
        em.add_command(label="Копировать (Ctrl+C)", command=self.copy)
        em.add_command(label="Вставить (Ctrl+V)", command=self.paste)
        em.add_separator()
        em.add_command(label="Выделить всё (Ctrl+A)", command=self.select_all)
        em.add_separator()
        em.add_command(label="Найти (Ctrl+F)", command=self.open_find)
        em.add_command(label="Перейти к строке (Ctrl+G)", command=self.go_to_line)

        git_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Git", menu=git_menu)
        git_menu.add_command(label="Обновить статус", command=self._refresh_git_status)
        git_menu.add_separator()
        git_menu.add_command(label="Инициализировать репозиторий", command=self.git_init)
        git_menu.add_separator()
        git_menu.add_command(label="Зафиксировать изменения...", command=self.git_commit)
        git_menu.add_command(label="Получить (Pull)", command=self.git_pull)
        git_menu.add_command(label="Отправить (Push)", command=self.git_push)
        git_menu.add_command(label="Fetch", command=self.git_fetch)
        git_menu.add_separator()
        git_menu.add_command(label="История коммитов", command=self.git_log)
        git_menu.add_command(label="Открыть в браузере", command=self.git_open_remote)

        pm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Плагины", menu=pm)
        pm.add_command(label="Магазин плагинов", command=self.open_marketplace)

        vm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=vm)
        self.show_explorer_var = tk.BooleanVar(value=self.explorer_visible)
        vm.add_checkbutton(label="Показать проводник", variable=self.show_explorer_var,
                           command=self.toggle_explorer)
        self.show_console_var = tk.BooleanVar(value=self.console_visible)
        vm.add_checkbutton(label="Показать консоль", variable=self.show_console_var,
                           command=self.toggle_console)
        vm.add_separator()
        epm = tk.Menu(vm, tearoff=0)
        vm.add_cascade(label="Позиция проводника", menu=epm)
        self.explorer_pos_var = tk.StringVar(value=self.config.get("explorer_position", "left"))
        epm.add_radiobutton(label="Слева", variable=self.explorer_pos_var, value="left",
                            command=self.move_explorer)
        epm.add_radiobutton(label="Справа", variable=self.explorer_pos_var, value="right",
                            command=self.move_explorer)
        cpm = tk.Menu(vm, tearoff=0)
        vm.add_cascade(label="Позиция консоли", menu=cpm)
        self.console_pos_var = tk.StringVar(value=self.config.get("console_position", "bottom"))
        cpm.add_radiobutton(label="Снизу", variable=self.console_pos_var, value="bottom",
                            command=self.move_console)
        cpm.add_radiobutton(label="Сверху", variable=self.console_pos_var, value="top",
                            command=self.move_console)
        vm.add_separator()
        vm.add_command(label="Увеличить шрифт (Ctrl++)", command=self.zoom_in)
        vm.add_command(label="Уменьшить шрифт (Ctrl+-)", command=self.zoom_out)

        rm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Запуск", menu=rm)
        rm.add_command(label="Запустить (F5)", command=self.run_code)
        rm.add_separator()
        rm.add_command(label="Очистить консоль", command=self.clear_console)

        tm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tm)
        tm.add_command(label="Настройки (F1)", command=self.open_settings)

        hm = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=hm)
        hm.add_command(label="Проверить обновления", command=self.manual_check_updates)
        hm.add_command(label="Сообщить о баге", command=self.report_bug)
        hm.add_command(label="О программе", command=self.show_about)

    def report_bug(self):
        BugReportDialog(self.root, self)

    # ------------------------------------------------------------------
    # ГОРЯЧИЕ КЛАВИШИ
    # ------------------------------------------------------------------
    def _bind_global_shortcuts(self):
        """Горячие клавиши с поддержкой русской раскладки.

        ВАЖНО: Ctrl+C/X/V/A НЕ перехватываются — их обрабатывает сам Tk Text,
        что исключает двойную вставку/копирование.
        """
        # Windows: Virtual-Key codes для A-Z
        VK_WINDOWS = {
            65: 'a', 66: 'b', 67: 'c', 68: 'd', 69: 'e', 70: 'f',
            71: 'g', 72: 'h', 73: 'i', 74: 'j', 75: 'k', 76: 'l',
            77: 'm', 78: 'n', 79: 'o', 80: 'p', 81: 'q', 82: 'r',
            83: 's', 84: 't', 85: 'u', 86: 'v', 87: 'w', 88: 'x',
            89: 'y', 90: 'z',
        }
        # Linux/X11: правильные keysym'ы для ЙЦУКЕН
        X11_CYRILLIC = {
            'Cyrillic_shorti': 'q', 'Cyrillic_tse': 'w', 'Cyrillic_u': 'e',
            'Cyrillic_ka': 'r', 'Cyrillic_ie': 't', 'Cyrillic_en': 'y',
            'Cyrillic_ghe': 'u', 'Cyrillic_sha': 'i', 'Cyrillic_shcha': 'o',
            'Cyrillic_ze': 'p',
            'Cyrillic_ef': 'a', 'Cyrillic_yeru': 's', 'Cyrillic_ve': 'd',
            'Cyrillic_a': 'f', 'Cyrillic_pe': 'g', 'Cyrillic_er': 'h',
            'Cyrillic_o': 'j', 'Cyrillic_el': 'k', 'Cyrillic_de': 'l',
            'Cyrillic_ya': 'z', 'Cyrillic_che': 'x', 'Cyrillic_es': 'c',
            'Cyrillic_em': 'v', 'Cyrillic_i': 'b', 'Cyrillic_te': 'n',
            'Cyrillic_softsign': 'm',
        }
        CHAR_CYRILLIC = {
            'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y',
            'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
            'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h',
            'о': 'j', 'л': 'k', 'д': 'l',
            'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
            'ё': '`', 'х': '[', 'ъ': ']', 'ж': ';', 'э': "'", 'б': ',', 'ю': '.',
        }

        def _get_letter(event):
            ks = event.keysym
            if len(ks) == 1 and ks.isalpha() and ord(ks) < 128:
                return ks.lower()
            if ks in X11_CYRILLIC:
                return X11_CYRILLIC[ks]
            if len(ks) == 1 and 'а' <= ks.lower() <= 'я':
                return CHAR_CYRILLIC.get(ks.lower())
            if ks == '??' and is_windows():
                return VK_WINDOWS.get(event.keycode)
            return None

        def handler(event):
            # Не реагируем, если открыт диалог
            if self._dialog_open or self._is_dialog_focused():
                return

            keysym = event.keysym
            state = event.state

            ctrl = (state & 0x4) != 0 or (state & 0x40000) != 0
            shift = (state & 0x1) != 0
            alt = (state & 0x80000) != 0

            letter = _get_letter(event)

            # F5 / F1
            if keysym == 'F5' and not ctrl and not alt and not shift:
                self.run_code()
                return "break"
            if keysym == 'F1' and not ctrl and not alt and not shift:
                self.open_settings()
                return "break"

            # Ctrl+<буква> — только то, что НЕ делает Tk сам
            # (Ctrl+C/X/V/A НЕ перехватываем!)
            if ctrl and letter:
                if letter == 'n':
                    self.add_new_tab(); return "break"
                if letter == 'o':
                    self.open_file(); return "break"
                if letter == 'k':
                    self.open_folder(); return "break"
                if letter == 's':
                    if shift:
                        self.save_file_as()
                    else:
                        self.save_file()
                    return "break"
                if letter == 'f':
                    self.open_find(); return "break"
                if letter == 'g':
                    self.go_to_line(); return "break"

            # Ctrl+Plus / Ctrl+Minus
            if ctrl:
                if keysym in ('plus', 'equal', 'KP_Add'):
                    self.zoom_in(); return "break"
                if keysym in ('minus', 'KP_Subtract'):
                    self.zoom_out(); return "break"

        self.root.bind_all('<Key>', handler)

    def show_about(self):
        about = f"""{APP_NAME} v{VERSION}

Привет, друг! Это K1sh-M1sh!
RealCode разработан на Python с использованием Tkinter.

Возможности:
• Подсветка синтаксиса (Python, C, C++, C#, Go, HolyC)
• Мультипроектная архитектура
• Сохранение закреплённых вкладок
• Discord Rich Presence
• Автоматическое обновление
• Номера строк и линтер
• Миникарта
• Поиск (Ctrl+F) и переход к строке (Ctrl+G)
• Встроенная консоль
• Git-интеграция
• Плагины

Предназначен для лёгких проектов на Python.
Сообщайте о багах: help.k1shm1sh@gmail.com или через Справка -> Сообщить о баге

Кроссплатформенная поддержка: Windows / Linux

© 2026 RealCode
"""
        messagebox.showinfo("О программе", about)

    # ------------------------------------------------------------------
    # ИНТЕРФЕЙС
    # ------------------------------------------------------------------
    def _create_widgets(self):
        self._create_toolbar()
        main = tk.Frame(self.root, bg=VSColorScheme.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)
        self.main_paned = tk.PanedWindow(main, orient=tk.HORIZONTAL,
                                         bg=VSColorScheme.BORDER, sashwidth=5,
                                         sashrelief=tk.FLAT,
                                         sashcursor="sb_h_double_arrow")
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        self._create_explorer()
        self._create_center_panel()
        self._create_status_bar()

        pos = self.config.get("explorer_position", "left")
        if pos == "left":
            self.main_paned.add(self.explorer_frame,
                                width=self.config.get("sidebar_width", 250))
            self.main_paned.add(self.center_paned)
        else:
            self.main_paned.add(self.center_paned)
            self.main_paned.add(self.explorer_frame,
                                width=self.config.get("sidebar_width", 250))

        if self.config.get("console_position", "bottom") == "top":
            self.center_paned.paneconfig(self.editor_area, after=self.console_area)

        self.welcome_screen = WelcomeScreen(self.editor_area, self)

    def _create_toolbar(self):
        ui = get_default_ui_font()
        self.toolbar = tk.Frame(self.root, bg=VSColorScheme.BG_MEDIUM, height=45)
        self.toolbar.pack(fill=tk.X)
        self.toolbar.pack_propagate(False)
        for icon, text, cmd in [
            ("📁", "Открыть файл", self.open_file),
            ("📂", "Открыть папку", self.open_folder),
            ("💾", "Сохранить", self.save_file),
            ("📄", "Новый", self.add_new_tab),
            ("▶", "Запуск", self.run_code),
            ("⚙", "Настройки", self.open_settings),
            ("🔄", "Обновления", self.manual_check_updates),
        ]:
            btn = tk.Label(self.toolbar, text=f"{icon}  {text}",
                           bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                           font=(ui, 9), padx=15, pady=12, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=VSColorScheme.BG_LIGHT))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=VSColorScheme.BG_MEDIUM))
            btn.bind('<Button-1>', lambda e, c=cmd: c())

    def _create_explorer(self):
        ui = get_default_ui_font()
        self.explorer_frame = tk.Frame(self.main_paned, bg=VSColorScheme.BG_MEDIUM)
        header = tk.Frame(self.explorer_frame, bg=VSColorScheme.BG_MEDIUM)
        header.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(header, text="ПРОВОДНИК", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG_LIGHT, font=(ui, 9, "bold")).pack(side=tk.LEFT)
        cb = tk.Label(header, text="✕", bg=VSColorScheme.BG_MEDIUM,
                      fg=VSColorScheme.FG, font=(ui, 10, "bold"),
                      padx=8, cursor="hand2")
        cb.pack(side=tk.RIGHT)
        cb.bind('<Enter>', lambda e: cb.configure(bg=VSColorScheme.ACCENT))
        cb.bind('<Leave>', lambda e: cb.configure(bg=VSColorScheme.BG_MEDIUM))
        cb.bind('<Button-1>', lambda e: self.toggle_explorer())

        self.folder_label = tk.Label(self.explorer_frame,
                                     text=os.path.basename(self.config["project_path"]),
                                     bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                                     font=(ui, 8), wraplength=230)
        self.folder_label.pack(anchor="w", padx=5, pady=(0, 5))

        bf = tk.Frame(self.explorer_frame, bg=VSColorScheme.BG_MEDIUM)
        bf.pack(fill=tk.X, padx=5, pady=5)
        ob = tk.Label(bf, text="📂 Открыть папку", bg=VSColorScheme.BG_LIGHT,
                      fg=VSColorScheme.FG, font=(ui, 9), pady=4, cursor="hand2")
        ob.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ob.bind('<Button-1>', lambda e: self.open_folder())
        rb = tk.Label(bf, text="↻", bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                      font=(ui, 9), width=3, pady=4, cursor="hand2")
        rb.pack(side=tk.RIGHT, padx=(2, 0))
        rb.bind('<Button-1>', lambda e: self.load_project_tree())

        tree_container = tk.Frame(self.explorer_frame, bg=VSColorScheme.BG_MEDIUM)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.file_tree = ttk.Treeview(tree_container, show="tree",
                                      selectmode="browse", height=20)
        style = ttk.Style()
        style.configure("Treeview",
                        background=VSColorScheme.BG_LIGHT,
                        foreground=VSColorScheme.FG,
                        fieldbackground=VSColorScheme.BG_LIGHT,
                        borderwidth=0, rowheight=25)
        style.map("Treeview",
                  background=[("selected", VSColorScheme.SELECTION)],
                  foreground=[("selected", "white")])
        style.configure("Treeview.Heading",
                        background=VSColorScheme.BG_MEDIUM,
                        foreground=VSColorScheme.FG, relief="flat")

        # Скроллбар пакуем ДО дерева, чтобы он был справа
        vsb = ttk.Scrollbar(tree_container, orient=tk.VERTICAL,
                            command=self.file_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_tree.configure(yscrollcommand=vsb.set)

        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_tree_open)

        # Цвета git-маркеров
        self.file_tree.tag_configure('git_modified', foreground='#e5c07b')
        self.file_tree.tag_configure('git_added', foreground='#98c379')
        self.file_tree.tag_configure('git_untracked', foreground='#abb2bf')
        self.file_tree.tag_configure('git_deleted', foreground='#e06c75')
        self.file_tree.tag_configure('git_renamed', foreground='#61afef')

    def _create_center_panel(self):
        self.center_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL,
                                           bg=VSColorScheme.BORDER, sashwidth=5,
                                           sashrelief=tk.FLAT,
                                           sashcursor="sb_v_double_arrow")
        self._create_editor_area()
        self._create_console_area()
        self.center_paned.add(self.editor_area, height=500)
        self.center_paned.add(self.console_area,
                              height=self.config.get("console_height", 200))

    def _create_editor_area(self):
        ui = get_default_ui_font()
        self.editor_area = tk.Frame(self.center_paned, bg=VSColorScheme.BG_DARK)

        # Панель вкладок — высота меняется динамически (55 без слайдера, 72 со слайдером)
        self.tab_bar = tk.Frame(self.editor_area, bg=VSColorScheme.BG_MEDIUM, height=55)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)
        self._tabs_scrollbar_visible = False

        ntb = tk.Label(self.tab_bar, text="+  Добавить вкладку",
                       bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                       font=(ui, 10), padx=20, pady=15, cursor="hand2")
        ntb.pack(side=tk.RIGHT, fill=tk.Y)
        ntb.bind('<Enter>', lambda e: ntb.configure(bg=VSColorScheme.BG_LIGHT))
        ntb.bind('<Leave>', lambda e: ntb.configure(bg=VSColorScheme.BG_MEDIUM))
        ntb.bind('<Button-1>', lambda e: self.add_new_tab())

        tabs_wrapper = tk.Frame(self.tab_bar, bg=VSColorScheme.BG_MEDIUM)
        tabs_wrapper.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tabs_scrollbar = tk.Scrollbar(
            tabs_wrapper, orient=tk.HORIZONTAL,
            bg=VSColorScheme.SCROLLBAR, troughcolor=VSColorScheme.BG_MEDIUM,
            highlightthickness=0, bd=0
        )
        # НЕ пакуем сразу — только когда есть переполнение

        self.tabs_canvas = tk.Canvas(
            tabs_wrapper, bg=VSColorScheme.BG_MEDIUM,
            highlightthickness=0, bd=0, height=50
        )
        self.tabs_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tabs_canvas.configure(xscrollcommand=self.tabs_scrollbar.set)
        self.tabs_scrollbar.configure(command=self.tabs_canvas.xview)

        self.tabs_container = tk.Frame(self.tabs_canvas, bg=VSColorScheme.BG_MEDIUM)
        self.tabs_container_id = self.tabs_canvas.create_window(
            (0, 0), window=self.tabs_container, anchor="nw", height=50
        )

        self.tabs_container.bind("<Configure>", self._update_tabs_scrollregion)
        self.tabs_canvas.bind("<Configure>", self._on_tabs_canvas_configure)

        for w in (self.tabs_canvas, self.tabs_container):
            w.bind("<MouseWheel>", self._scroll_tabs)
            w.bind("<Button-4>", self._scroll_tabs)
            w.bind("<Button-5>", self._scroll_tabs)

        # ─── Редактор ───
        self.editor_container = tk.Frame(self.editor_area, bg=VSColorScheme.BG_DARK)
        self.editor_container.pack(fill=tk.BOTH, expand=True)
        editor_inner = tk.Frame(self.editor_container, bg=VSColorScheme.BG_DARK)
        editor_inner.pack(fill=tk.BOTH, expand=True)

        self.line_numbers = LineNumbers(editor_inner, None, app=self)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.editor = tk.Text(
            editor_inner,
            wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
            font=(self.config["font_family"], self.config["font_size"]),
            bg=VSColorScheme.BG_DARK, fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            selectbackground=VSColorScheme.SELECTION,
            relief=tk.FLAT, borderwidth=0, padx=10, pady=10,
            undo=True, maxundo=100, tabs=(self.config["tab_size"] * 10,))
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._bind_tab_shortcuts()
        self.line_numbers.text_widget = self.editor
        self.line_numbers.update_numbers()

        self.editor_scrollbar = tk.Scrollbar(
            editor_inner, orient=tk.VERTICAL, command=self.on_editor_scroll,
            bg=VSColorScheme.SCROLLBAR, troughcolor=VSColorScheme.BG_DARK, width=12)
        self.editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=self.on_editor_scrollbar_move)

        if self.config.get("minimap_enabled", True):
            self.minimap = Minimap(editor_inner, self.editor)
            self.minimap.pack(side=tk.RIGHT, fill=tk.Y)

        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<<Modified>>', self.on_text_modified)
        self.editor.bind('<MouseWheel>', self.on_editor_wheel)
        self.editor.bind('<Button-4>', self.on_editor_wheel)
        self.editor.bind('<Button-5>', self.on_editor_wheel)
        self.editor.bind('<Button-3>', self.show_editor_context_menu)
        self.editor_scrollbar.bind('<B1-Motion>', self.on_scroll)

        self.highlighter = SyntaxHighlighter(self.editor)
        self.linter = Linter(self.editor, self)

    def _create_console_area(self):
        ui = get_default_ui_font()
        self.console_area = tk.Frame(self.center_paned, bg=VSColorScheme.BG_DARK)
        header = tk.Frame(self.console_area, bg=VSColorScheme.STATUS_BG, height=25)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="КОНСОЛЬ", bg=VSColorScheme.STATUS_BG, fg="white",
                 font=(ui, 9, "bold"), padx=10).pack(side=tk.LEFT)
        cb = tk.Label(header, text="🗑 Очистить", bg=VSColorScheme.STATUS_BG,
                      fg="white", font=(ui, 9), padx=10, cursor="hand2")
        cb.pack(side=tk.RIGHT)
        cb.bind('<Button-1>', lambda e: self.clear_console())
        xb = tk.Label(header, text="✕", bg=VSColorScheme.STATUS_BG, fg="white",
                      font=(ui, 10, "bold"), padx=10, cursor="hand2")
        xb.pack(side=tk.RIGHT)
        xb.bind('<Enter>', lambda e: xb.configure(bg="#e81123"))
        xb.bind('<Leave>', lambda e: xb.configure(bg=VSColorScheme.STATUS_BG))
        xb.bind('<Button-1>', lambda e: self.toggle_console())

        cc = tk.Frame(self.console_area, bg=VSColorScheme.BG_DARK)
        cc.pack(fill=tk.BOTH, expand=True)
        self.console = tk.Text(cc, wrap=tk.WORD, font=(get_default_mono_font(), 10),
                               bg=VSColorScheme.BG_DARK, fg=VSColorScheme.FG_LIGHT,
                               relief=tk.FLAT, borderwidth=0, padx=5, pady=5,
                               state=tk.DISABLED)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console_scrollbar = tk.Scrollbar(
            cc, orient=tk.VERTICAL, command=self.console.yview,
            bg=VSColorScheme.SCROLLBAR, troughcolor=VSColorScheme.BG_DARK, width=12)
        self.console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=self.console_scrollbar.set)

    def _create_status_bar(self):
        ui = get_default_ui_font()
        s = tk.Frame(self.root, bg=VSColorScheme.STATUS_BG, height=25)
        s.pack(side=tk.BOTTOM, fill=tk.X)
        s.pack_propagate(False)
        self.status_label = tk.Label(s, text="Готов", bg=VSColorScheme.STATUS_BG,
                                     fg="white", font=(ui, 9), padx=10)
        self.status_label.pack(side=tk.LEFT)

        self.git_label = tk.Label(
            s, text="", bg=VSColorScheme.STATUS_BG, fg="white",
            font=(ui, 9), padx=10, cursor="hand2"
        )
        self.git_label.pack(side=tk.LEFT, padx=(20, 0))
        self.git_label.bind("<Button-1>", lambda e: self._refresh_git_status())

        self.pos_label = tk.Label(s, text="Стр 1, Кол 1", bg=VSColorScheme.STATUS_BG,
                                  fg="white", font=(ui, 9), padx=10)
        self.pos_label.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # УВЕДОМЛЕНИЯ
    # ------------------------------------------------------------------
    def show_notification(self, message, duration=3000):
        if not self.root.winfo_exists():
            return
        if hasattr(self, '_notification') and self._notification.winfo_exists():
            self._notification.destroy()
        self._notification = tk.Toplevel(self.root)
        self._notification.overrideredirect(True)
        self._notification.configure(bg=VSColorScheme.BG_MEDIUM, relief=tk.RIDGE, bd=2)
        x = self.root.winfo_x() + self.root.winfo_width() - 420
        y = self.root.winfo_y() + self.root.winfo_height() - 80
        self._notification.geometry(f"400x70+{x}+{y}")
        tk.Label(self._notification, text=message, bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG, font=(get_default_ui_font(), 10, "bold"),
                 padx=10, pady=10, wraplength=380, justify="center"
                 ).pack(fill=tk.BOTH, expand=True)
        self._notification.after(duration, self._notification.destroy)

    # ------------------------------------------------------------------
    # ЗАКРЫТИЕ
    # ------------------------------------------------------------------
    def on_closing(self):
        if self.current_project:
            unsaved = [t.title for t in self.current_project.tabs if t.modified]
            if unsaved:
                r = messagebox.askyesnocancel(
                    "Несохранённые изменения",
                    f"Вы не сохранили:\n{', '.join(unsaved)}\n\nСохранить перед выходом?")
                if r is None:
                    return
                elif r:
                    for t in self.current_project.tabs:
                        if t.modified:
                            self.select_tab(t)
                            self.save_file()
            self.save_project_state()

        if self.discord:
            self.discord.disconnect()
            time.sleep(0.2)

        try:
            if self.editor:
                self.editor.focus_set()
        except Exception:
            pass

        self.config["sidebar_visible"] = self.explorer_visible
        self.config["console_visible"] = self.console_visible
        self.config["window_maximized"] = is_window_maximized(self.root)

        if not self.config["window_maximized"]:
            try:
                self.config["window_x"] = self.root.winfo_x()
                self.config["window_y"] = self.root.winfo_y()
                self.config["window_width"] = self.root.winfo_width()
                self.config["window_height"] = self.root.winfo_height()
            except Exception:
                pass

        self.config["sidebar_width"] = self._get_explorer_width()
        self.config["console_height"] = self._get_console_height()

        self.config["last_opened_folder"] = self.config.get("project_path", ".")
        save_config(self.config)

        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass


# =====================================================================
# ТОЧКА ВХОДА
# =====================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()
