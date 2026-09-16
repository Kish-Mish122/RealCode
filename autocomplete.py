#!/usr/bin/env python3
# autocomplete.py — автодополнение для RealCode
import ast
import os
import re
import threading
from typing import List, Set

# ─── Встроенные имена Python ─────────────────────────────────────────
PYTHON_KEYWORDS = [
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
    'while', 'with', 'yield',
]

PYTHON_BUILTINS = [
    'abs', 'aiter', 'all', 'anext', 'any', 'ascii', 'bin', 'bool',
    'breakpoint', 'bytearray', 'bytes', 'callable', 'chr', 'classmethod',
    'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate',
    'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
    'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map',
    'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
    'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
    'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
    'super', 'tuple', 'type', 'vars', 'zip',
    # Часто используемые модули
    'self', 'cls', '__init__', '__main__', '__name__', '__file__',
    '__doc__', '__class__', '__dict__', 'Exception', 'ValueError',
    'TypeError', 'KeyError', 'IndexError', 'AttributeError',
    'RuntimeError', 'StopIteration', 'OSError', 'ImportError',
    'True', 'False', 'None',
]

# Популярные модули и их типичные атрибуты
COMMON_MODULES = {
    'os': ['path', 'getcwd', 'listdir', 'mkdir', 'makedirs', 'remove',
           'rmdir', 'rename', 'walk', 'environ', 'name', 'sep', 'linesep',
           'startfile', 'system', 'popen'],
    'sys': ['argv', 'exit', 'path', 'stdin', 'stdout', 'stderr',
            'platform', 'version', 'version_info', 'executable',
            'modules', 'maxsize', 'getsitepackages'],
    're': ['match', 'search', 'findall', 'finditer', 'sub', 'split',
           'compile', 'escape', 'IGNORECASE', 'MULTILINE', 'DOTALL'],
    'json': ['loads', 'dumps', 'load', 'dump', 'JSONDecodeError'],
    'math': ['sqrt', 'pow', 'pi', 'e', 'sin', 'cos', 'tan', 'log',
             'log10', 'exp', 'floor', 'ceil', 'fabs'],
    'time': ['time', 'sleep', 'ctime', 'localtime', 'strftime', 'strptime',
             'perf_counter', 'monotonic'],
    'datetime': ['datetime', 'date', 'time', 'timedelta', 'now',
                 'today', 'strftime', 'strptime', 'timestamp'],
    'random': ['random', 'randint', 'choice', 'shuffle', 'sample',
               'uniform', 'seed'],
    'tkinter': ['Tk', 'Toplevel', 'Frame', 'Label', 'Button', 'Entry',
                'Text', 'Canvas', 'Menu', 'StringVar', 'IntVar',
                'BooleanVar', 'mainloop'],
    'pathlib': ['Path', 'PurePath', 'PurePosixPath', 'PureWindowsPath'],
    'typing': ['List', 'Dict', 'Set', 'Tuple', 'Optional', 'Union',
               'Any', 'Callable', 'Iterable', 'Iterator'],
    'requests': ['get', 'post', 'put', 'delete', 'head', 'patch',
                 'Session', 'Response'],
    'threading': ['Thread', 'Lock', 'RLock', 'Event', 'Condition',
                  'Semaphore', 'Timer', 'current_thread'],
    'subprocess': ['run', 'Popen', 'call', 'check_output', 'check_call',
                   'DEVNULL', 'PIPE', 'STDOUT'],
}


