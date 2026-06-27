# install_deps.py - Автоматическая установка зависимостей
import subprocess
import sys
import os

def install_package(package_name, install_name=None):
    """Установка пакета с обработкой ошибок"""
    if install_name is None:
        install_name = package_name
    
    print(f"📦 Установка {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
        print(f"✅ {package_name} установлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package_name}: {e}")
        return False

def main():
    print("=" * 50)
    print("🛠️  Установка зависимостей RealCode")
    print("=" * 50)
    
    # Обновляем pip
    print("\n📦 Обновление pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Список необходимых пакетов
    packages = [
        ("gitpython", "gitpython"),
        ("pygithub", "pygithub"),
        ("pypresence", "pypresence"),
        ("packaging", "packaging"),
    ]
    
    success = True
    for package_name, install_name in packages:
        if not install_package(package_name, install_name):
            success = False
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Все зависимости успешно установлены!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("⚠️ Некоторые пакеты не установились")
        print("=" * 50)
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
