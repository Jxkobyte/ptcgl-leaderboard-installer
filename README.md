# PTCGL Leaderboard & Match History — installer

Builds `ptcgl-leaderboard-setup.exe`: a per-user Windows installer (Inno Setup 6) that installs
the BepInEx injector plus the [Leaderboard & Match History](../../source/repos/PtcglLeaderboard) overlay into a
local Pokémon TCG Live install.

No admin rights are needed — PTCGL installs under the user profile, so the installer runs as the
current user.

## The problem this solves

A PTCGL update can replace the game folder and strip the injector — `winhttp.dll`,
`doorstop_config.ini`, `.doorstop_version`, `BepInEx\core`. When that happens **the plugin is not
loaded, so it cannot repair itself**: by the time anything is wrong, none of our code is running
inside the game.

It does not happen on every patch. `winhttp.dll` survived the 2026-08-27 update that replaced both
`Pokemon TCG Live.exe` and `UnityPlayer.dll`. So repair is written as a cheap check that hashes a
handful of small files and exits, not as a reinstall on a timer.

## How it is handled

Repair comes from a process outside the game, and everything it needs lives outside the game
folder so the same update cannot destroy it:

```
<game folder>                        ← a PTCGL update can wipe all of this
  winhttp.dll, doorstop_config.ini, .doorstop_version
  BepInEx\core\…, BepInEx\plugins\PtcglLeaderboard.dll

%LOCALAPPDATA%\PtcglLeaderboard\         ← survives, because the updater never touches it
  PtcglLeaderboardLauncher.exe           the repair tool
  payload\                           pristine copy of everything above
  manifest.tsv                       policy → sha256 → path
  gamepath.txt, repair.log
```

`manifest.tsv` carries a restore policy per file, derived from its path:

| policy | applies to | behaviour |
|---|---|---|
| `always` | `winhttp.dll`, `BepInEx\core\*`, the plugin | restore if missing **or** altered |
| `ifmissing` | `BepInEx\config\*` | restore only if gone |

The split matters: BepInEx rewrites its own config, and the tracker stores window position and
frame caps there. Treating those as `always` would silently reset the user's settings on every
repair.

**There is no background service and no scheduled task.** Repair happens two ways:

1. **Launching via the installed shortcut** — "Pokémon TCG Live (Leaderboard & Match History)". The launcher
   verifies and repairs, starts the game, then keeps watching for ~3 minutes. That watch is the
   point: PTCGL patches itself *during* launch, so a check that only runs beforehand runs before
   the damage, and the user plays a whole session with no overlay. If the injector vanishes
   mid-session the launcher restores it and offers a one-click restart.
2. **Rerunning this installer** — the manual fallback. Every `[Files]` entry is `ignoreversion`,
   so it is safe to run over an existing install and upgrades in place (same `AppId`).

The user's own PTCGL shortcuts are deliberately left untouched, and the new shortcut uses the
launcher's own icon so the two are visually distinguishable.

## Building

Requires the .NET SDK and [Inno Setup 6](https://jrsoftware.org/isinfo.php). **Close PTCGL first** —
it holds `BepInEx\core` open, and the plugin build deploys into the game folder.

```powershell
.\build.ps1
```

That builds the launcher and the plugin from the PtcglLeaderboard repo, stages both into `src\`, then
compiles the installer to `build\output\`. Staging from a fresh build is not optional: the
installer packages whatever is sitting in `src\`, so without it an edit compiles fine, the
installer compiles fine, and you ship the previous binary with no error anywhere.

```powershell
.\build.ps1 -NoRebuild                      # package what is already staged
.\build.ps1 -TrackerRepo D:\code\PtcglLeaderboard
```

## Layout

```
installer.iss                       Inno Setup script
build.ps1                           build + stage + compile
src/files/                          payload — mirrors the game folder exactly
  winhttp.dll, doorstop_config.ini, .doorstop_version
  BepInEx/{config,core,plugins}/
src/launcher/PtcglLeaderboardLauncher.exe   staged by build.ps1
src/branding/make_icon.py           generates ptcglleaderboard.ico (original artwork)
```

`src/files` is the payload *and* the repair source — it is copied to both the game folder and
`%LOCALAPPDATA%\PtcglLeaderboard\payload`, so the two can never drift.

## Gotchas worth keeping

- **`installer.iss` must be UTF-8 *with a BOM*.** The default install path contains `Pokémon`, and
  Inno 6 reads a BOM-less `.iss` as ANSI and corrupts it.
- **A line starting with `#` is a preprocessor directive to ISPP.** A Pascal `#13#10` at the start
  of a continuation line fails to compile; prefix it with `'' +`.
- **It is `{%USERPROFILE}`, not `{userprofile}`.** The latter is not an Inno constant.
- **The icon is original artwork.** The game's own icon is not used and must not be — it is TPCi's
  mark, and an installer wearing it would imply this is an official product.

## Testing

Do not run the installer on a development machine as-is. The dev loop deploys `PtcglLeaderboard.dll`
to `BepInEx\scripts\` for ScriptEngine hot-reload, while the installer puts it in
`BepInEx\plugins\`. Both would load, and you get two overlays.

Test against a throwaway folder instead — any directory containing a file named
`Pokemon TCG Live.exe` passes the installer's folder check:

```powershell
.\build\output\ptcgl-leaderboard-setup.exe /VERYSILENT /NOICONS /TASKS= /DIR="C:\temp\fakegame"
# simulate an update, then:
& "$env:LOCALAPPDATA\PtcglLeaderboard\PtcglLeaderboardLauncher.exe" --repair
& "C:\temp\fakegame\unins000.exe" /VERYSILENT
```

## Known limitation

The installer and launcher are **unsigned**. SmartScreen will show "Windows protected your PC" on
download, and an unsigned executable that writes `winhttp.dll` into a program folder is close to a
textbook DLL-hijack signature, so some scanners may object. Version and publisher metadata is
filled in on both binaries, which helps a little; a code-signing certificate is the real fix.
