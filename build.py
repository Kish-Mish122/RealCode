#!/usr/bin/env python3
# build.py - RealCode Builder
import os
import sys
import subprocess
import time
import glob
import shutil
import argparse
from datetime import datetime
import platform

# Папки для выходных бинарников
OUTPUT_DIRS = {
    "windows": "Windows_Bin",
    "linux":   "Linux_Bin",
    "macos":   "MacOS_Bin",
}

# Создавать ли копию с таймстампом рядом (True/False)
KEEP_TIMESTAMPED_COPY = False


# =====================================================================
# ПЛАТФОРМЕННЫЕ ХЕЛПЕРЫ
# =====================================================================

def get_native_platform():
    """Платформа, на которой мы реально запущены."""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'macos'
    return system


def get_executable_name(target_platform):
    if target_platform == 'windows':
        return "RealCode.exe"
    return "RealCode"


def get_icon_name(target_platform):
    if target_platform == 'windows':
        return "icon.ico"
    return "icon.png"


def get_icon_path(target_platform):
    icon_name = get_icon_name(target_platform)
    if os.path.exists(icon_name):
        return icon_name
    for ext in ['.ico', '.png', '.svg']:
        p = f"icon{ext}"
        if os.path.exists(p):
            return p
    return None


def backup_main_py():
    if not os.path.exists("main.py"):
        print("⚠️ main.py не найден, пропускаю бэкап")
        return False

    try:
        with open("main.py", "rb") as f:
            content = f.read()
            if b'\x00' in content:
                print("ОШИБКА: main.py содержит нулевые байты! Файл повреждён.")
                return False
    except Exception as e:
        print(f"Не удалось проверить main.py: {e}")
        return False

    backup_dir = "backup_main"
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"main_backup_{ts}.py")
    try:
        shutil.copy2("main.py", backup_path)
        print(f"✅ Резервная копия: {backup_path}")
        return True
    except Exception as e:
        print(f"Не удалось создать бэкап: {e}")
        return False


def force_remove(path):
    try:
        if os.path.isfile(path):
            os.chmod(path, 0o777)
            os.remove(path)
            return True
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        os.chmod(os.path.join(root, f), 0o777)
                    except Exception:
                        pass
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.exists(path):
                return True
            if get_native_platform() == 'windows':
                subprocess.run(f'rmdir /s /q "{path}"', shell=True, capture_output=True)
            else:
                subprocess.run(f'rm -rf "{path}"', shell=True, capture_output=True)
            return not os.path.exists(path)
    except Exception:
        pass
    return False


def cleanup_before_build():
    print("\n🧹 Очистка перед сборкой...")
    time.sleep(0.5)
    for d in ["build", "__pycache__"]:
        if os.path.exists(d):
            print(f"  Удаляю {d}...")
            if not force_remove(d):
                print(f"    ⚠️ Не удалось удалить {d}")
    for f in ["RealCode.spec", "RealCode.exe.spec"]:
        if os.path.exists(f):
            print(f"  Удаляю {f}...")
            try:
                os.remove(f)
            except Exception:
                pass


def cleanup_after_build():
    print("\n🧹 Очистка временных файлов...")
    for pattern in ["*.log", "*.tmp", "*.pyc", "*.pyo"]:
        for fp in glob.glob(pattern):
            try:
                os.remove(fp)
            except Exception:
                pass
    for d in ["build", "__pycache__"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)


# =====================================================================
# СБОРКА
# =====================================================================

