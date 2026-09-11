#!/usr/bin/env python3
# git_integration.py - Git-интеграция для RealCode
import os
import sys
import subprocess
from dataclasses import dataclass
from typing import List, Optional


def is_windows() -> bool:
    return sys.platform == 'win32'


# На Windows, чтобы не мигала консоль при вызове git
CREATE_NO_WINDOW = 0x08000000 if is_windows() else 0


@dataclass
class GitFileStatus:
    path: str        # путь относительно корня репозитория
    status: str      # 'M', 'A', 'D', 'R', '??', 'MM', 'AM', ...
    staged: bool     # изменения добавлены в индекс

    @property
    def marker(self) -> str:
        """Однобуквенный маркер для дерева файлов."""
        s = self.status
        if s == '??':
            return 'U'   # untracked
        if s.startswith('A'):
            return 'A'
        if s.startswith('M'):
            return 'M'
        if s.startswith('D'):
            return 'D'
        if s.startswith('R'):
            return 'R'
        if s.startswith('C'):
            return 'C'
        return s[:1] if s else '?'


class GitManager:
    """Обёртка над CLI git для конкретного проекта."""

    def __init__(self, project_path: str):
        self.path = os.path.abspath(project_path)

    # ---------- низкоуровневый запуск ----------
    def _run(self, args: List[str], check: bool = True, timeout: int = 30):
        """Запускает git. Возвращает (stdout, stderr) или (None, error)."""
        try:
            result = subprocess.run(
                ['git', '-c', 'core.quotepath=false'] + args,
                cwd=self.path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
            if check and result.returncode != 0:
                err = (result.stderr or result.stdout or '').strip()
                return None, err or f"git завершился с кодом {result.returncode}"
            return result.stdout or '', result.stderr or ''
        except FileNotFoundError:
            return None, "git не найден в PATH. Установите Git."
        except subprocess.TimeoutExpired:
            return None, "git: превышено время ожидания."
        except Exception as e:
            return None, f"git: {e}"

    # ---------- общие проверки ----------
    def is_git_installed(self) -> bool:
        out, _ = self._run(['--version'], check=False)
        return bool(out and 'git version' in out)

    def is_repo(self) -> bool:
        if not os.path.isdir(os.path.join(self.path, '.git')):
            return False
        out, _ = self._run(['rev-parse', '--is-inside-work-tree'], check=False)
        return bool(out and out.strip() == 'true')

    # ---------- основные операции ----------
    def init(self):
        return self._run(['init'])

    def current_branch(self) -> Optional[str]:
        out, err = self._run(['rev-parse', '--abbrev-ref', 'HEAD'], check=False)
        if out is None:
            return None
        branch = out.strip()
        if branch == 'HEAD':
            h, _ = self._run(['rev-parse', '--short', 'HEAD'], check=False)
            return f"(detached {h.strip()})" if h else "(detached)"
        return branch

    def has_commits(self) -> bool:
        out, _ = self._run(['rev-parse', '--verify', 'HEAD'], check=False)
        return out is not None and bool(out.strip())

    def has_remote(self) -> bool:
        out, _ = self._run(['remote'], check=False)
        return bool((out or '').strip())

    def remote_url(self) -> Optional[str]:
        out, _ = self._run(['remote', 'get-url', 'origin'], check=False)
        if out and out.strip():
            return out.strip()
        return None

    def status(self) -> List[GitFileStatus]:
        out, err = self._run(
            ['status', '--porcelain=v1', '--untracked-files=all'],
            check=False
        )
        if out is None:
            return []
        files: List[GitFileStatus] = []
        for line in out.splitlines():
            if len(line) < 4:
                continue
            index_status = line[0]
            worktree_status = line[1]
            raw = line[3:]
            if ' -> ' in raw:
                raw = raw.split(' -> ', 1)[1]
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1]

            if index_status == '?' and worktree_status == '?':
                status = '??'
            elif index_status != ' ' and index_status != '?':
                status = index_status
            else:
                status = worktree_status

            staged = index_status not in (' ', '?')
            files.append(GitFileStatus(path=raw, status=status, staged=staged))
        return files

    def add(self, paths: Optional[List[str]] = None):
        args = ['add'] + (paths if paths else ['-A'])
        return self._run(args)

    def commit(self, message: str, paths: Optional[List[str]] = None):
        if paths:
            # добавляем только выбранные файлы
            add_res = self._run(['add', '--'] + paths)
            if add_res[0] is None:
                return add_res
        return self._run(['commit', '-m', message], timeout=60)

    def push(self, set_upstream: bool = False):
        if set_upstream:
            branch = self.current_branch()
            if branch and not branch.startswith('('):
                return self._run(['push', '-u', 'origin', branch], timeout=120)
        return self._run(['push'], timeout=120)

    def pull(self):
        return self._run(['pull'], timeout=120)

    def fetch(self):
        return self._run(['fetch'], timeout=60)

    def log(self, n: int = 30) -> List[dict]:
        out, err = self._run(
            ['log', f'-n{n}', '--pretty=format:%h|%an|%ar|%s'],
            check=False
        )
        if not out:
            return []
        commits = []
        for line in out.splitlines():
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'subject': parts[3],
                })
        return commits

    def diff(self, path: Optional[str] = None) -> str:
        args = ['diff']
        if path:
            args += ['--', path]
        out, _ = self._run(args, check=False)
        return out or ''