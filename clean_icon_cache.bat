@echo off
echo Очистка кэша иконок Windows...
echo.

:: Закрываем проводник
taskkill /f /im explorer.exe >nul 2>&1

:: Удаляем кэш иконок
del /f /q %userprofile%\AppData\Local\IconCache.db >nul 2>&1
del /f /q %userprofile%\AppData\Local\Microsoft\Windows\Explorer\iconcache* >nul 2>&1

:: Очищаем кэш Thumbs.db
del /f /s /q /a:h Thumbs.db >nul 2>&1

:: Запускаем проводник заново
start explorer.exe

echo Готово! Кэш иконок очищен.
echo Теперь пересоберите RealCode с новой иконкой.
pause