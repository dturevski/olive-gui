; -- ISPPExample1.iss --
;
; This script shows various basic things you can achieve using Inno Setup Preprocessor (ISPP).
; To enable commented #define's, either remove the ';' or use ISCC with the /D switch.

#pragma option -v+
#pragma verboselevel 9

;#define Debug

;#define AppEnterprise

#define AppName "Olive"
#define AppVersion "1.2.1"
#define AppExeName "olive.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={pf64}\{#AppName}-{#AppVersion}
DefaultGroupName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\uninstall.exe
LicenseFile={#file AddBackslash(SourcePath) + "LICENSE.txt"}
OutputDir=dist\
OutputBaseFilename={#AppName}-{#AppVersion}-amd64
AllowNoIcons=yes
ChangesAssociations=yes

[Files]
Source: "dist\olive.exe"; DestDir: "{app}"
Source: "pywin64.exe"; DestDir: "{app}"
Source: "WinChest.exe"; DestDir: "{app}"
Source: "resources\fonts\*.ttf"; DestDir: "{app}\resources\fonts"
Source: "resources\fonts\gc2.gif"; DestDir: "{app}\resources\fonts"
Source: "resources\fonts\roboto\*.ttf"; DestDir: "{app}\resources\fonts\roboto"
Source: "conf\*"; DestDir: "{localappdata}\{#AppName}\conf\"
Source: "conf\dist\*"; DestDir: "{localappdata}\{#AppName}\conf"
Source: "yacpdb\indexer\indexer.md"; DestDir: "{app}\yacpdb\indexer"
Source: "yacpdb\schemas\*"; DestDir: "{app}\yacpdb\schemas"
Source: "p2w\parser.out"; DestDir: "{app}\p2w"
    

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\olive.exe"
Name: "{commondesktop}\{#AppName}-{#AppVersion}"; Filename: "{app}\olive.exe"

[Registry]
Root: HKCR; Subkey: ".olv";                             ValueData: "{#AppName}";          Flags: uninsdeletevalue; ValueType: string;  ValueName: ""
Root: HKCR; Subkey: "{#AppName}";                     ValueData: "Program {#AppName}";  Flags: uninsdeletekey;   ValueType: string;  ValueName: ""
Root: HKCR; Subkey: "{#AppName}\DefaultIcon";             ValueData: "{app}\{#AppExeName},0";               ValueType: string;  ValueName: ""
Root: HKCR; Subkey: "{#AppName}\shell\open\command";  ValueData: """{app}\{#AppExeName}"" ""%1""";  ValueType: string;  ValueName: ""