; RealCode - Инсталлятор
; (c) 2026 K1sh-M1sh

[Setup]
AppName=RealCode
AppVersion=3.5
AppPublisher=K1sh-M1sh
DefaultDirName={pf}\RealCode
DefaultGroupName=RealCode
UninstallDisplayIcon={app}\RealCode.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=RealCode_Install
; Требуем права администратора для записи в реестр
PrivilegesRequired=admin

[Files]
Source: "E:\RealCode\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Ярлык в меню Пуск
Name: "{group}\RealCode"; Filename: "{app}\RealCode.exe"; WorkingDir: "{app}"
; Ярлык на рабочем столе
Name: "{commondesktop}\RealCode"; Filename: "{app}\RealCode.exe"; WorkingDir: "{app}"

[Registry]
; --- Python (используем существующий класс, как у вас) ---
Root: HKCR; Subkey: "Python.File\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Python.File\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .cpp ---
Root: HKCR; Subkey: "SystemFileAssociations\.cpp\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.cpp\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .c ---
Root: HKCR; Subkey: "SystemFileAssociations\.c\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.c\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .h ---
Root: HKCR; Subkey: "SystemFileAssociations\.h\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.h\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .hpp ---
Root: HKCR; Subkey: "SystemFileAssociations\.hpp\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.hpp\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .cs ---
Root: HKCR; Subkey: "SystemFileAssociations\.cs\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.cs\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; --- Для .sln ---
Root: HKCR; Subkey: "SystemFileAssociations\.sln\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.sln\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey


; Если вы используете не скомпилированный .exe, а запуск через python.exe, замените команду:
; ValueData: """{sys}\python.exe"" ""{app}\main.py"" ""%1"""

; (Опционально) Ассоциация .rcp файлов с RealCode (если есть такой формат)
; Root: HKCR; Subkey: ".rcp"; ValueType: string; ValueName: ""; ValueData: "RealCode.Project"; Flags: uninsdeletekey
; Root: HKCR; Subkey: "RealCode.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey

; Добавляем иконку для .py файлов (если у вас есть иконка в ресурсах)
; Root: HKCR; Subkey: "Python.File\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\realcode.ico"; Flags: uninsdeletekey

[Run]
; Запуск RealCode после установки (опционально)
Filename: "{app}\RealCode.exe"; Description: "Запустить RealCode"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; Удаляем папку при деинсталляции (все файлы будут удалены автоматически)
Type: filesandordirs; Name: "{app}"