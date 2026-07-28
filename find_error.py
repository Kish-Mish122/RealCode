#!/usr/bin/env python3
import sys
import os
import traceback
import tkinter as tk

# Перенаправляем вывод, чтобы видеть все ошибки
sys.stderr = sys.stdout

print("=" * 60)
print("Поиск ошибки в RealCode")
print("=" * 60)

# Проверяем config
print("\n1. Проверка config.py...")
try:
    from config import *
    print(f"   ✅ VERSION_REALCODE = {VERSION_REALCODE}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

# Импортируем main по частям
print("\n2. Импорт main...")
try:
    import main as realcode
    print("   ✅ main импортирован")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    traceback.print_exc()
    sys.exit(1)

# Создаем приложение с отловом ошибок
print("\n3. Создание приложения...")
try:
    root = tk.Tk()
    root.title("RealCode - Отладка")
    root.geometry("800x600")
    
    # Добавляем метку для отладки
    label = tk.Label(root, text="Загрузка RealCode...", font=("Arial", 16))
    label.pack(pady=50)
    root.update()
    
    print("   ✅ Root создан")
    
    # Создаем приложение с обработкой ошибок
    try:
        app = realcode.CodeEditorApp(root)
        print("   ✅ App создан")
        
        # Обновляем метку
        label.config(text="RealCode загружен!", fg="green")
        root.update()
        
    except Exception as e:
        print(f"   ❌ Ошибка в CodeEditorApp: {e}")
        traceback.print_exc()
        label.config(text=f"Ошибка: {e}", fg="red")
        root.update()
        root.after(3000, root.destroy)
        root.mainloop()
        sys.exit(1)
    
    print("\n4. Запуск mainloop...")
    print("   ⏳ Приложение работает...")
    
    # Добавляем таймер, который покажет, что приложение живо
    def check_alive():
        print("   ✅ Приложение живо (5 секунд прошло)")
        label.config(text="RealCode работает! (5 сек)", fg="blue")
        root.update()
    
    root.after(5000, check_alive)
    root.after(10000, lambda: print("   ✅ Приложение живо (10 секунд)"))
    
    root.mainloop()
    print("   ✅ Mainloop завершен")
    
except Exception as e:
    print(f"   ❌ Критическая ошибка: {e}")
    traceback.print_exc()