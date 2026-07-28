#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import glob
import shutil
from datetime import datetime

def backup_main_py():
    """Create backup of main.py before build"""
    if not os.path.exists("main.py"):
        print("[WARN] main.py not found, skipping backup")
        return False
    
    # Проверка, что main.py не бинарный (нет нулевых байтов)
    try:
        with open("main.py", "rb") as f:
            content = f.read()
            if b'\x00' in content:
                print("ОШИБКА: main.py содержит нулевые байты! Файл повреждён.")
                print("   Сборка прервана. Восстановите main.py из резервной копии.")
                return False
    except Exception as e:
        print(f"Не удалось проверить main.py: {e}")
        return False
    
    # Создаём папку для бэкапов, если её нет
    backup_dir = "backup_main"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Имя бэкапа с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"main_backup_{timestamp}.py"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2("main.py", backup_path)
        print(f"[OK] Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {e}")
        return False

def check_windows():
    if os.name != 'nt':
        print("[ERROR] Build failed! Windows required")
        sys.exit(1)
    
    print("=" * 60)
    print("               RealCode Builder v3.2")
    print("=" * 60)
    print()
    
    main()

def cleanup_before_build():
    """Очистка перед сборкой"""
    print("[INFO] Cleaning before build...")
    
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["RealCode.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                print(f"   [OK] {dir_name} deleted")
            except Exception as e:
                print(f"   [WARN] {dir_name} not deleted: {e}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"   [OK] {file_name} deleted")
            except Exception as e:
                print(f"   [WARN] {file_name} not deleted: {e}")

def cleanup_after_build():
    """Очистка после сборки"""
    print("\n[INFO] Cleaning temporary files...")
    
    temp_patterns = ["*.log", "*.tmp", "*.pyc", "*.pyo"]
    dirs_to_remove = ["build", "__pycache__"]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
            except:
                pass
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
            except:
                pass

def main():
    print("=" * 60)
    print("               RealCode Builder v3.2")
    print("=" * 60)
    print()
    
    try:
        import PyInstaller
        print("[OK] PyInstaller found")
    except ImportError:
        print("[ERROR] PyInstaller not installed!")
        print("   Install: pip install pyinstaller")
        return

    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        print("[ERROR] icon.ico not found!")
        print(f"   Path: {os.getcwd()}")
        return
    
    print(f"[OK] Icon found: {icon_path}")
    size = os.path.getsize(icon_path)
    print(f"   Size: {size} bytes")

    if not os.path.exists("main.py"):
        print("[ERROR] main.py not found!")
        return
    
    if os.path.exists("settings.json"):
        print("[OK] settings.json found (will be saved)")

    print("\n[INFO] Creating version_info.txt...")
    version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(3, 7, 0, 0),
    prodvers=(3, 7, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'K1sh-M1sh'),
        StringStruct(u'FileDescription', u'RealCode for Scripting'),
        StringStruct(u'FileVersion', u'3.7.0'),
        StringStruct(u'InternalName', u'RealCode'),
        StringStruct(u'LegalCopyright', u'MIT'),
        StringStruct(u'OriginalFilename', u'RealCode.exe'),
        StringStruct(u'ProductName', u'RealCode'),
        StringStruct(u'ProductVersion', u'3.7.0'),
        StringStruct(u'Comments', u'RealCode for Scripting')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 0x04B0])])
  ]
)"""
    
    try:
        with open("version_info.txt", "w", encoding="utf-8") as f:
            f.write(version_info)
        print("[OK] version_info.txt created")
    except Exception as e:
        print(f"[ERROR] Error creating version_info.txt: {e}")
        return
    
    print("\n[INFO] Cleaning before build...")
    cleanup_before_build()
    
    print("\n[INFO] Starting build...\n")
    
    cmd = [
        "pyinstaller",
        "--windowed",
        "--onefile",
        "--name=RealCode",
        "--noconfirm",
        "--clean",
        f"--icon={icon_path}",
        f"--add-data={icon_path};.",
        "--version-file=version_info.txt",
        "main.py"
    ]
    
    print("Команда сборки:")
    print("  " + " ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("[SUCCESS] BUILD COMPLETED!")
            print("=" * 60)
            
            exe_path = "dist\\RealCode.exe"
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path)
                print(f"\n[FILE] File: {exe_path}")
                print(f"[SIZE] Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
                
                try:
                    from datetime import datetime
                    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"RealCode_{date_str}.exe"
                    shutil.copy2(exe_path, backup_name)
                    print(f"[BACKUP] Backup: {backup_name}")
                except Exception as e:
                    print(f"[WARN] Failed to create backup: {e}")
            else:
                print("[ERROR] File not found after build!")
            
            cleanup_after_build()
            
        else:
            print("\n" + "=" * 60)
            print("[ERROR] BUILD FAILED!")
            print("=" * 60)
            print(f"\n[ERROR] Return code: {result.returncode}")
            print("\n[ERROR] Error output:")
            print(result.stderr)
    
    except subprocess.TimeoutExpired:
        print("[ERROR] Build timeout exceeded!")
    except Exception as e:
        print(f"[ERROR] Execution error: {e}")
    
    print("\n" + "=" * 60)
    print("[INFO] IMPORTANT FILES SAVED:")
    print("   - settings.json (settings)")
    print("   - icon.ico (icon)")
    print("   - main.py (source code)")
    print("=" * 60)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    check_windows()