def build_for_platform(target_platform: str) -> bool:
    """Собирает под указанную платформу. Раскладывает бинарник
    в Linux_Bin/, Windows_Bin/ или MacOS_Bin/."""
    native = get_native_platform()

    print(f"\n{'=' * 60}")
    print(f"  Сборка под: {target_platform.upper()}")
    print(f"  На платформе: {native.upper()}")
    print(f"{'=' * 60}\n")

    # --- Проверка возможности сборки ---
    if target_platform != native:
        print(f"❌ НЕВОЗМОЖНО: PyInstaller не умеет кросс-компиляцию.")
        print(f"   Ты на {native}, а запросил {target_platform}.")
        print()
        print("   Что делать:")
        print("   1. Запусти build.py на машине с нужной ОС")
        print("   2. Или используй GitHub Actions (build.yml в .github/workflows/)")
        print("   3. Или Docker с wine для Windows-сборки из Linux")
        return False

    # --- PyInstaller ---
    try:
        import PyInstaller  # noqa: F401
        print("✅ PyInstaller найден")
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print("   Установи: pip install pyinstaller")
        return False

    if not os.path.exists("main.py"):
        print("❌ Файл main.py не найден!")
        return False

    if not backup_main_py():
        print("❌ Сборка прервана")
        return False

    # --- Иконка ---
    icon_file = get_icon_path(target_platform)
    if icon_file:
        print(f"✅ Иконка: {icon_file} ({os.path.getsize(icon_file)} байт)")
    else:
        print("⚠️ Иконка не найдена, сборка без неё")

    # --- version_info (только Windows) ---
    version_file = None
    if target_platform == 'windows':
        version_file = "version_info.txt"
        version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(4, 0, 0, 0),
    prodvers=(4, 0, 0, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
    ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'K1sh-M1sh'),
        StringStruct(u'FileDescription', u'RealCode for Scripting'),
        StringStruct(u'FileVersion', u'4.1'),
        StringStruct(u'InternalName', u'RealCode'),
        StringStruct(u'LegalCopyright', u'MIT'),
        StringStruct(u'OriginalFilename', u'RealCode.exe'),
        StringStruct(u'ProductName', u'RealCode'),
        StringStruct(u'ProductVersion', u'4.1')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 0x04B0])])
  ]
)"""
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(version_info)
        print(f"✅ Создан {version_file}")

    # --- Очистка ---
    cleanup_before_build()

    # --- Указываем PyInstaller, куда класть результат ---
    # По умолчанию PyInstaller пишет в ./dist — потом мы перенесём файл
    exe_name = get_executable_name(target_platform)

    # --- Собираем команду ---
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        f"--name={exe_name}",
        "--noconfirm",
        "--clean",
        "--hidden-import=config",
    ]

    # Иконка
    if icon_file:
        cmd.append(f"--icon={icon_file}")
        sep = ";" if target_platform == "windows" else ":"
        cmd.append(f"--add-data={icon_file}{sep}.")

    # version_info
    if version_file and os.path.exists(version_file):
        cmd.append(f"--version-file={version_file}")

    # --windowed только для GUI-приложений Windows
    if target_platform == "windows":
        cmd.append("--windowed")

    # Дополнительные данные
    for extra in ("settings.json",):
        if os.path.exists(extra):
            sep = ";" if target_platform == "windows" else ":"
            cmd.append(f"--add-data={extra}{sep}.")

    # Скрипт
    cmd.append("main.py")

    print("\n🔨 Команда сборки:")
    print("   " + " ".join(cmd))
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("\n" + "=" * 60)
            print("❌ ОШИБКА СБОРКИ")
            print("=" * 60)
            print(f"Код: {result.returncode}")
            print("\nSTDERR:")
            print(result.stderr)
            if result.stdout:
                print("\nSTDOUT:")
                print(result.stdout)
            return False

        # --- Успех ---
        print("\n" + "=" * 60)
        print("✅ СБОРКА УСПЕШНО ЗАВЕРШЕНА")
        print("=" * 60)

        src_path = os.path.join("dist", exe_name)
        if not os.path.exists(src_path):
            print("⚠️ Файл не найден в dist/")
            return False

        # --- Готовим целевую папку ---
        out_dir = OUTPUT_DIRS.get(target_platform, "dist")
        os.makedirs(out_dir, exist_ok=True)
        final_path = os.path.join(out_dir, exe_name)

        # Удаляем старую версию в целевой папке (если есть)
        if os.path.exists(final_path):
            try:
                os.remove(final_path)
            except Exception:
                force_remove(final_path)

        # Переносим
        try:
            shutil.move(src_path, final_path)
        except Exception as e:
            # Если перемещение между дисками не сработало — копируем
            print(f"⚠️ shutil.move не сработал ({e}), копирую")
            shutil.copy2(src_path, final_path)
            try:
                os.remove(src_path)
            except Exception:
                pass

        # Делаем бинарник исполняемым (Linux/macOS)
        if target_platform in ("linux", "macos"):
            try:
                os.chmod(final_path, 0o755)
            except Exception:
                pass

        size = os.path.getsize(final_path)
        print(f"\n📦 Файл:      {final_path}")
        print(f"📏 Размер:    {size:,} байт ({size / 1024 / 1024:.2f} MB)")
        print(f"📁 Папка:     {out_dir}/")

        # --- Опциональная копия с таймстампом ---
        if KEEP_TIMESTAMPED_COPY:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(exe_name)
            ts_name = f"{base}_{date_str}{ext}"
            ts_path = os.path.join(out_dir, ts_name)
            try:
                shutil.copy2(final_path, ts_path)
                print(f"💾 Снимок:    {ts_path}")
            except Exception as e:
                print(f"⚠️ Не удалось создать снимок: {e}")

        return True
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
        return False

# =====================================================================
# CLI
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RealCode Builder — сборка под Windows / Linux / macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python build.py                 # автоопределение (текущая ОС)
  python build.py --windows       # собрать .exe (только на Windows)
  python build.py --linux         # собрать ELF (только на Linux)
  python build.py --macos         # собрать .app (только на macOS)
  python build.py --all           # собрать под все ОС (если поддерживается)

Внимание: PyInstaller не умеет кросс-компиляцию. Флаги --windows/--linux
на неподходящей ОС выдадут понятную ошибку с подсказкой.
        """
    )
    parser.add_argument("--windows", action="store_true",
                        help="Собрать под Windows (.exe)")
    parser.add_argument("--linux", action="store_true",
                        help="Собрать под Linux (ELF)")
    parser.add_argument("--macos", action="store_true",
                        help="Собрать под macOS")
    parser.add_argument("--all", action="store_true",
                        help="Собрать под все поддерживаемые ОС (кросс-компиляция невозможна)")

    args = parser.parse_args()

    native = get_native_platform()
    print("=" * 60)
    print("           RealCode Builder v4.0")
    print(f"           Платформа: {native.upper()}")
    print("=" * 60)

    # Определяем целевые платформы
    targets = []
    if args.all:
        targets = ["windows", "linux", "macos"]
    elif args.windows:
        targets = ["windows"]
    elif args.linux:
        targets = ["linux"]
    elif args.macos:
        targets = ["macos"]
    else:
        targets = [native]
        print(f"\nℹ️ Флаг не указан — собираю под текущую ОС: {native}")

    # Фильтр: убираем всё, что не совпадает с native
    buildable = [t for t in targets if t == native]
    skipped = [t for t in targets if t != native]

    if skipped:
        print(f"\n⚠️ Пропускаю (кросс-компиляция невозможна): {', '.join(skipped)}")
        print("   Собери их на соответствующей ОС или через GitHub Actions.")
        print("   Готовый workflow: .github/workflows/build.yml")

    if not buildable:
        print("\n❌ Нечего собирать — все цели требуют другой ОС.")
        print("   Запусти build.py на Windows/Linux/macOS по отдельности.")
        sys.exit(1)

    # Собираем
    success = True
    for t in buildable:
        ok = build_for_platform(t)
        success = success and ok
        if not ok:
            break

    if success:
        cleanup_after_build()
        print("\n" + "=" * 60)
        print("ГОТОВО")
        print("=" * 60)

    if sys.stdin.isatty():
        input("\nНажми Enter для выхода...")


if __name__ == "__main__":
    main()