class AutocompleteProvider:
    """Собирает варианты автодополнения из разных источников."""

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self._project_words: Set[str] = set()
        self._project_lock = threading.Lock()
        self._scan_thread = None
        self._scan_done = False

    # ─── Публичное API ───────────────────────────────────────────────
    def set_project(self, path: str):
        """Меняет проект и запускает фоновое сканирование."""
        if path == self.project_path and self._scan_done:
            return
        self.project_path = path
        self._project_words = set()
        self._scan_done = False
        self._start_project_scan()

    def get_suggestions(self, current_text: str, prefix: str,
                        before_cursor: str) -> List[str]:
        """Возвращает список подсказок, начинающихся с prefix."""
        if not prefix:
            # Если после точки — подсказываем атрибуты модуля
            m = re.search(r'(\w+)\.\s*$', before_cursor)
            if m:
                module = m.group(1)
                if module in COMMON_MODULES:
                    return sorted(COMMON_MODULES[module])
            return []

        prefix_lower = prefix.lower()
        candidates: Set[str] = set()

        # 1. Из текущего файла
        candidates.update(self._extract_from_source(current_text))

        # 2. Встроенные Python
        candidates.update(PYTHON_KEYWORDS)
        candidates.update(PYTHON_BUILTINS)

        # 3. Из проекта (если уже отсканирован)
        with self._project_lock:
            candidates.update(self._project_words)

        # 4. Модули и их атрибуты, если пишут после import
        for mod_name, attrs in COMMON_MODULES.items():
            candidates.add(mod_name)
            for a in attrs:
                candidates.add(a)

        # Фильтруем по prefix
        filtered = [
            c for c in candidates
            if c.lower().startswith(prefix_lower) and c != prefix
        ]
        # Сортируем: сначала короткие, потом по алфавиту
        filtered.sort(key=lambda s: (len(s), s.lower()))
        return filtered[:50]

    def get_dot_suggestions(self, obj_name: str) -> List[str]:
        """Список после obj. — только атрибуты известных модулей."""
        if obj_name in COMMON_MODULES:
            return sorted(COMMON_MODULES[obj_name])
        return []

    # ─── Парсинг файла ───────────────────────────────────────────────
    def _extract_from_source(self, source: str) -> Set[str]:
        """Вытаскивает имена из исходника."""
        result: Set[str] = set()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Если код ещё не дописан — берём регулярками
            return self._extract_with_regex(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.add(node.name)
                # Аргументы функции
                for arg in node.args.args:
                    result.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    result.add(arg.arg)
                if node.args.vararg:
                    result.add(node.args.vararg.arg)
                if node.args.kwarg:
                    result.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                result.add(node.name)
            elif isinstance(node, ast.Name):
                result.add(node.id)
            elif isinstance(node, ast.Attribute):
                result.add(node.attr)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result.add(alias.name.split('.')[0])
                    if alias.asname:
                        result.add(alias.asname)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    result.add(alias.name)
                    if alias.asname:
                        result.add(alias.asname)
            elif isinstance(node, ast.arg):
                result.add(node.arg)
            elif isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal):
                for name in node.names:
                    result.add(name)
        return result

    def _extract_with_regex(self, source: str) -> Set[str]:
        """Fallback, если AST не распарсил (неполный код)."""
        result: Set[str] = set()
        patterns = [
            r'\bdef\s+(\w+)',
            r'\bclass\s+(\w+)',
            r'\b(\w+)\s*=',           # переменные
            r'\bimport\s+(\w+)',
            r'\bfrom\s+(\w+)',
            r'\bfor\s+(\w+)\s+in',
            r'\bwith\s+.*?\bas\s+(\w+)',
            r'\basync\s+def\s+(\w+)',
        ]
        for pat in patterns:
            for m in re.finditer(pat, source):
                result.add(m.group(1))
        return result

    # ─── Сканирование проекта ────────────────────────────────────────
    def _start_project_scan(self):
        if self._scan_thread and self._scan_thread.is_alive():
            return
        self._scan_thread = threading.Thread(
            target=self._scan_project, daemon=True)
        self._scan_thread.start()

    def _scan_project(self):
        words: Set[str] = set()
        try:
            skip_dirs = {'.git', '__pycache__', '.idea', 'venv', '.venv',
                         'node_modules', 'build', 'dist', '.RLCode'}
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in skip_dirs
                           and not d.startswith('.')]
                for fname in files:
                    if not fname.endswith('.py'):
                        continue
                    fp = os.path.join(root, fname)
                    try:
                        # Ограничим размер файла, чтобы не тормозить
                        if os.path.getsize(fp) > 1_000_000:
                            continue
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            src = f.read()
                        words.update(self._extract_from_source(src))
                    except Exception:
                        pass
                # Не уходим глубже 4 уровней
                if root.count(os.sep) - self.project_path.count(os.sep) > 4:
                    dirs[:] = []
        except Exception as e:
            print(f"Ошибка сканирования проекта: {e}")

        with self._project_lock:
            self._project_words = words
        self._scan_done = True
