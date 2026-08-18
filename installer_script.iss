[Setup]
AppName=FocusTodo Pro
AppVersion=1.0
DefaultDirName={localappdata}\Programs\FocusTodo
DefaultGroupName=FocusTodo
UninstallDisplayIcon={app}\FocusTodo.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\
OutputBaseFilename=FocusTodo_Installer
SetupIconFile=base_icon.ico

[Files]
Source: "FocusTodo.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FocusTodo"; Filename: "{app}\FocusTodo.exe"; IconFilename: "{app}\base_icon.ico"
Name: "{autodesktop}\FocusTodo"; Filename: "{app}\FocusTodo.exe"; IconFilename: "{app}\base_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\FocusTodo.exe"; Description: "Launch FocusTodo"; Flags: nowait postinstall skipifsilent
