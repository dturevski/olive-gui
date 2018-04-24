; -- ISPPExample1.iss --
;
; This script shows various basic things you can achieve using Inno Setup Preprocessor (ISPP).
; To enable commented #define's, either remove the ';' or use ISCC with the /D switch.

#pragma option -v+
#pragma verboselevel 9

;#define Debug

;#define AppEnterprise

#define AppName "Olive"


#define AppVersion "1.18.4"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={pf}\{#AppName}-{#AppVersion}
DefaultGroupName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\uninstall.exe
LicenseFile={#file AddBackslash(SourcePath) + "gpl.rtf"}
VersionInfoVersion={#AppVersion}
OutputDir=dist\
OutputBaseFilename={#AppName}-{#AppVersion}-amd64

[Files]
Source: "dist\olive.exe"; DestDir: "{app}"
Source: "dist\conf\*"; DestDir: "{app}\conf\"


[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\olive.exe"

#ifdef Debug
  #expr SaveToFile(AddBackslash(SourcePath) + "Preprocessed.iss"), \
        Exec(AddBackslash(CompilerPath) + "Compil32.exe", """" + AddBackslash(SourcePath) + "Preprocessed.iss""")
#endif