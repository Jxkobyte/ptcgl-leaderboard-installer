# WARP.md

Guidance for WARP (warp.dev) working in this repository.

**Read `README.md` first** — it holds the design rationale, the build instructions and the
platform gotchas. This file only covers what an assistant needs to avoid breaking things.

## What this repo is

Builds `ptcgl-leaderboard-setup.exe`, a per-user Inno Setup 6 installer that puts the BepInEx
injector and the Leaderboard & Match History plugin into a local Pokémon TCG Live install, and installs a
launcher that repairs the injector after a PTCGL update strips it.

The plugin and launcher **source** live in a separate repo (`..\..\source\repos\PtcglLeaderboard`).
This repo only packages them. `build.ps1` builds both from there and stages them into `src\`.

## Commands

```powershell
.\build.ps1                    # build launcher + plugin, stage, compile installer
.\build.ps1 -NoRebuild         # compile only, using whatever is staged in src\
```

Close PTCGL before building — it holds `BepInEx\core` open and `build.ps1` refuses to run while
it is up.

There is no linter and no test suite. Verification is manual, against a throwaway folder — see
the Testing section of `README.md`. Never test by installing over a development machine's own
game folder: the dev loop deploys the plugin to `BepInEx\scripts\` while the installer uses
`BepInEx\plugins\`, and both loading gives two overlays.

## Things that will bite you

- **`installer.iss` must stay UTF-8 with a BOM.** The default path contains `Pokémon`; Inno reads
  a BOM-less `.iss` as ANSI and corrupts it. Any tool that rewrites the file must preserve the BOM.
- **A line starting with `#` is an ISPP preprocessor directive.** A Pascal `#13#10` beginning a
  continuation line will not compile — prefix with `'' +`.
- **`{%USERPROFILE}`, not `{userprofile}`.** The latter is not an Inno constant.
- **`src\files` is both the payload and the repair source.** It is copied to the game folder *and*
  to `%LOCALAPPDATA%\PtcglLeaderboard\payload`. Adding a file there adds it to both, and its restore
  policy is derived from its path (`BepInEx\config\*` is `ifmissing`, everything else `always`).
- **Do not add a scheduled task or background service.** This was decided against deliberately:
  rerunning the installer is the manual fallback, and an unsigned exe registering a scheduled task
  is a large antivirus-heuristic liability.
- **Do not use the game's icon.** `src\branding\make_icon.py` generates original artwork. The
  game's icon is TPCi's mark.
- **`AppId` must not change.** It is what makes rerunning the installer upgrade in place instead
  of leaving a second Add/Remove Programs entry.
