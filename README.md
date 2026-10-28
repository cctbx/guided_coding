# GuidedCoding

GuidedCoding is a Claude Code skill, `/gc`, for making a bug fix or a bounded change you can trust, with little of
your attention:
- a test that proves the fix;
- one review pass;
- an outside review by another AI assistant for hard or consequential changes, and on request;
- extra checks only when a change needs them (a live call, a run on another platform);
- a short report.

`/gc batch` runs a supervised list of such jobs one at a time.

The skill is the [`guided_coding/`](guided_coding) folder. It is a set of instructions for Claude, with no code to
install. Start with [`guided_coding/SKILL.md`](guided_coding/SKILL.md).

## Requirements

- **Claude Code.** If you do not have it yet, follow
  [Anthropic's Claude Code quickstart](https://code.claude.com/docs/en/quickstart) first.
- **Git,** unless you install from the ZIP download.
- **macOS or Linux.** GuidedCoding has been tested on macOS and tried on a Linux server; it has not been tested on
  Windows.

The review step uses Claude Code's code-review skill when it is available. To let Claude Code install GuidedCoding
with you instead of running the commands yourself, see the website's
[Quick Start](https://www.thomasterwilliger.org/guided_coding/quick-start.html).

## Install and register it (once)

Put the repository somewhere, then make a link from your Claude Code skills folder to its `guided_coding/` folder.
Open Terminal (on a Mac) or a terminal window (on Linux), paste a whole block, and press Return. The blocks are
complete: copy each one whole, with no editing. They are for bash or zsh, the usual shells. If your shell is csh
or tcsh, type `bash` first, and `exit` afterwards. They check before they change anything, and they stop on anything
unexpected. If you set `CLAUDE_CONFIG_DIR`, they use that folder instead of `~/.claude`.

Most people should install GuidedCoding in their home folder. This works with any project, including PHENIX. If you
develop PHENIX, you can instead install it in your PHENIX installation, next to your PHENIX source code.

**Most people: in your home folder, with Git.** This puts GuidedCoding in `~/guided_coding` and registers it. If
`~/guided_coding` is already a clone of cctbx/guided_coding on `master`, it updates it with `git pull` instead:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.4
DIR="$HOME/guided_coding"
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To update or move an existing installation, see Update and If you used the earlier GuidedCoding kit."; exit 1; fi; done
if [ -e "$DIR" ]; then
  case "$(git -C "$DIR" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) ;; *) echo "$DIR exists but is not a clone of https://github.com/cctbx/guided_coding; nothing changed."; exit 1;; esac
  [ "$(git -C "$DIR" rev-parse --abbrev-ref HEAD)" = master ] || { echo "$DIR is not on the master branch; nothing changed."; exit 1; }
  git -C "$DIR" pull --ff-only || { echo "Could not update $DIR; nothing registered."; exit 1; }
else
  git clone https://github.com/cctbx/guided_coding.git "$DIR" || exit 1
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
VERSION=1.4
ROOT="${PHENIX:-$PWD}"
DIR="$ROOT/modules/guided_coding"
echo "PHENIX installation: $ROOT"
[ -d "$ROOT/modules" ] || { echo "No modules folder in $ROOT. Set up PHENIX in this shell, or cd to the installation folder that contains modules; nothing changed."; exit 1; }
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To move a home-folder installation here, see the line after this block. To update, see Update."; exit 1; fi; done
if [ -e "$DIR" ]; then
  case "$(git -C "$DIR" remote get-url origin 2>/dev/null)" in https://github.com/cctbx/guided_coding|https://github.com/cctbx/guided_coding.git|git@github.com:cctbx/guided_coding|git@github.com:cctbx/guided_coding.git|ssh://git@github.com/cctbx/guided_coding|ssh://git@github.com/cctbx/guided_coding.git) echo "Using the existing $DIR";; *) echo "$DIR exists but is not a clone of https://github.com/cctbx/guided_coding; nothing changed."; exit 1;; esac
else
  git clone https://github.com/cctbx/guided_coding.git "$DIR" || exit 1
fi
grep -qx "# GuidedCoding (version $VERSION)" "$DIR/guided_coding/SKILL.md" 2>/dev/null || { echo "$DIR/guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version; run git pull there); nothing registered."; exit 1; }
mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc" && grep -m1 '^# GuidedCoding' "$DIR/guided_coding/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

Already installed in your home folder? Remove that registration first. This removes only a link that points to
`~/guided_coding`, and prints the command to put it back; `~/guided_coding` stays until you delete it:

```
L="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/gc"; T="$(readlink "$L")"; if [ "$T" = "$HOME/guided_coding/guided_coding" ]; then rm "$L" && echo "Removed $L. To put it back: ln -s $T $L"; else echo "$L points to ${T:-nothing}, not $HOME/guided_coding/guided_coding; nothing removed."; fi
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
It unpacks the ZIP into `~/guided_coding` and registers it:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.4
DIR="$HOME/guided_coding"
ZIP="$HOME/Downloads/guided_coding.zip"
for L in gc guided_coding; do if [ -e "$SKILLS/$L" ] || [ -L "$SKILLS/$L" ]; then echo "$SKILLS/$L already exists; nothing changed:"; ls -l "$SKILLS/$L"; echo "To update or move an existing installation, see Update and If you used the earlier GuidedCoding kit."; exit 1; fi; done
[ -e "$DIR" ] && { echo "$DIR already exists; nothing changed. To update a ZIP installation, see Update."; exit 1; }
[ -f "$ZIP" ] || { echo "Not found: $ZIP. Download it first. If it was saved under another name, such as 'guided_coding (1).zip', rename it to guided_coding.zip. If Safari unpacked it, turn off Settings > General > Open safe files after downloading, and download it again."; exit 1; }
TMP="$(mktemp -d)" && unzip -q "$ZIP" -d "$TMP" || exit 1
set -- "$TMP"/guided_coding-*
[ $# -eq 1 ] && [ -f "$1/guided_coding/SKILL.md" ] || { echo "Unexpected ZIP contents; nothing changed."; rm -rf "$TMP"; exit 1; }
grep -qx "# GuidedCoding (version $VERSION)" "$1/guided_coding/SKILL.md" 2>/dev/null || { echo "the ZIP's guided_coding/SKILL.md is not GuidedCoding $VERSION (it may be the earlier kit or an older version); nothing registered."; rm -rf "$TMP"; exit 1; }
mv "$1" "$DIR" && rmdir "$TMP" && mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc" && grep -m1 '^# GuidedCoding' "$DIR/guided_coding/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
END
```

Each block ends by showing the link and the version line of the skill it registered,
`# GuidedCoding (version 1.4)`, and what to do next. The blocks register only that version
(`VERSION=1.4` in each block).

**Then** start a new Claude Code conversation in the folder of a software project, and type `/gc` followed by a small
task (or `/gc` alone for an introduction). If you plan to use GuidedCoding regularly on that project, run
`/gc setup` there once (recommended): it saves the project's build and test commands, commit rules and other local
defaults in `.claude/GC_NOTES.md`. Without it, `/gc` finds these from the project each time. Installing is once per
computer.

### Update

For an installation made with Git, run `git pull` in its folder (`~/guided_coding`, or
`modules/guided_coding` in PHENIX). A ZIP installation has no Git history. To update it:
1. remove the link `gc` in your Claude Code skills folder (`$CLAUDE_CONFIG_DIR/skills` if you set
   `CLAUDE_CONFIG_DIR`, otherwise `~/.claude/skills`); it is only a link, and removing it deletes nothing else;
2. rename `~/guided_coding` to keep it as a backup, outside the skills folder, so that only one registration remains
   (two skills named `gc` conflict);
3. download the new ZIP and run the ZIP block again.

### Uninstall

Type `/gc uninstall` in Claude Code: it shows which installation is registered and asks once. Or paste this block.
Either way, it removes only the registration, so `/gc` stops working in new conversations. It deletes no files: it
tells you where the GuidedCoding files are, and you can delete that folder yourself if you no longer want it.
Project notes that `/gc setup` saved (`.claude/GC_NOTES.md` in your projects) are kept.

```
sh <<'END'
L="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/gc"
[ -L "$L" ] || { echo "$L is not a link (or does not exist); nothing changed."; exit 1; }
T="$(readlink "$L")"; case "$T" in /*) ;; *) T="$(dirname "$L")/$T";; esac
[ "$(basename "$T")" = guided_coding ] || { echo "$L points to $T, not a GuidedCoding folder; nothing changed."; exit 1; }
if [ -e "$T" ]; then grep -q '^# GuidedCoding' "$T/SKILL.md" 2>/dev/null || { echo "$L points to $T, which is not GuidedCoding; nothing changed."; exit 1; }; fi
rm "$L" || { echo "Could not remove $L; nothing changed."; exit 1; }
echo "GuidedCoding is no longer registered; /gc stops working in new Claude Code conversations."
if [ -e "$T" ]; then echo "Its files are still in $(dirname "$T"). Delete that folder yourself if you no longer want it. To register it again: ln -s '$T' '$L'"; fi
echo "Project notes (.claude/GC_NOTES.md in your projects) are kept."
END
```

## What the evidence says

In a replay of 37 past bug-fix jobs in PHENIX and cctbx, adding one review pass to plain Claude Code cut missed
program errors per job from 0.81 to 0.47. GuidedCoding always includes that review pass, which is the main reason to
expect it to do better than plain Claude Code; it has not been shown to do better than Claude Code with one review. On 18 harder jobs (selected, not a random sample), an outside review by
another AI assistant removed further major errors when added to GuidedCoding, narrowly. Version 1.4 keeps those two
steps (the outside review for hard or consequential changes) and a test that proves the fix; it does not include a
second review pass, keeps the independent reviewer optional, and narrows a strict scope rule that probably cost errors.
GuidedCoding 1.4 as a whole has not itself been measured; it was checked in a small trial and is being evaluated in
real use. [EVIDENCE.md](EVIDENCE.md) goes through each part of `/gc` and what the evidence says about it.

## If you used the earlier GuidedCoding kit (revision 21 or older)

Revision 22 replaces the earlier kit with this much shorter procedure. The earlier kit had approval screens,
evidence packets checked by its own tools, and an unattended auto mode. They are retired, and kept on the branch
`full-kit-rev21`.

What you gain, and what you lose:
- **Gained:** a shorter, prompt-only procedure that asks for your attention only when a decision is needed.
- **Lost:** the screens, packets, checker tools and the unattended auto mode. `/gc batch` is supervised, not
  unattended.

**To move:**
- **Finish first.** Finish or stop any job or auto queue of the earlier kit before updating.
- **Your link.** If your link is `~/.claude/skills/guided_coding` and points to `modules/guided_coding/guided_coding`,
  updating the repository (`git pull`) is enough. The link keeps working and now gives the new `/gc`.
- **A link into cctbx_project.** If your link points to `cctbx_project/libtbx/guided_coding` (revision 20 or older),
  first clone it from the folder that contains `modules`, with
  `git clone https://github.com/cctbx/guided_coding.git modules/guided_coding` (not the PHENIX block, which
  stops while the old link exists), then run this from the same folder
  (in bash or zsh). It replaces only a link that points to the cctbx_project copy, creates
  the new link before removing the old one, and stops on anything else:

  ```
  sh <<'END'
  SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
VERSION=1.4
  OLD="$SKILLS/guided_coding"
  NEW="$PWD/modules/guided_coding/guided_coding"
  [ -f "$NEW/SKILL.md" ] || { echo "Not found: $NEW/SKILL.md. Clone first, and run this from the folder that contains modules."; exit 1; }
  grep -qx "# GuidedCoding (version $VERSION)" "$NEW/SKILL.md" || { echo "$NEW/SKILL.md is not GuidedCoding $VERSION; update the clone (git pull) first; nothing changed."; exit 1; }
  [ -L "$OLD" ] || { echo "$OLD is not a link (or does not exist); nothing changed."; exit 1; }
  case "$(readlink "$OLD")" in
    */cctbx_project/libtbx/guided_coding|*/cctbx_project/libtbx/guided_coding/) ;;
    *) echo "$OLD points to $(readlink "$OLD"), not the cctbx_project copy; nothing changed."; exit 1;;
  esac
  if [ -e "$SKILLS/gc" ] || [ -L "$SKILLS/gc" ]; then echo "$SKILLS/gc already exists; nothing changed."; exit 1; fi
  ln -s "$NEW" "$SKILLS/gc" && rm "$OLD" && ls -l "$SKILLS" && grep -m1 '^# GuidedCoding' "$NEW/SKILL.md" && echo "Done. Next: start a new Claude Code conversation in a project folder and type /gc followed by a small task. For a project you will use regularly, type /gc setup there once (recommended) to save its local defaults."
  END
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
broken cross-file reference is caught. It does not check whether Claude follows the procedure; that is checked by
running it in Claude Code, and the recorded runs are listed in [EVIDENCE.md](EVIDENCE.md).
