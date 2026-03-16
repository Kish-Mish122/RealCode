# RealCode
### Real Code - this is a code editor program. I tried to make it similar to VS Code, but with its own differences.

# Differences:
1. Simple - Easy to learn, requires no additional knowledge. Everything is easy and simple!
2. Completely open source python code - Since the developer needs to know what it works in and how this program works, I made it completely open to everyone!
3. Auto-save a file - Even if your RealCode crashes, you won't lose any changes to the file that you've been making for probably a lot of time.

##### The emphasis is on ease of use - there is nothing complicated, which can be, for example, in VS Code and the like. But another emphasis is openness! You can always download it and edit it the way you need, and even release your own code editing program!

##### Plus, you can also note: For those who may not understand the code, I made the arguments. Now, even if you don't understand the code, you can always look at the argument and figure out what kind of function it is.

*The program is completely in Russian, please keep this in mind when installing, as there is no English translation.*

*RealCode building: pyinstaller ``--onefile --windowed --name "RealCode" main.py`` - where you can replace "RealCode" with your program name. After building, the finished build will appear in the dist folder.*
*Check without building - ``python main.py``*

``python``
```# main.py - CodeCraft Pro (Исправленная версия с рабочей миникартой)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import sys
from pathlib import Path
import subprocess
import threading
import re
from datetime import datetime

APP_NAME = "RealCode"
VERSION = "3.1"
CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "font_family": "Consolas",
    "font_size": 11,
    "project_path": ".",
    "sidebar_width": 250,
    "window_x": 100,
    "window_y": 100,
    "window_width": 1300,
    "window_height": 800,
    "auto_save": False,
    "word_wrap": False,
    "tab_size": 4,
    "show_line_numbers": True,
    "syntax_highlight": True,
    "last_opened_folder": ".",
    "minimap_enabled": True,
    "minimap_width": 100
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return {**DEFAULT_CONFIG, **config}
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except:
        pass

class VSColorScheme:
    """Цвета VS Code Dark+"""
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2d2d2d"
    FG = "#d4d4d4"
    FG_LIGHT = "#cccccc"
    ACCENT = "#007acc"
    ACCENT_HOVER = "#1a8cff"
    SELECTION = "#264f78"
    LINE_NUMBERS = "#858585"
    BORDER = "#3e3e42"
    SCROLLBAR = "#3e3e42"
    TAB_ACTIVE = "#1e1e1e"
    TAB_INACTIVE = "#2d2d2d"
    CONSOLE_BG = "#1e1e1e"
    STATUS_BG = "#007acc"
    BUTTON_BG = "#0e639c"
    
    # Цвета синтаксиса
    KEYWORD = "#569cd6"
    STRING = "#ce9178"
    COMMENT = "#6a9955"
    NUMBER = "#b5cea8"
    FUNCTION = "#dcdcaa"
    CLASS = "#4ec9b0"
    DECORATOR = "#c586c0"
    BUILTIN = "#4ec9b0"

class LineNumbers(tk.Canvas):
    """Номера строк слева от редактора"""
    
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.configure(bg=VSColorScheme.BG_MEDIUM, highlightthickness=0, width=50)
        
        if self.text_widget:
            self.attach_to_text_widget()
            self.update_numbers()
    
    def attach_to_text_widget(self):
        """Привязка к текстовому виджету"""
        self.text_widget.bind('<KeyRelease>', self.on_change)
        self.text_widget.bind('<MouseWheel>', self.on_change)
        self.text_widget.bind('<Button-4>', self.on_change)
        self.text_widget.bind('<Button-5>', self.on_change)
        self.text_widget.bind('<Configure>', self.on_change)
        self.text_widget.bind('<<Modified>>', self.on_change)
    
    def on_change(self, event=None):
        """Обновление номеров строк при изменениях"""
        self.update_numbers()
    
    def update_numbers(self):
        """Обновление номеров строк"""
        self.delete("all")
        
        if not self.text_widget:
            return
        
        try:
            # Получаем первую видимую строку
            first_line = int(self.text_widget.index("@0,0").split('.')[0])
            
            # Получаем последнюю видимую строку
            last_line = int(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            
            # Получаем общее количество строк
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            
            # Получаем информацию о первой строке для расчета высоты
            dline_info = self.text_widget.dlineinfo("1.0")
            if dline_info:
                line_height = dline_info[3]
            else:
                line_height = 20
            
            # Отрисовываем номера строк
            for line_num in range(first_line, min(last_line + 1, total_lines + 1)):
                # Получаем координаты строки
                bbox = self.text_widget.bbox(f"{line_num}.0")
                if bbox:
                    y = bbox[1] + 2
                    self.create_text(
                        45, y,
                        text=str(line_num),
                        anchor="ne",
                        fill=VSColorScheme.LINE_NUMBERS,
                        font=("Consolas", 9)
                    )
        except:
            pass

class Minimap(tk.Canvas):
    """Миникарта для быстрой навигации по коду - ИСПРАВЛЕННАЯ"""
    
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
        self.visible_area = None
        self.update_after_id = None
        
        # Привязка событий миникарты
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<MouseWheel>', self.on_minimap_scroll)
        
        # Привязка к редактору
        if self.text_widget:
            self.attach_to_text_widget()
            self.update_minimap()
    
    def attach_to_text_widget(self):
        """Привязка к текстовому виджету"""
        self.text_widget.bind('<KeyRelease>', self.schedule_update)
        self.text_widget.bind('<MouseWheel>', self.on_editor_scroll)
        self.text_widget.bind('<Button-4>', self.on_editor_scroll)
        self.text_widget.bind('<Button-5>', self.on_editor_scroll)
        self.text_widget.bind('<Configure>', self.schedule_update)
        self.text_widget.bind('<<Modified>>', self.schedule_update)
        
        # Привязка к скроллбару
        self.text_widget.bind('<FocusIn>', self.schedule_update)
    
    def schedule_update(self, event=None):
        """Планирование обновления с задержкой"""
        if self.update_after_id:
            self.after_cancel(self.update_after_id)
        self.update_after_id = self.after(100, self.update_minimap)
    
    def update_minimap(self, event=None):
        """Обновление содержимого миникарты"""
        if not self.text_widget or not self.text_widget.winfo_exists():
            return
        
        self.delete("all")
        
        try:
            # Получаем текст
            text = self.text_widget.get("1.0", tk.END)
            self.content_lines = text.split('\n')
            
            # Ограничиваем количество строк для производительности
            max_lines = len(self.content_lines)
            if max_lines == 0:
                return
            
            # Высота миникарты
            minimap_height = self.winfo_height()
            if minimap_height <= 1:
                return
            
            # Высота строки в миникарте
            self.line_height = max(2, minimap_height / max_lines)
            
            # Рисуем линии (упрощенно - только полоски)
            y = 0
            for i, line in enumerate(self.content_lines[:2000]):  # Ограничиваем для производительности
                if y > minimap_height:
                    break
                
                # Определяем цвет линии в зависимости от содержимого
                if line.strip():
                    if line.strip().startswith(('#', '//', '/*')):
                        color = VSColorScheme.COMMENT
                    elif line.strip().startswith(('def ', 'class ')):
                        color = VSColorScheme.FUNCTION
                    elif any(kw in line for kw in ['import ', 'from ', 'return ']):
                        color = VSColorScheme.KEYWORD
                    else:
                        color = VSColorScheme.FG
                else:
                    color = VSColorScheme.BG_LIGHT
                
                # Рисуем линию
                self.create_rectangle(
                    0, y,
                    self.winfo_width(), y + self.line_height,
                    fill=color,
                    outline=""
                )
                y += self.line_height
            
            # Рисуем область видимости
            self.draw_visible_area()
            
        except Exception as e:
            print(f"Minimap error: {e}")
    
    def draw_visible_area(self):
        """Отрисовка видимой области"""
        try:
            if not self.content_lines:
                return
            
            # Получаем видимые строки
            first_line = int(self.text_widget.index("@0,0").split('.')[0])
            last_line = int(self.text_widget.index(f"@0,{self.text_widget.winfo_height()}").split('.')[0])
            
            total_lines = len(self.content_lines)
            if total_lines == 0:
                return
            
            # Рассчитываем позиции
            y1 = (first_line - 1) * self.line_height
            y2 = last_line * self.line_height
            
            # Удаляем старую область видимости
            if self.visible_area:
                self.delete(self.visible_area)
            
            # Рисуем новую область видимости
            self.visible_area = self.create_rectangle(
                0, y1, self.winfo_width(), y2,
                fill="#264f78",
                stipple="gray50",
                outline=VSColorScheme.ACCENT,
                width=1,
                tags="visible_area"
            )
        except:
            pass
    
    def on_editor_scroll(self, event):
        """Обработка прокрутки редактора"""
        self.schedule_update()
    
    def on_minimap_scroll(self, event):
        """Обработка прокрутки миникарты колесиком"""
        if self.content_lines:
            delta = -1 if event.delta > 0 else 1
            self.text_widget.yview_scroll(delta, "units")
            self.update_minimap()
    
    def on_click(self, event):
        """Обработка клика по миникарте"""
        self.dragging = True
        self.scroll_to_position(event.y)
    
    def on_drag(self, event):
        """Обработка перетаскивания"""
        if self.dragging:
            self.scroll_to_position(event.y)
    
    def on_release(self, event):
        """Обработка отпускания"""
        self.dragging = False
    
    def scroll_to_position(self, y):
        """Прокрутка к позиции"""
        try:
            if not self.content_lines:
                return
            
            total_lines = len(self.content_lines)
            if total_lines == 0:
                return
            
            # Рассчитываем позицию
            fraction = y / self.winfo_height()
            target_line = int(fraction * total_lines) + 1
            target_line = max(1, min(total_lines, target_line))
            
            # Прокручиваем
            self.text_widget.see(f"{target_line}.0")
            self.text_widget.focus_set()
            
            # Обновляем миникарту
            self.update_minimap()
        except:
            pass

class FindDialog:
    """Диалог поиска (Ctrl+F)"""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text_widget = text_widget
        self.dialog = None
        self.show()
    
    def show(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Поиск")
        self.dialog.geometry("400x150")
        self.dialog.configure(bg=VSColorScheme.BG_MEDIUM)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Поле ввода
        tk.Label(
            self.dialog,
            text="Найти:",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG
        ).pack(pady=(10, 0))
        
        self.search_var = tk.StringVar()
        entry = tk.Entry(
            self.dialog,
            textvariable=self.search_var,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            insertbackground=VSColorScheme.FG,
            width=40
        )
        entry.pack(pady=5, padx=20)
        entry.focus()
        entry.bind('<Return>', lambda e: self.find())
        
        # Кнопки
        btn_frame = tk.Frame(self.dialog, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="Найти далее",
            command=self.find,
            bg=VSColorScheme.BUTTON_BG,
            fg="white",
            relief=tk.FLAT,
            padx=15
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Закрыть",
            command=self.dialog.destroy,
            bg=VSColorScheme.BG_LIGHT,
            fg=VSColorScheme.FG,
            relief=tk.FLAT,
            padx=15
        ).pack(side=tk.LEFT, padx=5)
    
    def find(self):
        """Поиск текста"""
        search_text = self.search_var.get()
        if not search_text:
            return
        
        # Убираем предыдущее выделение
        self.text_widget.tag_remove("search", "1.0", tk.END)
        
        # Начинаем поиск с текущей позиции
        start = self.text_widget.index(tk.INSERT)
        
        # Ищем текст
        pos = self.text_widget.search(search_text, start, tk.END)
        
        if not pos:
            # Если не нашли, начинаем сначала
            pos = self.text_widget.search(search_text, "1.0", tk.END)
        
        if pos:
            # Выделяем найденный текст
            end = f"{pos}+{len(search_text)}c"
            self.text_widget.tag_add("search", pos, end)
            self.text_widget.tag_config("search", background=VSColorScheme.SELECTION)
            self.text_widget.mark_set(tk.INSERT, end)
            self.text_widget.see(tk.INSERT)

class SyntaxHighlighter:
    """Подсветка синтаксиса Python - ОПТИМИЗИРОВАННАЯ"""
    
    def __init__(self, text_widget):
        self.text = text_widget
        self.update_after_id = None
        self.last_content = ""
        self.highlight_enabled = True
        self.max_file_size = 100000
        
        # Настройка тегов
        self.setup_tags()
        
        # Паттерны для Python
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
    
    def setup_tags(self):
        """Настройка цветовых тегов"""
        self.text.tag_configure("keyword", foreground=VSColorScheme.KEYWORD)
        self.text.tag_configure("builtin", foreground=VSColorScheme.BUILTIN)
        self.text.tag_configure("decorator", foreground=VSColorScheme.DECORATOR)
        self.text.tag_configure("function", foreground=VSColorScheme.FUNCTION)
        self.text.tag_configure("class", foreground=VSColorScheme.CLASS)
        self.text.tag_configure("comment", foreground=VSColorScheme.COMMENT, font=("Consolas", 10, "italic"))
        self.text.tag_configure("string", foreground=VSColorScheme.STRING)
        self.text.tag_configure("number", foreground=VSColorScheme.NUMBER)
    
    def should_highlight(self):
        """Проверка, нужно ли применять подсветку"""
        if not self.highlight_enabled:
            return False
        
        content_length = len(self.text.get("1.0", tk.END))
        return content_length < self.max_file_size
    
    def highlight(self, force=False):
        """Применение подсветки с проверкой изменений"""
        if not self.should_highlight():
            return
        
        try:
            current_content = self.text.get("1.0", tk.END)
            
            if not force and current_content == self.last_content:
                return
            
            self.last_content = current_content
            
            for tag in ["keyword", "builtin", "decorator", "function", "class", 
                       "comment", "string", "number"]:
                self.text.tag_remove(tag, "1.0", tk.END)
            
            for tag_name, pattern in self.patterns.items():
                try:
                    for match in re.finditer(pattern, current_content, re.MULTILINE):
                        start = f"1.0+{match.start()}c"
                        end = f"1.0+{match.end()}c"
                        self.text.tag_add(tag_name, start, end)
                except:
                    pass
        except:
            pass

class ModernTab(tk.Frame):
    """Вкладка в стиле VS Code"""
    def __init__(self, parent, title, close_callback, select_callback, *args, **kwargs):
        super().__init__(parent, bg=VSColorScheme.TAB_INACTIVE, height=45, width=150)
        self.pack_propagate(False)
        self.close_callback = close_callback
        self.select_callback = select_callback
        self.title = title
        self.is_active = False
        self.modified = False
        
        self.configure(cursor="hand2")
        
        # Заголовок
        self.title_label = tk.Label(
            self,
            text=title,
            bg=VSColorScheme.TAB_INACTIVE,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 11),
            cursor="hand2",
            padx=15,
            pady=12
        )
        self.title_label.place(x=10, y=0, width=100, height=45)
        
        # Кнопка закрытия
        self.close_btn = tk.Label(
            self,
            text="✕",
            bg=VSColorScheme.TAB_INACTIVE,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        self.close_btn.place(x=115, y=10, width=25, height=25)
        
        # Привязка событий
        self.bind('<Button-1>', self.on_select)
        self.title_label.bind('<Button-1>', self.on_select)
        
        self.close_btn.bind('<Button-1>', self.on_close)
        self.close_btn.bind('<Enter>', self.on_close_enter)
        self.close_btn.bind('<Leave>', self.on_close_leave)
        
        self.bind('<Enter>', self.on_enter)
        self.title_label.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.title_label.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        if not self.is_active:
            self.configure(bg=VSColorScheme.BG_LIGHT)
            self.title_label.configure(bg=VSColorScheme.BG_LIGHT)
            self.close_btn.configure(bg=VSColorScheme.BG_LIGHT)
    
    def on_leave(self, e):
        if not self.is_active:
            self.configure(bg=VSColorScheme.TAB_INACTIVE)
            self.title_label.configure(bg=VSColorScheme.TAB_INACTIVE)
            self.close_btn.configure(bg=VSColorScheme.TAB_INACTIVE)
    
    def on_close_enter(self, e):
        self.close_btn.configure(fg=VSColorScheme.ACCENT, bg=VSColorScheme.ACCENT_HOVER)
    
    def on_close_leave(self, e):
        bg = VSColorScheme.TAB_ACTIVE if self.is_active else VSColorScheme.TAB_INACTIVE
        self.close_btn.configure(fg=VSColorScheme.FG, bg=bg)
    
    def on_select(self, e):
        self.select_callback(self)
    
    def on_close(self, e):
        if self.close_callback:
            self.close_callback(self)
    
    def set_active(self, active):
        self.is_active = active
        bg = VSColorScheme.TAB_ACTIVE if active else VSColorScheme.TAB_INACTIVE
        self.configure(bg=bg)
        self.title_label.configure(bg=bg)
        self.close_btn.configure(bg=bg)
    
    def set_modified(self, modified):
        self.modified = modified
        text = self.title + (" ●" if modified else "")
        self.title_label.config(text=text)

class SettingsDialog:
    """Диалог настроек"""
    
    def __init__(self, parent, config, callback):
        self.parent = parent
        self.config = config.copy()
        self.callback = callback
        self.window = None
        self.show()
    
    def show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Настройки")
        self.window.geometry("500x500")
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
        
        frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        row = 0
        
        # Шрифт
        tk.Label(frame, text="Шрифт:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5)
        self.font_var = tk.StringVar(value=self.config["font_family"])
        fonts = ["Consolas", "Courier New", "Monaco", "Lucida Console", "DejaVu Sans Mono"]
        font_combo = ttk.Combobox(frame, textvariable=self.font_var, values=fonts, width=20)
        font_combo.grid(row=row, column=1, pady=5, padx=10)
        row += 1
        
        # Размер шрифта
        tk.Label(frame, text="Размер шрифта:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5)
        self.size_var = tk.IntVar(value=self.config["font_size"])
        size_spin = tk.Spinbox(frame, from_=8, to=24, textvariable=self.size_var, width=10)
        size_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        # Размер табуляции
        tk.Label(frame, text="Размер табуляции:", bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG).grid(row=row, column=0, sticky="w", pady=5)
        self.tab_var = tk.IntVar(value=self.config["tab_size"])
        tab_spin = tk.Spinbox(frame, from_=2, to=8, textvariable=self.tab_var, width=10)
        tab_spin.grid(row=row, column=1, sticky="w", pady=5, padx=10)
        row += 1
        
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # Автосохранение
        self.auto_save_var = tk.BooleanVar(value=self.config.get("auto_save", False))
        tk.Checkbutton(
            frame,
            text="Автосохранение",
            variable=self.auto_save_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1
        
        # Перенос строк
        self.wrap_var = tk.BooleanVar(value=self.config.get("word_wrap", False))
        tk.Checkbutton(
            frame,
            text="Перенос строк",
            variable=self.wrap_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1
        
        # Подсветка синтаксиса
        self.highlight_var = tk.BooleanVar(value=self.config.get("syntax_highlight", True))
        tk.Checkbutton(
            frame,
            text="Подсветка синтаксиса",
            variable=self.highlight_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1
        
        # Миникарта
        self.minimap_var = tk.BooleanVar(value=self.config.get("minimap_enabled", True))
        tk.Checkbutton(
            frame,
            text="Показывать миникарту",
            variable=self.minimap_var,
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            selectcolor=VSColorScheme.BG_MEDIUM,
            activebackground=VSColorScheme.BG_MEDIUM
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1
        
        btn_frame = tk.Frame(self.window, bg=VSColorScheme.BG_MEDIUM)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(
            btn_frame,
            text="Сохранить",
            command=self.save,
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
    
    def save(self):
        self.config["font_family"] = self.font_var.get()
        self.config["font_size"] = self.size_var.get()
        self.config["tab_size"] = self.tab_var.get()
        self.config["auto_save"] = self.auto_save_var.get()
        self.config["word_wrap"] = self.wrap_var.get()
        self.config["syntax_highlight"] = self.highlight_var.get()
        self.config["minimap_enabled"] = self.minimap_var.get()
        
        self.callback(self.config)
        self.window.destroy()

class CodeEditorApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.tabs = []
        self.current_tab = None
        self.files = {}
        self.highlighter = None
        self._highlight_after_id = None
        self.auto_save_timer = None
        self.line_numbers = None
        self.minimap = None
        self.editor_scrollbar = None
        self.console_scrollbar = None
        
        self.setup_window()
        self.create_widgets()
        self.create_menu()
        self.bind_shortcuts()
        
        self.add_new_tab()
        
        last_folder = self.config.get("last_opened_folder", ".")
        if os.path.exists(last_folder):
            self.config["project_path"] = last_folder
            self.load_project_tree()
        else:
            self.load_project_tree()
        
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def setup_window(self):
        self.root.title(f"{APP_NAME} v{VERSION}")
        
        x = self.config.get("window_x", 100)
        y = self.config.get("window_y", 100)
        width = self.config.get("window_width", 1300)
        height = self.config.get("window_height", 800)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1000, 600)
        self.root.configure(bg=VSColorScheme.BG_DARK)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.bind('<Configure>', self.on_window_move)
    
    def on_window_move(self, event):
        if event.widget == self.root and self.root.state() == 'normal':
            self.config["window_x"] = self.root.winfo_x()
            self.config["window_y"] = self.root.winfo_y()
            self.config["window_width"] = self.root.winfo_width()
            self.config["window_height"] = self.root.winfo_height()
    
    def create_menu(self):
        menubar = tk.Menu(self.root, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый файл (Ctrl+N)", command=self.add_new_tab)
        file_menu.add_command(label="Открыть файл (Ctrl+O)", command=self.open_file)
        file_menu.add_command(label="Открыть папку (Ctrl+K)", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить (Ctrl+S)", command=self.save_file)
        file_menu.add_command(label="Сохранить как... (Ctrl+Shift+S)", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход (Alt+F4)", command=self.on_closing)
        
        edit_menu = tk.Menu(menubar, tearoff=0, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Найти (Ctrl+F)", command=self.open_find)
        edit_menu.add_command(label="Перейти к строке (Ctrl+G)", command=self.go_to_line)
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить всё (Alt+A)", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Настройки (F1)", command=self.open_settings)
        
        run_menu = tk.Menu(menubar, tearoff=0, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        menubar.add_cascade(label="Запуск", menu=run_menu)
        run_menu.add_command(label="Запустить (F5)", command=self.run_code)
        run_menu.add_separator()
        run_menu.add_command(label="Очистить консоль", command=self.clear_console)
        
        view_menu = tk.Menu(menubar, tearoff=0, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Показать/скрыть миникарту", command=self.toggle_minimap)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=VSColorScheme.BG_MEDIUM, fg=VSColorScheme.FG)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_widgets(self):
        # Верхняя панель
        toolbar = tk.Frame(self.root, bg=VSColorScheme.BG_MEDIUM, height=45)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        buttons = [
            ("📁", "Открыть файл", self.open_file),
            ("📂", "Открыть папку", self.open_folder),
            ("💾", "Сохранить", self.save_file),
            ("📄", "Новый", self.add_new_tab),
            ("▶", "Запуск", self.run_code),
            ("⚙", "Настройки", self.open_settings)
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
        
        # Основной контейнер
        main = tk.Frame(self.root, bg=VSColorScheme.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Горизонтальный сплиттер
        h_paned = tk.PanedWindow(
            main,
            orient=tk.HORIZONTAL,
            bg=VSColorScheme.BORDER,
            sashwidth=1,
            sashrelief=tk.FLAT
        )
        h_paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель
        left = tk.Frame(h_paned, bg=VSColorScheme.BG_MEDIUM, width=250)
        h_paned.add(left, width=250)
        
        # Заголовок
        header_frame = tk.Frame(left, bg=VSColorScheme.BG_MEDIUM)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            header_frame,
            text="ПРОВОДНИК",
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG_LIGHT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        
        self.folder_label = tk.Label(
            header_frame,
            text=os.path.basename(self.config["project_path"]),
            bg=VSColorScheme.BG_MEDIUM,
            fg=VSColorScheme.FG,
            font=("Segoe UI", 8),
            wraplength=230
        )
        self.folder_label.pack(anchor="w", pady=(2, 0))
        
        # Кнопки управления
        btn_frame = tk.Frame(left, bg=VSColorScheme.BG_MEDIUM)
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
            left,
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
        
        # Центральная область
        center = tk.Frame(h_paned, bg=VSColorScheme.BG_DARK)
        h_paned.add(center, width=800)
        
        # Вертикальный сплиттер
        v_paned = tk.PanedWindow(
            center,
            orient=tk.VERTICAL,
            bg=VSColorScheme.BORDER,
            sashwidth=1,
            sashrelief=tk.FLAT
        )
        v_paned.pack(fill=tk.BOTH, expand=True)
        
        # Область редактора
        editor_area = tk.Frame(v_paned, bg=VSColorScheme.BG_DARK)
        v_paned.add(editor_area, height=500)
        
        # Панель вкладок
        self.tab_bar = tk.Frame(editor_area, bg=VSColorScheme.BG_MEDIUM, height=55)
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
        
        # Горизонтальный контейнер для редактора и дополнительных элементов
        editor_container = tk.Frame(editor_area, bg=VSColorScheme.BG_DARK)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Номера строк
        self.line_numbers = LineNumbers(editor_container, None)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Редактор
        self.editor = tk.Text(
            editor_container,
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
        
        # Привязываем номера строк к редактору
        self.line_numbers.text_widget = self.editor
        self.line_numbers.attach_to_text_widget()
        
        # Скроллбар для редактора
        self.editor_scrollbar = tk.Scrollbar(
            editor_container,
            orient=tk.VERTICAL,
            command=self.on_editor_scroll,
            bg=VSColorScheme.SCROLLBAR,
            troughcolor=VSColorScheme.BG_DARK,
            width=12
        )
        self.editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor.config(yscrollcommand=self.on_editor_scrollbar_move)
        
        # Миникарта
        if self.config.get("minimap_enabled", True):
            self.minimap = Minimap(editor_container, self.editor)
            self.minimap.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка событий редактора
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<<Modified>>', self.on_text_modified)
        self.editor.bind('<MouseWheel>', self.on_editor_wheel)
        
        self.highlighter = SyntaxHighlighter(self.editor)
        
        # Консоль
        console_frame = tk.Frame(v_paned, bg=VSColorScheme.BG_DARK, height=150)
        v_paned.add(console_frame, height=150)
        
        console_header = tk.Frame(console_frame, bg=VSColorScheme.STATUS_BG, height=25)
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
        
        # Контейнер для консоли и скроллбара
        console_container = tk.Frame(console_frame, bg=VSColorScheme.BG_DARK)
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
        
        # Скроллбар для консоли
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
        
        # Строка состояния
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
    
    def on_editor_scroll(self, *args):
        """Обработка прокрутки скроллбаром редактора"""
        self.editor.yview(*args)
        self.line_numbers.update_numbers()
        if self.minimap:
            self.minimap.update_minimap()
    
    def on_editor_scrollbar_move(self, *args):
        """Обновление позиции скроллбара"""
        self.editor_scrollbar.set(*args)
        self.line_numbers.update_numbers()
        if self.minimap:
            self.minimap.update_minimap()
    
    def on_editor_wheel(self, event):
        """Обработка колесика мыши в редакторе"""
        self.line_numbers.update_numbers()
        if self.minimap:
            self.minimap.schedule_update()
    
    def open_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.config.get("last_opened_folder", "."),
            title="Выберите папку проекта"
        )
        
        if folder:
            self.config["project_path"] = folder
            self.config["last_opened_folder"] = folder
            save_config(self.config)
            
            self.folder_label.config(text=os.path.basename(folder))
            self.load_project_tree()
            self.status_label.config(text=f"Открыта папка: {folder}")
    
    def add_new_tab(self, filename=None, content=""):
        tab_title = Path(filename).name if filename else f"Безымянный {len(self.tabs) + 1}"
        tab = ModernTab(
            self.tabs_container,
            tab_title,
            self.close_tab,
            self.select_tab
        )
        tab.pack(side=tk.LEFT, padx=2, pady=3)
        
        self.tabs.append(tab)
        self.files[tab] = filename
        
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.editor.edit_modified(False)
        
        self.select_tab(tab)
        
        if filename:
            self.status_label.config(text=f"Открыт: {filename}")
        
        return tab
    
    def close_tab(self, tab):
        if len(self.tabs) <= 1:
            return
        
        if tab.modified:
            response = messagebox.askyesnocancel(
                "Сохранение",
                f"Сохранить изменения в '{tab.title}'?"
            )
            if response is None:
                return
            elif response:
                self.select_tab(tab)
                self.save_file()
        
        idx = self.tabs.index(tab)
        tab.destroy()
        self.tabs.remove(tab)
        del self.files[tab]
        
        if idx >= len(self.tabs):
            idx = len(self.tabs) - 1
        if self.tabs:
            self.select_tab(self.tabs[idx])
    
    def select_tab(self, tab):
        for t in self.tabs:
            t.set_active(t == tab)
        
        self.current_tab = tab
        
        filename = self.files.get(tab)
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.delete("1.0", tk.END)
                    self.editor.insert("1.0", content)
                    self.editor.edit_modified(False)
                    tab.set_modified(False)
                    
                    if self.config.get("syntax_highlight", True):
                        self.highlighter.highlight(force=True)
                    
                    self.line_numbers.update_numbers()
                    if self.minimap:
                        self.minimap.update_minimap()
            except Exception as e:
                self.log(f"Ошибка загрузки: {e}")
        else:
            self.editor.delete("1.0", tk.END)
            self.editor.edit_modified(False)
    
    def on_key_release(self, event):
        self.update_cursor_position()
        self.line_numbers.update_numbers()
        
        if self.config.get("syntax_highlight", True):
            if self._highlight_after_id:
                self.root.after_cancel(self._highlight_after_id)
            self._highlight_after_id = self.root.after(300, self.delayed_highlight)
        
        if self.config.get("auto_save", False) and self.current_tab:
            if self.auto_save_timer:
                self.root.after_cancel(self.auto_save_timer)
            self.auto_save_timer = self.root.after(2000, self.auto_save)
        
        if self.minimap:
            self.minimap.schedule_update()
    
    def on_text_modified(self, event):
        if self.editor.edit_modified() and self.current_tab:
            self.current_tab.set_modified(True)
            self.editor.edit_modified(False)
    
    def delayed_highlight(self):
        if self.highlighter:
            self.highlighter.highlight()
        self._highlight_after_id = None
    
    def auto_save(self):
        if self.current_tab and self.current_tab.modified:
            self.save_file()
    
    def update_cursor_position(self, event=None):
        try:
            pos = self.editor.index(tk.INSERT)
            line, col = pos.split('.')
            self.pos_label.config(text=f"Стр {line}, Кол {int(col) + 1}")
        except:
            pass
    
    def select_all(self, event=None):
        self.editor.tag_add("sel", "1.0", tk.END)
        return "break"
    
    def open_find(self, event=None):
        FindDialog(self.root, self.editor)
    
    def go_to_line(self, event=None):
        try:
            total_lines = int(self.editor.index('end-1c').split('.')[0])
            line = simpledialog.askinteger(
                "Перейти к строке",
                f"Номер строки (1-{total_lines}):",
                minvalue=1,
                maxvalue=total_lines
            )
            if line:
                self.editor.mark_set(tk.INSERT, f"{line}.0")
                self.editor.see(tk.INSERT)
                self.update_cursor_position()
        except:
            pass
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.config.get("project_path", "."),
            filetypes=[
                ("Python", "*.py"),
                ("JavaScript", "*.js"),
                ("HTML", "*.html"),
                ("CSS", "*.css"),
                ("JSON", "*.json"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.add_new_tab(filename=file_path, content=content)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def save_file(self):
        if not self.current_tab:
            return
        
        filename = self.files.get(self.current_tab)
        
        if not filename:
            self.save_file_as()
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.editor.get("1.0", tk.END).rstrip() + "\n")
            self.current_tab.set_modified(False)
            self.status_label.config(text=f"Сохранено: {filename}")
            self.log(f"✅ Сохранено: {Path(filename).name}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
    
    def save_file_as(self):
        if not self.current_tab:
            return
        
        file_path = filedialog.asksaveasfilename(
            initialdir=self.config.get("project_path", "."),
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            self.files[self.current_tab] = file_path
            self.current_tab.title_label.config(text=Path(file_path).name)
            self.save_file()
    
    def load_project_tree(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        project_root = self.config.get("project_path", ".")
        if not os.path.exists(project_root):
            project_root = "."
        
        self.folder_label.config(text=os.path.basename(project_root))
        
        root_name = os.path.basename(os.path.abspath(project_root)) or "Проект"
        root_node = self.file_tree.insert("", "end", text=f"📁 {root_name}", open=True)
        self.process_directory(project_root, root_node)
    
    def process_directory(self, path, parent):
        try:
            items = sorted(os.listdir(path))
            for item in items:
                if item.startswith('.') or item in ["__pycache__"]:
                    continue
                
                full_path = os.path.join(path, item)
                
                if os.path.isdir(full_path):
                    node = self.file_tree.insert(parent, "end", text=f"📁 {item}", open=False)
                    self.process_directory(full_path, node)
                else:
                    ext = os.path.splitext(item)[1].lower()
                    icons = {
                        ".py": "🐍",
                        ".js": "📜",
                        ".html": "🌐",
                        ".css": "🎨",
                        ".json": "📦",
                        ".md": "📘",
                        ".txt": "📝"
                    }
                    icon = icons.get(ext, "📄")
                    self.file_tree.insert(parent, "end", text=f"{icon} {item}", values=(full_path,))
        except:
            pass
    
    def on_file_double_click(self, event):
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
                    
                    for tab, fname in self.files.items():
                        if fname == file_path:
                            self.select_tab(tab)
                            return
                    
                    self.add_new_tab(filename=file_path, content=content)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def run_code(self):
        if not self.current_tab:
            return
        
        filename = self.files.get(self.current_tab)
        if not filename:
            self.save_file_as()
            filename = self.files.get(self.current_tab)
        
        if filename and os.path.exists(filename):
            self.save_file()
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
            self.log("="*50)
            self.log("✅ Завершено")
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
    
    def log(self, text):
        """Вывод в консоль"""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        # Автопрокрутка вниз
        self.console.yview_moveto(1.0)
    
    def write(self, text):
        self.log(text.rstrip())
        return len(text)
    
    def flush(self):
        pass
    
    def clear_console(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        self.log("✅ Консоль очищена")
    
    def toggle_minimap(self):
        self.config["minimap_enabled"] = not self.config.get("minimap_enabled", True)
        save_config(self.config)
        messagebox.showinfo("Миникарта", "Изменения вступят после перезапуска")
    
    def open_settings(self):
        SettingsDialog(self.root, self.config, self.apply_settings)
    
    def apply_settings(self, new_config):
        self.config = new_config
        save_config(self.config)
        
        self.editor.config(
            font=(self.config["font_family"], self.config["font_size"]),
            wrap=tk.WORD if self.config.get("word_wrap", False) else tk.NONE,
            tabs=(self.config["tab_size"] * 10,)
        )
        
        if self.config.get("syntax_highlight", True):
            self.highlighter.highlight(force=True)
        
        self.line_numbers.update_numbers()
        self.status_label.config(text="Настройки применены")
    
    def show_about(self):
        about_text = f"""{APP_NAME} v{VERSION}

Современный редактор кода в стиле VS Code
Разработан на Python с использованием Tkinter

Возможности:
• Подсветка синтаксиса Python
• Открытие папок и файлов
• Множественные вкладки
• Номера строк
• Миникарта для навигации
• Поиск (Ctrl+F)
• Переход к строке (Ctrl+G)
• Встроенная консоль
• Скроллбары в редакторе и консоли
• Сохранение позиции окна
• Настраиваемый интерфейс
• Автосохранение
• Горячие клавиши

© 2024 CodeCraft Pro
        """
        messagebox.showinfo("О программе", about_text)
    
    def bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.add_new_tab())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-k>', lambda e: self.open_folder())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_file_as())
        self.root.bind('<Control-w>', lambda e: self.close_current_tab())
        self.root.bind('<Alt-a>', self.select_all)
        self.root.bind('<Alt-A>', self.select_all)
        self.root.bind('<Control-f>', self.open_find)
        self.root.bind('<Control-g>', self.go_to_line)
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<F1>', lambda e: self.open_settings())
    
    def close_current_tab(self, event=None):
        if self.current_tab:
            self.close_tab(self.current_tab)
    
    def on_closing(self):
        unsaved = []
        for tab in self.tabs:
            if tab.modified:
                unsaved.append(tab.title)
        
        if unsaved:
            response = messagebox.askyesnocancel(
                "Несохраненные изменения",
                f"Есть несохраненные файлы:\n{', '.join(unsaved)}\n\nСохранить перед выходом?"
            )
            if response is None:
                return
            elif response:
                for tab in self.tabs:
                    if tab.modified:
                        self.select_tab(tab)
                        self.save_file()
        
        self.config["last_opened_folder"] = self.config.get("project_path", ".")
        save_config(self.config)
        
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()
```
