# main.py - RealCode
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

from config import DISCORD_ID_CONFIG
from config import VERSION_REALCODE
from config import DOWNLOAD_URL
from config import GITHUB_VERSION_URL_CONFIG
from config import GITHUB_TOKEN

DISCORD_ID = DISCORD_ID_CONFIG
GITHUB_VERSION_URL = GITHUB_VERSION_URL_CONFIG

# ========== КОНСТАНТЫ И НАСТРОЙКИ ==========
APP_NAME = "RealCode"
VERSION = VERSION_REALCODE
CONFIG_FILE = "settings.json"
DISCORD_CLIENT_ID = DISCORD_ID

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
    def __init__(self, parent, text_widget, *args, **kwargs):
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
    def __init__(self, text_widget):
        self.text = text_widget
        self.highlight_enabled = True
        self.max_file_size = 100000
        self.update_after_id = None
        self.last_content = ""
        self._setup_tags()
        self._setup_patterns()
    
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
    
    def _setup_patterns(self):
        self.patterns = {
            'keyword': r'\b(def|class|if|else|elif|for|while|import|from|return|try|except|finally|with|as|in|is|not|and|or|True|False|None|break|continue|pass|lambda|yield|async|await)\b',
            'builtin': r'\b(print|len|range|input|str|int|float|list|dict|set|tuple|open|file|type|isinstance|issubclass|super|staticmethod|classmethod|property|abs|all|any|bin|bool|chr|complex|enumerate|filter|format|hex|id|max|min|next|oct|ord|pow|repr|reversed|round|sorted|sum|vars|zip)\b',
            'decorator': r'@\w+',
            'function': r'\b\w+(?=\s*\()',
            'class': r'(?<=class\s)\w+',
            'comment': r'#.*$',
            'string': r'".*?"|\'.*?\'|""".*?"""|\'\'\'.*?\'\'\'',
            'number': r'\b\d+\.?\d*\b',
        }
    
    def should_highlight(self):
        if not self.highlight_enabled:
            return False
        try:
            content_length = len(self.text.get("1.0", tk.END))
            return content_length < self.max_file_size
        except:
            return False
    
    def highlight(self, force=False):
        if not self.should_highlight():
            return
        try:
            current_content = self.text.get("1.0", tk.END)
            if not force and current_content == self.last_content:
                return
            self.last_content = current_content
            for tag_name in self.patterns.keys():
                self.text.tag_remove(tag_name, "1.0", tk.END)
            for tag_name, pattern in self.patterns.items():
                self._apply_pattern(tag_name, pattern, current_content)
        except Exception as e:
            print(f"Ошибка подсветки: {e}")
    
    def _apply_pattern(self, tag_name, pattern, text):
        try:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add(tag_name, start, end)
        except Exception as e:
            print(f"Ошибка применения паттерна {tag_name}: {e}")
    
    def incremental_highlight(self, start_line=1, end_line=None):
        if not self.should_highlight():
            return
        try:
            if end_line is None:
                end_line = int(self.text.index('end-1c').split('.')[0])
            for tag_name in self.patterns.keys():
                self.text.tag_remove(tag_name, f"{start_line}.0", f"{end_line}.0")
            text_to_highlight = self.text.get(f"{start_line}.0", f"{end_line}.0")
            if not text_to_highlight:
                return
            try:
                base_offset = int(self.text.index(f"{start_line}.0").split('.')[1])
                for i in range(1, start_line):
                    line_length = len(self.text.get(f"{i}.0", f"{i}.end"))
                    base_offset += line_length + 1
            except:
                base_offset = 0
            for tag_name, pattern in self.patterns.items():
                try:
                    for match in re.finditer(pattern, text_to_highlight, re.MULTILINE):
                        abs_start = base_offset + match.start()
                        abs_end = base_offset + match.end()
                        start_pos = f"1.0+{abs_start}c"
                        end_pos = f"1.0+{abs_end}c"
                        self.text.tag_add(tag_name, start_pos, end_pos)
                except:
                    pass
        except Exception as e:
            print(f"Ошибка инкрементальной подсветки: {e}")

    def highlight_visible(self):
        if not self.should_highlight():
            return
        try:
            first = int(self.text.index("@0,0").split('.')[0])
            last = int(self.text.index(f"@0,{self.text.winfo_height()}").split('.')[0])
            first = max(1, first - 3)
            last = min(int(self.text.index('end-1c').split('.')[0]), last + 3)
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
        self.window.grab_set()
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
            project_name = "Нет проекта" if not self.app.current_project else self.app.current_project.name
            files_count = len(self.app.current_project.tabs) if self.app.current_project else 0
            state_text = {
                "editing": "Редактирует код",
                "running": "Запустил выполнение кода",
                "idle": "Отошел"
            }.get(self.current_state, "Редактирует код")
            details = f"{filename} • {project_name}"
            buttons = [
                {"label": "RealCode in GitHub", "url": "https://github.com/Kish-Mish122/RealCode"},
                {"label": "Download RealCode", "url": "https://github.com/Kish-Mish122/RealCode/releases"},
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
        self.update_url = GITHUB_VERSION_URL  # из config.py
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

            print("🔍 Проверка обновлений")

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

            # Ищем файл .exe в assets
            download_url = None
            for asset in release_info.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                raise ValueError("В релизе не найден .exe-файл")

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
                print(f"✅ Найдено обновление! {current} -> {latest}")
                if not silent:
                    self.app.root.after(0, self._show_update_dialog)
                return True
            else:
                if not silent:
                    self.app.log("✅ RealCode актуален")
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
        self.update_dialog.title("Новая версия RealCode")
        self.update_dialog.geometry("650x540")
        self.update_dialog.configure(bg=VSColorScheme.BG_MEDIUM)
        self.update_dialog.transient(self.app.root)
        self.update_dialog.grab_set()
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
            f"Доступна новая версия RealCode {latest_version} с улучшениями!")
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
            notes_title = tk.Label(notes_frame, text="Что нового:", bg=VSColorScheme.BG_LIGHT,
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

        update_btn = tk.Button(btn_frame, text="⬇Обновиться", command=self._start_update,
                               bg=VSColorScheme.ACCENT, fg="white", relief=tk.FLAT,
                               padx=25, pady=8, font=("Segoe UI", 11, "bold"), cursor="hand2")
        update_btn.pack(side=tk.LEFT, padx=10)

        later_btn = tk.Button(btn_frame, text="Напомнить позже", command=self.update_dialog.destroy,
                              bg=VSColorScheme.BG_LIGHT, fg=VSColorScheme.FG, relief=tk.FLAT,
                              padx=25, pady=8, font=("Segoe UI", 11), cursor="hand2")
        later_btn.pack(side=tk.LEFT, padx=10)

        warning_label = tk.Label(self.update_dialog, text="При закрытии RealCode он будет обновлён",
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
        self.status_label.config(text="Подготовка к скачиванию...")
        threading.Thread(target=self._download_and_install, daemon=True).start()

    def _download_and_install(self):
        try:
            download_url = self.update_info.get('download_url')

            if not download_url:
                self._show_error("Ссылка для скачивания не найдена")
                return

            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                download_path = current_exe + ".new"
            else:
                current_exe = os.path.abspath(__file__)
                download_path = current_exe + ".new"

            self._update_status("Скачивание обновления...", 10)

            import urllib.request
            import ssl
            context = ssl._create_unverified_context()

            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(int(downloaded * 100 / total_size), 99)
                    self.update_dialog.after(0, lambda: self._update_progress(percent))

            urllib.request.urlretrieve(download_url, download_path, reporthook=report_progress)

            # Проверяем, что файл скачался
            if not os.path.exists(download_path) or os.path.getsize(download_path) == 0:
                self._show_error("Скачанный файл повреждён или пуст")
                return

            self._update_status("Установка обновления...", 100)
            time.sleep(0.5)

            if getattr(sys, 'frozen', False):
                self._create_update_bat(current_exe, download_path)
            else:
                os.replace(download_path, current_exe)
                self.update_dialog.after(0, self.update_dialog.destroy)
                messagebox.showinfo("Обновление завершено",
                                    "Обновление успешно установлено! Перезапустите программу.")

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
        response = messagebox.askyesno("Обновление готово",
                                       "Обновление успешно скачано! Перезапустить RealCode сейчас?")
        if response:
            self.update_dialog.after(100, lambda: os.startfile(bat_path))
            self.app.root.after(100, self.app.on_closing)
        else:
            messagebox.showinfo("Обновление запланировано",
                                "Обновление будет установлено при следующем запуске.")

    def _update_progress(self, value):
        if self.progress_bar:
            self.progress_bar['value'] = value

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
        self._dialog_open = False
        
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
        
        threading.Thread(target=self._check_updates_thread, daemon=True).start()
    
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
            self.root.state('zoomed')
    
    def _init_discord(self):
        try:
            self.discord = DiscordPresence(self)
        except Exception as e:
            print(f"Ошибка инициализации Discord: {e}")
            self.discord = None
    
    def _check_updates_thread(self):
        time.sleep(2)
        self.updater.check_for_updates(silent=False)
    
    def manual_check_updates(self):
        self.updater.check_for_updates(silent=False)
    
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
            if self.config.get("syntax_highlight", True) and self.highlighter:
                filename = self.current_project.files.get(tab)
                if filename:
                    ext = os.path.splitext(filename)[1].lower()
                    supported_exts = ['.py']
                    if ext not in supported_exts:
                        self.show_notification("⚠️ Подсветка синтаксиса не поддерживается для этого файла", duration=3000)
                        self.highlighter.highlight_enabled = False
                    else:
                        self.highlighter.highlight_enabled = True
                else:
                    self.highlighter.highlight_enabled = True
                if self.highlighter.highlight_enabled:
                    self.highlighter.highlight_visible()
            self.line_numbers.update_numbers()
            if self.minimap:
                self.minimap.update_minimap()
        if self.discord:
            self.discord._update_presence()
        self.current_project.save_state()
    
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
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        project_root = self.config.get("project_path", ".")
        if not os.path.exists(project_root):
            project_root = "."
        self.folder_label.config(text=os.path.basename(project_root))
        root_name = os.path.basename(os.path.abspath(project_root)) or "Проект"
        root_node = self.file_tree.insert("", "end", text=f"📁 {root_name}", open=True)
        self._process_directory(project_root, root_node)
    
    def _process_directory(self, path, parent):
        try:
            items = os.listdir(path)
            dirs = []
            files = []
            show_hidden = self.config.get("show_hidden_files", False)
            for item in items:
                if not show_hidden and item.startswith('.'):
                    continue
                if item in ["__pycache__"]:
                    continue
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            dirs.sort()
            files.sort()
            for item in dirs + files:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    node = self.file_tree.insert(parent, "end", text=f"📁 {item}", open=False)
                    self._process_directory(full_path, node)
                else:
                    ext = os.path.splitext(item)[1].lower()
                    icons = {
                        ".py": "🐍",
                        ".js": "📜",
                        ".html": "🌐",
                        ".css": "🎨",
                        ".json": "📦",
                        ".md": "📘",
                        ".txt": "📝",
                        ".exe": "⚙️"
                    }
                    icon = icons.get(ext, "📄")
                    self.file_tree.insert(parent, "end", text=f"{icon} {item}", values=(full_path,))
        except Exception as e:
            print(f"Ошибка обхода директории {path}: {e}")
    
    def on_file_double_click(self, event):
        if not self.current_project:
            temp_path = os.path.join(os.path.expanduser("~"), "RealCode_temp")
            os.makedirs(temp_path, exist_ok=True)
            self.load_project(temp_path)
        selection = self.file_tree.selection()
        if not selection:
            return
        values = self.file_tree.item(selection[0], "values")
        if values:
            file_path = values[0]
            if os.path.isfile(file_path):
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
    
    # ========== РЕДАКТОР ==========
    def on_key_release(self, event):
        if not self.current_project or not self.current_project.current_tab or not self.editor:
            return
        self.update_cursor_position()
        self.line_numbers.update_numbers()
        try:
            current_line = int(self.editor.index(tk.INSERT).split('.')[0])
        except:
            current_line = 1
        if self.config.get("syntax_highlight", True) and self.highlighter:
            start_line = max(1, current_line - 2)
            end_line = current_line + 2
            self.highlighter.incremental_highlight(start_line, end_line)
        if self._highlight_after_id:
            self.root.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.root.after(1000, self._delayed_full_highlight)
        if self.config.get("auto_save", False) and self.current_project.current_tab:
            if self.auto_save_timer:
                self.root.after_cancel(self.auto_save_timer)
            self.auto_save_timer = self.root.after(2000, self._auto_save)
        if self.minimap:
            if self._minimap_after_id:
                self.root.after_cancel(self._minimap_after_id)
            self._minimap_after_id = self.root.after(500, self._update_minimap_delayed)
    
    def _delayed_full_highlight(self):
        if self.highlighter and self.current_project and self.current_project.current_tab:
            self.highlighter.highlight()
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
    
    def open_find(self, event=None):
        if self.editor and self.current_project and self.current_project.current_tab:
            FindDialog(self.root, self.editor, self)
        return "break"
    
    def go_to_line(self, event=None):
        if not self.editor or not self.current_project or not self.current_project.current_tab:
            return "break"
        try:
            total_lines = int(self.editor.index('end-1c').split('.')[0])
            self._dialog_open = True
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
            
            def on_close():
                self._dialog_open = False
                dialog.destroy()
                try:
                    line = int(var.get())
                    if 1 <= line <= total_lines:
                        self.editor.mark_set(tk.INSERT, f"{line}.0")
                        self.editor.see(tk.INSERT)
                        self.update_cursor_position()
                except ValueError:
                    pass
            
            # Закрытие по Enter
            entry.bind('<Return>', lambda e: on_close())
            
            dialog.protocol("WM_DELETE_WINDOW", on_close)
            tk.Button(dialog, text="Перейти", command=on_close,
                      bg=VSColorScheme.BUTTON_BG, fg="white", relief=tk.FLAT, padx=15).pack(pady=10)
            
            self.root.wait_window(dialog)
            # Дополнительная страховка: если по какой-то причине флаг не сбросился
            self._dialog_open = False
            
        except Exception as e:
            print(f"Ошибка перехода к строке: {e}")
            self._dialog_open = False
        return "break"
    
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
    
    def _run_thread(self, filename):
        try:
            result = subprocess.run(
                [sys.executable, filename],
                capture_output=True,
                text=True,
                encoding='utf-8'
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
        SettingsDialog(self.root, self.config, self.apply_settings)
    
    def apply_settings(self, new_config):
        old_pos = self.config.get("explorer_position")
        old_console_pos = self.config.get("console_position")
        self.config = new_config
        save_config(self.config)
        if self.editor:
            self.editor.config(
                font=(self.config["font_family"], self.config["font_size"]),
                wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
                tabs=(self.config["tab_size"] * 10,)
            )
        if self.config.get("syntax_highlight", True) and self.highlighter:
            self.highlighter.highlight(force=True)
        if self.explorer_visible:
            self.main_paned.paneconfig(self.explorer_frame, width=self.config.get("sidebar_width", 250))
        if self.console_visible:
            self.center_paned.paneconfig(self.console_area, height=self.config.get("console_height", 200))
        if old_pos != self.config.get("explorer_position"):
            self.move_explorer()
        if old_console_pos != self.config.get("console_position"):
            self.move_console()
        if self.config.get("minimap_enabled", True):
            if not self.minimap:
                self.minimap = Minimap(self.editor_container, self.editor)
                self.minimap.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            if self.minimap:
                self.minimap.destroy()
                self.minimap = None
        self.line_numbers.update_numbers()
        self.status_label.config(text="Настройки применены")
        self.load_project_tree()
    
    # ========== МЕНЮ И ГОРЯЧИЕ КЛАВИШИ ==========
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
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
        help_menu.add_command(label="🔄 Проверить обновления", command=self.manual_check_updates)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    # ГЛОБАЛЬНЫЕ ГОРЯЧИЕ КЛАВИШИ
    def _bind_global_shortcuts(self):
        def handler(event):
            if self._dialog_open:
                return
            mod = event.state & 0x0F
            key = event.keycode
            ctrl = (mod & 4) != 0
            shift = (mod & 1) != 0
            alt = (mod & 8) != 0

            if key == 78 and ctrl and not shift:   # Ctrl+N
                self.add_new_tab(); return "break"
            if key == 79 and ctrl and not shift:   # Ctrl+O
                self.open_file(); return "break"
            if key == 75 and ctrl and not shift:   # Ctrl+K
                self.open_folder(); return "break"
            if key == 83 and ctrl and not shift:   # Ctrl+S
                self.save_file(); return "break"
            if key == 83 and ctrl and shift:       # Ctrl+Shift+S
                self.save_file_as(); return "break"
            if key == 87 and ctrl and not shift:   # Ctrl+W
                self.close_current_tab(); return "break"
            if key == 88 and ctrl and not shift:   # Ctrl+X
                self.cut(); return "break"
            if key == 67 and ctrl and not shift:   # Ctrl+C
                self.copy(); return "break"
            if key == 86 and ctrl and not shift:   # Ctrl+V
                self.paste(); return "break"
            if key == 65 and ctrl and not shift:   # Ctrl+A (выделить всё)
                self.select_all(); return "break"
            if key == 70 and ctrl and not shift:   # Ctrl+F
                self.open_find(); return "break"
            if key == 71 and ctrl and not shift:   # Ctrl+G
                self.go_to_line(); return "break"
            if key == 116 and mod == 0:   # F5
                self.run_code(); return "break"
            if key == 112 and mod == 0:   # F1
                self.open_settings(); return "break"
            if (key == 187 or key == 61) and ctrl and not shift:  # Ctrl++
                self.zoom_in(); return "break"
            if key == 189 and ctrl and not shift:   # Ctrl+-
                self.zoom_out(); return "break"

        self.root.bind_all('<Key>', handler)
        if self.editor:
            self.editor.bind('<Key>', handler)
    
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
        
        self.file_tree = ttk.Treeview(
            self.explorer_frame,
            show="tree",
            selectmode="browse"
        )
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=VSColorScheme.BG_LIGHT,
            foreground=VSColorScheme.FG,
            fieldbackground=VSColorScheme.BG_LIGHT,
            borderwidth=0
        )
        style.map(
            "Treeview",
            background=[("selected", VSColorScheme.SELECTION)]
        )
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_tree_open)
    
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
            text="+  Новая вкладка",
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
        editor_inner = tk.Frame(self.editor_container, bg=VSColorScheme.BG_DARK)
        editor_inner.pack(fill=tk.BOTH, expand=True)
        self.line_numbers = LineNumbers(editor_inner, None)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
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
        self.line_numbers.text_widget = self.editor
        
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
        
        if self.config.get("minimap_enabled", True):
            self.minimap = Minimap(editor_inner, self.editor)
            self.minimap.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<<Modified>>', self.on_text_modified)
        self.editor.bind('<MouseWheel>', self.on_editor_wheel)
        self.editor.bind('<Button-3>', self.show_editor_context_menu)
        self.editor_scrollbar.bind('<B1-Motion>', self.on_scroll)
        
        self.highlighter = SyntaxHighlighter(self.editor)
    
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
        self.dialog.grab_set()
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

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()
