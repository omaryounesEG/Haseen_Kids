; Inno Setup Script for Haseen Kids (Windows 7 / 8 / 10 / 11 Compatible)
#define MyAppName "حَصِين للأطفال | Haseen Kids"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "SAIP Consulting"
#define MyAppURL "https://github.com/omaryounesEG/Haseen_Kids"
#define MyAppExeName "run.py"

[Setup]
AppId={{9F7B3E42-6D1C-4B9A-98C3-2A6E91F71B88}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Haseen_Kids
DefaultGroupName=Haseen Kids
DisableProgramGroupPage=yes
; MinVersion 6.1 means Windows 7 SP1 or newer!
MinVersion=6.1
OutputDir=..\dist
OutputBaseFilename=Haseen_Kids_Setup_v1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git,venv,*.pyc,__pycache__,Backup_OldVersion,temp_update"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\scripts\run_all.bat"; WorkingDir: "{app}"
Name: "{group}\إلغاء تثبيت حصين"; Filename: "{app}\scripts\uninstall.bat"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\scripts\run_all.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\scripts\setup_policies.bat"; Description: "تطبيق سياسات الأمان وجدار الحماية"; Flags: runhidden
Filename: "{app}\scripts\run_all.bat"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\scripts\uninstall.bat"; Flags: waituntilterminated
