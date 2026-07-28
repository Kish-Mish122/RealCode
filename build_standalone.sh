#!/bin/bash
echo "========================================"
echo "Сборка RealCode (без build.py)"
echo "========================================"

# Добавляем pipx в PATH
export PATH="$HOME/.local/bin:$PATH"

# Проверяем PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller не найден!"
    exit 1
fi

echo "✅ PyInstaller: $(pyinstaller --version)"

# Устанавливаем зависимости в venv (если есть)
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install pillow pyflakes pycodestyle packaging pypresence requests 2>/dev/null || true
fi

# Сборка напрямую через PyInstaller
echo "🔨 Сборка..."
pyinstaller \
    --onefile \
    --windowed \
    --name=RealCode \
    --icon=icon.ico \
    --add-data="icon.ico:." \
    --add-data="icon.svg:." \
    --add-data="realcode.desctop:." \
    main.py

# Проверка результата
if [ -f "dist/RealCode" ]; then
    echo "✅ Сборка успешна!"
    echo "📁 Файл: dist/RealCode"
    ls -lh dist/RealCode
else
    echo "❌ Ошибка сборки!"
fi