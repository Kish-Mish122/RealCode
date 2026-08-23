#!/bin/bash
# install_realcode.sh - Установка RealCode из AppImage

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Установка RealCode на Linux${NC}"
echo -e "${BLUE}========================================${NC}"

# Определяем версию
VERSION="3.8.0"
APPIMAGE_FILE="RealCode-Linux-v${VERSION}.AppImage"

# Проверяем, что AppImage существует
if [ ! -f "$APPIMAGE_FILE" ]; then
    echo -e "${RED}❌ Файл $APPIMAGE_FILE не найден!${NC}"
    echo -e "${YELLOW}Сначала соберите AppImage:${NC}"
    echo "  ./build_appimage.sh"
    exit 1
fi

echo -e "${GREEN}✅ Найден AppImage: $APPIMAGE_FILE${NC}"

# 1. Делаем AppImage исполняемым
echo -e "${BLUE}📦 Делаем исполняемым...${NC}"
chmod +x "$APPIMAGE_FILE"
echo -e "${GREEN}✅ Готово${NC}"

# 2. Копируем в /usr/local/bin
echo -e "${BLUE}📦 Копируем в /usr/local/bin...${NC}"
sudo cp "$APPIMAGE_FILE" /usr/local/bin/realcode
sudo chmod +x /usr/local/bin/realcode
echo -e "${GREEN}✅ Теперь можно запускать: realcode${NC}"

# 3. Создаем .desktop файл для меню
echo -e "${BLUE}📦 Создаем .desktop файл...${NC}"

# Путь к иконке
ICON_PATH=$(pwd)/icon.svg
if [ ! -f "$ICON_PATH" ]; then
    # Создаем заглушку, если нет иконки
    echo -e "${YELLOW}⚠️ icon.svg не найден, создаю заглушку...${NC}"
    convert -size 256x256 xc:blue -fill white -draw "text 40,150 'RC'" icon.svg 2>/dev/null || true
    ICON_PATH=$(pwd)/icon.svg
fi

cat > ~/.local/share/applications/realcode.desktop << EOF
[Desktop Entry]
Type=Application
Name=RealCode
Comment=RealCode for Scripting
Exec=/usr/local/bin/realcode
Icon=${ICON_PATH}
Terminal=false
Categories=Development;IDE;
StartupNotify=true
StartupWMClass=RealCode
MimeType=text/plain;
EOF

# Обновляем кэш
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
echo -e "${GREEN}✅ .desktop файл создан${NC}"

# 4. Копируем иконку в систему (опционально)
if [ -f "icon.svg" ]; then
    echo -e "${BLUE}📦 Копируем иконку в систему...${NC}"
    mkdir -p ~/.local/share/icons/hicolor/256x256/apps/
    cp icon.svg ~/.local/share/icons/hicolor/256x256/apps/realcode.png
    gtk-update-icon-cache ~/.local/share/icons/hicolor/ -f 2>/dev/null || true
    echo -e "${GREEN}✅ Иконка скопирована${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ RealCode успешно установлен!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}📌 Теперь вы можете:${NC}"
echo "  • Запустить из меню приложений (RealCode)"
echo "  • Запустить командой: ${YELLOW}realcode${NC}"
echo "  • Запустить из папки: ${YELLOW}./$APPIMAGE_FILE${NC}"
echo ""
echo -e "${YELLOW}ℹ️  Для удаления выполните:${NC}"
echo "  sudo rm /usr/local/bin/realcode"
echo "  rm ~/.local/share/applications/realcode.desktop"