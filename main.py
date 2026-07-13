#!/usr/bin/env python3

# main.py - RealCode
# Внимание! Данная версия - бета, тут могут быть не дороботки, баги, вылеты и другие ошибки, мещающие работе RealCode. Пожалуйста, если вы заметите какой-то либо баг в коде, не остовайтесь в стороне.
# Помогите проекту стать лучше. Напишите на help.k1shm1sh@gmail.com с темой "Баги RealCode". Если баг будет существенный, то я вас добавлю как помощников в Справка->О программе.
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
import threading
import queue
from dataclasses import dataclass
from typing import List, Dict, Set
import requests
import threading

from pyflakes import reporter
from pyflakes.api import check
from io import StringIO
from packaging import version

import zipfile
import io
import shutil
from tkinter import ttk

import importlib.util

try:
    if sys.platform == "win32" and sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8') # Это нужно для поддержки русского языка
except (AttributeError, ValueError):
    pass

old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()

def get_os_type():
    """Определяет тип ОС для скачивания обновлений"""
    if sys.platform == 'win32':
        return 'windows'
    elif sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform == 'darwin':
        return 'macos'
    return 'unknown'

def is_linux():
    return sys.platform.startswith('linux')


# Хардкорить токены, ID и другие важные данные, которые как бы нельзя вставлять просто в код - не лучшая идея. Поэтому, советую создать файл config.py и туда вставлять все то, что
# важно для скрипта, но и важно для безопасности

# Также, можно в config.py вставлять то, что упоминается постоянно и чтобы не лазить в коде

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

# ========== КОНСТАНТЫ И НАСТРОЙКИ ==========
APP_NAME = "RealCode"
VERSION = VERSION_REALCODE
CONFIG_FILE = "settings.json"
DISCORD_CLIENT_ID = DISCORD_ID

MIN_REALCODE = MIN_REALCODE_VERSION

def get_app_dir():
    """Возвращает директорию, где находится исполняемый файл (или скрипт)."""
    if getattr(sys, 'frozen', False):
        # Запущено как .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Запущено как скрипт
        return os.path.dirname(os.path.abspath(__file__))

def is_windows():
    return sys.platform == 'win32'

def is_linux():
    return sys.platform.startswith('linux')

@dataclass
class LintMessage:
    line: int
    column: int
    message: str
    code: str       # например, 'F401' для pyflakes, 'E501' для pep8
    level: str      # 'error' или 'warning'
    source: str     # 'pyflakes' или 'pep8'

class StringIOReporter(reporter.Reporter):
    def __init__(self, output):
        self.output = output
    def flake(self, message):
        self.output.write(str(message) + "\n")
    def unexpectedError(self, filename, msg):
        self.output.write(f"{filename}: {msg}\n")

def get_app_dir():
    """Возвращает директорию, где находится исполняемый файл (или скрипт)."""
    if getattr(sys, 'frozen', False):
        # Запущено как .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Запущено как скрипт
        return os.path.dirname(os.path.abspath(__file__))
    
