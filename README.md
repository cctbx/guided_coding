# GuidedCoding

GuidedCoding is a Claude Code skill, `/gc`, for making a bug fix or a bounded change you can trust, with little of
your attention:
- a test that proves the fix;
- one review pass;
- an outside review by another AI assistant for hard or consequential changes, and on request: Claude puts one
  review packet on your clipboard, you paste it into the other assistant and paste its answer back;
- extra checks only when a change needs them (a live call, a run on another platform);
- one page for you at the end of every job: what was wrong and what is true now, the change and its code, the tests
  on the old and new code, the outside review if there was one, and the commits a push would publish.

`/gc batch` runs a supervised list of such jobs one at a time.

The skill is the [`guided_coding/`](guided_coding) folder. It is a set of instructions for Claude, plus one Python
script (`guided_coding/tools/review_pages.py`) that Claude runs to build the review packet and
your page; nothing is compiled or installed. Start with [`guided_coding/SKILL.md`](guided_coding/SKILL.md).

## Requirements

- **Claude Code.** If you do not have it yet, follow
  [Anthropic's Claude Code quickstart](https://code.claude.com/docs/en/quickstart) first.
- **Git,** unless you install from the ZIP download.
- **macOS, Linux or Windows.** GuidedCoding has been tested on macOS, Linux and Windows. On Windows, use the
  Windows block below.
- **For the review packet and your page:** a Python 3 with the `markdown` package (Python-Markdown). PHENIX's
  `libtbx.python` has it. For another Python, add it for your user only with `python3 -m pip install --user markdown`
  (on Windows, `python -m pip install --user markdown`; GuidedCoding installs nothing itself). The page also needs
  a change whose tests the review tool can run (Python code tested in the test's own process). Without either,
  Claude makes the evidence by hand and gives a written report instead of the page; nothing else changes. Opening a
  page needs only a web browser.

The review step uses Claude Code's code-review skill when it is available. To let Claude Code install GuidedCoding
with you instead of running the commands yourself, see the website's
[Quick Start](https://www.thomasterwilliger.org/guided_coding/quick-start.html).

## Install and register it (once)

Put the repository somewhere, then make a link from your Claude Code skills folder to its `guided_coding/` folder.
Open Terminal (on a Mac) or a terminal window (on Linux), paste a whole block, and press Return. The blocks are
complete: copy each one whole, with no editing. They are for bash or zsh, the usual shells. If your shell is csh
or tcsh, type `bash` first, and `exit` afterwards. They check before they change anything, and they stop on anything
unexpected. If you set `CLAUDE_CONFIG_DIR`, they use that folder instead of `~/.claude`. On Windows, use the
Windows block below instead of these.

Most people should install GuidedCoding in their home folder, or in a folder where they keep software. This works
with any project, including PHENIX. If you develop PHENIX, you can instead install it in your PHENIX installation,
next to your PHENIX source code.

**To choose the folder:** the home-folder and ZIP blocks below put GuidedCoding in `~/guided_coding`. To put it
somewhere else, first run this line in the same terminal window, with your folder in place of `$HOME/software`
(keep the quotes and the `/guided_coding` at the end), then paste the block:

```
export GC_DIR="$HOME/software/guided_coding"
```

The block prints the folder it uses. `/gc update` and `/gc uninstall` find the folder by themselves.

**Most people: in your home folder, with Git.** This puts GuidedCoding in `~/guided_coding` (or the folder in
`GC_DIR`) and registers it. If that folder is already a clone of cctbx/guided_coding on `master`, it updates it with
`git pull` instead:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.5
DIR="${GC_DIR:-$HOME/guided_coding}"
case "$DIR" in /*) ;; *) echo "GC_DIR must be a full path, such as $HOME/software/guided_coding; nothing changed."; exit 1;; esac
echo "GuidedCoding folder: $DIR"
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To update or move an existing installation, see Update and If you used the earlier GuidedCoding kit."; exit 1; fi; done
if [ -e "$DIR" ]; then
  case "$(git -C "$DIR" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) ;; *) echo "$DIR exists but is not a clone of https://github.com/cctbx/guided_coding; nothing changed."; exit 1;; esac
  [ "$(git -C "$DIR" rev-parse --abbrev-ref HEAD)" = master ] || { echo "$DIR is not on the master branch; nothing changed."; exit 1; }
  git -C "$DIR" pull --ff-only || { echo "Could not update $DIR; nothing registered."; exit 1; }
else
  mkdir -p "$(dirname "$DIR")" && git clone https://github.com/cctbx/guided_coding.git "$DIR" || exit 1
fi
grep -qx "# GuidedCoding (version $VERSION)" "$DIR/guided_coding/SKILL.md" 2>/dev/null || { echo "$DIR/guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version); nothing registered."; exit 1; }
mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc" && grep -m1 '^# GuidedCoding' "$DIR/guided_coding/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

**PHENIX developers (optional): in your PHENIX installation.** This puts GuidedCoding in the installation's
`modules/guided_coding` and registers it; if that folder is already a clone of cctbx/guided_coding, it uses it as it
is. The installation is the one `$PHENIX` names, or else the current folder, which must contain `modules`. Check
which one first with `echo $PHENIX`; the block prints the folder it uses. The registration is for your whole
account, so `/gc` uses this copy even when you work in another PHENIX installation. PHENIX's own update does not
update it yet; run `git pull` in `modules/guided_coding`. For a shared installation, use the home-folder block unless
you are allowed to change it.

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.5
ROOT="${PHENIX:-$PWD}"
DIR="$ROOT/modules/guided_coding"
echo "PHENIX installation: $ROOT"
[ -d "$ROOT/modules" ] || { echo "No modules folder in $ROOT. Set up PHENIX in this shell, or cd to the installation folder that contains modules; nothing changed."; exit 1; }
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then
  case "$(readlink "$SKILLS/$L")" in */cctbx_project/libtbx/guided_coding|*/cctbx_project/libtbx/guided_coding/) echo "$SKILLS/$L is the earlier GuidedCoding kit; nothing changed. To move from it, use the move block below.";; *) echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To move a home-folder installation here, see the line after the move block. To update, see Update.";; esac
  exit 1
fi; done
if [ -e "$DIR" ]; then
  case "$(git -C "$DIR" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) echo "Using the existing $DIR";; *) echo "$DIR exists but is not a clone of https://github.com/cctbx/guided_coding; nothing changed."; exit 1;; esac
else
  git clone https://github.com/cctbx/guided_coding.git "$DIR" || exit 1
fi
grep -qx "# GuidedCoding (version $VERSION)" "$DIR/guided_coding/SKILL.md" 2>/dev/null || { echo "$DIR/guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version; run git pull there); nothing registered."; exit 1; }
mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" || { echo "Could not register GuidedCoding at $SKILLS/gc; nothing changed."; exit 1; }
echo "Registered $SKILLS/gc -> $DIR/guided_coding (GuidedCoding $VERSION)."
echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

**Moving from the earlier kit** (a `gc` or `guided_coding` link into `cctbx_project/libtbx/guided_coding`)? Use this
block instead. It does the same, and replaces only that registration with the new one (it removes the old link,
which is why Claude Code asks you to approve an `rm`); if anything fails, it puts the old link back:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.5
ROOT="${PHENIX:-$PWD}"
DIR="$ROOT/modules/guided_coding"
echo "PHENIX installation: $ROOT"
[ -d "$ROOT/modules" ] || { echo "No modules folder in $ROOT. Set up PHENIX in this shell, or cd to the installation folder that contains modules; nothing changed."; exit 1; }
OLD=""
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then
  case "$(readlink "$SKILLS/$L")" in */cctbx_project/libtbx/guided_coding|*/cctbx_project/libtbx/guided_coding/) [ -z "$OLD" ] && OLD="$SKILLS/$L" && continue;; esac
  echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To move a home-folder installation here, see the line after this block. To update, see Update."; exit 1
