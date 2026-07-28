#!/usr/bin/env python3
import tkinter as tk
import sys
import os
import traceback

print("=" * 60)
print("Диагностика Tkinter")
print("=" * 60)

print("1. Импорт tkinter...")
try:
    import tkinter as tk
    print(f"   ✅ Tkinter версия: {tk.TkVersion}")
    print(f"   ✅ Tcl версия: {tk.TclVersion}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

print("2. Создание root окна...")
try:
    root = tk.Tk()
    print("   ✅ Root создан")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

print("3. Настройка окна...")
try:
    root.title("RealCode Debug")
    root.geometry("600x400")
    print("   ✅ Окно настроено")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("4. Добавление виджетов...")
try:
    label = tk.Label(root, text="RealCode Debug Window", font=("Arial", 24))
    label.pack(pady=50)
    
    info = tk.Label(root, text=f"Python: {sys.version}\nTkinter: {tk.TkVersion}", font=("Arial", 12))
    info.pack(pady=20)
    
    def on_close():
        print("   🔴 Окно закрыто")
        root.destroy()
    
    btn = tk.Button(root, text="Закрыть", command=on_close, bg="#4CAF50", fg="white", font=("Arial", 14))
    btn.pack(pady=20)
    
    print("   ✅ Виджеты добавлены")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("5. Проверка окружения...")
print(f"   DISPLAY: {os.environ.get('DISPLAY', 'не установлен')}")
print(f"   XAUTHORITY: {os.environ.get('XAUTHORITY', 'не установлен')}")
print(f"   WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'не установлен')}")

print("6. Запуск mainloop...")
print("   ⏳ Ожидание... (окно должно появиться)")
try:
    root.update()  # Принудительное обновление
    print("   ✅ Root обновлен")
    root.deiconify()  # Показать окно (если скрыто)
    root.lift()  # Поднять на передний план
    root.focus_force()  # Принудительный фокус
    print("   ⏳ Вход в mainloop...")
    root.mainloop()
    print("   ✅ Mainloop завершен")
except Exception as e:
    print(f"   ❌ Ошибка в mainloop: {e}")
    traceback.print_exc()

print("7. Программа завершена")