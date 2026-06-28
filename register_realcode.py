import os
import sys
import winreg

def register():
    # Путь к main.py или exe
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        app_path = f'"{sys.executable}" "{main_py}"'

    extensions = ['.py', '.cpp', '.c', '.h', '.hpp', '.cs', '.sln']
    for ext in extensions:
        key_path = f"{ext}\\shell\\Open with RealCode\\command"
        try:
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, f'{app_path} "%1"')
            winreg.CloseKey(key)
            print(f"✅ Зарегистрировано {ext}")
        except Exception as e:
            print(f"❌ Ошибка для {ext}: {e}")

if __name__ == "__main__":
    register()
    input("Нажмите Enter для выхода...")