fi; done
[ -n "$OLD" ] || { echo "No registration of the earlier kit was found; nothing changed. To install, use the install block above."; exit 1; }
if [ -e "$DIR" ]; then
  case "$(git -C "$DIR" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) echo "Using the existing $DIR";; *) echo "$DIR exists but is not a clone of https://github.com/cctbx/guided_coding; nothing changed."; exit 1;; esac
else
  git clone https://github.com/cctbx/guided_coding.git "$DIR" || { echo "Could not clone into $DIR; nothing changed. If git said Permission denied (for example in a PHENIX binary installation), see 'In a PHENIX binary installation' under 'If you used the earlier GuidedCoding kit'."; exit 1; }
fi
grep -qx "# GuidedCoding (version $VERSION)" "$DIR/guided_coding/SKILL.md" 2>/dev/null || { echo "$DIR/guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version; run git pull there); nothing registered."; exit 1; }
if [ -n "$OLD" ]; then OLDT="$(readlink "$OLD")"; rm "$OLD" || { echo "Could not remove the earlier kit's registration $OLD; nothing changed."; exit 1; }; echo "Removed the earlier kit's registration $OLD (it pointed to $OLDT)."; fi
CREATED=""; mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && CREATED=1
if [ -z "$CREATED" ] || ! grep -qx "# GuidedCoding (version $VERSION)" "$SKILLS/gc/SKILL.md" 2>/dev/null; then
  if [ -n "$CREATED" ] && [ "$(readlink "$SKILLS/gc")" = "$DIR/guided_coding" ]; then rm "$SKILLS/gc"; fi
  if [ -n "$OLD" ]; then ln -s "$OLDT" "$OLD" && echo "Restored $OLD."; fi
  echo "Could not register GuidedCoding; nothing changed."; exit 1
