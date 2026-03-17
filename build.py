import os
import sys
import subprocess
import time
import glob

def force_remove(path):
    """Принудительное удаление файла/папки"""
    try:
        if os.path.isfile(path):
            os.chmod(path, 0o777)
            os.remove(path)
            return True
        elif os.path.isdir(path):
            import stat
            import shutil
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, 0o777)
                    except:
                        pass
            
            shutil.rmtree(path, ignore_errors=True)
            
            if not os.path.exists(path):
                return True
            
            try:
                subprocess.run(f'rmdir /s /q "{path}"', shell=True, capture_output=True)
            except:
                pass
            
            return not os.path.exists(path)
    except:
        pass
    return False

def cleanup_before_build():
    """Очистка перед сборкой"""
    print("\n🧹 Очистка перед сборкой...")
    
    time.sleep(1)
    
    # Папки для удаления (НО НЕ трогаем текущую папку с файлами)
    dirs_to_remove = ["build", "__pycache__"]
    
    # Файлы для удаления (НО НЕ settings.json и НЕ version_info.txt)
    files_to_remove = ["RealCode.spec"]
    
    # НЕ УДАЛЯЕМ dist - там может быть старый exe, но его можно перезаписать
    
    # Удаляем папки
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"  Удаляю {dir_name}...")
            try:
                import shutil
                shutil.rmtree(dir_name, ignore_errors=True)
                time.sleep(0.5)
                print(f"    ✅ {dir_name} удален")
            except:
                if force_remove(dir_name):
                    print(f"    ✅ {dir_name} удален")
                else:
                    print(f"    ⚠️  Не удалось удалить {dir_name}")
    
    # Удаляем файлы
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            print(f"  Удаляю {file_name}...")
            try:
                os.remove(file_name)
                print(f"    ✅ {file_name} удален")
            except:
                pass

def cleanup_after_build():
    """Очистка после сборки"""
    print("\n🧹 Очистка временных файлов...")
    
    # Удаляем только временные файлы
    temp_patterns = ["*.log", "*.tmp", "*.pyc", "*.pyo"]
    dirs_to_remove = ["build", "__pycache__"]
    
    # Удаляем временные файлы
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"  Удаляю {file_path}... ✅")
            except:
                pass
    
    # Удаляем папку build
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                import shutil
                shutil.rmtree(dir_name, ignore_errors=True)
                print(f"  Удаляю {dir_name}... ✅")
            except:
                pass

def main():
    print("=" * 60)
    print("               RealCode Builder v2.9")
    print("=" * 60)
    print()
    
    # Проверяем PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller найден")
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print("\nУстановка: pip install pyinstaller")
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверяем иконку - ДОЛЖНА БЫТЬ В ТЕКУЩЕЙ ПАПКЕ
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        print("❌ Файл icon.ico не найден!")
        print("\nСоздайте иконку и сохраните её как 'icon.ico' в папке:")
        print(f"   {os.getcwd()}")
        print("\nИли скачайте пример иконки и переименуйте в icon.ico")
        input("\nНажмите Enter для выхода...")
        return
    else:
        print(f"✅ Иконка найдена: {icon_path}")
        # Показываем размер иконки
        size = os.path.getsize(icon_path)
        print(f"   Размер: {size} байт")
    
    # Проверяем main.py
    if not os.path.exists("main.py"):
        print("❌ Файл main.py не найден!")
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверяем settings.json - ЕГО НЕ УДАЛЯТЬ!
    if os.path.exists("settings.json"):
        print("✅ settings.json найден (будет сохранен)")
    
    # Создаем version_info.txt
    print("\n📄 Создание version_info.txt...")
    version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 9, 0, 0),
    prodvers=(2, 9, 0, 0),
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
        StringStruct(u'FileDescription', u'RealCode - Lightweight Code Editor'),
        StringStruct(u'FileVersion', u'2.9.0'),
        StringStruct(u'InternalName', u'RealCode'),
        StringStruct(u'LegalCopyright', u'(C) 2026 K1sh-M1sh'),
        StringStruct(u'OriginalFilename', u'RealCode.exe'),
        StringStruct(u'ProductName', u'RealCode'),
        StringStruct(u'ProductVersion', u'2.9.0'),
        StringStruct(u'Comments', u'Code editor in VS Code style')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 0x04B0])])
  ]
)"""
    
    try:
        with open("version_info.txt", "w", encoding="utf-8") as f:
            f.write(version_info)
        print("✅ version_info.txt создан")
    except Exception as e:
        print(f"❌ Ошибка создания version_info.txt: {e}")
        input("\nНажмите Enter для выхода...")
        return
    
    # Очистка перед сборкой
    cleanup_before_build()
    
    print("\n🚀 Начинаю сборку...\n")
    
    # Базовая команда
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=RealCode",
        "--noconfirm",
        "--clean",
        "main.py"
    ]
    
    # Добавляем иконку (ОБЯЗАТЕЛЬНО)
    cmd.insert(3, f"--icon={icon_path}")
    cmd.insert(4, f"--add-data={icon_path};.")
    
    # Добавляем версионную информацию
    cmd.insert(3, "--version-file=version_info.txt")
    
    print("Команда сборки:")
    print("  " + " ".join(cmd))
    print()
    
    # Запуск сборки
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ СБОРКА УСПЕШНО ЗАВЕРШЕНА!")
            print("=" * 60)
            
            exe_path = "dist\\RealCode.exe"
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path)
                print(f"\n📁 Файл: {exe_path}")
                print(f"📊 Размер: {size:,} байт ({size/1024/1024:.2f} MB)")
                
                # Проверяем, что иконка встроена
                print("\n🔍 Проверка иконки:")
                print("   Иконка должна быть видна в проводнике")
                print("   Если нет - проверьте формат icon.ico")
                
                # Копируем в текущую папку
                try:
                    import shutil
                    from datetime import datetime
                    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"RealCode_{date_str}.exe"
                    shutil.copy2(exe_path, backup_name)
                    print(f"\n📋 Резервная копия: {backup_name}")
                except Exception as e:
                    print(f"⚠️  Не удалось создать копию: {e}")
            else:
                print("\n❌ Файл не найден после сборки!")
            
            # Очистка после сборки
            cleanup_after_build()
            
        else:
            print("\n" + "=" * 60)
            print("❌ ОШИБКА ПРИ СБОРКЕ!")
            print("=" * 60)
            print(f"\nКод ошибки: {result.returncode}")
            print("\nВывод ошибки:")
            print(result.stderr)
    
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ВАЖНЫЕ ФАЙЛЫ СОХРАНЕНЫ:")
    print("   - settings.json (настройки)")
    print("   - icon.ico (иконка)")
    print("   - main.py (исходный код)")
    print("=" * 60)
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
