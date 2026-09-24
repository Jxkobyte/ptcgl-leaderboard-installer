; PTCGL Leaderboard & Match History - Inno Setup 6 script
;
; Installs the BepInEx injector + the Leaderboard & Match History plugin into a per-user PTCGL install,
; and caches a pristine copy of everything OUTSIDE the game folder.
;
; Why the cache and the launcher live in {localappdata} and not in the game folder:
; a PTCGL update can replace the game folder and strip the injector (winhttp.dll,
; doorstop_config.ini, BepInEx\core). Anything we need in order to REPAIR that has to survive
; it, so it cannot be stored in the thing that gets wiped.
;
; There is deliberately no background service and no scheduled task. Repair happens when the
; user launches through our shortcut, and rerunning this installer is the manual fallback -
; which is why every [Files] entry is `ignoreversion` and this script is safe to rerun over
; an existing install.
;
; NOTE: this file must be saved as UTF-8 WITH a BOM. The default install path contains
; non-ASCII characters (Pokémon), and Inno 6 reads a BOM-less .iss as ANSI, which corrupts them.

#define AppName    "PTCGL Leaderboard & Match History"
#define AppVer     "1.0.3"
#define AppPub     "Inevitable2002"
#define GameExe    "Pokemon TCG Live.exe"
#define LauncherEx "PtcglLeaderboardLauncher.exe"
#define CacheDir   "{localappdata}\PtcglLeaderboard"

