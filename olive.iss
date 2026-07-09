#define AppName "Olive"
#define AppVersion "1.5.7"
#define AppExeName "olive.exe"

[Setup]
AppId={{C6178033-29E5-4D11-B403-949B02FCD5B4}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
LicenseFile={#file AddBackslash(SourcePath) + "LICENSE.txt"}
OutputDir=dist
OutputBaseFilename={#AppName}-{#AppVersion}-amd64
AllowNoIcons=yes
PrivilegesRequired=lowest
ChangesAssociations=yes

[Files]
Source: "dist\olive.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "pywin64.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "WinChest.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\fonts\*.ttf"; DestDir: "{app}\resources\fonts"; Flags: ignoreversion
Source: "resources\fonts\gc2.gif"; DestDir: "{app}\resources\fonts"; Flags: ignoreversion
Source: "resources\fonts\roboto\*.ttf"; DestDir: "{app}\resources\fonts\roboto"; Flags: ignoreversion
Source: "conf\*"; DestDir: "{localappdata}\{#AppName}\conf\"
Source: "conf\dist\*"; DestDir: "{localappdata}\{#AppName}\conf"
Source: "yacpdb\indexer\indexer.md"; DestDir: "{app}\yacpdb\indexer"; Flags: ignoreversion
Source: "yacpdb\schemas\*"; DestDir: "{app}\yacpdb\schemas"; Flags: ignoreversion
Source: "p2w\parser.out"; DestDir: "{app}\p2w"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\olive.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\olive.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\.olv"; ValueType: string; ValueName: ""; ValueData: "{#AppName}.File"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\{#AppName}.File"; ValueType: string; ValueName: ""; ValueData: "{#AppName} file"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\{#AppName}.File\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"
Root: HKCU; Subkey: "Software\Classes\{#AppName}.File\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""
