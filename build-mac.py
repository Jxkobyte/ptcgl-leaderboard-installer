"""
Builds the macOS download: build/output/ptcgl-leaderboard-mac.zip.

    python build-mac.py [--repo ../../source/repos/PtcglLeaderboard] [--no-rebuild]

Rebuilds the plugin and the Mac loader from the PtcglLeaderboard repo (same reasoning as
build.ps1: packaging whatever happens to be in bin\ is how a stale binary ships), then zips:

    PTCGL Leaderboard (Mac)/
        Install PTCGL Leaderboard.command
        Uninstall PTCGL Leaderboard.command
        READ ME.txt
        files/BepInEx/{core,config,plugins}/...
        files/mac/  launch.sh, unity-hook.js, launcher.applescript, the loader, the icon, version.txt
        files/LICENSE.txt, files/THIRD-PARTY-NOTICES.md

Two things matter because this is built on Windows for a Mac:
  - Line endings. bash on a Mac rejects CRLF, so every script is written with LF whatever git's
    autocrlf did to the checkout.
  - Permissions. The zip records Unix modes (0755 for the .command and .sh files), or
    double-clicking the installer on a Mac says it has no permission to run.

The BepInEx core DLLs come from src/files/BepInEx/core, the same files the Windows installer
ships - byte-identical to BepInEx's own macOS download (checked: BepInEx_macos_x64_5.4.23.4.zip).
"""
import argparse
import hashlib
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOP = "PTCGL Leaderboard (Mac)"
TEXT_EXT = {".sh", ".command", ".js", ".applescript", ".txt", ".md"}
EXEC_EXT = {".sh", ".command"}


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def build(repo):
    for proj in ("PtcglLeaderboard.csproj", os.path.join("Mac", "Loader", "PtcglLeaderboard.MacLoader.csproj")):
        print("building " + proj + " ...")
        r = subprocess.run(["dotnet", "build", os.path.join(repo, proj), "-c", "Release", "-v", "quiet", "-nologo"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout + r.stderr)
            fail("build failed: " + proj)


def plugin_version(repo):
    s = io.open(os.path.join(repo, "Plugin.cs"), encoding="utf-8-sig").read()
    m = re.search(r'VERSION\s*=\s*"(\d+\.\d+\.\d+)"', s)
    if not m:
        fail("no VERSION in Plugin.cs")
    return m.group(1)


def loader_version(repo):
    s = io.open(os.path.join(repo, "Mac", "Loader", "PtcglLeaderboard.MacLoader.csproj"), encoding="utf-8-sig").read()
    m = re.search(r"<Version>([^<]+)</Version>", s)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join("..", "..", "source", "repos", "PtcglLeaderboard"))
    ap.add_argument("--no-rebuild", action="store_true")
    args = ap.parse_args()
    repo = os.path.normpath(os.path.join(ROOT, args.repo))
    if not os.path.isfile(os.path.join(repo, "PtcglLeaderboard.csproj")):
        fail("PtcglLeaderboard repo not found at " + repo)

    version = plugin_version(repo)
    if loader_version(repo) != version:
        fail("version mismatch: Plugin.cs says %s, the Mac loader says %s" % (version, loader_version(repo)))
    if not args.no_rebuild:
        build(repo)

    scripts = os.path.join(repo, "Mac", "scripts")
    # (source, path inside TOP)
    items = [
        (os.path.join(scripts, "Install PTCGL Leaderboard.command"), "Install PTCGL Leaderboard.command"),
        (os.path.join(scripts, "Uninstall PTCGL Leaderboard.command"), "Uninstall PTCGL Leaderboard.command"),
        (os.path.join(ROOT, "mac", "READ ME.txt"), "READ ME.txt"),
        (os.path.join(ROOT, "src", "files", "BepInEx", "config", "BepInEx.cfg"), "files/BepInEx/config/BepInEx.cfg"),
        (os.path.join(repo, "bin", "Release", "PtcglLeaderboard.dll"), "files/BepInEx/plugins/PtcglLeaderboard.dll"),
        (os.path.join(scripts, "launch.sh"), "files/mac/launch.sh"),
        (os.path.join(scripts, "unity-hook.js"), "files/mac/unity-hook.js"),
        (os.path.join(scripts, "launcher.applescript"), "files/mac/launcher.applescript"),
        (os.path.join(repo, "Mac", "Loader", "bin", "Release", "PtcglLeaderboard.MacLoader.dll"), "files/mac/PtcglLeaderboard.MacLoader.dll"),
        (os.path.join(ROOT, "src", "branding", "ptcglleaderboard.icns"), "files/mac/PTCGL Leaderboard.icns"),
        (os.path.join(ROOT, "LICENSE"), "files/LICENSE.txt"),
        (os.path.join(ROOT, "mac", "THIRD-PARTY-NOTICES.md"), "files/THIRD-PARTY-NOTICES.md"),
    ]
    core = os.path.join(ROOT, "src", "files", "BepInEx", "core")
    for f in sorted(os.listdir(core)):
        if f.lower().endswith(".dll"):
            items.append((os.path.join(core, f), "files/BepInEx/core/" + f))

    for src, _ in items:
        if not os.path.isfile(src):
            fail("missing: " + src)

    out_dir = os.path.join(ROOT, "build", "output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "ptcgl-leaderboard-mac.zip")

    def info(name, mode):
        zi = zipfile.ZipInfo(TOP + "/" + name, date_time=STAMP)
        zi.create_system = 3                          # Unix, so the modes below are honoured
        zi.external_attr = (mode & 0xFFFF) << 16
        return zi

    import time
    global STAMP
    STAMP = time.localtime()[:6]
    dirs = set()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name in items:
            parts = name.split("/")[:-1]
            for i in range(len(parts)):
                d = "/".join(parts[: i + 1])
                if d not in dirs:
                    dirs.add(d)
                    zi = info(d + "/", stat.S_IFDIR | 0o755)
                    zi.external_attr |= 0x10              # MS-DOS directory flag
                    z.writestr(zi, b"")
            ext = os.path.splitext(name)[1].lower()
            data = open(src, "rb").read()
            if ext in TEXT_EXT:
                if data.startswith(b"\xef\xbb\xbf") and ext in EXEC_EXT:
                    fail("BOM in " + name + " - bash would not see its #! line")
                data = data.replace(b"\r\n", b"\n")
            mode = stat.S_IFREG | (0o755 if ext in EXEC_EXT else 0o644)
            z.writestr(info(name, mode), data, zipfile.ZIP_DEFLATED)
        z.writestr(info("files/mac/version.txt", stat.S_IFREG | 0o644), (version + "\n").encode("ascii"))

    # Verify what was written, not what was meant to be.
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        for zi in z.infolist():
            if zi.is_dir():
                continue
            mode = (zi.external_attr >> 16) & 0o777
            ext = os.path.splitext(zi.filename)[1].lower()
            want = 0o755 if ext in EXEC_EXT else 0o644
            if mode != want:
                fail("%s has mode %o, expected %o" % (zi.filename, mode, want))
            if ext in TEXT_EXT and b"\r" in z.read(zi):
                fail("CR in " + zi.filename)
            if ext in EXEC_EXT and not z.read(zi).startswith(b"#!/bin/bash\n"):
                fail(zi.filename + " does not start with #!/bin/bash")
        if z.read(TOP + "/files/mac/version.txt").decode().strip() != version:
            fail("version.txt mismatch")
        for src, name in items:
            data = open(src, "rb").read()
            if os.path.splitext(name)[1].lower() not in TEXT_EXT and z.read(TOP + "/" + name) != data:
                fail("content mismatch: " + name)

    print("\n%s  (%s bytes, version %s)" % (out, format(os.path.getsize(out), ","), version))
    print("sha256 " + hashlib.sha256(open(out, "rb").read()).hexdigest())
    for n in names:
        print("  " + n)


if __name__ == "__main__":
    main()