[Setup]
; Same AppId as the previous installer on purpose: rerunning upgrades in place instead of
; leaving a second entry in Add/Remove Programs.
AppId={{8F0B9F8E-3D1A-4B4D-9F2B-9E5E2B1C7A41}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#AppPub}
DefaultDirName={%USERPROFILE}\The Pokémon Company International\Pokémon Trading Card Game Live
DefaultGroupName={#AppName}
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#GameExe}
OutputDir=build\output
OutputBaseFilename=ptcgl-leaderboard-setup
Compression=lzma2/max
SolidCompression=yes
; x64compatible rather than x64: it also covers ARM64 Windows running the x64 client under
; emulation, and plain "x64" is deprecated in Inno 6.3+.
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user install, so no admin prompt and no UAC shield.
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
; The folder page stays ON. If it points at the wrong place nothing works at all, so the user
; must see and confirm it - and users with a non-default install need to be able to change it.
DisableDirPage=no
DirExistsWarning=no
AppendDefaultDirName=no
; Restart Manager: detect PTCGL holding BepInEx\core open and offer to close it, rather than
; failing halfway through with a locked-file error.
CloseApplications=yes
RestartApplications=no
WizardStyle=modern

; Original artwork - see src\branding\make_icon.py. The game's own icon is deliberately not
; used: it is TPCi's mark, and an installer wearing it would imply this is official.
SetupIconFile=src\branding\ptcglleaderboard.ico

; An unsigned setup.exe with an empty Details tab is indistinguishable from malware at a glance.
; This does not stop SmartScreen, but it is the difference between "unknown publisher" plus a
; blank properties sheet and one that at least names the product.
VersionInfoVersion={#AppVer}.0
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVer}.0
VersionInfoCompany={#AppPub}
VersionInfoDescription={#AppName} Setup
VersionInfoCopyright=Copyright (C) 2026 {#AppPub}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
; 1. the payload, into the game folder - this is the actual install
Source: "src\files\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; 2. the SAME payload, cached where a game update cannot reach it - this is the repair source
Source: "src\files\*"; DestDir: "{#CacheDir}\payload"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; 3. the launcher, also outside the game folder for the same reason
Source: "src\launcher\{#LauncherEx}"; DestDir: "{#CacheDir}"; Flags: ignoreversion

[Icons]
; Launching through this shortcut is what keeps the tracker alive across game updates: the
; launcher verifies and repairs the injector, starts the game, then watches for the updater
; wiping it mid-session. The user's own PTCGL shortcuts are deliberately left untouched.
;
; No IconFilename, so these use the launcher's OWN embedded icon rather than the game's. That is
; the point: this shortcut has to be visually distinguishable from the PTCGL shortcut already on
; the user's desktop, or they cannot tell which one they are clicking.
Name: "{group}\Pokémon TCG Live (Leaderboard & Match History)"; Filename: "{#CacheDir}\{#LauncherEx}"; \
    WorkingDir: "{app}"; \
    Comment: "Start Pokémon TCG Live with the Leaderboard & Match History overlay"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Pokémon TCG Live (Leaderboard & Match History)"; Filename: "{#CacheDir}\{#LauncherEx}"; \
    WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Record where the game is and hash the payload, so a later repair knows what "good" looks like.
; Also renames any leftover GameStateReader.dll - the old combined plugin, which would otherwise
; run alongside this one and draw a second overlay.
Filename: "{#CacheDir}\{#LauncherEx}"; Parameters: "--seed --game ""{app}"""; \
    StatusMsg: "Recording this install so it can repair itself after a game update..."; \
    Flags: runhidden waituntilterminated

Filename: "{#CacheDir}\{#LauncherEx}"; WorkingDir: "{app}"; \
    Description: "Start Pokémon TCG Live now"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\BepInEx"
Type: files;          Name: "{app}\winhttp.dll"
Type: files;          Name: "{app}\doorstop_config.ini"
Type: files;          Name: "{app}\.doorstop_version"
; BepInEx's own changelog.txt shipped in older payloads and landed in the game root. It is no
; longer installed, but remove it so an upgrade from an older build cleans up after itself.
Type: files;          Name: "{app}\changelog.txt"
; Only OUR files in the cache folder - never the whole folder. The plugin keeps the player's match
; history (matches.jsonl) and avatar cache there too, precisely so a game update cannot destroy
; them, and deleting the folder on uninstall would destroy them instead. Reinstalling picks the
; history straight back up.
Type: filesandordirs; Name: "{#CacheDir}\payload"
Type: files;          Name: "{#CacheDir}\manifest.tsv"
Type: files;          Name: "{#CacheDir}\gamepath.txt"
Type: files;          Name: "{#CacheDir}\repair.log"
Type: files;          Name: "{#CacheDir}\update-check.txt"
Type: files;          Name: "{#CacheDir}\{#LauncherEx}"

[Code]

function IsGameFolder(Dir: String): Boolean;
begin
  Result := FileExists(AddBackslash(Dir) + '{#GameExe}');
end;

{ Refuse to install into a folder that is not a PTCGL install. Getting this wrong is silent:
  every file copies successfully and nothing ever loads, which reads to the user as "the mod
  is broken" rather than "the path is wrong". }
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    if not IsGameFolder(WizardDirValue) then
    begin
      MsgBox('That folder does not contain {#GameExe}.' + #13#10#13#10 +
             'Choose the folder where Pokémon TCG Live is installed. The usual location is:' +
             { the leading '' is load-bearing: ISPP treats a line STARTING with # as a
               preprocessor directive, so a bare #13#10 at the start of a line fails to compile }
             '' + #13#10#13#10 +
             ExpandConstant('{%USERPROFILE}') +
             '\The Pokémon Company International\Pokémon Trading Card Game Live',
             mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsGameFolder(ExpandConstant('{%USERPROFILE}') +
                      '\The Pokémon Company International\Pokémon Trading Card Game Live') then
  begin
    { Not fatal - they may have installed the game elsewhere and can point at it on the next
      page. Just say so up front instead of letting them discover it at the folder step. }
    MsgBox('Pokémon TCG Live was not found in the usual place.' + #13#10#13#10 +
           'You will be asked to choose its folder. Please also close the game before ' +
           'continuing, so its files are not locked.',
           mbInformation, MB_OK);
  end;
end;
