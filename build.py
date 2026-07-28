import os
import sys
import subprocess
import time
import glob
import shutil
from datetime import datetime
import platform

def backup_main_py():
    """Создание резервной копии main.py перед сборкой"""
    if not os.path.exists("main.py"):
        print("⚠️ main.py не найден, пропускаю бэкап")
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
        print(f"Создана резервная копия: {backup_path}")
        return True
    except Exception as e:
        print(f"Не удалось создать бэкап: {e}")
        return False

def get_platform():
    """Определяет платформу для сборки"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'macos'
    else:
        return system

def get_executable_name():
    """Возвращает имя исполняемого файла в зависимости от ОС"""
    if get_platform() == 'windows':
        return "RealCode.exe"
    else:
        return "RealCode"

def get_pyinstaller_args():
    """Возвращает специфичные для ОС аргументы PyInstaller"""
    args = []
    if get_platform() == 'windows':
        args.append("--windowed")
    else:
        # На Linux создаём консольное приложение (можно убрать --windowed)
        # Если нужно скрыть консоль на Linux, используйте --noconsole
        pass
    return args

def get_icon_path():
    """Возвращает путь к иконке в зависимости от ОС"""
    icon_name = "icon.ico" if get_platform() == 'windows' else "icon.png"
    if os.path.exists(icon_name):
        return icon_name
    # fallback - ищем любой файл иконки
    for ext in ['.ico', '.png', '.svg']:
        if os.path.exists(f"icon{ext}"):
            return f"icon{ext}"
    return None

def force_remove(path):
    """Принудительное удаление файла/папки (кроссплатформенный вариант)"""
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
        
        # Попытка удалить через системную команду
        if get_platform() == 'windows':
            subprocess.run(f'rmdir /s /q "{path}"', shell=True, capture_output=True)
        else:
            subprocess.run(f'rm -rf "{path}"', shell=True, capture_output=True)
        
        return not os.path.exists(path)
    except:
        pass
    return False

def cleanup_before_build():
    """Очистка перед сборкой"""
    print("\nОчистка перед сборкой...")
    
    time.sleep(1)
    
    # Папки для удаления
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["RealCode.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"  Удаляю {dir_name}...")
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                time.sleep(0.5)
                print(f"    {dir_name} удален")
            except:
                if force_remove(dir_name):
                    print(f"    {dir_name} удален")
                else:
                    print(f"    Не удалось удалить {dir_name}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            print(f"  Удаляю {file_name}...")
            try:
                os.remove(file_name)
                print(f"    {file_name} удален")
            except:
                pass

def cleanup_after_build():
    """Очистка после сборки"""
    print("\nОчистка временных файлов...")
    
    temp_patterns = ["*.log", "*.tmp", "*.pyc", "*.pyo"]
    dirs_to_remove = ["build", "__pycache__"]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"  Удаляю {file_path}... ")
            except:
                pass
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                print(f"  Удаляю {dir_name}... ")
            except:
                pass

def main():
    print("=" * 60)
    print("               RealCode Builder v3.1")
    print(f"               Платформа: {get_platform().upper()}")
    print("=" * 60)
    print()
    
    # Проверяем PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller найден")
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print("\nУстановить: pip install pyinstaller")
        print("Или через pipx: pipx install pyinstaller")
        input("\nНажмите Enter для выхода...")
        return

    # Проверяем иконку
    icon_file = get_icon_path()
    if not icon_file:
        print("⚠️ Иконка не найдена! Сборка без иконки.")
        print("   Для Windows нужен icon.ico")
        print("   Для Linux нужен icon.png")
    else:
        print(f"✅ Иконка найдена: {icon_file}")
        size = os.path.getsize(icon_file)
        print(f"   Размер: {size} байт")

    if not os.path.exists("main.py"):
        print("❌ Файл main.py не найден!")
        input("\nНажмите Enter для выхода...")
        return

    # Создаём бэкап и проверяем целостность
    if not backup_main_py():
        print("❌ Сборка прервана из-за проблем с main.py")
        input("\nНажмите Enter для выхода...")
        return
    
    if os.path.exists("settings.json"):
        print("✅ settings.json найден (будет сохранен)")
    
    # Создаем version_info.txt (только для Windows)
    if get_platform() == 'windows':
        print("\nСоздание version_info.txt...")
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
        StringStruct(u'FileDescription', u'RealCode for Scripting'),
        StringStruct(u'FileVersion', u'3.8.0'),
        StringStruct(u'InternalName', u'RealCode'),
        StringStruct(u'LegalCopyright', u'MIT'),
        StringStruct(u'OriginalFilename', u'RealCode.exe'),
        StringStruct(u'ProductName', u'RealCode'),
        StringStruct(u'ProductVersion', u'3.8.0'),
        StringStruct(u'Comments', u'RealCode for Scripting')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 0x04B0])])
  ]
)"""
        try:
            with open("version_info.txt", "w", encoding="utf-8") as f:
                f.write(version_info)
            print("✅ version_info.txt создан")
        except Exception as e:
            print(f"Ошибка создания version_info.txt: {e}")
            input("\nНажмите Enter для выхода...")
            return
    
    # Очистка перед сборкой
    cleanup_before_build()
    
    print("\nНачинаю сборку...\n")
    
    # Базовая команда
    exe_name = get_executable_name()
    cmd = [
        "pyinstaller",
        "--onefile",
        f"--name={exe_name}",
        "--noconfirm",
        "--clean",
        "main.py"
    ]
    
    # Добавляем специфичные для ОС аргументы
    cmd.extend(get_pyinstaller_args())
    
    # Добавляем иконку (если есть)
    if icon_file:
        cmd.insert(3, f"--icon={icon_file}")
        cmd.insert(4, f"--add-data={icon_file};." if get_platform() == 'windows' else f"--add-data={icon_file}:.")
    
    # Добавляем версионную информацию (только для Windows)
    if get_platform() == 'windows' and os.path.exists("version_info.txt"):
        cmd.insert(3, "--version-file=version_info.txt")
    
    # Добавляем дополнительные файлы, если нужно
    # Для Linux может понадобиться добавить библиотеки
    if get_platform() == 'linux':
        # Добавляем пути для поиска библиотек
        # Это может помочь с зависимостями
        pass
    
    print("Команда сборки:")
    print("  " + " ".join(cmd))
    print()
    
    # Запуск сборки
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("СБОРКА УСПЕШНО ЗАВЕРШЕНА!")
            print("=" * 60)
            
            exe_path = os.path.join("dist", exe_name)
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path)
                print(f"\nФайл: {exe_path}")
                print(f"Размер: {size:,} байт ({size/1024/1024:.2f} MB)")
                
                # Проверяем, что иконка встроена
                if icon_file:
                    print("\nПроверка иконки:")
                    if get_platform() == 'windows':
                        print("   Иконка должна быть видна в проводнике")
                    else:
                        print("   Иконка встроена в исполняемый файл")
                    print("   Если нет - проверьте формат иконки")
                
                # Копируем в текущую папку с датой
                try:
                    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"RealCode_{get_platform()}_{date_str}"
                    if get_platform() == 'windows':
                        backup_name += ".exe"
                    shutil.copy2(exe_path, backup_name)
                    print(f"\nРезервная копия: {backup_name}")
                except Exception as e:
                    print(f"Не удалось создать копию: {e}")
            else:
                print("\nФайл не найден после сборки!")
            
            # Очистка после сборки
            cleanup_after_build()
            
        else:
            print("\n" + "=" * 60)
            print("ОШИБКА ПРИ СБОРКЕ!")
            print("=" * 60)
            print(f"\nКод ошибки: {result.returncode}")
            print("\nВывод ошибки:")
            print(result.stderr)
            if result.stdout:
                print("\nВывод stdout:")
                print(result.stdout)
    
    except Exception as e:
        print(f"\nОшибка выполнения: {e}")
    
    print("\n" + "=" * 60)
    print("ВАЖНЫЕ ФАЙЛЫ СОХРАНЕНЫ:")
    print("   - settings.json (настройки)")
    if icon_file:
        print(f"   - {icon_file} (иконка)")
    print("   - main.py (исходный код)")
    print("=" * 60)
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    # Убираем проверку на Windows, теперь кроссплатформенный
    main()