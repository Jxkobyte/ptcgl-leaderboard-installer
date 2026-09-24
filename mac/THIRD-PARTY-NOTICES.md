# Third-party software

The Mac download bundles these components unmodified. Each is the work of its own authors and is
distributed under its own licence. Their source code is available at the links below.

| component | files | licence | source |
|---|---|---|---|
| BepInEx 5 | `BepInEx/core/BepInEx*.dll` | LGPL-2.1 | https://github.com/BepInEx/BepInEx |
| HarmonyX | `0Harmony.dll`, `BepInEx.Harmony.dll`, `HarmonyXInterop.dll` | MIT | https://github.com/BepInEx/HarmonyX |
| Harmony 2 | `0Harmony20.dll` | MIT | https://github.com/pardeike/Harmony |
| MonoMod | `MonoMod.*.dll` | MIT | https://github.com/MonoMod/MonoMod |
| Mono.Cecil | `Mono.Cecil*.dll` | MIT | https://github.com/jbevain/cecil |

The LGPL components are used as separate, unmodified libraries; you may replace them with any
compatible build of your own. These are the same files as BepInEx's own macOS download
(BepInEx_macos_x64_5.4.23.4.zip).

The idea of starting BepInEx from inside a notarized macOS game, rather than through
DYLD_INSERT_LIBRARIES, comes from Tobey Blaber's BepInEx hardpatcher
(https://tobey.me/mods/bepinex/hardpatcher/). This project does it differently and ships none of
its code.

PTCGL Leaderboard & Match History itself is MIT-licensed: see `LICENSE.txt`.

*Unofficial fan-made mod. Not affiliated with, endorsed by, or connected to The Pokémon Company,
Nintendo, Creatures or GAME FREAK. Pokémon and Pokémon TCG Live are trademarks of their respective
owners.*
