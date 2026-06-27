import os
import sys
import winreg

def register_realcode():
    # Путь к вашему RealCode.exe или main.py
    # Если вы запускаете скрипт из папки с RealCode, путь определится автоматически
    if getattr(sys, 'frozen', False):
        # Если это скомпилированный .exe
        app_path = sys.executable
    else:
        # Если это .py скрипт, используем python.exe для запуска main.py
        # Замените путь ниже на актуальный путь к вашему main.py
        main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        app_path = f'"{sys.executable}" "{main_py_path}"'
    
    # Ключ для ассоциации .py файлов
    key_path = r"Python.File\shell\Open with RealCode\command"
    
    try:
        # Открываем ключ реестра HKEY_CLASSES_ROOT
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        # Если ключа нет, создаем его
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
    
    # Устанавливаем команду для открытия файла
    # %1 передает путь к выбранному файлу
    command = f'{app_path} "%1"'
    winreg.SetValue(key, "", winreg.REG_SZ, command)
    winreg.CloseKey(key)
    
    print(f"✅ Пункт 'Open with RealCode' успешно добавлен в контекстное меню для .py файлов!")
    print(f"Команда: {command}")

if __name__ == "__main__":
    register_realcode()
