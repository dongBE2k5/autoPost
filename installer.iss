[Setup]
AppName=Komeify AI Auto Post
AppVersion=1.0
DefaultDirName={pf}\Komeify
DefaultGroupName=Komeify
OutputDir=Output
OutputBaseFilename=Komeify_Setup_v1.0
SetupIconFile=assets\logo.ico
Compression=lzma
SolidCompression=yes

[Files]
; Lấy toàn bộ thư mục mà Nuitka vừa build ra
Source: "main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Tạo shortcut ngoài màn hình
Name: "{commondesktop}\Komeify"; Filename: "{app}\Komeify.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Desktop"; GroupDescription: "Additional icons:"