fi
ls -l "$SKILLS/gc" && grep -m1 '^# GuidedCoding' "$SKILLS/gc/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

Already installed in your home folder or another folder? Remove that registration first. This removes only a
`gc` link that points to a GuidedCoding copy (not the earlier kit, and not one in a PHENIX `modules` folder), and
prints the command to put it back; the copy stays until you delete it:

```
L="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/gc"; T="$(readlink "$L" | sed 's:/*$::')"; case "$T" in ""|*/cctbx_project/libtbx/guided_coding|*/modules/guided_coding/guided_coding) echo "$L points to ${T:-nothing}, not a GuidedCoding copy this line moves; nothing removed.";; *) if grep -q '^# GuidedCoding (version' "$T/SKILL.md" 2>/dev/null; then rm "$L" && echo "Removed $L. To put it back: ln -s '$(printf %s "$T" | sed "s/'/'\\\\''/g")' '$(printf %s "$L" | sed "s/'/'\\\\''/g")'"; else echo "$L points to $T, which is not GuidedCoding; nothing removed."; fi;; esac
```

**Without Git: from the ZIP download.** Download
[`guided_coding.zip`](https://www.thomasterwilliger.org/guided_coding/guided_coding.zip) into your Downloads folder.
To check it against the published
[`guided_coding.zip.sha256`](https://www.thomasterwilliger.org/guided_coding/guided_coding.zip.sha256), run this; it
should print `guided_coding.zip: OK`:

```
(cd ~/Downloads && curl -fsS https://www.thomasterwilliger.org/guided_coding/guided_coding.zip.sha256 | shasum -a 256 -c)
```

Then run this.
It unpacks the ZIP into `~/guided_coding` (or the folder in `GC_DIR`) and registers it:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.5
DIR="${GC_DIR:-$HOME/guided_coding}"
case "$DIR" in /*) ;; *) echo "GC_DIR must be a full path, such as $HOME/software/guided_coding; nothing changed."; exit 1;; esac
echo "GuidedCoding folder: $DIR"
ZIP="$HOME/Downloads/guided_coding.zip"
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To update or move an existing installation, see Update and If you used the earlier GuidedCoding kit."; exit 1; fi; done
[ -e "$DIR" ] && { echo "$DIR already exists; nothing changed. To update a ZIP installation, see Update."; exit 1; }
[ -f "$ZIP" ] || { echo "Not found: $ZIP. Download it first. If it was saved under another name, such as 'guided_coding (1).zip', rename it to guided_coding.zip. If Safari unpacked it, turn off Settings > General > Open safe files after downloading, and download it again."; exit 1; }
TMP="$(mktemp -d)" && unzip -q "$ZIP" -d "$TMP" || exit 1
set -- "$TMP"/guided_coding-*
[ $# -eq 1 ] && [ -f "$1/guided_coding/SKILL.md" ] || { echo "Unexpected ZIP contents; nothing changed."; rm -rf "$TMP"; exit 1; }
grep -qx "# GuidedCoding (version $VERSION)" "$1/guided_coding/SKILL.md" 2>/dev/null || { echo "the ZIP's guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version); nothing registered."; rm -rf "$TMP"; exit 1; }
mkdir -p "$(dirname "$DIR")" && mv "$1" "$DIR" && rmdir "$TMP" && mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc" && grep -m1 '^# GuidedCoding' "$DIR/guided_coding/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

**Windows: in your home folder, without Git.** Open **Windows PowerShell** (press the Windows key, type
`PowerShell`, and open it; not Command Prompt). Paste the whole block below and press Enter; if the window is still
waiting after the last line, press Enter once more. The block downloads
[`guided_coding.zip`](https://www.thomasterwilliger.org/guided_coding/guided_coding.zip), checks it against the
published [`guided_coding.zip.sha256`](https://www.thomasterwilliger.org/guided_coding/guided_coding.zip.sha256),
unpacks it into `guided_coding` in your home folder (or the folder in `GC_DIR`; the block prints the folder it
uses), and registers it with a directory junction, a kind of link that needs no special Windows setting and no
administrator rights. Git is not needed. If you set `CLAUDE_CONFIG_DIR`, the block uses that folder instead of
`.claude` in your home folder. Like the blocks above, it checks before it changes anything and stops on anything
unexpected; if the registration fails, it removes the files it had just unpacked, so you can run it again. To put
GuidedCoding somewhere else, first run this line in the same PowerShell window, with your folder in place of
`C:\software` (a folder on this computer, not a network share; keep the quotes and the `\guided_coding` at the
end), then paste the block:

```
$env:GC_DIR = "C:\software\guided_coding"
```

```
& {
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Version = "1.5"
if ($env:CLAUDE_CONFIG_DIR) { $Skills = Join-Path $env:CLAUDE_CONFIG_DIR "skills" } else { $Skills = Join-Path (Join-Path $HOME ".claude") "skills" }
if ($env:GC_DIR) { $Dir = $env:GC_DIR.TrimEnd([char[]]"\/") } else { $Dir = Join-Path $HOME "guided_coding" }
if ($Dir.StartsWith("\\")) { "GC_DIR must be a folder on this computer, not on a network share (a junction cannot point to a share); nothing changed."; return }
if ($Dir -notmatch '^[A-Za-z]:[\\/][^\\/]') { "GC_DIR must be a full path, such as $HOME\software\guided_coding; nothing changed."; return }
"GuidedCoding folder: $Dir"
foreach ($L in "gc", "guided_coding") {
  $P = Join-Path $Skills $L
  $I = Get-Item -LiteralPath $P -Force -ErrorAction SilentlyContinue
  if ($I) { "$P already exists; nothing changed:"; "  $($I.FullName)  type: $($I.LinkType)  target: $($I.Target)"; "To update or move an existing installation, see Update."; return }
}
if (Get-Item -LiteralPath $Dir -Force -ErrorAction SilentlyContinue) { "$Dir already exists; nothing changed. To update a ZIP installation, see Update."; return }
$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("guided_coding_" + [System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $Tmp | Out-Null
try {
$Url = "https://www.thomasterwilliger.org/guided_coding/guided_coding.zip"
$Zip = Join-Path $Tmp "guided_coding.zip"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing
$Sum = (Invoke-WebRequest -Uri "$Url.sha256" -UseBasicParsing).Content
if ($Sum -is [byte[]]) { $Sum = [System.Text.Encoding]::ASCII.GetString($Sum) }
$Want = ($Sum -split "\s+")[0].ToLower()
$Have = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLower()
if ($Want -ne $Have) { "guided_coding.zip does not match its published checksum; nothing changed."; Remove-Item -LiteralPath $Tmp -Recurse -Force; return }
"guided_coding.zip: OK"
$Unpacked = Join-Path $Tmp "unpacked"
Expand-Archive -LiteralPath $Zip -DestinationPath $Unpacked
} catch { "Could not download or unpack guided_coding.zip ($($_.Exception.Message)); nothing changed."; Remove-Item -LiteralPath $Tmp -Recurse -Force; return }
$Top = @(Get-ChildItem -LiteralPath $Unpacked -Directory -Filter "guided_coding-*")
if ($Top.Count -ne 1 -or -not (Test-Path -LiteralPath (Join-Path (Join-Path $Top[0].FullName "guided_coding") "SKILL.md"))) { "Unexpected ZIP contents; nothing changed."; Remove-Item -LiteralPath $Tmp -Recurse -Force; return }
$Skill = Join-Path (Join-Path $Top[0].FullName "guided_coding") "SKILL.md"
if (-not (Select-String -LiteralPath $Skill -Pattern ("^# GuidedCoding \(version " + [regex]::Escape($Version) + "\)$") -Quiet)) { "the ZIP's guided_coding/SKILL.md is not GuidedCoding $Version (it may be the earlier kit or an older version); nothing registered."; Remove-Item -LiteralPath $Tmp -Recurse -Force; return }
$Link = Join-Path $Skills "gc"
$Target = Join-Path $Dir "guided_coding"
$Parent = Split-Path -Parent $Dir
$Stage = Join-Path $Parent (".guided_coding_" + [System.IO.Path]::GetRandomFileName())
$StageMade = $false; $DirMade = $false; $LinkMade = $false
try {
  if (-not (Test-Path -LiteralPath $Parent)) { New-Item -ItemType Directory -Path $Parent | Out-Null }
  $StageMade = $true
  Copy-Item -LiteralPath $Top[0].FullName -Destination $Stage -Recurse -Force
  [System.IO.Directory]::Move($Stage, $Dir)
  $DirMade = $true
  if (-not (Test-Path -LiteralPath $Skills)) { New-Item -ItemType Directory -Path $Skills | Out-Null }
  New-Item -ItemType Junction -Path $Link -Value $Target | Out-Null
  $LinkMade = $true
  $I = Get-Item -LiteralPath $Link -Force
  if ($I.LinkType -ne "Junction" -or -not (Test-Path -LiteralPath (Join-Path $Link "SKILL.md"))) { throw "$Link was created but is not a junction to $Target" }
} catch {
  $Why = $_.Exception.Message
  if ($LinkMade) { [System.IO.Directory]::Delete($Link) }
  if ($DirMade) { Remove-Item -LiteralPath $Dir -Recurse -Force }
  if ($StageMade -and (Test-Path -LiteralPath $Stage)) { Remove-Item -LiteralPath $Stage -Recurse -Force }
  Remove-Item -LiteralPath $Tmp -Recurse -Force -ErrorAction SilentlyContinue
  "Could not register GuidedCoding at $Link ($Why); nothing registered, and the files it unpacked were removed. Check that you can create folders in $Skills and in $Dir, then run this block again."
  return
}
Remove-Item -LiteralPath $Tmp -Recurse -Force
"Registered $($I.FullName)  type: $($I.LinkType)  target: $($I.Target)"
(Select-String -LiteralPath (Join-Path $Target "SKILL.md") -Pattern "^# GuidedCoding" | Select-Object -First 1).Line
"Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
}
```

Do not use the macOS and Linux blocks in Git Bash on Windows: there, `ln -s` makes a copy of the folder instead of a
link, so `/gc` would work but `/gc update` would update the downloaded files and not the copy Claude Code uses.

Each block ends by showing the link and the version line of the skill it registered,
`# GuidedCoding (version 1.5)`, and what to do next. The blocks register only that version
(`VERSION=1.5` in each block).

**Then** start a new Claude Code conversation in the folder of a software project, and type `/gc` followed by a small
task (or `/gc help` for an introduction and the list of commands: `setup`, `batch`, `history`, `undo`, `update`,
`uninstall`). Type `/gc` at the very start of the message, with nothing before it, not even a space; otherwise
Claude Code takes it as ordinary text: GuidedCoding does not run, and Claude may then make the change without it.
If you plan to use GuidedCoding regularly on that project, run `/gc setup` there once (recommended): it saves the
project's build and test commands, commit rules and other local defaults in `.claude/GC_NOTES.md`. Without it, `/gc`
finds these from the project each time. Installing is once per computer.

### Update

Type `/gc update` in Claude Code: it says whether a newer version exists, and updates after asking once. By hand: for
an installation made with Git, run `git pull` in its folder (`~/guided_coding`, the folder you chose, or
`modules/guided_coding` in PHENIX; `/gc help` shows which). A ZIP installation has no Git history. To update it:
1. remove the link `gc` in your Claude Code skills folder (`$CLAUDE_CONFIG_DIR/skills` if you set
   `CLAUDE_CONFIG_DIR`, otherwise `~/.claude/skills`); it is only a link, and removing it deletes nothing else;
2. rename its folder (`~/guided_coding`, or the folder you chose) to keep it as a backup, outside the skills folder, so that only one registration remains
   (two skills named `gc` conflict);
3. download the new ZIP and run the ZIP block again (after the `GC_DIR` line, if you chose a folder).

On Windows: paste the Windows uninstall block below into PowerShell (it removes only the link), rename the folder to
keep it as a backup, and paste the Windows install block again (after the `$env:GC_DIR` line, if you chose a folder).

### Uninstall

Type `/gc uninstall` in Claude Code, or paste this block. It removes GuidedCoding from Claude Code: it removes only
the registration link (`gc`, or `guided_coding` for an older registration), so `/gc` stops working, and deletes
nothing. If both exist, it changes nothing and says so. It then tells you where GuidedCoding's files are and
whether they hold anything of yours (changes, other files, commits that are not on GitHub, other branches or
stashes). A copy under a `modules` folder (`modules/guided_coding`) may belong to a larger installation such as
PHENIX, and stays. Project notes that `/gc setup` saved (`.claude/GC_NOTES.md` in your projects) are kept.

```
sh <<'END'
S="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"; L=""; N=0
for C in "$S/gc" "$S/guided_coding"; do if [ -L "$C" ]; then L="$C"; N=$((N+1)); fi; done
[ "$N" -gt 0 ] || { echo "GuidedCoding is not registered at $S/gc or $S/guided_coding; nothing changed."; exit 1; }
[ "$N" -eq 1 ] || { echo "GuidedCoding is registered twice, as $S/gc and $S/guided_coding; keep one (choose which yourself); nothing changed."; exit 1; }
T="$(readlink "$L")"; case "$T" in /*) ;; *) T="$(dirname "$L")/$T";; esac
COPY="$(dirname "$T")"
[ "$(basename "$T")" = guided_coding ] || { echo "$L points to $T, not GuidedCoding; nothing changed."; exit 1; }
if [ -e "$T" ]; then grep -q '^# GuidedCoding' "$T/SKILL.md" 2>/dev/null || { echo "$L points to $T, which is not GuidedCoding; nothing changed."; exit 1; }; fi
unlink "$L" || { echo "Could not remove $L; nothing changed."; exit 1; }
echo "Removed GuidedCoding from Claude Code; /gc stops working in new conversations."
KEEP=""
if [ ! -e "$T" ]; then KEEP="-"
elif [ "$(basename "$(dirname "$COPY")")" = modules ]; then KEEP="phenix"
elif [ -e "$COPY/.git" ]; then
  [ -d "$COPY/.git" ] || KEEP="it is a linked Git working folder"
  [ -n "$KEEP" ] || case "$(git -C "$COPY" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) ;; *) KEEP="it is not a clone of cctbx/guided_coding";; esac
  NC="Git could not check it"
  [ -n "$KEEP" ] || { ST="$(git -C "$COPY" status --porcelain --ignored)" || KEEP="$NC"; }
  [ -n "$KEEP" ] || [ -z "$ST" ] || KEEP="it has changes or files of its own"
  [ -n "$KEEP" ] || { BR="$(git -C "$COPY" for-each-ref --format=x refs/heads)" || KEEP="$NC"; }
  [ -n "$KEEP" ] || [ "$BR" = x ] || KEEP="it has more than one branch"
  [ -n "$KEEP" ] || { UP="$(git -C "$COPY" log --oneline --branches --not --remotes)" || KEEP="$NC"; }
  [ -n "$KEEP" ] || [ -z "$UP" ] || KEEP="it has commits that are not on GitHub"
  [ -n "$KEEP" ] || { SL="$(git -C "$COPY" stash list)" || KEEP="$NC"; }
  [ -n "$KEEP" ] || [ -z "$SL" ] || KEEP="it has stashed changes"
else
  LIST="$(cd "$COPY" && find . ! -type d)" || KEEP="its files could not be listed"
  if [ -z "$KEEP" ] && [ ! -f "$COPY/RELEASE.sha256" ]; then KEEP="it has no RELEASE.sha256 to show it is unchanged"; fi
  if [ -z "$KEEP" ]; then
    WANT="$( (sed 's/^[0-9a-f]*  /.\//' "$COPY/RELEASE.sha256"; echo ./RELEASE.sha256) | sort)"
    [ "$(printf '%s\n' "$LIST" | sort)" = "$WANT" ] || KEEP="its files do not match the release list"
  fi
  if [ -z "$KEEP" ]; then
    if command -v shasum >/dev/null 2>&1; then SUM="shasum -a 256"; else SUM="sha256sum"; fi
    (cd "$COPY" && $SUM -c RELEASE.sha256 >/dev/null 2>&1) || KEEP="some of its files were changed"
  fi
fi
if [ "$KEEP" = phenix ]; then echo "Its files stay in $COPY, which is part of a larger installation such as PHENIX."
elif [ -z "$KEEP" ]; then echo "Its files are still in $COPY. They hold nothing of yours; delete that folder if you no longer need it."
elif [ "$KEEP" != "-" ]; then echo "Its files are still in $COPY. Before deleting that folder, note that $KEEP."; fi
echo "Project notes (.claude/GC_NOTES.md in your projects) are kept."
END
```

To delete GuidedCoding's files too, delete the folder it names: `rm -rf <that folder>`. Check it first if the
block says it holds something of yours.

On Windows, paste this block into Windows PowerShell instead. It removes only the registration link (`gc`, or
`guided_coding` for an older registration) and deletes nothing; it does not check whether the folder holds anything
of yours, so look before you delete the folder. To delete GuidedCoding's files too, delete the folder it names in
File Explorer.

```
& {
$ErrorActionPreference = "Stop"
if ($env:CLAUDE_CONFIG_DIR) { $Skills = Join-Path $env:CLAUDE_CONFIG_DIR "skills" } else { $Skills = Join-Path (Join-Path $HOME ".claude") "skills" }
$Found = @()
foreach ($L in "gc", "guided_coding") { $P = Join-Path $Skills $L; if (Get-Item -LiteralPath $P -Force -ErrorAction SilentlyContinue) { $Found += $P } }
if ($Found.Count -eq 0) { "GuidedCoding is not registered at $Skills\gc or $Skills\guided_coding; nothing changed."; return }
if ($Found.Count -gt 1) { "GuidedCoding is registered twice, as $Skills\gc and $Skills\guided_coding; keep one (choose which yourself); nothing changed."; return }
$I = Get-Item -LiteralPath $Found[0] -Force
if (-not $I.LinkType) { "$($I.FullName) is a folder, not a link, so it may hold GuidedCoding's only copy; nothing changed. If it is only a copy of another GuidedCoding folder, delete it yourself."; return }
$T = "$($I.Target)"
if ((Split-Path -Leaf $T) -ne "guided_coding") { "$($I.FullName) points to $T, not GuidedCoding; nothing changed."; return }
if ((Test-Path -LiteralPath $T) -and -not (Select-String -LiteralPath (Join-Path $T "SKILL.md") -Pattern "^# GuidedCoding" -Quiet)) { "$($I.FullName) points to $T, which is not GuidedCoding; nothing changed."; return }
try { [System.IO.Directory]::Delete($I.FullName) } catch { try { [System.IO.File]::Delete($I.FullName) } catch { } }
if (Get-Item -LiteralPath $I.FullName -Force -ErrorAction SilentlyContinue) { "Could not remove $($I.FullName); nothing changed."; return }
"Removed GuidedCoding from Claude Code; /gc stops working in new conversations."
if (Test-Path -LiteralPath $T) { "Its files are still in $(Split-Path -Parent $T). Delete that folder yourself if you no longer need it." } else { "The link pointed to $T, which no longer exists; there are no files to delete." }
}
```

## What the evidence says

In a replay of 37 past bug-fix jobs in PHENIX and cctbx, adding one review pass to plain Claude Code cut missed
program errors per job from 0.81 to 0.47. GuidedCoding always includes that review pass, which is the main reason to
expect it to do better than plain Claude Code; it has not been shown to do better than Claude Code with one review. On 18 harder jobs (selected, not a random sample), an outside review by
another AI assistant removed further major errors when added to GuidedCoding, narrowly. Version 1.4 kept those two
steps (the outside review for hard or consequential changes) and a test that proves the fix; it does not include a
second review pass, keeps the independent reviewer optional, and narrows a strict scope rule that probably cost errors.
Version 1.5 keeps the same steps and changes how the outside review is prepared and how the result is shown to you
(the packet and the page). Neither version as a whole has itself been measured; 1.5 was tried on three real jobs and
is being evaluated in real use. [EVIDENCE.md](EVIDENCE.md) goes through each part of `/gc` and what the evidence says about it.

## If you used the earlier GuidedCoding kit (revision 21 or older)

Revision 22 replaces the earlier kit with this much shorter procedure. The earlier kit had approval screens,
evidence packets checked by its own tools, and an unattended auto mode. They are retired, and kept on the branch
`full-kit-rev21`.

What you gain, and what you lose:
- **Gained:** a shorter, prompt-only procedure that asks for your attention only when a decision is needed.
- **Lost:** the screens, packets, checker tools and the unattended auto mode. `/gc batch` is supervised, not
  unattended. The earlier `help`, `status` and `history` commands have new versions (`/gc help`, `/gc status`,
  `/gc history`), and the job history is kept by default.

**To move:**
- **Finish first.** Finish or stop any job or auto queue of the earlier kit before updating.
- **Your link.** If your link is `~/.claude/skills/guided_coding` and points to `modules/guided_coding/guided_coding`,
  updating the repository (`git pull`) is enough. The link keeps working and now gives the new `/gc`.
- **A link into cctbx_project.** If your link points to `cctbx_project/libtbx/guided_coding` (revision 20 or older),
  run the move block ("Moving from the earlier kit") under "Install and register it (once)" (in bash, with `$PHENIX`
  set or from the folder that contains `modules`). It clones the new GuidedCoding into `modules/guided_coding` and replaces that old
  registration with the new one. Or type `/gc` with the earlier kit: it offers to do this for you.
- **In a PHENIX binary installation** (one you downloaded rather than built with bootstrap), or wherever you cannot
  write to `modules`: the move block cannot clone there, and stops without changing anything. Instead, type `bash`
  (the line needs bash or zsh, not csh or tcsh), remove the earlier kit's registration with this line, which removes
  only a `gc` or `guided_coding` link into `cctbx_project/libtbx/guided_coding` and prints the command to put it
  back, then use the home-folder block. If the home-folder block then fails, run the printed command to put the
  earlier kit back:

  ```
  S="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"; F=""; for N in gc guided_coding; do T="$(readlink "$S/$N")"; case "$T" in */cctbx_project/libtbx/guided_coding|*/cctbx_project/libtbx/guided_coding/) rm "$S/$N" && F=1 && echo "Removed $S/$N. To put it back: ln -s '$(printf %s "$T" | sed "s/'/'\\\\''/g")' '$(printf %s "$S/$N" | sed "s/'/'\\\\''/g")'";; esac; done; [ -n "$F" ] || echo "No registration of the earlier kit was found in $S; nothing removed."
  ```
- **Two links.** Keep only one link to GuidedCoding. Two skills both named `gc` conflict.
- **Your instructions.** If your `CLAUDE.local.md` adopts the earlier kit's "Developer–Guide Contract", that line can
  go. Your project method file is not used by the new `/gc`; `/gc setup` writes short notes instead.
- **Then** start a new Claude Code conversation.

**To go back to the earlier kit:**

```
cd modules/guided_coding
git fetch origin full-kit-rev21
git checkout full-kit-rev21
```

Your link then gives the earlier kit again. Keep your single link, and do not run the earlier kit's registration step
(`register-skill`), which would add a second one. Restore your `CLAUDE.local.md` contract line if you removed it. To
return to the new GuidedCoding, `git checkout master`.

## Tests

```
python3 tst_guided_coding.py
```

It checks that the skill's files are present and consistent: the frontmatter, the cross-references between files
(including section references into other files), and the version lines. It includes a check of its own that a
broken cross-file reference is caught, and the tests of the review tool (`guided_coding/tools/tst_review_pages.py`):
that its checker refuses incomplete or unconvincing evidence, and that the page keeps untrusted text safe. The page's
safety depends on how Python-Markdown is configured and on one of its internal steps, so run the tests again (with
`libtbx.python` in PHENIX) after upgrading Python-Markdown or changing its extensions. It does not check whether Claude follows the procedure; that is checked by
running it in Claude Code, and the recorded runs are listed in [EVIDENCE.md](EVIDENCE.md).
