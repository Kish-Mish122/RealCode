; RealCode - Инсталлятор
; (c) 2026 K1sh-M1sh

[Setup]
AppName=RealCode
AppVersion=3.6
AppPublisher=K1sh-M1sh
DefaultDirName={pf}\RealCode
DefaultGroupName=RealCode
UninstallDisplayIcon={app}\RealCode.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=RealCode_Install
PrivilegesRequired=admin

[Tasks]
Name: "associatepy"; Description: "Добавить поддержку .py файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associatecpp"; Description: "Добавить поддержку .cpp файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associatec"; Description: "Добавить поддержку .c файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associateh"; Description: "Добавить поддержку .h файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associatehpp"; Description: "Добавить поддержку .hpp файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associatecs"; Description: "Добавить поддержку .cs файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked
Name: "associatesln"; Description: "Добавить поддержку .sln файлы с RealCode"; GroupDescription: "Ассоциации файлов:"; Flags: unchecked

[Files]
Source: "E:\RealCode\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\RealCode"; Filename: "{app}\RealCode.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\RealCode"; Filename: "{app}\RealCode.exe"; WorkingDir: "{app}"

[Registry]
; --- Регистрация приложения в списке "Открыть с помощью" ---
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".py"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".cpp"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".c"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".h"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".hpp"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".cs"; ValueData: ""; Flags: uninsdeletekey
Root: HKCR; Subkey: "Applications\RealCode.exe\SupportedTypes"; ValueType: string; ValueName: ".sln"; ValueData: ""; Flags: uninsdeletekey

; --- Python ---
Root: HKCR; Subkey: "Python.File\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatepy
Root: HKCR; Subkey: "Python.File\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatepy
; (Опционально) иконка для .py
; Root: HKCR; Subkey: "Python.File\DefaultIcon"; ValueType: string; ValueData: "{app}\realcode.ico"; Flags: uninsdeletekey; Tasks: associatepy

; --- .cpp ---
Root: HKCR; Subkey: "SystemFileAssociations\.cpp\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatecpp
Root: HKCR; Subkey: "SystemFileAssociations\.cpp\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatecpp

; --- .c ---
Root: HKCR; Subkey: "SystemFileAssociations\.c\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatec
Root: HKCR; Subkey: "SystemFileAssociations\.c\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatec

; --- .h ---
Root: HKCR; Subkey: "SystemFileAssociations\.h\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associateh
Root: HKCR; Subkey: "SystemFileAssociations\.h\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associateh

; --- .hpp ---
Root: HKCR; Subkey: "SystemFileAssociations\.hpp\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatehpp
Root: HKCR; Subkey: "SystemFileAssociations\.hpp\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatehpp

; --- .cs ---
Root: HKCR; Subkey: "SystemFileAssociations\.cs\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatecs
Root: HKCR; Subkey: "SystemFileAssociations\.cs\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatecs

; --- .sln ---
Root: HKCR; Subkey: "SystemFileAssociations\.sln\shell\Open with RealCode"; ValueType: string; ValueData: "Open With RealCode"; Flags: uninsdeletekey; Tasks: associatesln
Root: HKCR; Subkey: "SystemFileAssociations\.sln\shell\Open with RealCode\command"; ValueType: string; ValueData: """{app}\RealCode.exe"" ""%1"""; Flags: uninsdeletekey; Tasks: associatesln

[Run]
Filename: "{app}\RealCode.exe"; Description: "Запустить RealCode"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"