def ensure_directories(app_dir):
    """Создаёт все необходимые папки в директории приложения."""
    dirs = [
        'plugins'          # для плагинов
    ]
    for dir_name in dirs:
        dir_path = os.path.join(app_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Создана папка: {dir_path}")

    # Также создаём системную папку .RLCode (она создаётся проектом, но для уверенности)
    # Это может быть в проекте, но лучше создать в корне приложения (не обязательно)
    # .RLCode создаётся внутри каждого проекта, так что здесь не нужно.


class VSColorScheme:
    """Цветовая схема RealCode в стиле VS Code"""
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
    
    # Синтаксис
    KEYWORD = "#81c784"
    STRING = "#ce9178"
    COMMENT = "#6a9955"
    NUMBER = "#b5cea8"
    FUNCTION = "#dcdcaa"
    CLASS = "#4ec9b0"
    DECORATOR = "#c586c0"
    BUILTIN = "#4ec9b0"


DEFAULT_CONFIG = {
    "font_family": "Consolas",
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

def load_icon(filename, size=(16, 16)):
    """Загружает иконку из папки icons и масштабирует"""
    path = os.path.join("icons", filename)
    if os.path.exists(path):
        try:
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except:
            pass
    return None


# ========== УТИЛИТЫ ==========
def setup_python_paths():
    """Автоматическое добавление всех возможных путей к пакетам Python"""
    added_paths = []
    
    try:
        user_site = site.getusersitepackages()
        if user_site not in sys.path and os.path.exists(user_site):
            sys.path.insert(0, user_site)
            added_paths.append(f"Пользовательский: {user_site}")
    except:
        pass
    
    try:
        system_site = site.getsitepackages()
        for path in system_site:
            if path not in sys.path and os.path.exists(path):
                sys.path.insert(0, path)
                added_paths.append(f"Системный: {path}")
    except:
        pass
    
    # Кроссплатформенные пути
    if sys.platform == 'win32':
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
    else:  # Linux, macOS
        common_paths = [
            os.path.expanduser("~/.local/lib/python3.*/site-packages"),
            "/usr/local/lib/python3.*/dist-packages",
            "/usr/lib/python3.*/dist-packages",
        ]
        # Используем glob для поиска
        import glob
        expanded_paths = []
        for path in common_paths:
            expanded_paths.extend(glob.glob(path))
        common_paths = expanded_paths
    
    for path in common_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            added_paths.append(f"Найденный: {path}")
    
    if added_paths:
        print(f"✅ Добавлено путей: {len(added_paths)}")

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
            json.dump(config, f, indent=4)
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


# ========== ПРОВЕРКА ЗАВИСИМОСТЕЙ ==========
setup_python_paths()

discord_ok, discord_module = check_and_import("pypresence", "pypresence")
DISCORD_AVAILABLE = discord_ok
if DISCORD_AVAILABLE:
    from pypresence import Presence
else:
    Presence = None

packaging_ok, packaging_module = check_and_import("packaging", "packaging")
PACKAGING_AVAILABLE = packaging_ok


# ========== МОДЕЛЬ ПРОЕКТА ==========
class Project:
    STATE_FILE = "project_state.json"
    PINS_FILE = "pinned_items.json"
    RECENT_FILE = "recent_files.json"
    
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path) or "Unknow_Project"
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
                if sys.platform == "win32":
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(self.rlcode_path, 2)
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
                self.state = {
                    "last_opened_files": [],
                    "expanded_folders": [],
                    "last_active_tab": None,
                    "window_state": {}
                }
            
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
            opened_files = []
            pinned_files = []
            
            for tab in self.tabs:
                file_path = self.files.get(tab)
                if file_path:
                    opened_files.append(file_path)
                    if tab.pinned:
                        pinned_files.append(file_path)
            
            last_active = None
            if self.current_tab:
                last_active = self.files.get(self.current_tab)
            
            self.state["last_opened_files"] = opened_files
            self.state["last_active_tab"] = last_active
            
            with open(self._get_file_path(self.STATE_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)
            
            self.pins["pinned_files"] = pinned_files
            with open(self._get_file_path(self.PINS_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.pins, f, indent=4)
            
            self.recent_files = self.recent_files[:20]
            with open(self._get_file_path(self.RECENT_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.recent_files, f, indent=4)
                
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


# ========== КОМПОНЕНТЫ ИНТЕРФЕЙСА ==========
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
        self.text_widget.bind('<KeyRelease>', lambda e: self.update_numbers())
        self.text_widget.bind('<MouseWheel>', lambda e: self.update_numbers())
        self.text_widget.bind('<Button-4>', lambda e: self.update_numbers())
        self.text_widget.bind('<Button-5>', lambda e: self.update_numbers())
        self.text_widget.bind('<Configure>', lambda e: self.update_numbers())
        self.text_widget.bind('<<Modified>>', lambda e: self.update_numbers())

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
                    self.create_text(
                        45, y + height//2,
                        text=str(line_num),
                        anchor="e",
                        fill=VSColorScheme.LINE_NUMBERS,
                        font=("Consolas", 9)
                    )
                    # Маркеры ошибок (если есть linter)
                    if self.app and hasattr(self.app, 'linter') and self.app.linter:
                        messages = self.app.linter.get_messages_at_line(line_num)
                        if messages:
                            color = "red" if any(m.level == 'error' for m in messages) else "orange"
                            self.create_oval(
                                5, y + height//2 - 4,
                                13, y + height//2 + 4,
                                fill=color, outline=color
                            )
        except Exception as e:
            print(f"Ошибка обновления номеров строк: {e}")


class Minimap(tk.Canvas):
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.configure(
            bg=VSColorScheme.BG_MEDIUM,
            highlightthickness=1,
            highlightcolor=VSColorScheme.BORDER,
            width=100
        )
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
    
    def _bind_text_events(self):
        self.text_widget.bind('<KeyRelease>', self._schedule_update)
        self.text_widget.bind('<MouseWheel>', self._on_editor_scroll)
        self.text_widget.bind('<Button-4>', self._on_editor_scroll)
        self.text_widget.bind('<Button-5>', self._on_editor_scroll)
        self.text_widget.bind('<Configure>', self._schedule_update)
        self.text_widget.bind('<<Modified>>', self._schedule_update)
    
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
        return (self.text_widget and self.text_widget.winfo_exists() and 
                self.winfo_exists())
    
    def _draw_minimap_lines(self, total_lines, minimap_height):
        y = 0
        max_display_lines = min(total_lines, 2000)
        for i in range(max_display_lines):
            if y > minimap_height:
                break
            line = self.content_lines[i]
            line_h = max(2, self.scale_factor)
            color = self._get_line_color(line)
            self.create_rectangle(
                0, y,
                self.winfo_width(), y + line_h,
                fill=color,
                outline="",
                tags=f"line_{i}"
            )
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
            if indent > 0:
                return VSColorScheme.FG_LIGHT
            else:
                return VSColorScheme.FG
    
    def _draw_visible_area(self):
        try:
            if not hasattr(self, 'scale_factor') or not self.content_lines:
                return
            first_line = float(self.text_widget.index("@0,0").split('.')[0])
            last_line = float(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            y1 = (first_line - 1) * self.scale_factor
            y2 = last_line * self.scale_factor
            y1 = max(0, y1)
            y2 = min(self.winfo_height(), y2)
            self.delete("visible_area")
            self.create_rectangle(
                0, y1, self.winfo_width(), y2,
                fill="#264f78",
                stipple="gray50",
                outline=VSColorScheme.ACCENT,
                width=1,
                tags="visible_area"
            )
        except Exception as e:
            print(f"Ошибка отрисовки области видимости: {e}")
    
    def _on_editor_scroll(self, event):
        if self.scroll_after_id:
            self.after_cancel(self.scroll_after_id)
        self.scroll_after_id = self.after(50, self._draw_visible_area)
    
    def _on_minimap_scroll(self, event):
        if hasattr(self, 'scale_factor') and self.content_lines:
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
            if not hasattr(self, 'scale_factor') or not self.content_lines:
                return
            total_lines = len(self.content_lines)
            if total_lines == 0:
                return
            fraction = y / self.winfo_height()
            target_line = int(fraction * total_lines) + 1
            target_line = max(1, min(total_lines, target_line))
            self.text_widget.see(f"{target_line}.0")
            self.text_widget.focus_set()
            self._draw_visible_area()
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")


class SyntaxHighlighter:
    FULL_HIGHLIGHT_LIMIT = 1 * 1024 * 1024  # 1 МБ

    def __init__(self, text_widget):
        self.text = text_widget
        self.highlight_enabled = True
        self.current_language = 'python'
        self.update_after_id = None
        self.last_content = ""
        self.compiled_patterns = {}  # для быстрого доступа
        self._setup_tags()
        self._load_language_patterns('python')

    def _setup_tags(self):
        self.text.tag_configure("keyword", foreground=VSColorScheme.KEYWORD)
        self.text.tag_configure("builtin", foreground=VSColorScheme.BUILTIN)
        self.text.tag_configure("decorator", foreground=VSColorScheme.DECORATOR)
        self.text.tag_configure("function", foreground=VSColorScheme.FUNCTION)
        self.text.tag_configure("class", foreground=VSColorScheme.CLASS)
        self.text.tag_configure("comment", foreground=VSColorScheme.COMMENT,
                               font=("Consolas", 10, "italic"))
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
                'keyword': r'\b(if|else|for|while|do|switch|case|break|continue|return|using|goto|void|int|float|double|char|bool|long|short|uint|ulong|ushort|byte|sbyte|decimal|string|object|dynamic|var|const|static|readonly|class|struct|enum|interface|delegate|event|namespace|using|public|private|protected|internal|abstract|sealed|override|virtual|new|async|await|throw|try|catch|finally|lock|unsafe|fixed|sizeof|typeof|nameof|is|as|base|this)\b',
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

        # Компилируем все паттерны для ускорения
        self.compiled_patterns = {}
        for tag, pat in self.patterns.items():
            try:
                self.compiled_patterns[tag] = re.compile(pat, re.MULTILINE)
            except:
                pass
        for tag, pat in self.block_patterns.items():
            try:
                self.compiled_patterns[tag] = re.compile(pat, re.DOTALL | re.MULTILINE)
            except:
                pass

        self.current_language = language

    def set_language(self, extension):
        ext_map = {
            '.py': 'python',
            '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.hc': 'holyc', '.holyc': 'holyc',
        }
        lang = ext_map.get(extension.lower(), 'python')
        self._load_language_patterns(lang)

    def should_highlight(self):
        return self.highlight_enabled

    def get_file_size(self):
        try:
            return len(self.text.get("1.0", tk.END).encode('utf-8'))
        except:
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

            for tag in ('keyword', 'builtin', 'decorator', 'function', 'class', 'comment', 'string', 'number'):
                self.text.tag_remove(tag, "1.0", tk.END)

            # Применяем все скомпилированные паттерны
            for tag_name, compiled in self.compiled_patterns.items():
                try:
                    for match in compiled.finditer(current_content):
                        start = f"1.0+{match.start()}c"
                        end = f"1.0+{match.end()}c"
                        self.text.tag_add(tag_name, start, end)
                except Exception as e:
                    print(f"Ошибка применения паттерна {tag_name}: {e}")

        except Exception as e:
            print(f"Ошибка подсветки: {e}")

    def incremental_highlight(self, start_line=1, end_line=None):
        if not self.should_highlight():
            return
        if end_line is None:
            end_line = start_line

        for tag in ('keyword', 'builtin', 'decorator', 'function', 'class', 'comment', 'string', 'number'):
            self.text.tag_remove(tag, f"{start_line}.0", f"{end_line + 1}.0")

        text_range = self.text.get(f"{start_line}.0", f"{end_line + 1}.0")
        if not text_range:
            return

        base_offset = 0
        try:
            for i in range(1, start_line):
                line_len = len(self.text.get(f"{i}.0", f"{i}.end")) + 1
                base_offset += line_len
        except:
            base_offset = 0

        # Используем скомпилированные паттерны, но пропускаем блочные комментарии
        for tag_name, compiled in self.compiled_patterns.items():
            if tag_name == 'comment' and hasattr(self, 'block_patterns') and 'comment' in self.block_patterns:
                continue  # пропускаем блочные комментарии в инкрементальной
            try:
                for match in compiled.finditer(text_range):
                    abs_start = base_offset + match.start()
                    abs_end = base_offset + match.end()
                    start_pos = f"1.0+{abs_start}c"
                    end_pos = f"1.0+{abs_end}c"
                    self.text.tag_add(tag_name, start_pos, end_pos)
            except:
                pass

    def highlight_visible(self):
        if not self.should_highlight():
            return
        try:
            first = int(self.text.index("@0,0").split('.')[0])
            last = int(self.text.index(f"@0,{self.text.winfo_height()}").split('.')[0])
            # Если высота окна не определена (виджет ещё не отрисован), берем первые 50 строк
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
        self.pin_btn = tk.Label(
            self,
            text="📌",
            bg=VSColorScheme.TAB_INACTIVE,
            fg=VSColorScheme.FG_LIGHT,
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        self.pin_btn.place(x=5, y=12, width=20, height=20)
        
        self.title_label = tk.Label(
            self,
            text=self.title,
            bg=VSColorScheme.TAB_INACTIVE,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 11),
            cursor="hand2",
            padx=10,
            pady=12
        )
        self.title_label.place(x=30, y=0, width=120, height=45)
        
        self.close_btn = tk.Label(
            self,
            text="✕",
            bg=VSColorScheme.TAB_INACTIVE,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
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
        if self.pinned:
            self.pin_btn.configure(fg=VSColorScheme.PINNED)
        else:
            self.pin_btn.configure(fg=VSColorScheme.ACCENT)
    
    def _on_pin_leave(self, e):
        if self.pinned:
            self.pin_btn.configure(fg=VSColorScheme.PINNED)
        else:
            self.pin_btn.configure(fg=VSColorScheme.FG_LIGHT)
    
    def _on_close_enter(self, e):
        self.close_btn.configure(fg=VSColorScheme.ACCENT, 
                                 bg=VSColorScheme.ACCENT_HOVER)
    
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
        self.frame = tk.Frame(self.parent, bg=VSColorScheme.BG_DARK)
        center_frame = tk.Frame(self.frame, bg=VSColorScheme.BG_DARK)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self._create_title(center_frame)
        self._create_action_buttons(center_frame)
        self._create_shortcuts(center_frame)
    
    def _create_title(self, parent):
        title_label = tk.Label(
            parent,
            text=APP_NAME,
            bg=VSColorScheme.BG_DARK,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 48, "bold")
        )
        title_label.pack(pady=(0, 10))
        version_label = tk.Label(
            parent,
            text=f"Версия {VERSION}",
            bg=VSColorScheme.BG_DARK,
            fg=VSColorScheme.FG_LIGHT,
            font=("Segoe UI", 14)
        )
        version_label.pack(pady=(0, 40))
    
    def _create_action_buttons(self, parent):
        actions_frame = tk.Frame(parent, bg=VSColorScheme.BG_DARK)
        actions_frame.pack(pady=20)
        new_btn = self._create_action_button(
            actions_frame, "📄  Новый файл", 
            lambda e: self.app.add_new_tab()
        )
        new_btn.pack(side=tk.LEFT, padx=10)
        open_btn = self._create_action_button(
            actions_frame, "📂  Открыть файл",
            lambda e: self.app.open_file()
        )
        open_btn.pack(side=tk.LEFT, padx=10)
        folder_btn = self._create_action_button(
            actions_frame, "📁  Открыть папку",
            lambda e: self.app.open_folder()
        )
        folder_btn.pack(side=tk.LEFT, padx=10)
    
    def _create_action_button(self, parent, text, command):
        btn = tk.Label(
            parent,
            text=text,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 11),
            padx=30,
            pady=10,
            cursor="hand2"
        )
        btn.bind('<Enter>', lambda e: btn.configure(bg=VSColorScheme.ACCENT))
        btn.bind('<Leave>', lambda e: btn.configure(bg=VSColorScheme.BG_LIGHT))
        btn.bind('<Button-1>', command)
        return btn
    
    def _create_shortcuts(self, parent):
        shortcuts_frame = tk.Frame(parent, bg=VSColorScheme.BG_DARK)
        shortcuts_frame.pack(pady=30)
        shortcuts = [
            ("Ctrl+N", "Новый файл"),
            ("Ctrl+O", "Открыть файл"),
            ("Ctrl+K", "Открыть папку"),
            ("Ctrl+S", "Сохранить"),
            ("Ctrl+F", "Поиск"),
            ("Ctrl+G", "Перейти к строке"),
            ("F5", "Запустить код"),
            ("F1", "Настройки")
        ]
        left_col = tk.Frame(shortcuts_frame, bg=VSColorScheme.BG_DARK)
        left_col.pack(side=tk.LEFT, padx=20)
        right_col = tk.Frame(shortcuts_frame, bg=VSColorScheme.BG_DARK)
        right_col.pack(side=tk.LEFT, padx=20)
        for i, (key, desc) in enumerate(shortcuts[:4]):
            self._create_shortcut_item(left_col, key, desc)
        for i, (key, desc) in enumerate(shortcuts[4:]):
            self._create_shortcut_item(right_col, key, desc)
    
    def _create_shortcut_item(self, parent, key, desc):
        frame = tk.Frame(parent, bg=VSColorScheme.BG_DARK)
        frame.pack(pady=5)
        key_label = tk.Label(
            frame,
            text=key,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.ACCENT,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=2
        )
        key_label.pack(side=tk.LEFT, padx=5)
        desc_label = tk.Label(
            frame,
            text=desc,
            bg=VSColorScheme.BG_DARK,
            fg=VSColorScheme.FG_LIGHT,
            font=("Segoe UI", 10)
        )
        desc_label.pack(side=tk.LEFT, padx=5)
    
    def hide(self):
        if self.frame and self.frame.winfo_ismapped():
            self.frame.pack_forget()
    
    def show(self):
        if self.frame and not self.frame.winfo_ismapped():
            self.frame.pack(fill=tk.BOTH, expand=True)

class SettingsDialog:
    def __init__(self, parent, config, callback):
        self.parent = parent
        self.config = config.copy()
        self.callback = callback
        self.window = None
        self._show()
    
    def _show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Настройки")
        self.window.geometry("600x600")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        # self.window.grab_set()
        tk.Label(
            self.window,
            text="НАСТРОЙКИ",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 12, "bold"),
            pady=10
        ).pack()
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        editor_frame = tk.Frame(notebook, bg=VSColorScheme.BG_MEDIUM)
        notebook.add(editor_frame, text="Редактор")
        self._create_editor_settings(editor_frame)
        windows_frame = tk.Frame(notebook, bg=VSColorScheme.BG_MEDIUM)
        notebook.add(windows_frame, text="Окна")
        self._create_window_settings(windows_frame)
        self._create_buttons()
    
    def _create_editor_settings(self, parent):
        row = 0
        tk.Label(parent, text="Шрифт:", bg=VSColorScheme.BG_MEDIUM, 
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.font_var = tk.StringVar(value=self.config["font_family"])
        fonts = ["Consolas", "Courier New", "Monaco", "Lucida Console", "DejaVu Sans Mono"]
        font_combo = ttk.Combobox(parent, textvariable=self.font_var, values=fonts, width=20)
        font_combo.grid(row=row, column=1, pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Размер шрифта:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.size_var = tk.IntVar(value=self.config["font_size"])
        size_spin = tk.Spinbox(parent, from_=8, to=24, textvariable=self.size_var, width=10)
        size_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Размер табуляции:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.tab_var = tk.IntVar(value=self.config["tab_size"])
        tab_spin = tk.Spinbox(parent, from_=2, to=8, textvariable=self.tab_var, width=10)
        tab_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, 
                                                        sticky="ew", pady=10, padx=10)
        row += 1
        self.save_scroll_var = tk.BooleanVar(value=self.config.get("save_scroll_position", True))
        tk.Checkbutton(
            parent,
            text="Сохранять позицию прокрутки",
            variable=self.save_scroll_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        row += 1
        self.auto_save_var = tk.BooleanVar(value=self.config.get("auto_save", False))
        tk.Checkbutton(
            parent,
            text="Автосохранение",
            variable=self.auto_save_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        row += 1
        self.wrap_var = tk.BooleanVar(value=self.config.get("word_wrap", False))
        tk.Checkbutton(
            parent,
            text="Перенос строк",
            variable=self.wrap_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        row += 1
        self.highlight_var = tk.BooleanVar(value=self.config.get("syntax_highlight", True))
        tk.Checkbutton(
            parent,
            text="Подсветка синтаксиса",
            variable=self.highlight_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        row += 1
        self.minimap_var = tk.BooleanVar(value=self.config.get("minimap_enabled", True))
        tk.Checkbutton(
            parent,
            text="Показывать миникарту",
            variable=self.minimap_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        self.hidden_var = tk.BooleanVar(value=self.config.get("show_hidden_files", False))
        tk.Checkbutton(
            parent,
            text="Показывать скрытые файлы (.env, .gitignore и др.)",
            variable=self.hidden_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5, padx=10)
        row += 1
    
    def _create_window_settings(self, parent):
        row = 0
        tk.Label(parent, text="Ширина проводника:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.sidebar_width_var = tk.IntVar(value=self.config.get("sidebar_width", 250))
        sidebar_spin = tk.Spinbox(parent, from_=150, to=500, 
                                  textvariable=self.sidebar_width_var, width=10)
        sidebar_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        tk.Label(parent, text="Высота консоли:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.console_height_var = tk.IntVar(value=self.config.get("console_height", 200))
        console_spin = tk.Spinbox(parent, from_=100, to=500, 
                                  textvariable=self.console_height_var, width=10)
        console_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2,
                                                        sticky="ew", pady=10, padx=10)
        row += 1
        tk.Label(parent, text="Позиция проводника:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.explorer_pos_var = tk.StringVar(value=self.config.get("explorer_position", "left"))
        pos_frame = tk.Frame(parent, bg=VSColorScheme.BG_MEDIUM)
        pos_frame.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        tk.Radiobutton(pos_frame, text="Слева", variable=self.explorer_pos_var, value="left",
                      bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                      selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(pos_frame, text="Справа", variable=self.explorer_pos_var, value="right",
                      bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                      selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)
        row += 1
        tk.Label(parent, text="Позиция консоли:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5, padx=10)
        self.console_pos_var = tk.StringVar(value=self.config.get("console_position", "bottom"))
        pos_frame2 = tk.Frame(parent, bg=VSColorScheme.BG_MEDIUM)
        pos_frame2.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        tk.Radiobutton(pos_frame2, text="Снизу", variable=self.console_pos_var, value="bottom",
                      bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                      selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(pos_frame2, text="Сверху", variable=self.console_pos_var, value="top",
                      bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG,
                      selectcolor=VSColorScheme.BG_MEDIUM).pack(side=tk.LEFT, padx=5)
    
    def _create_buttons(self):
        btn_frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Button(
            btn_frame,
            text="Сохранить",
            command=self._save,
            bg=VSColorScheme.BUTTON_BG,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)
        tk.Button(
            btn_frame,
            text="Отмена",
            command=self.window.destroy,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
    
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


# ========== DISCORD INTEGRATION ==========
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
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            print("✅ Discord Rich Presence подключен")
            self.thread_running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
        except NameError:
            print("❌ Ошибка: Presence не определен. Проверьте установку pypresence")
            self.connected = False
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
            except:
                pass
        self.connected = False
        print("👋 Discord Rich Presence отключен")
    
    def _update_loop(self):
        try:
            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())
            while self.thread_running and self.connected:
                try:
                    self._update_presence()
                    time.sleep(15)
                except Exception as e:
                    print(f"Ошибка в update_loop: {e}")
                    break
        except Exception as e:
            print(f"Критическая ошибка в update_loop: {e}")
        finally:
            self.connected = False
    
    def set_state(self, state):
        self.current_state = state
        self._update_presence()
    
    def _get_file_info(self):
        if not self.app.current_project or not self.app.current_project.current_tab:
            return "Без имени", "unknown"
        filename = self.app.current_project.files.get(self.app.current_project.current_tab)
        if not filename:
            return "Без имени", "unknown"
        name = os.path.basename(filename)
        ext = os.path.splitext(name)[1].lower()
        file_type = "unknown"
        if ext == '.py':
            file_type = "python"
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            file_type = "javascript"
        elif ext in ['.html', '.htm']:
            file_type = "html"
        elif ext == '.css':
            file_type = "css"
        elif ext == '.json':
            file_type = "json"
        elif ext in ['.md', '.txt']:
            file_type = "text"
        elif ext == '.cpp':
            file_type = "cpp"
        elif ext == '.cs':
            file_type = "cs"
        elif ext == '.h':
            file_type = "holdc"
        elif ext == '.c':
            file_type = "c"

        return name, file_type
    
    def _update_presence(self):
        if not self.connected or not self.rpc:
            return
        try:
            filename, file_type = self._get_file_info()
            project_name = "Безымянный проект" if not self.app.current_project else self.app.current_project.name
            files_count = len(self.app.current_project.tabs) if self.app.current_project else 0
            state_text = {
                "editing": "Редактирует код",
                "running": "Запустил выполнение кода",
                "idle": "Отошел"
            }.get(self.current_state, "Редактирует код")
            details = f"{filename} • {project_name}"
            buttons = [
                {"label": "RealCode in GitLab", "url": "https://gitlab.com/K1sh-M1sh/RealCode"},
                {"label": "Download RealCode", "url": "https://gitlab.com/K1sh-M1sh/RealCode/-/releases/"},
			 {"label": "Following Creator on GitHub", "url": "https://github.com/Kish-Mish122"},
			 {"label": "Following Creator on GitLab", "url": "https://gitlab.com/K1sh-M1sh"},
            ]
            self.rpc.update(
                state=state_text,
                details=details,
                start=self.start_time,
                large_image="realcode_logo",
                large_text=f"RealCode v{VERSION}",
                small_image=file_type if file_type != "unknown" else "file",
                small_text=file_type.upper() if file_type != "unknown" else "Файл",
                buttons=buttons,
                party_size=[files_count, 10]
            )
        except Exception as e:
            print(f"Ошибка обновления Discord: {e}")
            self.connected = False


# ========== UPDATE CHECKER ==========
class UpdateChecker:
    """Проверка обновлений RealCode"""

    def __init__(self, app):
        self.app = app
        self.current_version = VERSION
        self.update_url = GITHUB_VERSION_URL
        self.update_info = None
        self.update_available = False
        self.update_dialog = None
        self.progress_bar = None
        self.status_label = None

    def check_for_updates(self, silent=False):
        try:
            import urllib.request
            import ssl
            import json
            from packaging import version

            # GitHub API URL
            api_url = "https://api.github.com/repos/Kish-Mish122/RealCode/releases/latest"

            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                api_url,
                headers={
                    'User-Agent': 'RealCode Updater',
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': f'token {GITHUB_TOKEN}'
                }
            )

            print("🔍 Просмотр обновлений...")

            with urllib.request.urlopen(req, context=context, timeout=5) as response:
                data = response.read().decode('utf-8')
                release_info = json.loads(data)

            # Получаем версию из tag_name (например, "v3.1" -> "3.1")
            latest_tag = release_info.get('tag_name', '')
            # Извлекаем версию вида x.y.z или x.y (числа с точками)
            import re
            match = re.search(r'(\d+(?:\.\d+)+)', latest_tag)
            if match:
                latest_version_str = match.group(1)
            else:
                # fallback: удаляем v и возможные точки в начале
                latest_version_str = latest_tag.lstrip('v').lstrip('.')
                if not latest_version_str:
                    raise ValueError("Не удалось извлечь номер версии из тега")

            # Ищем файл для текущей ОС
            download_url = None
            os_type = get_os_type()

            print(f"🔍 Поиск файла для {os_type}...")

            for asset in release_info.get('assets', []):
                asset_name = asset['name'].lower()
                
                # Windows: ищем .exe
                if os_type == 'windows' and asset_name.endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
                
                # Linux: ищем .AppImage или файлы с linux в имени
                elif os_type == 'linux':
                    if asset_name.endswith('.appimage') or 'linux' in asset_name:
                        download_url = asset['browser_download_url']
                        break
                    # Если ничего не нашли, ищем файл без расширения (бинарник)
                    elif not asset_name.endswith(('.exe', '.dmg', '.appimage')):
                        download_url = asset['browser_download_url']
                        break
                
                # macOS: ищем .dmg или .app
                elif os_type == 'macos':
                    if asset_name.endswith(('.dmg', '.app')):
                        download_url = asset['browser_download_url']
                        break

            # Если не нашли специфичный файл - пробуем найти любой подходящий
            if not download_url:
                print("⚠️ Специфичный файл не найден, ищем любой...")
                for asset in release_info.get('assets', []):
                    # Пропускаем файлы с исходниками
                    if 'source' not in asset['name'].lower() and 'src' not in asset['name'].lower():
                        download_url = asset['browser_download_url']
                        print(f"⚠️ Используем: {asset['name']}")
                        break

            if not download_url:
                raise ValueError(f"Не найден файл для {os_type} в релизе")

            # Сравниваем версии
            latest = version.parse(latest_version_str)
            current = version.parse(str(self.current_version))
            self.update_available = latest > current

            # Сохраняем данные для диалога
            self.update_info = {
                'latest_version': latest_version_str,
                'download_url': download_url,
                'update_message': release_info.get('name', f'Доступна новая версия {latest_version_str}'),
                'release_notes': release_info.get('body', '')
            }

            if self.update_available:
                print(f"✅ Пора обновляться! {current} -> {latest}")
                if not silent:
                    self.app.root.after(0, self._show_update_dialog)
                return True
            else:
                if not silent:
                    self.app.log("✅ RealCode новой версии")
                return False

        except Exception as e:
            print(f"❌ Ошибка проверки обновлений: {e}")
            if not silent:
                self.app.log(f"⚠️ Не удалось проверить обновления: {e}")
                return False

    def _show_update_dialog(self):
        if not self.update_info or not isinstance(self.update_info, dict):
            print("❌ Нет информации об обновлении")
            return

        self.update_dialog = tk.Toplevel(self.app.root)
        self.update_dialog.title("Не хотите обновить RealCode?")
        self.update_dialog.geometry("650x540")
        self.update_dialog.configure(bg=VSColorScheme.BG_MEDIUM)
        self.update_dialog.transient(self.app.root)
        # self.update_dialog.grab_set()
        self.update_dialog.resizable(False, False)

        self.update_dialog.update_idletasks()
        x = (self.update_dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.update_dialog.winfo_screenheight() // 2) - (540 // 2)
        self.update_dialog.geometry(f'+{x}+{y}')

        latest_version = self.update_info.get('latest_version', 'неизвестна')

        title_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        title_frame.pack(pady=(30, 10))

        icon_label = tk.Label(
            title_frame,
            text="🔄",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.ACCENT,
            font=("Segoe UI", 48)
        )
        icon_label.pack(side=tk.LEFT, padx=10)

        title_label = tk.Label(
            title_frame,
            text=f"Пора обновляться! Новая версия RealCode {latest_version}",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 14, "bold"),
            wraplength=400,
            justify="center"
        )
        title_label.pack(side=tk.LEFT, padx=10)

        version_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_LIGHT, padx=20, pady=15)
        version_frame.pack(fill=tk.X, padx=30, pady=10)

        current_frame = tk.Frame(version_frame, bg=VSColorScheme.BG_LIGHT)
        current_frame.pack(fill=tk.X, pady=2)
        tk.Label(current_frame, text="Текущая версия:", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.FG_LIGHT, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        tk.Label(current_frame, text=f"  {self.current_version}", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.FG, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        new_frame = tk.Frame(version_frame, bg=VSColorScheme.BG_LIGHT)
        new_frame.pack(fill=tk.X, pady=2)
        tk.Label(new_frame, text="Новая версия:  ", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.ACCENT, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        tk.Label(new_frame, text=f"{latest_version}", bg=VSColorScheme.BG_LIGHT,
                 fg=VSColorScheme.ACCENT, font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        message_text = self.update_info.get('update_message',
            f"Новая версия RealCode {latest_version} с улучшениями и исправлениями извесных багов!")
        message_label = tk.Label(
            self.update_dialog,
            text=message_text,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 11),
            wraplength=500,
            justify="center"
        )
        message_label.pack(pady=15, padx=30)

        if 'release_notes' in self.update_info:
            notes_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_LIGHT, padx=15, pady=15)
            notes_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
            notes_title = tk.Label(notes_frame, text="Что обновилось:", bg=VSColorScheme.BG_LIGHT,
                                   fg=VSColorScheme.FG, font=("Segoe UI", 11, "bold"))
            notes_title.pack(anchor="w", pady=(0, 5))
            notes_text = tk.Text(notes_frame, height=6, bg=VSColorScheme.BG_LIGHT,
                                 fg=VSColorScheme.FG_LIGHT, font=("Segoe UI", 10),
                                 wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
            notes_text.pack(fill=tk.BOTH, expand=True)
            notes_text.insert("1.0", self.update_info['release_notes'])
            notes_text.config(state=tk.DISABLED)

        self.progress_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        self.progress_frame.pack(fill=tk.X, padx=30, pady=10)
        self.progress_frame.pack_forget()

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        self.status_label = tk.Label(self.progress_frame, text="", bg=VSColorScheme.BG_MEDIUM,
                                     fg=VSColorScheme.FG_LIGHT, font=("Segoe UI", 9))
        self.status_label.pack()

        btn_frame = tk.Frame(self.update_dialog, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(pady=20)

        update_btn = tk.Button(btn_frame, text="Обновиться", command=self._start_update,
                               bg=VSColorScheme.ACCENT, fg="white", relief=tk.FLAT,
                               padx=25, pady=8, font=("Segoe UI", 11, "bold"), cursor="hand2")
        update_btn.pack(side=tk.LEFT, padx=10)

        later_btn = tk.Button(btn_frame, text="Напомнить позже", command=self.update_dialog.destroy,
                              bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT,
                              padx=25, pady=8, font=("Segoe UI", 11), cursor="hand2")
        later_btn.pack(side=tk.LEFT, padx=10)

        warning_label = tk.Label(self.update_dialog, text="При завершении работы RealCode будет обновлен",
                                 bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.PINNED,
                                 font=("Segoe UI", 9, "italic"))
        warning_label.pack(pady=(10, 5))

    def _start_update(self):
        print("🚀 Начинаю обновление...")
        if not self.update_info or not isinstance(self.update_info, dict):
            print("❌ Нет информации об обновлении")
            return

        for widget in self.update_dialog.winfo_children():
            if isinstance(widget, tk.Frame) and widget == self.progress_frame:
                continue
            if hasattr(widget, 'pack'):
                try:
                    widget.pack_forget()
                except:
                    pass

        self.progress_frame.pack(fill=tk.X, padx=30, pady=20)
        self.status_label.config(text="Подготовка...")
        threading.Thread(target=self._download_and_install, daemon=True).start()

    def _download_and_install(self):
        """Скачивание и установка обновления (кроссплатформенный)"""
        try:
            download_url = self.update_info.get('download_url')

            if not download_url:
                self._show_error("Ссылка для скачивания не найдена")
                return

            # Определяем тип ОС
            os_type = get_os_type()
            print(f"📥 Скачивание для {os_type}...")

            # Определяем путь для сохранения
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                if os_type == 'windows':
                    download_path = current_exe.replace('.exe', '.new.exe')
                else:
                    download_path = current_exe + '.new'
            else:
                # Режим разработки
                download_path = os.path.join(os.getcwd(), f'RealCode-{os_type}.new')

            self._update_status("Загрузка обновления...", 10)

            import urllib.request
            import ssl
            context = ssl._create_unverified_context()

            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(int(downloaded * 100 / total_size), 99)
                    self.update_dialog.after(0, lambda: self._update_progress(percent))

            urllib.request.urlretrieve(download_url, download_path, reporthook=report_progress)

            # Проверяем загрузку
            if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
                self._show_error("Скачанный файл поврежден или пустой")
                return

            self._update_status("Установка обновления...", 100)
            time.sleep(0.5)

            # Устанавливаем в зависимости от ОС
            if os_type == 'windows':
                self._install_windows_update(download_path)
            elif os_type == 'linux':
                self._install_linux_update(download_path)
            elif os_type == 'macos':
                self._install_macos_update(download_path)

        except Exception as e:
            self._show_error(f"Ошибка обновления:\n{e}")

    def _create_update_bat(self, current_exe, download_path):
        bat_path = os.path.join(os.path.dirname(current_exe), "update.bat")
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f"""@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Обновление RealCode...
timeout /t 2 /nobreak >nul
:loop
taskkill /f /im RealCode.exe 2>nul
timeout /t 1 /nobreak >nul
copy /y "{os.path.basename(download_path)}" "{os.path.basename(current_exe)}" >nul
if %errorlevel% neq 0 goto loop
del /f /q "{os.path.basename(download_path)}"
set _PYI_APPLICATION_HOME_DIR=%~dp0
start "" "{os.path.basename(current_exe)}"
del /f /q "%~f0"
""")

        self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление было загружено!",
                                       "Обновление было загружено успешно! Хотите закончить установку RealCode?")
        if response:
            self.update_dialog.after(100, lambda: os.startfile(bat_path))
            self.app.root.after(100, self.app.on_closing)
        else:
            messagebox.showinfo("Обновление перенесено...",
                                "Обновление будет окончательно загружено при повторном запуске программы.")

    def _update_progress(self, value):
        if self.progress_bar:
            self.progress_bar['value'] = value

    def _install_windows_update(self, download_path):
        """Установка на Windows"""
        current_exe = sys.executable
        bat_path = os.path.join(os.path.dirname(current_exe), "update.bat")
        
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f"""@echo off
    chcp 65001 >nul
    cd /d "%~dp0"
    echo Обновление RealCode...
    timeout /t 2 /nobreak >nul
    :loop
    taskkill /f /im RealCode.exe 2>nul
    timeout /t 1 /nobreak >nul
    copy /y "{os.path.basename(download_path)}" "{os.path.basename(current_exe)}" >nul
    if %errorlevel% neq 0 goto loop
    del /f /q "{os.path.basename(download_path)}"
    start "" "{os.path.basename(current_exe)}"
    del /f /q "%~f0"
    """)
        
        self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление загружено!",
                                    "Обновление загружено успешно! Установить сейчас?")
        if response:
            os.startfile(bat_path)
            self.app.root.after(100, self.app.on_closing)

    def _install_linux_update(self, download_path):
        """Установка на Linux"""
        current_exe = sys.executable
        
        # Делаем файл исполняемым
        os.chmod(download_path, 0o755)
        
        script_path = os.path.join(os.path.dirname(current_exe), "update.sh")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
    cd "$(dirname "$0")"
    echo "Обновление RealCode..."
    sleep 2
    # Закрываем все экземпляры
    pkill -f RealCode 2>/dev/null || true
    sleep 1
    # Заменяем файл
    cp "{os.path.basename(download_path)}" "{os.path.basename(current_exe)}"
    chmod +x "{os.path.basename(current_exe)}"
    rm "{os.path.basename(download_path)}"
    # Запускаем новую версию
    "./{os.path.basename(current_exe)}" &
    rm "$0"
    """)
        os.chmod(script_path, 0o755)
        
        self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление загружено!",
                                    "Обновление загружено успешно! Установить сейчас?")
        if response:
            subprocess.Popen(['bash', script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.app.root.after(100, self.app.on_closing)

    def _install_macos_update(self, download_path):
        """Установка на macOS"""
        # Аналогично Linux
        os.chmod(download_path, 0o755)
        current_exe = sys.executable
        
        script_path = os.path.join(os.path.dirname(current_exe), "update.sh")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
    cd "$(dirname "$0")"
    echo "Обновление RealCode..."
    sleep 2
    pkill -f RealCode 2>/dev/null || true
    sleep 1
    cp "{os.path.basename(download_path)}" "{os.path.basename(current_exe)}"
    chmod +x "{os.path.basename(current_exe)}"
    rm "{os.path.basename(download_path)}"
    open "{os.path.basename(current_exe)}"
    rm "$0"
    """)
        os.chmod(script_path, 0o755)
        
        self.update_dialog.after(0, self.update_dialog.destroy)
        response = messagebox.askyesno("Обновление загружено!",
                                    "Обновление загружено успешно! Установить сейчас?")
        if response:
            subprocess.Popen(['bash', script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.app.root.after(100, self.app.on_closing)

    def _update_status(self, text, progress=None):
        if self.status_label:
            self.status_label.config(text=text)
        if progress is not None:
            self._update_progress(progress)

    def _show_error(self, message):
        if self.update_dialog and self.update_dialog.winfo_exists():
            self.update_dialog.after(0, self.update_dialog.destroy)
        self.app.root.after(0, lambda: messagebox.showerror("Ошибка обновления", message))


# ========== ОСНОВНОЕ ПРИЛОЖЕНИЕ ==========
class CodeEditorApp:
    """Главный класс приложения RealCode"""
    
    def __init__(self, root):
        url = GITHUB_VERSION_MIN
        
        self.root = root
        self.config = load_config()
        self.root.title(APP_NAME)
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
        
        self.current_project = None
        self.projects = {}
        self.discord = None
        self.updater = UpdateChecker(self)
        self.highlighter = None
        self.linter = None
        self._dialog_open = False

        self.app_dir = get_app_dir()
    
        # Создаём все необходимые папки
        ensure_directories(self.app_dir)
        
        # Теперь загружаем конфиг и остальное
        self.root = root
        self.config = load_config() 

        if is_linux():
            try:
                # Для Linux используем .png иконку
                icon_paths = ['icon.png', 'icon.svg', 'icon.ico']
                for path in icon_paths:
                    if os.path.exists(path):
                        # Для Tkinter на Linux иконка устанавливается через PhotoImage
                        from PIL import Image, ImageTk
                        img = Image.open(path)
                        photo = ImageTk.PhotoImage(img)
                        self.root.iconphoto(True, photo)
                        break
            except:
                pass
        
        self._highlight_after_id = None
        self._minimap_after_id = None
        self._minimap_scroll_id = None
        self.auto_save_timer = None
        
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
        self.tab_bar = None
        self.status_label = None
        self.pos_label = None
        self.console_scrollbar = None
        
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

        threading.Thread(target=self._check_updates_thread, daemon=True).start()
        print("Привет, Юзер! Удачного кодинга!")

    def open_marketplace(self):
        PluginMarketplaceDialog(self.root, self)

    def apply_theme(self):
        """Применяет текущие цвета из VSColorScheme ко всем виджетам."""
        # Обновляем корневое окно
        self.root.configure(bg=VSColorScheme.BG_DARK)
        
        # Обновляем строку состояния
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.configure(bg=VSColorScheme.STATUS_BG, fg="white")
        if hasattr(self, 'pos_label') and self.pos_label:
            self.pos_label.configure(bg=VSColorScheme.STATUS_BG, fg="white")
        
        # Обновляем панели
        if hasattr(self, 'main_paned') and self.main_paned:
            self.main_paned.configure(bg=VSColorScheme.BORDER)
        if hasattr(self, 'center_paned') and self.center_paned:
            self.center_paned.configure(bg=VSColorScheme.BORDER)
        
        # Обновляем редактор
        if hasattr(self, 'editor') and self.editor:
            self.editor.configure(
                bg=VSColorScheme.BG_DARK,
                fg=VSColorScheme.FG,
                insertbackground=VSColorScheme.FG,
                selectbackground=VSColorScheme.SELECTION
            )
        
        # Обновляем номера строк
        if hasattr(self, 'line_numbers') and self.line_numbers:
            self.line_numbers.configure(bg=VSColorScheme.BG_MEDIUM)
            self.line_numbers.update_numbers()
        
        # Обновляем консоль
        if hasattr(self, 'console') and self.console:
            self.console.configure(
                bg=VSColorScheme.BG_DARK,
                fg=VSColorScheme.FG_LIGHT
            )
        
        # Обновляем панель проводника
        if hasattr(self, 'explorer_frame') and self.explorer_frame:
            self.explorer_frame.configure(bg=VSColorScheme.BG_MEDIUM)
        
        # Обновляем дерево файлов (если есть)
        if hasattr(self, 'file_tree') and self.file_tree:
            style = ttk.Style()
            style.theme_use("clam")
            style.configure(
                "Treeview",
                background=VSColorScheme.BG_LIGHT,
                foreground=VSColorScheme.FG,
                fieldbackground=VSColorScheme.BG_LIGHT
            )
            style.map(
                "Treeview",
                background=[("selected", VSColorScheme.SELECTION)]
            )
        
        # Обновляем вкладки (tab bar)
        if hasattr(self, 'tab_bar') and self.tab_bar:
            self.tab_bar.configure(bg=VSColorScheme.BG_MEDIUM)
        
        if hasattr(self, 'tabs_container') and self.tabs_container:
            self.tabs_container.configure(bg=VSColorScheme.BG_MEDIUM)
        
        # Обновляем панель инструментов
        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.configure(bg=VSColorScheme.BG_MEDIUM)
            for child in self.toolbar.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        
        # Обновляем мини-карту
        if hasattr(self, 'minimap') and self.minimap:
            self.minimap.configure(bg=VSColorScheme.BG_MEDIUM)
            self.minimap.update_minimap()
        
        # Обновляем фон редакторной области
        if hasattr(self, 'editor_area') and self.editor_area:
            self.editor_area.configure(bg=VSColorScheme.BG_DARK)
        
        if hasattr(self, 'editor_container') and self.editor_container:
            self.editor_container.configure(bg=VSColorScheme.BG_DARK)
        
        # Обновляем консольную область
        if hasattr(self, 'console_area') and self.console_area:
            self.console_area.configure(bg=VSColorScheme.BG_DARK)
        
        # Обновляем консольный заголовок
        if hasattr(self, 'console_header') and self.console_header:
            self.console_header.configure(bg=VSColorScheme.STATUS_BG)
            for child in self.console_header.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=VSColorScheme.STATUS_BG, fg="white")
        
        # Перерисовываем все вкладки
        if hasattr(self, 'current_project') and self.current_project:
            for tab in self.current_project.tabs:
                if tab.pinned:
                    tab.pin_btn.configure(fg=VSColorScheme.PINNED)
                else:
                    tab.pin_btn.configure(fg=VSColorScheme.FG_LIGHT)
                if tab.is_active:
                    tab._set_bg_color(VSColorScheme.TAB_ACTIVE)
                else:
                    tab._set_bg_color(VSColorScheme.TAB_INACTIVE)
        
        # Обновляем статусную строку
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.configure(bg=VSColorScheme.STATUS_BG)
        
        # Обновляем экран приветствия
        if hasattr(self, 'welcome_screen') and self.welcome_screen:
            for child in self.welcome_screen.frame.winfo_children():
                child.configure(bg=VSColorScheme.BG_DARK)
            # Можно пересоздать экран, но для простоты просто обновим фон
            self.welcome_screen.frame.configure(bg=VSColorScheme.BG_DARK)
        
        self.log("✅ Тема применена")
    
    def _setup_window(self):
        x = self.config.get("window_x", 100)
        y = self.config.get("window_y", 100)
        width = self.config.get("window_width", 1300)
        height = self.config.get("window_height", 800)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)
        self.root.configure(bg=VSColorScheme.BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Исправление для Linux - проверка на zoomed
        if self.config.get("window_maximized", False):
            try:
                # Для Windows
                self.root.state('zoomed')
            except tk.TclError:
                try:
                    # Для Linux (X11)
                    self.root.attributes('-zoomed', True)
                except:
                    try:
                        # Альтернативный способ для Linux
                        self.root.state('iconic')
                        self.root.update()
                        self.root.state('normal')
                        # Разворачиваем на весь экран
                        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
                    except:
                        # Если ничего не работает - просто максимизируем
                        try:
                            self.root.wm_attributes('-fullscreen', False)
                            self.root.state('normal')
                        except:
                            pass
    
    def _init_discord(self):
        try:
            self.discord = DiscordPresence(self)
        except Exception as e:
            print(f"Ошибка инициализации Discord: {e}")
            self.discord = None

    def _is_python_file(self, tab):
        if not self.current_project or not tab:
            return False
        filename = self.current_project.files.get(tab)
        if filename:
            return filename.endswith('.py')
        return False
    
    def _check_updates_thread(self):
        time.sleep(2)
        self.updater.check_for_updates(silent=False)
    
    def manual_check_updates(self):
        self.updater.check_for_updates(silent=False)

    def _fix_menu_rendering(self):
        """Исправляет отображение меню на Linux"""
        if not is_linux():
            return
        
        try:
            # Способ 1: Принудительная перерисовка
            self.root.update_idletasks()
            self.root.tk.call('update', 'idletasks')
            
            # Способ 2: Сброс масштабирования
            self.root.tk.call('tk', 'scaling', 1.0)
            
            # Способ 3: Пересоздание меню с задержкой
            self.root.after(100, self._rebuild_menu)
            
        except Exception as e:
            print(f"⚠️ Ошибка фикса меню: {e}")

    def _rebuild_menu(self):
        """Пересоздает меню (для исправления отображения)"""
        try:
            # Получаем текущее меню
            current_menu = self.root.cget('menu')
            if current_menu:
                # Пересоздаем меню
                self._create_menu()
                self.root.update()
        except Exception as e:
            print(f"⚠️ Ошибка пересоздания меню: {e}")
    
    # ========== УПРАВЛЕНИЕ ПРОЕКТАМИ ==========
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
    
    def save_project_state(self):
        if not self.current_project:
            return
        if self.editor and self.current_project.current_tab:
            self.current_project.file_contents[self.current_project.current_tab] = self.editor.get("1.0", tk.END)
        self.current_project.save_state()
    
    def _restore_project_state(self):
        if not self.current_project:
            self.show_welcome_screen()
            return
        last_files = self.current_project.get_last_opened_files()
        pinned_files = self.current_project.get_pinned_files()
        if last_files:
            for file_path in last_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        is_pinned = file_path in pinned_files
                        self.add_new_tab(filename=file_path, content=content,
                                        restore=True, pinned=is_pinned)
                    except Exception as e:
                        print(f"Ошибка загрузки файла {file_path}: {e}")
            self._reorder_tabs()
            last_tab_file = self.current_project.get_last_active_tab()
            if last_tab_file:
                for tab in self.current_project.tabs:
                    if self.current_project.files.get(tab) == last_tab_file:
                        self.select_tab(tab)
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
        if tab in self.current_project.files:
            del self.current_project.files[tab]
        if tab in self.current_project.file_contents:
            del self.current_project.file_contents[tab]
        tab.destroy()
    
    def _reorder_tabs(self):
        if not self.current_project:
            return
        pinned = [t for t in self.current_project.tabs if t.pinned]
        unpinned = [t for t in self.current_project.tabs if not t.pinned]
        new_order = pinned + unpinned
        if new_order != self.current_project.tabs:
            for tab in self.current_project.tabs:
                tab.pack_forget()
            for tab in new_order:
                tab.pack(side=tk.LEFT, padx=2, pady=3)
            self.current_project.tabs = new_order
    
    # ========== УПРАВЛЕНИЕ ВКЛАДКАМИ ==========
    def add_new_tab(self, filename=None, content="", restore=False, pinned=False):
        if not self.current_project:
            temp_path = os.path.join(os.path.expanduser("~"), "RealCode_temp")
            os.makedirs(temp_path, exist_ok=True)
            self.load_project(temp_path)
        tab_title = Path(filename).name if filename else f"Безымянный {len(self.current_project.tabs) + 1}"
        tab = ModernTab(
            self.tabs_container,
            tab_title,
            self._close_tab,
            self.select_tab,
            self._toggle_pin
        )
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
        if filename:
            self.status_label.config(text=f"Открыт: {filename}")
        return tab
    
    def select_tab(self, tab):
        if not self.current_project or tab not in self.current_project.tabs:
            return
        if self.current_project.current_tab and self.current_project.current_tab in self.current_project.file_contents and self.editor:
            self.current_project.file_contents[self.current_project.current_tab] = self.editor.get("1.0", tk.END)
            if self.config.get("save_scroll_position", True):
                scroll_pos = self.editor.yview()[0]
                self.current_project.current_tab.save_scroll_position(scroll_pos)

        for t in self.current_project.tabs:
            t.set_active(t == tab)
        self.current_project.current_tab = tab

        if tab in self.current_project.file_contents:
            content = self.current_project.file_contents[tab]
        else:
            filename = self.current_project.files.get(tab)
            if filename and os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.current_project.file_contents[tab] = content
                except Exception as e:
                    content = ""
                    self.log(f"Ошибка загрузки: {e}")
            else:
                content = ""
                self.current_project.file_contents[tab] = ""

        if self.editor:
            self.editor.edit_modified(False)
            self.editor.delete("1.0", tk.END)
            display_content = content.rstrip('\n')
            self.editor.insert("1.0", display_content)
            self.editor.edit_modified(False)
            tab.set_modified(False)

            if self.config.get("save_scroll_position", True):
                scroll_pos = tab.get_scroll_position()
                if scroll_pos > 0:
                    self.editor.yview_moveto(scroll_pos)

            self.editor.mark_set(tk.INSERT, "1.0")
            self.editor.see("1.0")

            # === ПОДСВЕТКА ===
        if self.config.get("syntax_highlight", True) and self.highlighter:
            filename = self.current_project.files.get(tab)
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                self.highlighter.set_language(ext)
                self.highlighter.highlight_enabled = True
            else:
                self.highlighter.highlight_enabled = True

            if self.highlighter.highlight_enabled:
                # Принудительно обновляем геометрию перед подсветкой
                self.editor.update_idletasks()
                file_size = self.highlighter.get_file_size()
                if file_size <= self.highlighter.FULL_HIGHLIGHT_LIMIT:
                    self.highlighter.highlight(force=True)
                else:
                    self.highlighter.highlight_visible()

            # Обновляем номера строк и мини-карту
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap.update_minimap()

        if self.discord:
            self.discord._update_presence()
        self.current_project.save_state()

        if self.linter is not None:
            self.linter.schedule_lint(500)
    
    def _close_tab(self, tab):
        if not self.current_project or tab not in self.current_project.tabs:
            return
        if tab.pinned:
            messagebox.showinfo("Закрепленная вкладка", "Эта вкладка закреплена. Открепите её, чтобы закрыть.")
            return
        if tab.modified:
            response = messagebox.askyesnocancel("Сохранение", f"Сохранить изменения в '{tab.title}'?")
            if response is None:
                return
            elif response:
                self.select_tab(tab)
                self.save_file()
        try:
            idx = self.current_project.tabs.index(tab)
        except ValueError:
            idx = 0
        if tab in self.current_project.file_contents:
            del self.current_project.file_contents[tab]
        if tab in self.current_project.files:
            del self.current_project.files[tab]
        if tab in self.current_project.pinned_tabs:
            self.current_project.pinned_tabs.remove(tab)
        tab.destroy()
        if tab in self.current_project.tabs:
            self.current_project.tabs.remove(tab)
        if self.current_project.tabs:
            if idx >= len(self.current_project.tabs):
                idx = len(self.current_project.tabs) - 1
            self.select_tab(self.current_project.tabs[idx])
        else:
            self.current_project.current_tab = None
            self.show_welcome_screen()
            if self.editor:
                self.editor.delete("1.0", tk.END)
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
    
    # ========== УПРАВЛЕНИЕ ФАЙЛАМИ ==========
    def open_file(self):
        if not self.current_project:
            temp_path = os.path.join(os.path.expanduser("~"), "RealCode_temp")
            os.makedirs(temp_path, exist_ok=True)
            self.load_project(temp_path)
        file_path = filedialog.askopenfilename(
            initialdir=self.config.get("project_path", "."),
            filetypes=[
                ("Python", "*.py"),
                ("JavaScript", "*.js"),
                ("HTML", "*.html"),
                ("CSS", "*.css"),
                ("JSON", "*.json"),
                ("C++", "*.cpp"),
                ("C#", "*.cs"),
                ("Hold C", "*.h"),
                ("C", "*.c"),
                ("sh", "*.sh"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                for tab, fname in self.current_project.files.items():
                    if fname == file_path:
                        self.select_tab(tab)
                        return
                self.add_new_tab(filename=file_path, content=content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def save_file(self):
        if not self.current_project or not self.current_project.current_tab:
            return
        filename = self.current_project.files.get(self.current_project.current_tab)
        if not filename:
            self.save_file_as()
            return
        try:
            content = self.editor.get("1.0", tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            self.current_project.file_contents[self.current_project.current_tab] = content
            self.current_project.current_tab.set_modified(False)
            self.status_label.config(text=f"Сохранено: {filename}")
            self.log(f"✅ Сохранено: {Path(filename).name}")
            if self.current_project:
                self.current_project.add_to_recent(filename)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
    
    def save_file_as(self):
        if not self.current_project or not self.current_project.current_tab:
            return
        file_path = filedialog.asksaveasfilename(
            initialdir=self.config.get("project_path", "."),
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.current_project.files[self.current_project.current_tab] = file_path
            self.current_project.current_tab.title_label.config(text=Path(file_path).name)
            self.save_file()
    
    def open_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.config.get("last_opened_folder", "."),
            title="Выберите папку проекта"
        )
        if folder:
            self.load_project(folder)
            self.status_label.config(text=f"Открыта папка: {folder}")
    
    def load_project_tree(self):
        # Очищаем дерево
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        project_root = self.config.get("project_path", ".")
        if not os.path.exists(project_root):
            project_root = "."
        
        self.folder_label.config(text=os.path.basename(project_root))
        root_name = os.path.basename(os.path.abspath(project_root)) or "Проект"
        
        # Добавляем корневой узел с правильным отображением
        root_node = self.file_tree.insert(
            "", 
            "end", 
            text=f"📁 {root_name}", 
            open=True,
            values=("",)  # Пустое значение для корня
        )
        
        # Загружаем содержимое
        self._process_directory(project_root, root_node)
        
        # Обновляем отображение
        self.file_tree.update()
    
    def _process_directory(self, path, parent):
        try:
            items = os.listdir(path)
            dirs = []
            files = []
            show_hidden = self.config.get("show_hidden_files", False)
            
            for item in items:
                if not show_hidden and item.startswith('.'):
                    continue
                if item in ["__pycache__", ".git", ".idea", "venv", "node_modules"]:
                    continue
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)
            
            for item in dirs:
                full_path = os.path.join(path, item)
                # Добавляем папку с правильным тегом
                node = self.file_tree.insert(
                    parent, 
                    "end", 
                    text=f"📁 {item}", 
                    open=False,
                    values=(full_path, "dir")  # Добавляем тип
                )
                self._process_directory(full_path, node)
                self.file_tree.update()  # Обновляем после каждой папки
            
            for item in files:
                full_path = os.path.join(path, item)
                ext = os.path.splitext(item)[1].lower()
                icons = {
                    ".py": "🐍",
                    ".js": "📜",
                    ".html": "🌐",
                    ".css": "🎨",
                    ".json": "📦",
                    ".md": "📘",
                    ".txt": "📝",
                    ".exe": "⚙️",
                    ".png": "🖼️",
                    ".jpg": "🖼️",
                    ".jpeg": "🖼️",
                    ".gif": "🖼️",
                    ".svg": "🖼️",
                    ".ico": "🖼️",
                    ".gitignore": "🙈",
                    ".env": "🔑",
                    ".pyc": "🐍",
                    ".pyo": "🐍",
                    ".so": "📦",
                    ".dll": "📦",
                    ".dylib": "📦"
                }
                icon = icons.get(ext, "📄")
                self.file_tree.insert(
                    parent, 
                    "end", 
                    text=f"{icon} {item}", 
                    values=(full_path, "file")
                )
            
            # Обновляем отображение после обработки
            self.file_tree.update()
            
        except Exception as e:
            print(f"Ошибка обхода директории {path}: {e}")
            import traceback
            traceback.print_exc()
    
    def on_file_double_click(self, event):
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.file_tree.item(item, "values")
        
        if not values or len(values) < 1:
            return
        
        file_path = values[0]
        
        # Проверяем, что это файл, а не папка
        if os.path.isdir(file_path):
            # Разворачиваем/сворачиваем папку
            if self.file_tree.item(item, "open"):
                self.file_tree.item(item, open=False)
            else:
                self.file_tree.item(item, open=True)
            return
        
        # Открываем файл
        if os.path.isfile(file_path):
            try:
                # Проверяем, не открыт ли уже этот файл
                for tab, fname in self.current_project.files.items():
                    if fname == file_path:
                        self.select_tab(tab)
                        return
                
                # Читаем содержимое
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Добавляем новую вкладку
                self.add_new_tab(filename=file_path, content=content)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def on_tree_open(self, event):
        if not self.current_project:
            return
        expanded = []
        for item in self.file_tree.get_children():
            if self.file_tree.item(item, "open"):
                values = self.file_tree.item(item, "values")
                if values:
                    expanded.append(values[0])
        self.current_project.set_expanded_folders(expanded)

    def refresh_file_tree(self):
        """Обновляет дерево файлов"""
        if hasattr(self, 'file_tree'):
            # Сохраняем раскрытые папки
            expanded = []
            def save_expanded(parent=""):
                for item in self.file_tree.get_children(parent):
                    if self.file_tree.item(item, "open"):
                        values = self.file_tree.item(item, "values")
                        if values and len(values) > 0:
                            expanded.append(values[0])
                    save_expanded(item)
            
            save_expanded()
            
            # Перезагружаем дерево
            self.load_project_tree()
            
            # Восстанавливаем раскрытые папки
            def restore_expanded(parent=""):
                for item in self.file_tree.get_children(parent):
                    values = self.file_tree.item(item, "values")
                    if values and len(values) > 0 and values[0] in expanded:
                        self.file_tree.item(item, open=True)
                        restore_expanded(item)
            
            restore_expanded()
    
    # ========== РЕДАКТОР ==========
    def on_key_release(self, event):
        if not self.current_project or not self.current_project.current_tab or not self.editor:
            return
        self.update_cursor_position()

        # Обновляем номера строк с задержкой
        if hasattr(self, '_line_numbers_after_id') and self._line_numbers_after_id:
            self.root.after_cancel(self._line_numbers_after_id)
        self._line_numbers_after_id = self.root.after(200, self._update_line_numbers_delayed)

        # Подсветка синтаксиса
        if self.config.get("syntax_highlight", True) and self.highlighter:
            file_size = self.highlighter.get_file_size()
            # Для файлов > 50 КБ не делаем инкрементальную подсветку при наборе (только после паузы)
            if file_size > 50 * 1024:
                if self._highlight_after_id:
                    self.root.after_cancel(self._highlight_after_id)
                self._highlight_after_id = self.root.after(500, self._delayed_highlight_visible)
            else:
                # Для маленьких файлов – подсвечиваем только текущую строку
                try:
                    current_line = int(self.editor.index(tk.INSERT).split('.')[0])
                except:
                    current_line = 1
                self.highlighter.incremental_highlight(current_line, current_line)
                # Полная подсветка после паузы (для обновления блочных комментариев и остальных строк)
                if self._highlight_after_id:
                    self.root.after_cancel(self._highlight_after_id)
                self._highlight_after_id = self.root.after(600, self._delayed_full_highlight)

        # Автосохранение
        if self.config.get("auto_save", False) and self.current_project.current_tab:
            if self.auto_save_timer:
                self.root.after_cancel(self.auto_save_timer)
            self.auto_save_timer = self.root.after(2000, self._auto_save)

        # Мини-карта с задержкой
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
        if not self.current_project or not self.current_project.current_tab or not self.editor:
            return
        if self.editor.edit_modified() and self.current_project.current_tab:
            self.current_project.current_tab.set_modified(True)
            self.editor.edit_modified(False)
    
    def _auto_save(self):
        if self.current_project and self.current_project.current_tab and self.current_project.current_tab.modified:
            self.save_file()
    
    def update_cursor_position(self, event=None):
        if not self.editor:
            return
        try:
            pos = self.editor.index(tk.INSERT)
            line, col = pos.split('.')
            self.pos_label.config(text=f"Стр {line}, Кол {int(col) + 1}")
        except:
            pass
    
    def on_editor_scroll(self, *args):
        if self.editor:
            self.editor.yview(*args)
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
            if self.highlighter and self.config.get("syntax_highlight", True) and self.highlighter.highlight_enabled:
                self.highlighter.highlight_visible()
    
    def on_editor_scrollbar_move(self, *args):
        if self.editor_scrollbar:
            self.editor_scrollbar.set(*args)
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
    
    def on_editor_wheel(self, event):
        if self.editor:
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap._draw_visible_area()
    
    def on_scroll(self, event=None):
        self.line_numbers.update_numbers()
        if self.minimap:
            if self._minimap_scroll_id:
                self.root.after_cancel(self._minimap_scroll_id)
            self._minimap_scroll_id = self.root.after(100, self._update_minimap_after_scroll)
    
    def _update_minimap_after_scroll(self):
        if self.minimap:
            self.minimap._draw_visible_area()
        self._minimap_scroll_id = None
    
    # ========== КОНТЕКСТНОЕ МЕНЮ И ПРАВКА ==========
    def show_editor_context_menu(self, event):
        if not self.current_project or not self.current_project.current_tab:
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

        # Проверяем, есть ли линт-сообщения в строке под курсором
        if self.linter and self._is_python_file(self.current_project.current_tab):
            try:
                # Получаем индекс строки по координатам клика
                index = self.editor.index(f"@{event.x},{event.y}")
                line = int(index.split('.')[0])
                messages = self.linter.get_messages_at_line(line)
                if messages:
                    menu.add_separator()
                    submenu = tk.Menu(menu, tearoff=0)
                    menu.add_cascade(label="Предупреждения", menu=submenu)
                    for msg in messages[:5]:  # показываем не более 5
                        text = f"{msg.code}: {msg.message[:50]}"
                        submenu.add_command(
                            label=text,
                            command=lambda m=msg: self._ignore_lint_message(m)
                        )
                    # Добавляем пункт "Игнорировать все в этой строке"
                    if len(messages) > 1:
                        menu.add_command(
                            label="Игнорировать все предупреждения в строке",
                            command=lambda msgs=messages: self._ignore_all_in_line(msgs)
                        )
            except:
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
        """Игнорировать конкретное сообщение."""
        if self.linter is not None:
            self.linter.ignore_message(msg)

    def _ignore_all_in_line(self, messages):
        """Игнорировать все сообщения в строке."""
        for msg in messages:
            if self.linter is not None:
                self.linter.ignore_message(msg)
    
    # ========== ЗАПУСК КОДА ==========
    def run_code(self):
        if not self.current_project or not self.current_project.current_tab:
            messagebox.showinfo("Информация", "Сначала откройте или создайте файл")
            return
        filename = self.current_project.files.get(self.current_project.current_tab)
        if not filename:
            self.save_file_as()
            filename = self.current_project.files.get(self.current_project.current_tab)
        if filename and os.path.exists(filename):
            self.save_file()
            if self.discord:
                self.discord.set_state("running")
            self.log(f"\n{'='*50}")
            self.log(f"▶ Запуск: {Path(filename).name}")
            self.log(f"📅 {datetime.now().strftime('%H:%M:%S')}")
            self.log('='*50)
            thread = threading.Thread(target=self._run_thread, args=(filename,), daemon=True)
            thread.start()

    def open_find(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            from tkinter import Toplevel, Label, Entry, Button, Frame
            dialog = Toplevel(self.root)
            dialog.title("Найти")
            dialog.geometry("400x150")
            dialog.configure(bg=VSColorScheme.BG_MEDIUM)
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            Label(dialog, text="Найти:", bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG).pack(pady=(10, 0))
            search_var = tk.StringVar()
            entry = Entry(dialog, textvariable=search_var, bg=VSColorScheme.BG_LIGHT,
                        fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG, width=40)
            entry.pack(pady=5, padx=20)
            entry.focus()
            entry.bind('<Return>', lambda e: self._find_text(search_var.get()))
            entry.bind('<Escape>', lambda e: dialog.destroy())
            
            btn_frame = Frame(dialog, bg=VSColorScheme.BG_MEDIUM)
            btn_frame.pack(pady=10)
            Button(btn_frame, text="Найти далее", command=lambda: self._find_text(search_var.get()),
                bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
            Button(btn_frame, text="Закрыть", command=dialog.destroy,
                bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        return "break"

    def _find_text(self, search_text):
        if not search_text:
            return
        self.editor.tag_remove("search", "1.0", tk.END)
        start = self.editor.index(tk.INSERT)
        pos = self.editor.search(search_text, start, tk.END)
        if not pos:
            pos = self.editor.search(search_text, "1.0", tk.END)
        if pos:
            end = f"{pos}+{len(search_text)}c"
            self.editor.tag_add("search", pos, end)
            self.editor.tag_config("search", background=VSColorScheme.SELECTION)
            self.editor.mark_set(tk.INSERT, end)
            self.editor.see(tk.INSERT)

    def go_to_line(self, event=None):
        if not self.editor or not self.current_project or not self.current_project.current_tab:
            return "break"
        try:
            total_lines = int(self.editor.index('end-1c').split('.')[0])
            dialog = tk.Toplevel(self.root)
            dialog.title("Перейти к строке")
            dialog.geometry("300x120")
            dialog.configure(bg=VSColorScheme.BG_MEDIUM)
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            tk.Label(dialog, text=f"Номер строки (1-{total_lines}):",
                    bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG).pack(pady=(10, 5))
            var = tk.StringVar()
            entry = tk.Entry(dialog, textvariable=var, bg=VSColorScheme.BG_LIGHT,
                            fg=VSColorScheme.FG, insertbackground=VSColorScheme.FG, width=10)
            entry.pack(pady=5)
            entry.focus()
            entry.bind('<Return>', lambda e: self._go_to_line_confirm(dialog, var, total_lines))
            entry.bind('<Escape>', lambda e: dialog.destroy())
            
            def on_close():
                try:
                    line = int(var.get())
                    if 1 <= line <= total_lines:
                        self.editor.mark_set(tk.INSERT, f"{line}.0")
                        self.editor.see(tk.INSERT)
                        self.update_cursor_position()
                except ValueError:
                    pass
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", on_close)
            tk.Button(dialog, text="Перейти", command=on_close,
                    bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT, padx=15).pack(pady=10)
            
            # Добавим обработку Enter через отдельную функцию, чтобы не дублировать код
            def on_enter(e):
                on_close()
            entry.bind('<Return>', on_enter)
            
        except Exception as e:
            print(f"Ошибка перехода к строке: {e}")
        return "break"

    def _go_to_line_confirm(self, dialog, var, total_lines):
        try:
            line = int(var.get())
            if 1 <= line <= total_lines:
                self.editor.mark_set(tk.INSERT, f"{line}.0")
                self.editor.see(tk.INSERT)
                self.update_cursor_position()
        except ValueError:
            pass
        dialog.destroy()
    
    def _run_thread(self, filename):
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            result = subprocess.run(
                [sys.executable, filename],
                capture_output=True,
                text=True,
                encoding='utf-8',
                env=env
            )
            if result.stdout:
                self.log(result.stdout)
            if result.stderr:
                self.log("❌ ОШИБКА:")
                self.log(result.stderr)
            self.log("=" * 50)
            self.log("✅ Завершено")
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
        finally:
            if self.discord:
                self.discord.set_state("editing")
    
    # ========== КОНСОЛЬ ==========
    def log(self, text):
        if not self.console or not self.console.winfo_exists():
            return
        try:
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, text + "\n")
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
            self.console.yview_moveto(1.0)
        except:
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
    
    # ========== УПРАВЛЕНИЕ ЭКРАНОМ ПРИВЕТСТВИЯ ==========
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
    
    # ========== УПРАВЛЕНИЕ ПАНЕЛЯМИ ==========
    def toggle_explorer(self):
        if self.explorer_visible:
            self.main_paned.forget(self.explorer_frame)
            self.explorer_visible = False
        else:
            explorer_pos = self.config.get("explorer_position", "left")
            if explorer_pos == "left":
                self.main_paned.insert(0, self.explorer_frame, width=self.config.get("sidebar_width", 250))
            else:
                self.main_paned.add(self.explorer_frame, width=self.config.get("sidebar_width", 250))
            self.explorer_visible = True
        self.show_explorer_var.set(self.explorer_visible)
        self.config["sidebar_visible"] = self.explorer_visible
    
    def toggle_console(self):
        if self.console_visible:
            self.center_paned.forget(self.console_area)
            self.console_visible = False
        else:
            console_pos = self.config.get("console_position", "bottom")
            if console_pos == "bottom":
                self.center_paned.add(self.console_area, height=self.config.get("console_height", 200))
            else:
                self.center_paned.insert(0, self.console_area, height=self.config.get("console_height", 200))
            self.console_visible = True
        self.show_console_var.set(self.console_visible)
        self.config["console_visible"] = self.console_visible
    
    def move_explorer(self):
        new_pos = self.explorer_pos_var.get()
        old_pos = self.config.get("explorer_position")
        if old_pos == new_pos:
            return
        self.config["explorer_position"] = new_pos
        if self.explorer_visible:
            try:
                current_width = self.main_paned.sash_coord(0)[0]
            except:
                current_width = self.config.get("sidebar_width", 250)
            self.main_paned.forget(self.explorer_frame)
            self.main_paned.forget(self.center_paned)
            if new_pos == "left":
                self.main_paned.add(self.explorer_frame, width=current_width)
                self.main_paned.add(self.center_paned)
            else:
                self.main_paned.add(self.center_paned)
                self.main_paned.add(self.explorer_frame, width=current_width)
    
    def move_console(self):
        new_pos = self.console_pos_var.get()
        old_pos = self.config.get("console_position")
        if old_pos == new_pos:
            return
        self.config["console_position"] = new_pos
        if self.console_visible:
            try:
                current_height = self.center_paned.sash_coord(0)[1]
            except:
                current_height = self.config.get("console_height", 200)
            self.center_paned.forget(self.editor_area)
            self.center_paned.forget(self.console_area)
            if new_pos == "bottom":
                self.center_paned.add(self.editor_area)
                self.center_paned.add(self.console_area, height=current_height)
            else:
                self.center_paned.add(self.console_area, height=current_height)
                self.center_paned.add(self.editor_area)
    
    # ========== НАСТРОЙКИ ==========
    def zoom_in(self):
        self.config["font_size"] = min(24, self.config["font_size"] + 1)
        if self.editor:
            self.editor.config(font=(self.config["font_family"], self.config["font_size"]))
    
    def zoom_out(self):
        self.config["font_size"] = max(8, self.config["font_size"] - 1)
        if self.editor:
            self.editor.config(font=(self.config["font_family"], self.config["font_size"]))
    
    def open_settings(self):
        """Открытие настроек"""
        SettingsDialog(self.root, self.config, self.apply_settings)
    
    def apply_settings(self, new_config):
        old_pos = self.config.get("explorer_position")
        old_console_pos = self.config.get("console_position")
        self.config = new_config
        save_config(self.config)

        # Применяем настройки шрифта
        if self.editor:
            self.editor.config(
                font=(self.config["font_family"], self.config["font_size"]),
                wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
                tabs=(self.config["tab_size"] * 10,)
            )

        # Подсветка синтаксиса
        if self.config.get("syntax_highlight", True) and self.highlighter:
            tab = self.current_project.current_tab if self.current_project else None
            if tab:
                filename = self.current_project.files.get(tab)
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    self.highlighter.set_language(ext)
                    self.highlighter.highlight_enabled = True
                else:
                    self.highlighter.highlight_enabled = True

                if self.highlighter.highlight_enabled:
                    self.editor.update_idletasks()
                    file_size = self.highlighter.get_file_size()
                    if file_size <= self.highlighter.FULL_HIGHLIGHT_LIMIT:
                        self.highlighter.highlight(force=True)
                    else:
                        self.highlighter.highlight_visible()

        # Размеры панелей
        if self.explorer_visible:
            self.main_paned.paneconfig(self.explorer_frame, width=self.config.get("sidebar_width", 250))
        if self.console_visible:
            self.center_paned.paneconfig(self.console_area, height=self.config.get("console_height", 200))

        # Перемещение панелей, если изменилась позиция
        if old_pos != self.config.get("explorer_position"):
            self.move_explorer()
        if old_console_pos != self.config.get("console_position"):
            self.move_console()

        # Мини-карта
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

        # Обновляем номера строк
        if self.line_numbers:
            self.line_numbers.update_numbers()

        self.status_label.config(text="Настройки применены")
        self.load_project_tree()

    def _bind_tab_shortcuts(self):
        """Привязка Tab и Shift+Tab в редакторе"""
        if not self.editor:
            return
        
        try:
            # Tab - вставляет 4 пробела
            self.editor.bind('<Tab>', self._on_tab_pressed)
            # Shift+Tab - удаляет 4 пробела в начале строки
            self.editor.bind('<Shift-Tab>', self._on_shift_tab_pressed)
            # Альтернатива для Linux
            self.editor.bind('<ISO_Left_Tab>', self._on_shift_tab_pressed)
            print("✅ Tab/Shift+Tab привязаны")
        except Exception as e:
            print(f"⚠️ Ошибка привязки Tab: {e}")

    def _on_tab_pressed(self, event):
        """Tab - вставляет 4 пробела или сдвигает выделенные строки"""
        try:
            # Проверяем, есть ли выделение
            if self.editor.tag_ranges('sel'):
                # Получаем выделение
                sel_start = self.editor.index(tk.SEL_FIRST)
                sel_end = self.editor.index(tk.SEL_LAST)
                
                # Определяем строки
                start_line = int(sel_start.split('.')[0])
                end_line = int(sel_end.split('.')[0])
                
                # Если выделение заканчивается в начале строки, корректируем
                if int(sel_end.split('.')[1]) == 0 and end_line > start_line:
                    end_line -= 1
                
                # Добавляем 4 пробела в начало каждой строки
                for line in range(start_line, end_line + 1):
                    self.editor.insert(f"{line}.0", '    ')
                
                # Восстанавливаем выделение
                self.editor.tag_remove(tk.SEL, "1.0", tk.END)
                self.editor.tag_add(tk.SEL, f"{start_line}.0", f"{end_line + 1}.0")
                
                return "break"
            else:
                # Нет выделения - просто вставляем пробелы
                self.editor.insert(tk.INSERT, '    ')
                return "break"
        except Exception as e:
            print(f"Tab error: {e}")
            return "break"

    def _on_shift_tab_pressed(self, event):
        """Shift+Tab - удаляет 4 пробела в начале выделенных строк"""
        try:
            if self.editor.tag_ranges('sel'):
                sel_start = self.editor.index(tk.SEL_FIRST)
                sel_end = self.editor.index(tk.SEL_LAST)
                
                start_line = int(sel_start.split('.')[0])
                end_line = int(sel_end.split('.')[0])
                
                if int(sel_end.split('.')[1]) == 0 and end_line > start_line:
                    end_line -= 1
                
                for line in range(start_line, end_line + 1):
                    # Проверяем первые 4 символа
                    text = self.editor.get(f"{line}.0", f"{line}.0+4c")
                    if text == '    ':
                        self.editor.delete(f"{line}.0", f"{line}.0+4c")
                
                # Восстанавливаем выделение
                self.editor.tag_remove(tk.SEL, "1.0", tk.END)
                self.editor.tag_add(tk.SEL, f"{start_line}.0", f"{end_line + 1}.0")
                
                return "break"
            else:
                # Нет выделения - удаляем 4 пробела в текущей строке
                line = self.editor.index(tk.INSERT).split('.')[0]
                text = self.editor.get(f"{line}.0", f"{line}.0+4c")
                if text == '    ':
                    self.editor.delete(f"{line}.0", f"{line}.0+4c")
                return "break"
        except Exception as e:
            print(f"Shift+Tab error: {e}")
            return "break"
    
    # ========== МЕНЮ И ГОРЯЧИЕ КЛАВИШИ ==========
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Настройка меню для предотвращения мерцания
        menubar.bind('<Enter>', lambda e: self.root.focus_force())
        menubar.bind('<Motion>', lambda e: self.root.update_idletasks())

        style = ttk.Style()
        style.theme_use('classic')  # или 'alt'
        
        menubar = tk.Menu(self.root, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый (Ctrl+N)", command=self.add_new_tab)
        file_menu.add_command(label="Открыть (Ctrl+O)", command=self.open_file)
        file_menu.add_command(label="Открыть папку (Ctrl+K)", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить (Ctrl+S)", command=self.save_file)
        file_menu.add_command(label="Сохранить как... (Ctrl+Shift+S)", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход (Alt+F4)", command=self.on_closing)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Вырезать (Ctrl+X)", command=self.cut)
        edit_menu.add_command(label="Копировать (Ctrl+C)", command=self.copy)
        edit_menu.add_command(label="Вставить (Ctrl+V)", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить всё (Alt+A)", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Найти (Ctrl+F)", command=self.open_find)
        edit_menu.add_command(label="Перейти к строке (Ctrl+G)", command=self.go_to_line)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Плагины", menu=tools_menu)
        tools_menu.add_command(label="Магазин плагинов", command=self.open_marketplace)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        self.show_explorer_var = tk.BooleanVar(value=self.explorer_visible)
        view_menu.add_checkbutton(label="Показать проводник", variable=self.show_explorer_var,
                                  command=self.toggle_explorer)
        self.show_console_var = tk.BooleanVar(value=self.console_visible)
        view_menu.add_checkbutton(label="Показать консоль", variable=self.show_console_var,
                                  command=self.toggle_console)
        view_menu.add_separator()
        explorer_pos_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Позиция проводника", menu=explorer_pos_menu)
        self.explorer_pos_var = tk.StringVar(value=self.config.get("explorer_position", "left"))
        explorer_pos_menu.add_radiobutton(label="Слева", variable=self.explorer_pos_var,
                                          value="left", command=self.move_explorer)
        explorer_pos_menu.add_radiobutton(label="Справа", variable=self.explorer_pos_var,
                                          value="right", command=self.move_explorer)
        console_pos_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Позиция консоли", menu=console_pos_menu)
        self.console_pos_var = tk.StringVar(value=self.config.get("console_position", "bottom"))
        console_pos_menu.add_radiobutton(label="Снизу", variable=self.console_pos_var,
                                         value="bottom", command=self.move_console)
        console_pos_menu.add_radiobutton(label="Сверху", variable=self.console_pos_var,
                                         value="top", command=self.move_console)
        view_menu.add_separator()
        view_menu.add_command(label="Увеличить шрифт (Ctrl++)", command=self.zoom_in)
        view_menu.add_command(label="Уменьшить шрифт (Ctrl+-)", command=self.zoom_out)
        
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Запуск", menu=run_menu)
        run_menu.add_command(label="Запустить (F5)", command=self.run_code)
        run_menu.add_separator()
        run_menu.add_command(label="Очистить консоль", command=self.clear_console)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Настройки (F1)", command=self.open_settings)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="Проверить обновления", command=self.manual_check_updates)
        help_menu.add_command(label="Сообщить о баге", command=self.report_bug)
        help_menu.add_command(label="О программе", command=self.show_about)

        self.root.update_idletasks()
        self.root.tk.call('update', 'idletasks')
        
        # Для Linux дополнительно:
        if is_linux():
            try:
                # Принудительная перерисовка меню
                menubar.tk.call('update', 'idletasks')
                self.root.after(10, lambda: menubar.tk.call('update', 'idletasks'))
            except:
                pass

    def report_bug(self):
        """Открывает диалог для отправки баг-репорта."""
        BugReportDialog(self.root, self)
    
    # ГЛОБАЛЬНЫЕ ГОРЯЧИЕ КЛАВИШИ
    def _bind_global_shortcuts(self):
        """Горячие клавиши с поддержкой русской раскладки"""
        
        def handler(event):
            if self._dialog_open:
                return
            
            # Получаем символ и модификаторы
            keysym = event.keysym
            state = event.state
            
            # Проверяем модификаторы
            ctrl = (state & 0x4) != 0 or (state & 0x40000) != 0
            shift = (state & 0x1) != 0 or (state & 0x20000) != 0
            alt = (state & 0x8) != 0 or (state & 0x80000) != 0
            
            # Словарь для преобразования русских клавиш в латинские
            # (только для комбинаций с Ctrl)
            if ctrl:
                # Если нажата русская клавиша - конвертируем в латиницу
                cyrillic_to_latin = {
                    'Cyrillic_a': 'a', 'Cyrillic_b': 'b', 'Cyrillic_c': 'c',
                    'Cyrillic_d': 'd', 'Cyrillic_e': 'e', 'Cyrillic_f': 'f',
                    'Cyrillic_g': 'g', 'Cyrillic_h': 'h', 'Cyrillic_i': 'i',
                    'Cyrillic_j': 'j', 'Cyrillic_k': 'k', 'Cyrillic_l': 'l',
                    'Cyrillic_m': 'm', 'Cyrillic_n': 'n', 'Cyrillic_o': 'o',
                    'Cyrillic_p': 'p', 'Cyrillic_r': 'r', 'Cyrillic_s': 's',
                    'Cyrillic_t': 't', 'Cyrillic_u': 'u', 'Cyrillic_v': 'v',
                    'Cyrillic_w': 'w', 'Cyrillic_x': 'x', 'Cyrillic_y': 'y',
                    'Cyrillic_z': 'z',
                    # Заглавные
                    'Cyrillic_A': 'a', 'Cyrillic_B': 'b', 'Cyrillic_C': 'c',
                    'Cyrillic_D': 'd', 'Cyrillic_E': 'e', 'Cyrillic_F': 'f',
                    'Cyrillic_G': 'g', 'Cyrillic_H': 'h', 'Cyrillic_I': 'i',
                    'Cyrillic_J': 'j', 'Cyrillic_K': 'k', 'Cyrillic_L': 'l',
                    'Cyrillic_M': 'm', 'Cyrillic_N': 'n', 'Cyrillic_O': 'o',
                    'Cyrillic_P': 'p', 'Cyrillic_R': 'r', 'Cyrillic_S': 's',
                    'Cyrillic_T': 't', 'Cyrillic_U': 'u', 'Cyrillic_V': 'v',
                    'Cyrillic_W': 'w', 'Cyrillic_X': 'x', 'Cyrillic_Y': 'y',
                    'Cyrillic_Z': 'z'
                }
                
                # Если это русская клавиша - заменяем на латинскую
                if keysym in cyrillic_to_latin:
                    keysym = cyrillic_to_latin[keysym]
            
            # Обработка специальных клавиш (F1, F5 и т.д.)
            if keysym == 'F5' and not ctrl and not alt and not shift:
                self.run_code()
                return "break"
            
            if keysym == 'F1' and not ctrl and not alt and not shift:
                self.open_settings()
                return "break"
            
            # Ctrl+комбинации (с поддержкой русских клавиш)
            if ctrl and not alt:
                # Новый файл (Ctrl+N)
                if keysym in ['n', 'N']:
                    self.add_new_tab()
                    return "break"
                
                # Открыть (Ctrl+O)
                if keysym in ['o', 'O']:
                    self.open_file()
                    return "break"
                
                # Открыть папку (Ctrl+K)
                if keysym in ['k', 'K']:
                    self.open_folder()
                    return "break"
                
                # Сохранить (Ctrl+S)
                if keysym in ['s', 'S']:
                    if shift:
                        self.save_file_as()
                    else:
                        self.save_file()
                    return "break"
                
                # Закрыть вкладку (Ctrl+W)
                if keysym in ['w', 'W']:
                    self.close_current_tab()
                    return "break"
                
                # Вырезать (Ctrl+X)
                if keysym in ['x', 'X']:
                    self.cut()
                    return "break"
                
                # Копировать (Ctrl+C)
                if keysym in ['c', 'C']:
                    self.copy()
                    return "break"
                
                # Вставить (Ctrl+V)
                if keysym in ['v', 'V']:
                    self.paste()
                    return "break"
                
                # Выделить всё (Ctrl+A)
                if keysym in ['a', 'A']:
                    self.select_all()
                    return "break"
                
                # Найти (Ctrl+F)
                if keysym in ['f', 'F']:
                    self.open_find()
                    return "break"
                
                # Перейти к строке (Ctrl+G)
                if keysym in ['g', 'G']:
                    self.go_to_line()
                    return "break"
                
                # Запуск (Ctrl+R) - альтернатива F5
                if keysym in ['r', 'R']:
                    self.run_code()
                    return "break"
                
                # Увеличение шрифта (Ctrl+Plus/Ctrl+=)
                if keysym in ['plus', 'equal', 'KP_Add']:
                    self.zoom_in()
                    return "break"
                
                # Уменьшение шрифта (Ctrl+Minus)
                if keysym in ['minus', 'KP_Subtract']:
                    self.zoom_out()
                    return "break"
        
        # Привязываем обработчик
        self.root.bind_all('<Key>', handler)
        
        # Дополнительно привязываем к редактору
        if self.editor:
            self.editor.bind_all('<Key>', handler)
        
        print("✅ Горячие клавиши настроены (с поддержкой русского языка)")
    
    # ========== ДИАЛОГИ ==========
    def show_about(self):
        about_text = f"""{APP_NAME} v{VERSION}

Привет, друг! Это K1sh-M1sh! Да, я параллельно разрабатываю и Warshot и RealCode!
Вообще, я разрабатывал для личного использования, но позже решил выложить исходники на Github, вот ты и читаешь данную писанину...
Разработан на Python с использованием Tkinter.
Пытался спарадировать VS Code, да что-то и получилось.

Возможности:
• Подсветка синтаксиса Python
• Мультипроектная архитектура
• Сохранение закрепленных вкладок
• Discord Rich Presence
• Автоматическое обновление
• Номера строк
• Миникарта для навигации
• Поиск (Ctrl+F)
• Переход к строке (Ctrl+G)
• Встроенная консоль
• Экран приветствия
• Настраиваемые панели
• Горячие клавиши

Также, я начал поддерживать Linux подобные системы, но система не доработана. Поэтому, если вы заметите баги, то напишите мне, буду благодарен.

© 2026 RealCode
        """
        messagebox.showinfo("О программе", about_text)
    
    # ========== ИНТЕРФЕЙС ==========
    def _create_widgets(self):
        self._create_toolbar()
        main = tk.Frame(self.root, bg=VSColorScheme.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)
        self.main_paned = tk.PanedWindow(
            main,
            orient=tk.HORIZONTAL,
            bg=VSColorScheme.BORDER,
            sashwidth=5,
            sashrelief=tk.FLAT,
            sashcursor="sb_h_double_arrow"
        )
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        self._create_explorer()
        self._create_center_panel()
        self._create_status_bar()
        explorer_pos = self.config.get("explorer_position", "left")
        if explorer_pos == "left":
            self.main_paned.add(self.explorer_frame, width=self.config.get("sidebar_width", 250))
            self.main_paned.add(self.center_paned)
        else:
            self.main_paned.add(self.center_paned)
            self.main_paned.add(self.explorer_frame, width=self.config.get("sidebar_width", 250))
        console_pos = self.config.get("console_position", "bottom")
        if console_pos == "top":
            self.center_paned.paneconfig(self.editor_area, after=self.console_area)
        self.welcome_screen = WelcomeScreen(self.editor_area, self)
    
    def _create_toolbar(self):
        toolbar = tk.Frame(self.root, bg=VSColorScheme.BG_MEDIUM, height=45)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        buttons = [
            ("📁", "Открыть файл", self.open_file),
            ("📂", "Открыть папку", self.open_folder),
            ("💾", "Сохранить", self.save_file),
            ("📄", "Новый", self.add_new_tab),
            ("▶", "Запуск", self.run_code),
            ("⚙", "Настройки", self.open_settings),
            ("🔄", "Обновления", self.manual_check_updates)
        ]
        for icon, text, cmd in buttons:
            btn = tk.Label(
                toolbar,
                text=f"{icon}  {text}",
                bg=VSColorScheme.BG_MEDIUM,
                fg=VSColorScheme.FG,
                font=("Segoe UI", 9),
                padx=15,
                pady=12,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=VSColorScheme.BG_LIGHT))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=VSColorScheme.BG_MEDIUM))
            btn.bind('<Button-1>', lambda e, c=cmd: c())
    
    def _create_explorer(self):
        self.explorer_frame = tk.Frame(self.main_paned, bg=VSColorScheme.BG_MEDIUM)
        explorer_header = tk.Frame(self.explorer_frame, bg=VSColorScheme.BG_MEDIUM)
        explorer_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            explorer_header,
            text="ПРОВОДНИК",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG_LIGHT,
            font=("Segoe UI", 9, "bold")
        ).pack(side=tk.LEFT)
        
        close_explorer_btn = tk.Label(
            explorer_header,
            text="✕",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10, "bold"),
            padx=8,
            cursor="hand2"
        )
        close_explorer_btn.pack(side=tk.RIGHT)
        close_explorer_btn.bind('<Enter>', lambda e: close_explorer_btn.configure(bg=VSColorScheme.ACCENT))
        close_explorer_btn.bind('<Leave>', lambda e: close_explorer_btn.configure(bg=VSColorScheme.BG_MEDIUM))
        close_explorer_btn.bind('<Button-1>', lambda e: self.toggle_explorer())
        
        self.folder_label = tk.Label(
            self.explorer_frame,
            text=os.path.basename(self.config["project_path"]),
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 8),
            wraplength=230
        )
        self.folder_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        btn_frame = tk.Frame(self.explorer_frame, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        open_folder_btn = tk.Label(
            btn_frame,
            text="📂 Открыть папку",
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 9),
            pady=4,
            cursor="hand2"
        )
        open_folder_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        open_folder_btn.bind('<Button-1>', lambda e: self.open_folder())
        
        refresh_btn = tk.Label(
            btn_frame,
            text="↻",
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 9),
            width=3,
            pady=4,
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(2, 0))
        refresh_btn.bind('<Button-1>', lambda e: self.load_project_tree())
        
        # ИСПРАВЛЕНИЕ: Создаем Treeview с правильными настройками
        self.file_tree = ttk.Treeview(
            self.explorer_frame,
            show="tree",  # Показываем только дерево
            selectmode="browse",
            height=20  # Высота в строках
        )
        
        # Настройка стилей для Treeview
        style = ttk.Style()
        style.theme_use("clam")
        
        # Настройка цветов
        style.configure(
            "Treeview",
            background=VSColorScheme.BG_LIGHT,
            foreground=VSColorScheme.FG,
            fieldbackground=VSColorScheme.BG_LIGHT,
            borderwidth=0,
            rowheight=25  # Высота строки для лучшей читаемости
        )
        
        # Настройка выделения
        style.map(
            "Treeview",
            background=[("selected", VSColorScheme.SELECTION)],
            foreground=[("selected", "white")]
        )
        
        # Настройка заголовков (скрываем)
        style.configure(
            "Treeview.Heading",
            background=VSColorScheme.BG_MEDIUM,
            foreground=VSColorScheme.FG,
            relief="flat"
        )
        
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Привязываем события
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        
        # Добавляем прокрутку (опционально)
        scrollbar = ttk.Scrollbar(
            self.explorer_frame,
            orient=tk.VERTICAL,
            command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_center_panel(self):
        self.center_paned = tk.PanedWindow(
            self.main_paned,
            orient=tk.VERTICAL,
            bg=VSColorScheme.BORDER,
            sashwidth=5,
            sashrelief=tk.FLAT,
            sashcursor="sb_v_double_arrow"
        )
        self._create_editor_area()
        self._create_console_area()
        self.center_paned.add(self.editor_area, height=500)
        self.center_paned.add(self.console_area, height=self.config.get("console_height", 200))
    
    def _create_editor_area(self):
        self.editor_area = tk.Frame(self.center_paned, bg=VSColorScheme.BG_DARK)
        self.tab_bar = tk.Frame(self.editor_area, bg=VSColorScheme.BG_MEDIUM, height=55)
        self.tab_bar.pack(fill=tk.X)
        self.tab_bar.pack_propagate(False)

        self.tabs_container = tk.Frame(self.tab_bar, bg=VSColorScheme.BG_MEDIUM, height=50)
        self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tabs_container.pack_propagate(False)

        new_tab_btn = tk.Label(
            self.tab_bar,
            text="+  Добавить вкладку",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10),
            padx=20,
            pady=15,
            cursor="hand2"
        )
        new_tab_btn.pack(side=tk.RIGHT)
        new_tab_btn.bind('<Enter>', lambda e: new_tab_btn.configure(bg=VSColorScheme.BG_LIGHT))
        new_tab_btn.bind('<Leave>', lambda e: new_tab_btn.configure(bg=VSColorScheme.BG_MEDIUM))
        new_tab_btn.bind('<Button-1>', lambda e: self.add_new_tab())

        self.editor_container = tk.Frame(self.editor_area, bg=VSColorScheme.BG_DARK)
        self.editor_container.pack(fill=tk.BOTH, expand=True)

        editor_inner = tk.Frame(self.editor_container, bg=VSColorScheme.BG_DARK)
        editor_inner.pack(fill=tk.BOTH, expand=True)

        # Номера строк
        self.line_numbers = LineNumbers(editor_inner, None, app=self)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Редактор
        self.editor = tk.Text(
            editor_inner,
            wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
            font=(self.config["font_family"], self.config["font_size"]),
            bg=VSColorScheme.BG_DARK,
            fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            selectbackground=VSColorScheme.SELECTION,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10,
            undo=True,
            maxundo=100,
            tabs=(self.config["tab_size"] * 10,)
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._bind_tab_shortcuts()

        # Привязываем line_numbers к редактору
        self.line_numbers.text_widget = self.editor
        self.line_numbers.update_numbers()

        # Скроллбар
        self.editor_scrollbar = tk.Scrollbar(
            editor_inner,
            orient=tk.VERTICAL,
            command=self.on_editor_scroll,
            bg=VSColorScheme.SCROLLBAR,
            troughcolor=VSColorScheme.BG_DARK,
            width=12
        )
        self.editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=self.on_editor_scrollbar_move)

        # Мини-карта
        if self.config.get("minimap_enabled", True):
            self.minimap = Minimap(editor_inner, self.editor)
            self.minimap.pack(side=tk.RIGHT, fill=tk.Y)

        # События
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<<Modified>>', self.on_text_modified)
        self.editor.bind('<MouseWheel>', self.on_editor_wheel)
        self.editor.bind('<Button-3>', self.show_editor_context_menu)
        self.editor_scrollbar.bind('<B1-Motion>', self.on_scroll)

        # Подсветка синтаксиса
        self.highlighter = SyntaxHighlighter(self.editor)

        # Линтер (проверка Python)
        self.linter = Linter(self.editor, self)

        # ВНИМАНИЕ: welcome_screen создаётся в _create_widgets, НЕ создаём его здесь!
    
    def _create_console_area(self):
        self.console_area = tk.Frame(self.center_paned, bg=VSColorScheme.BG_DARK)
        console_header = tk.Frame(self.console_area, bg=VSColorScheme.STATUS_BG, height=25)
        console_header.pack(fill=tk.X)
        console_header.pack_propagate(False)
        tk.Label(
            console_header,
            text="КОНСОЛЬ",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            padx=10
        ).pack(side=tk.LEFT)
        clear_console_btn = tk.Label(
            console_header,
            text="🗑 Очистить",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 9),
            padx=10,
            cursor="hand2"
        )
        clear_console_btn.pack(side=tk.RIGHT)
        clear_console_btn.bind('<Button-1>', lambda e: self.clear_console())
        close_console_btn = tk.Label(
            console_header,
            text="✕",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            cursor="hand2"
        )
        close_console_btn.pack(side=tk.RIGHT)
        close_console_btn.bind('<Enter>', lambda e: close_console_btn.configure(bg="#e81123"))
        close_console_btn.bind('<Leave>', lambda e: close_console_btn.configure(bg=VSColorScheme.STATUS_BG))
        close_console_btn.bind('<Button-1>', lambda e: self.toggle_console())
        
        console_container = tk.Frame(self.console_area, bg=VSColorScheme.BG_DARK)
        console_container.pack(fill=tk.BOTH, expand=True)
        self.console = tk.Text(
            console_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=VSColorScheme.BG_DARK,
            fg=VSColorScheme.FG_LIGHT,
            relief=tk.FLAT,
            borderwidth=0,
            padx=5,
            pady=5,
            state=tk.DISABLED
        )
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console_scrollbar = tk.Scrollbar(
            console_container,
            orient=tk.VERTICAL,
            command=self.console.yview,
            bg=VSColorScheme.SCROLLBAR,
            troughcolor=VSColorScheme.BG_DARK,
            width=12
        )
        self.console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=self.console_scrollbar.set)
    
    def _create_status_bar(self):
        status = tk.Frame(self.root, bg=VSColorScheme.STATUS_BG, height=25)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        status.pack_propagate(False)
        self.status_label = tk.Label(
            status,
            text="Готов",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 9),
            padx=10
        )
        self.status_label.pack(side=tk.LEFT)
        self.pos_label = tk.Label(
            status,
            text="Стр 1, Кол 1",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 9),
            padx=10
        )
        self.pos_label.pack(side=tk.RIGHT)
    
    # ========== УВЕДОМЛЕНИЕ ==========
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
        label = tk.Label(
            self._notification,
            text=message,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10,
            wraplength=380,
            justify="center"
        )
        label.pack(fill=tk.BOTH, expand=True)
        self._notification.after(duration, self._notification.destroy)
    
    # ========== ЗАВЕРШЕНИЕ РАБОТЫ ==========
    def on_closing(self):
        if self.current_project:
            unsaved = []
            for tab in self.current_project.tabs:
                if tab.modified:
                    unsaved.append(tab.title)
            if unsaved:
                response = messagebox.askyesnocancel(
                    "Несохраненные изменения",
                    f"Вы не сохранили:\n{', '.join(unsaved)}\n\nСохранить перед выходом?"
                )
                if response is None:
                    return
                elif response:
                    for tab in self.current_project.tabs:
                        if tab.modified:
                            self.select_tab(tab)
                            self.save_file()
            self.save_project_state()
        if self.discord:
            self.discord.disconnect()
            time.sleep(0.2)
        self.config["sidebar_visible"] = self.explorer_visible
        self.config["console_visible"] = self.console_visible
        self.config["window_maximized"] = (self.root.state() == 'zoomed')
        if not self.config["window_maximized"]:
            self.config["window_x"] = self.root.winfo_x()
            self.config["window_y"] = self.root.winfo_y()
            self.config["window_width"] = self.root.winfo_width()
            self.config["window_height"] = self.root.winfo_height()
        if self.explorer_visible and len(self.main_paned.panes()) > 1:
            try:
                self.config["sidebar_width"] = self.main_paned.sash_coord(0)[0]
            except:
                pass
        if self.console_visible and len(self.center_paned.panes()) > 1:
            try:
                self.config["console_height"] = self.center_paned.sash_coord(0)[1]
            except:
                pass
        self.config["last_opened_folder"] = self.config.get("project_path", ".")
        save_config(self.config)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.root.quit()
        self.root.destroy()

class FindDialog:
    def __init__(self, parent, text_widget, app):
        self.parent = parent
        self.text_widget = text_widget
        self.app = app
        self.dialog = None
        self.search_var = tk.StringVar()
        self.app._dialog_open = True
        self._show()
    
    def _show(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Поиск")
        self.dialog.geometry("400x150")
        self.dialog.configure(bg=VSColorScheme.BG_MEDIUM)
        self.dialog.transient(self.parent)
        # self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        # Сброс флага при любом уничтожении
        self.dialog.bind('<Destroy>', lambda e: setattr(self.app, '_dialog_open', False))
        
        tk.Label(self.dialog, text="Найти:", bg=VSColorScheme.BG_MEDIUM,
                 fg=VSColorScheme.FG).pack(pady=(10, 0))
        
        entry = tk.Entry(self.dialog, textvariable=self.search_var,
                         bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG,
                         insertbackground=VSColorScheme.FG, width=40)
        entry.pack(pady=5, padx=20)
        entry.focus()
        entry.bind('<Return>', lambda e: self._find())
        entry.bind('<Escape>', lambda e: self._on_close())
        
        btn_frame = tk.Frame(self.dialog, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Найти далее", command=self._find,
                  bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT, padx=15
                  ).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=self._on_close,
                  bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT, padx=15
                  ).pack(side=tk.LEFT, padx=5)
    
    def _find(self):
        search_text = self.search_var.get()
        if not search_text:
            return
        self.text_widget.tag_remove("search", "1.0", tk.END)
        start = self.text_widget.index(tk.INSERT)
        pos = self.text_widget.search(search_text, start, tk.END)
        if not pos:
            pos = self.text_widget.search(search_text, "1.0", tk.END)
        if pos:
            end = f"{pos}+{len(search_text)}c"
            self.text_widget.tag_add("search", pos, end)
            self.text_widget.tag_config("search", background=VSColorScheme.SELECTION)
            self.text_widget.mark_set(tk.INSERT, end)
            self.text_widget.see(tk.INSERT)
    
    def _on_close(self):
        self.app._dialog_open = False
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()

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

            # Определяем язык
            lang = 'python'
            if self.app.current_project and self.app.current_project.current_tab:
                filename = self.app.current_project.files.get(self.app.current_project.current_tab)
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    ext_map = {
                        '.py': 'python',
                        '.c': 'c',
                        '.cpp': 'cpp',
                        '.cxx': 'cpp',
                        '.cc': 'cpp',
                        '.cs': 'csharp',
                        '.hc': 'holyc',
                        '.holyc': 'holyc'
                    }
                    lang = ext_map.get(ext, 'python')

            if lang == 'python':
                messages = self._lint_python(code)
            elif lang in ('c', 'cpp'):
                messages = self._lint_with_clang(code, lang)
            elif lang == 'csharp':
                messages = self._lint_with_csc(code)
            elif lang == 'holyc':
                messages = self._lint_holyc_basic(code)

            # Фильтр игнорируемых
            filtered = []
            for msg in messages:
                key = (msg.code, msg.line, msg.message)
                if key not in self.ignored_messages:
                    filtered.append(msg)

            self.app.root.after(0, self._apply_lint_results, filtered)
        except Exception as e:
            print(f"Lint thread error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False

    # ---------- Python (pyflakes + pycodestyle) ----------
    def _lint_python(self, code):
        messages = []
        # pyflakes
        if pyflakes is not None:
            try:
                import sys
                from io import StringIO
                import contextlib
                with contextlib.redirect_stdout(StringIO()) as output:
                    pyflakes.api.check(code, filename='<string>')
                    output_text = output.getvalue()
                for line in output_text.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            line_num = int(parts[1])
                            col = int(parts[2])
                            msg = parts[3].strip()
                            code_match = re.search(r'([A-Z]\d+)\s+(.*)', msg)
                            if code_match:
                                code_str = code_match.group(1)
                                msg_text = code_match.group(2)
                            else:
                                code_str = 'F?'
                                msg_text = msg
                            messages.append(LintMessage(
                                line=line_num, column=col, message=msg_text,
                                code=code_str, level='warning', source='pyflakes'
                            ))
                        except:
                            pass
            except Exception:
                pass

        # pycodestyle
        if pycodestyle is not None:
            try:
                import tempfile
                import sys
                from io import StringIO
                import contextlib
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(code)
                    tmpname = f.name
                with contextlib.redirect_stdout(StringIO()) as output:
                    style_guide = pycodestyle.StyleGuide()
                    style_guide.check_files([tmpname])
                    output_text = output.getvalue()
                os.unlink(tmpname)
                ignored_codes = {'E501', 'E225', 'E302', 'E303'}  # можно настроить
                for line in output_text.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            line_num = int(parts[1])
                            col = int(parts[2])
                            rest = parts[3].strip()
                            code_match = re.match(r'([A-Z]\d+)\s+(.*)', rest)
                            if code_match:
                                code_str = code_match.group(1)
                                msg_text = code_match.group(2)
                            else:
                                code_str = 'E?'
                                msg_text = rest
                            if code_str in ignored_codes:
                                continue
                            messages.append(LintMessage(
                                line=line_num, column=col, message=msg_text,
                                code=code_str, level='warning', source='pep8'
                            ))
                        except:
                            pass
            except Exception:
                pass
        return messages

    # ---------- Clang для C/C++ ----------
    def _lint_with_clang(self, code, lang):
        messages = []
        tmpname = None
        try:
            import tempfile, subprocess, os, re
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False, encoding='utf-8') as f:
                f.write(code)
                tmpname = f.name

            lang_flag = '-x c' if lang == 'c' else '-x c++'
            cmd = ['clang', '-fsyntax-only', '-fno-caret-diagnostics', lang_flag, tmpname]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            for line in result.stderr.splitlines():
                match = re.match(r'.+?:(\d+):(\d+):\s*(error|warning):\s*(.*)', line)
                if match:
                    line_num = int(match.group(1))
                    col = int(match.group(2))
                    level = match.group(3)
                    msg = match.group(4)
                    code_match = re.search(r'\[(.*?)\]', msg)
                    code_str = code_match.group(1) if code_match else 'C?'
                    messages.append(LintMessage(
                        line=line_num, column=col, message=msg.strip(),
                        code=code_str, level='error' if level == 'error' else 'warning',
                        source='clang'
                    ))
        except FileNotFoundError:
            self.app.log("⚠️ Clang не установлен. Установите LLVM.")
        except Exception as e:
            self.app.log(f"⚠️ Clang ошибка: {e}")
        finally:
            if tmpname and os.path.exists(tmpname):
                os.unlink(tmpname)
        return messages

    # ---------- C# через csc.exe ----------
    def _lint_with_csc(self, code):
        messages = []
        tmpname = None
        try:
            import tempfile, subprocess, os, re, shutil, glob
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False, encoding='utf-8') as f:
                f.write(code)
                tmpname = f.name

            csc_path = self._find_csc()
            if not csc_path:
                self.app.log("⚠️ C# компилятор не найден. Установите .NET SDK.")
                return []

            # Запускаем с кодировкой OEM (cp866) для русского вывода
            cmd = [csc_path, '/nologo', '/target:module', '/nowarn:1701,1702', tmpname]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='cp866', errors='ignore')
            
            # Используем stderr, если есть, иначе stdout
            output = result.stderr if result.stderr else result.stdout
            if not output:
                return messages  # нет вывода — нет ошибок

            for line in output.splitlines():
                # Формат: filename(line,col): error/warning CSxxxx: message
                match = re.match(r'.+?\((\d+),(\d+)\):\s*(error|warning)\s+(\w+):\s*(.*)', line)
                if match:
                    line_num = int(match.group(1))
                    col = int(match.group(2))
                    level = match.group(3)
                    code_str = match.group(4)
                    msg = match.group(5)
                    messages.append(LintMessage(
                        line=line_num,
                        column=col,
                        message=msg.strip(),
                        code=code_str,
                        level='error' if level == 'error' else 'warning',
                        source='csc'
                    ))
        except Exception as e:
            self.app.log(f"⚠️ C# ошибка: {e}")
        finally:
            if tmpname and os.path.exists(tmpname):
                os.unlink(tmpname)
        return messages

    def _find_csc(self):
        import shutil, glob, os
        
        # 1. Проверяем PATH
        csc = shutil.which('csc.exe')
        if csc:
            return csc
        
        # 2. .NET Framework
        base_paths = [
            r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319",
            r"C:\Windows\Microsoft.NET\Framework\v4.0.30319",
        ]
        for path in base_paths:
            candidate = os.path.join(path, 'csc.exe')
            if os.path.exists(candidate):
                return candidate
        
        # 3. .NET SDK через DOTNET_ROOT
        dotnet_root = os.environ.get('DOTNET_ROOT')
        if dotnet_root:
            sdk_path = os.path.join(dotnet_root, 'sdk')
            if os.path.exists(sdk_path):
                for sdk_dir in glob.glob(os.path.join(sdk_path, '*')):
                    roslyn = os.path.join(sdk_dir, 'Roslyn', 'bincore', 'csc.exe')
                    if os.path.exists(roslyn):
                        return roslyn
                    roslyn2 = os.path.join(sdk_dir, 'Roslyn', 'bin', 'csc.exe')
                    if os.path.exists(roslyn2):
                        return roslyn2
        
        # 4. Visual Studio
        vs_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe",
        ]
        for path in vs_paths:
            if os.path.exists(path):
                return path
        
        return None

    # ---------- HolyC базовая проверка ----------
    def _lint_holyc_basic(self, code):
        messages = []
        lines = code.splitlines()
        open_braces = open_parens = open_brackets = 0
        in_string = in_comment = False

        for i, line in enumerate(lines, start=1):
            j = 0
            while j < len(line):
                ch = line[j]
                if in_comment:
                    if ch == '*' and j+1 < len(line) and line[j+1] == '/':
                        in_comment = False
                        j += 2
                        continue
                    j += 1
                    continue
                if ch == '/' and j+1 < len(line):
                    if line[j+1] == '/':
                        break
                    if line[j+1] == '*':
                        in_comment = True
                        j += 2
                        continue
                if in_string:
                    if ch == '"' and (j == 0 or line[j-1] != '\\'):
                        in_string = False
                    j += 1
                    continue
                if ch == '"':
                    in_string = True
                    j += 1
                    continue
                if ch == '{': open_braces += 1
                elif ch == '}': open_braces -= 1
                elif ch == '(': open_parens += 1
                elif ch == ')': open_parens -= 1
                elif ch == '[': open_brackets += 1
                elif ch == ']': open_brackets -= 1
                j += 1

            stripped = line.strip()
            if stripped and not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}'):
                if not (stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('#')):
                    messages.append(LintMessage(
                        line=i, column=len(line)+1,
                        message="Возможно, отсутствует точка с запятой",
                        code='H004', level='warning', source='holyc'
                    ))

        if open_braces != 0:
            messages.append(LintMessage(1,1,f"Несбалансированные фигурные скобки: {open_braces}",'H001','error','holyc'))
        if open_parens != 0:
            messages.append(LintMessage(1,1,f"Несбалансированные круглые скобки: {open_parens}",'H002','error','holyc'))
        if open_brackets != 0:
            messages.append(LintMessage(1,1,f"Несбалансированные квадратные скобки: {open_brackets}",'H003','error','holyc'))
        return messages

    # ---------- Применение результатов ----------
    def _apply_lint_results(self, messages):
        self.text.tag_remove("lint_error", "1.0", tk.END)
        self.text.tag_remove("lint_warning", "1.0", tk.END)

        self.messages = messages
        for msg in messages:
            line_start = f"{msg.line}.0"
            line_end = f"{msg.line}.end"
            tag = "lint_error" if msg.level == 'error' else "lint_warning"
            self.text.tag_add(tag, line_start, line_end)

        self.text.tag_config("lint_error", underline=True, foreground="red")
        self.text.tag_config("lint_warning", underline=True, foreground="orange")

        if self.app.line_numbers:
            self.app.line_numbers.update_numbers()

        errors = len([m for m in messages if m.level == 'error'])
        warnings = len([m for m in messages if m.level == 'warning'])
        self.app.status_label.config(text=f"Ошибок: {errors}, Предупреждений: {warnings}")

    def get_messages_at_line(self, line):
        if not self.messages:
            return []
        return [m for m in self.messages if m.line == line]

    def ignore_message(self, msg):
        key = (msg.code, msg.line, msg.message)
        self.ignored_messages.add(key)
        self._save_ignored()
        self._start_lint()

class BugReportDialog:
    def __init__(self, parent, app):
        self.parent = parent
        
        try:
            if os.path.exists("iconBugReport.ico"):
                self.root.iconbitmap("iconBugReport.ico")
        except:
            pass

        self.app = app
        self.window = None
        self._show()

    def _set_grab(self):
        """Безопасный захват фокуса после отображения окна"""
        try:
            if self.window and self.window.winfo_exists():
                self.window.grab_set()
                self.window.focus_force()
        except Exception as e:
            print(f"⚠️ Ошибка захвата фокуса: {e}")

    def _show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Создание баг-репорта...")
        self.window.geometry("450x400")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        self.window.resizable(False, False)
        self.window.update_idletasks()
        self.window.after(100, self._set_grab)

        tk.Label(
            self.window,
            text="Создать баг-репорт:",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 14, "bold"),
            pady=10
        ).pack()

        tk.Label(
            self.window,
            text="Ваше имя (необязательно, можно никнейм):",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=30, pady=(10, 0))

        self.name_var = tk.StringVar()
        name_entry = tk.Entry(
            self.window,
            textvariable=self.name_var,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            font=("Segoe UI", 10),
            width=40
        )
        name_entry.pack(padx=30, pady=5)
        name_entry.focus()

        tk.Label(
            self.window,
            text="Email (для связи с вами по вопросам):",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=30, pady=(10, 0))

        self.email_var = tk.StringVar()
        email_entry = tk.Entry(
            self.window,
            textvariable=self.email_var,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            font=("Segoe UI", 10),
            width=40
        )
        email_entry.pack(padx=30, pady=5)

        tk.Label(
            self.window,
            text="Описание проблемы (что не так, как воспроизвести):",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=30, pady=(10, 0))

        self.message_text = tk.Text(
            self.window,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            font=("Segoe UI", 10),
            height=6,
            width=40,
            relief=tk.FLAT,
            borderwidth=0,
            padx=5,
            pady=5
        )
        self.message_text.pack(padx=30, pady=5)

        btn_frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(pady=20)

        send_btn = tk.Button(
            btn_frame,
            text="Отправить",
            command=self._on_send_click,
            bg=VSColorScheme.BUTTON_BG,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )
        send_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = tk.Button(
            btn_frame,
            text="Отмена",
            command=self.window.destroy,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            relief=tk.FLAT,
            padx=20,
            pady=5,
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)


    def _on_send_click(self):
        message = self.message_text.get("1.0", tk.END).strip()
        self._send_report(message)

    def _send_report(self, message):
        url = GITHUB_VERSION_MIN
        if not message:
            messagebox.showwarning("Напишите что не так", "Опишите вашу проблему подробнее")
            return

        name = self.name_var.get().strip() or "Аноним"
        email = self.email_var.get().strip()

        if email and not self._is_valid_email(email):
            messagebox.showwarning("Невалидный email!", "Пожалуйста, введите валидный email.")
            return

        if not email:
            messagebox.showwarning("Требуется email", "Для связи с вами по некоторым вопросам (например, если надо что-либо добавить), необходим email. Также, в описании проблемы вы можете добавить дополнительные средства связи.")
            return

        report_data = {
            "name": name,
            "email": email,
            "message": message,
            "_subject": f"Баг-репорт от {name} (RealCode {VERSION})"
        }

        # Блокируем интерфейс
        self.window.config(cursor="watch")
        for child in self.window.winfo_children():
            if isinstance(child, tk.Button):
                child.config(state=tk.DISABLED)

        try:
            # Получаем JSON
            response = requests.get(url)
            response.raise_for_status()
            github_data = response.json()
            
            MIN_REALCODE_VERSION = github_data['min_version']
            
            current = version.parse(VERSION_REALCODE)
            required = version.parse(MIN_REALCODE_VERSION)
            
            if current < required:
                messagebox.showwarning(
                    f"Ваша версия RealCode ({VERSION_REALCODE}) больше не поддерживается!", 
                    f"Сейчас ваша версия RealCode: {VERSION_REALCODE}, она не поддерживается разработчиком. Пожалуйста, обновитесь до последней версии, так как, возможно, этот баг был исправлен."
                )
                self._unblock_interface() # Разблокируем кнопки, если обновляться принудительно не заставляем
            else:
                threading.Thread(target=self._send_thread, args=(report_data,), daemon=True).start()

        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети: {e}")
            messagebox.showerror("Ошибка сети", "Не удалось проверить актуальность версии. Проверьте интернет-соединение.")
            self._unblock_interface()
        except KeyError:
            print("В JSON отсутствует ключ 'min_version'.")
            self._unblock_interface()
        except version.InvalidVersion:
            print("Ошибка: один из номеров версий имеет некорректный формат.")
            self._unblock_interface()
        except json.JSONDecodeError: # Перехватываем ошибку невалидного JSON
            print("Ошибка: Файл содержит некорректный JSON.")
            self._unblock_interface()

    def _unblock_interface(self):
        """Вспомогательный метод для возврата интерфейса в нормальное состояние"""
        self.window.config(cursor="")
        for child in self.window.winfo_children():
            if isinstance(child, tk.Button):
                child.config(state=tk.NORMAL)

    def _is_valid_email(self, email):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _send_thread(self, data):
        try:
            url = FORMSPREE_ID # Тут должен быть ваш FormSpree адрес (не хардкорьте, лучше сделайте в config.py для удобства)
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.window.after(0, self._on_success)
            else:
                self.window.after(0, lambda: self._on_error(f"Ошибка: {response.status_code}: {response.text[:200]}..."))
        except Exception as e:
            self.window.after(0, lambda: self._on_error(str(e)))

    def _on_success(self):
        self.window.destroy()
        messagebox.showinfo("Благодарим за ваш вклад в развитие RealCode!", "Ваш баг-репорт был отправлен! Мы рассмотрим его и ответим в ближайшее время. Спасибо, что делайте RealCode лучше!")

    def _on_error(self, error_msg):
        self.window.config(cursor="")
        for child in self.window.winfo_children():
            if isinstance(child, tk.Button):
                child.config(state=tk.NORMAL)
        messagebox.showerror("Ошибка отправки", f"Не удалось отправить сообщение:\n{error_msg}\n\nПожалуйста, попробуйте позже.")

class PluginManager:
    PLUGINS_URL = PLUGIN_URL_CONF
    PLUGINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")

    def __init__(self, app):
        self.app = app
        self.PLUGINS_DIR = os.path.join(self.app.app_dir, 'plugins')
        self.plugins = []
        self.installed_plugins = self._get_installed()
        os.makedirs(self.PLUGINS_DIR, exist_ok=True)

    def uninstall_plugin(self, plugin_id):
        plugin_dir = os.path.join(self.PLUGINS_DIR, plugin_id)
        if os.path.exists(plugin_dir):
            shutil.rmtree(plugin_dir)
            return True
        return False

    def _get_installed(self):
        """Возвращает список установленных плагинов (по названиям папок)."""
        if not os.path.exists(self.PLUGINS_DIR):
            return []
        return [d for d in os.listdir(self.PLUGINS_DIR) if os.path.isdir(os.path.join(self.PLUGINS_DIR, d))]

    def fetch_plugins(self, callback):
        """Асинхронно загружает список плагинов из GitHub."""
        def _fetch():
            try:
                response = requests.get(self.PLUGINS_URL, timeout=5)
                if response.status_code == 200:
                    plugins = json.loads(response.text)
                    self.plugins = plugins
                    self.app.root.after(0, lambda: callback(plugins, None))
                else:
                    self.app.root.after(0, lambda: callback(None, f"HTTP {response.status_code}"))
            except Exception as e:
                self.app.root.after(0, lambda: callback(None, str(e)))
        threading.Thread(target=_fetch, daemon=True).start()

    def install_plugin(self, plugin, callback):
        def _install():
            try:
                download_url = plugin['download_url']
                response = requests.get(download_url, timeout=30)
                if response.status_code != 200:
                    self.app.root.after(0, lambda: callback(False, f"Ошибка скачивания: {response.status_code}"))
                    return

                plugin_id = plugin['id']
                plugin_dir = os.path.join(self.PLUGINS_DIR, plugin_id)

                # Создаём временную папку для распаковки
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Распаковываем архив
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        for name in z.namelist():
                            if '..' in name or os.path.isabs(name):
                                self.app.root.after(0, lambda: callback(False, "Архив содержит недопустимые пути"))
                                return
                        z.extractall(tmpdir)

                    # Ищем main.py рекурсивно
                    main_file = None
                    for root, dirs, files in os.walk(tmpdir):
                        if 'main.py' in files:
                            main_file = os.path.join(root, 'main.py')
                            break

                    if not main_file:
                        self.app.root.after(0, lambda: callback(False, "В архиве не найден main.py"))
                        return

                    # Удаляем старую папку плагина
                    if os.path.exists(plugin_dir):
                        shutil.rmtree(plugin_dir)

                    # Копируем папку, содержащую main.py, в plugin_dir
                    source_dir = os.path.dirname(main_file)
                    shutil.copytree(source_dir, plugin_dir)

                self.app.root.after(0, lambda: callback(True, None))
            except Exception as e:
                self.app.root.after(0, lambda: callback(False, str(e)))

        threading.Thread(target=_install, daemon=True).start()

    def load_plugins(self):
        for plugin_id in self._get_installed():
            plugin_path = os.path.join(self.PLUGINS_DIR, plugin_id)
            if os.path.isdir(plugin_path):
                # Добавляем путь в sys.path (если ещё не добавлен)
                if plugin_path not in sys.path:
                    sys.path.insert(0, plugin_path)
                try:
                    # Пробуем импортировать main.py
                    # Используем importlib для гибкости
                    import importlib
                    spec = importlib.util.spec_from_file_location(f"{plugin_id}.main", os.path.join(plugin_path, "main.py"))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'init'):
                            module.init(self.app)
                            self.app.log(f"✅ Плагин '{plugin_id}' загружен")
                        else:
                            self.app.log(f"⚠️ Плагин '{plugin_id}' не содержит функцию init()")
                    else:
                        self.app.log(f"⚠️ Не найден main.py в плагине '{plugin_id}'")
                except Exception as e:
                    self.app.log(f"⚠️ Ошибка загрузки плагина '{plugin_id}': {e}")
                    import traceback
                    traceback.print_exc()

class PluginMarketplaceDialog:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.plugin_manager = PluginManager(app)

        try:
            if os.path.exists("iconPluginMarketplace.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass

        self.window = None
        self.tree = None
        self._show()
        self.tooltip_window = None

    def _show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Маркетплейс плагинов")
        self.window.geometry("700x500")
        self.window.configure(bg=VSColorScheme.BG_MEDIUM)
        self.window.transient(self.parent)
        self.window.focus_force()
        self.window.lift()
        self.window.resizable(True, True)

        # Заголовок
        tk.Label(
            self.window,
            text="Маркетплейс плагинов",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 14, "bold"),
            pady=10
        ).pack()

        # Фрейм для таблицы
        frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview (столбцы: Название, Версия, Автор, Категория)
        columns = ("name", "version", "author", "category")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.tree.heading("name", text="Название")
        self.tree.heading("version", text="Версия")
        self.tree.heading("author", text="Автор")
        self.tree.heading("category", text="Категория")
        self.tree.column("name", width=200)
        self.tree.column("version", width=70)
        self.tree.column("author", width=150)
        self.tree.column("category", width=100)

        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки
        btn_frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.install_btn = tk.Button(
            btn_frame,
            text="Установить выбранный",
            command=self._install_selected,
            bg=VSColorScheme.BUTTON_BG,
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.install_btn.pack(side=tk.LEFT, padx=5)

        self.uninstall_btn = tk.Button(
            btn_frame,
            text="Удалить",
            command=self._uninstall_selected,
            bg="#d9534f",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.uninstall_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(
            btn_frame,
            text="Обновить список",
            command=self._refresh,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=5)

        self.close_btn = tk.Button(
            btn_frame,
            text="Закрыть",
            command=self.window.destroy,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5)

        # Статус-бар
        self.status_label = tk.Label(
            self.window,
            text="Загрузка списка плагинов...",
            bg=VSColorScheme.STATUS_BG,
            fg="white",
            font=("Segoe UI", 9),
            anchor="w",
            padx=10
        )
        self.status_label.pack(fill=tk.X)

        # Загружаем список
        self._refresh()

    def _refresh(self):
        """Обновляет список плагинов из GitHub."""
        self.status_label.config(text="Загрузка...")
        self.install_btn.config(state=tk.DISABLED)
        self.uninstall_btn.config(state=tk.DISABLED)

        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.plugin_manager.fetch_plugins(self._on_plugins_loaded)

    def _on_tree_motion(self, event):
        """Показывает описание плагина при наведении на строку"""
        item = self.tree.identify_row(event.y)
        if not item:
            self._hide_tooltip()
            return

        # Получаем ID плагина из тегов
        tags = self.tree.item(item, "tags")
        plugin_id = tags[0] if tags else None
        if not plugin_id:
            self._hide_tooltip()
            return

        # Ищем плагин по ID
        plugin = next((p for p in self.plugin_manager.plugins if p['id'] == plugin_id), None)
        if not plugin:
            self._hide_tooltip()
            return

        # Если есть описание, показываем его
        description = plugin.get('description', '')
        if description:
            # Получаем координаты мыши
            x, y, _, _ = self.tree.bbox(item)
            x += self.tree.winfo_rootx() + 50
            y += self.tree.winfo_rooty() + 20
            self._show_tooltip(description, x, y)
        else:
            self._hide_tooltip()

    def _on_tree_leave(self, event):
        """Скрывает подсказку при выходе мыши из Treeview"""
        self._hide_tooltip()

    def _show_tooltip(self, text, x, y):
        """Показывает всплывающую подсказку"""
        self._hide_tooltip()
        self.tooltip_window = tk.Toplevel(self.window)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Segoe UI", 9, "normal"), padx=5, pady=3)
        label.pack()

    def _hide_tooltip(self):
        """Уничтожает окно подсказки"""
        if hasattr(self, 'tooltip_window') and self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def _on_plugins_loaded(self, plugins, error):
        if error:
            self.status_label.config(text=f"❌ Ошибка: {error}")
            return

        installed = self.plugin_manager._get_installed()
        self.status_label.config(text=f"✅ Загружено {len(plugins)} плагинов")
        for plugin in plugins:
            is_installed = plugin['id'] in installed
            values = (
                plugin['name'] + (" ✅" if is_installed else ""),
                plugin['version'],
                plugin['author'],
                plugin['category']
            )
            item = self.tree.insert("", tk.END, values=values, tags=(plugin['id'],))
            if is_installed:
                self.tree.item(item, tags=(plugin['id'], 'installed'))

            # Добавляем всплывающую подсказку для строки (при наведении)
            # Описание берём из plugin['description'], если есть
            if 'description' in plugin:
                # Привязываем к ячейке "Название" (в столбце 0)
                # Можно к целой строке, но проще к отдельному элементу
                # Получаем идентификатор ячейки (нестандартно, но можно через теги)
                # Вместо этого привяжем к самому item через обработку события
                # Сделаем через bind на Treeview с проверкой item
                pass

        # Альтернативный способ: единый обработчик для всего Treeview
        self.tree.bind('<Motion>', self._on_tree_motion)
        self.tree.bind('<Leave>', self._on_tree_leave)

        self.install_btn.config(state=tk.NORMAL)
        self.uninstall_btn.config(state=tk.NORMAL)

    def _install_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выберите плагин", "Пожалуйста, выберите плагин из списка.")
            return
        item = selected[0]
        plugin_id = self.tree.item(item, "tags")[0]
        # Находим плагин по id
        plugin = next((p for p in self.plugin_manager.plugins if p['id'] == plugin_id), None)
        if not plugin:
            return

        # Проверяем, не установлен ли уже
        if plugin_id in self.plugin_manager._get_installed():
            messagebox.showinfo("Уже установлен", "Этот плагин уже установлен.")
            return

        self.status_label.config(text=f"Установка {plugin['name']}...")
        self.install_btn.config(state=tk.DISABLED)
        self.plugin_manager.install_plugin(plugin, self._on_install_done)

    def _on_install_done(self, success, error):
        self.install_btn.config(state=tk.NORMAL)
        if success:
            self.status_label.config(text="Установка завершена успешно")
            self._refresh()  # обновляем список
            messagebox.showinfo("Плагин успешно установлен!", "Плагин установлен! Перезапустите RealCode для активации.")
        else:
            self.status_label.config(text=f"Ошибка: {error}")
            messagebox.showerror("Ошибка", f"Не удалось установить плагин:\n{error}")

    def _uninstall_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = selected[0]
        plugin_id = self.tree.item(item, "tags")[0]
        if not plugin_id:
            return
        if plugin_id not in self.plugin_manager._get_installed():
            messagebox.showinfo("Не установлен", "Плагин не установлен.")
            return
        if messagebox.askyesno(f"Удаление плагина {plugin_id}", f"Удалить плагин '{plugin_id}'?"):
            self.plugin_manager.uninstall_plugin(plugin_id)
            self.status_label.config(text=f"Плагин {plugin_id} удалён")
            self._refresh()

class ToolTip:
    """Всплывающая подсказка для виджетов"""
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
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9, "normal"))
        label.pack()

    def hide_tip(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def move_tip(self, event):
        if self.tip_window:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
            self.tip_window.wm_geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()
