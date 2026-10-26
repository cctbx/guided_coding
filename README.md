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
- **macOS or Linux.** GuidedCoding has been tested on macOS; it should work on Linux, and has not been tested on
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

**Most people: in your home folder, with Git.** This puts GuidedCoding in `~/guided_coding` and registers it:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
DIR="$HOME/guided_coding"
if [ -e "$SKILLS/gc" ] || [ -L "$SKILLS/gc" ]; then echo "$SKILLS/gc already exists; nothing changed:"; ls -l "$SKILLS/gc"; exit 1; fi
[ -e "$DIR" ] || git clone https://github.com/cctbx/guided_coding.git "$DIR" || exit 1
[ -f "$DIR/guided_coding/SKILL.md" ] || { echo "Not found: $DIR/guided_coding/SKILL.md; nothing registered."; exit 1; }
mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc"
END
```

**Without Git: from the ZIP download.** Download
[`guided_coding.zip`](https://www.thomasterwilliger.org/guided_coding/guided_coding.zip) into your Downloads folder, then run this. It
unpacks the ZIP into `~/guided_coding` and registers it:

```
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
DIR="$HOME/guided_coding"
ZIP="$HOME/Downloads/guided_coding.zip"
if [ -e "$SKILLS/gc" ] || [ -L "$SKILLS/gc" ]; then echo "$SKILLS/gc already exists; nothing changed:"; ls -l "$SKILLS/gc"; exit 1; fi
[ -e "$DIR" ] && { echo "$DIR already exists; nothing changed."; exit 1; }
[ -f "$ZIP" ] || { echo "Not found: $ZIP. Download it first. If it was saved under another name, such as 'guided_coding (1).zip', rename it to guided_coding.zip. If Safari unpacked it, turn off Settings > General > Open safe files after downloading, and download it again."; exit 1; }
TMP="$(mktemp -d)" && unzip -q "$ZIP" -d "$TMP" || exit 1
set -- "$TMP"/guided_coding-*
[ $# -eq 1 ] && [ -f "$1/guided_coding/SKILL.md" ] || { echo "Unexpected ZIP contents in $TMP; nothing changed."; exit 1; }
mv "$1" "$DIR" && rmdir "$TMP" && mkdir -p "$SKILLS" && ln -s "$DIR/guided_coding" "$SKILLS/gc" && ls -l "$SKILLS/gc"
END
```

To update an installation made with Git, run `git pull` in its folder. A ZIP installation has no Git history: to
update it, remove the link `~/.claude/skills/gc` (it is only a link; removing it deletes nothing else), rename
`~/guided_coding` to keep it as a backup, then download the new ZIP and run the block again. Keep any backup outside
the skills folder, so that only one GuidedCoding registration remains: two skills named `gc` conflict. The `git`
commands further down this page are for installations made with Git.

**In a PHENIX installation:** from the folder that contains `modules` and `build`, clone the repository if it is not
there yet, then register:

```
git clone https://github.com/cctbx/guided_coding.git modules/guided_coding
sh <<'END'
SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
NEW="$PWD/modules/guided_coding/guided_coding"
[ -f "$NEW/SKILL.md" ] || { echo "Not found: $NEW/SKILL.md. Run this from the folder that contains modules."; exit 1; }
if [ -e "$SKILLS/gc" ] || [ -L "$SKILLS/gc" ]; then echo "$SKILLS/gc already exists; nothing changed:"; ls -l "$SKILLS/gc"; exit 1; fi
mkdir -p "$SKILLS" && ln -s "$NEW" "$SKILLS/gc" && ls -l "$SKILLS/gc"
END
```

**Then** start a new Claude Code conversation in the folder of the project you want to change, and type `/gc`. It
should introduce itself. After that, type `/gc` followed by what you want done. Installing is once per computer;
optionally, run `/gc setup` once per project to save its build and test commands in `.claude/GC_NOTES.md`.

## What the evidence says

In a replay of 37 past bug-fix jobs in PHENIX and cctbx, adding one review pass to plain Claude Code cut missed
program errors per job from 0.81 to 0.47. On 18 harder jobs (selected, not a random sample), an outside review by
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
  first clone as in "In a PHENIX installation" under "Install and register it (once)", then run this from the folder
  that contains `modules` (in bash or zsh). It replaces only a link that points to the cctbx_project copy, creates
  the new link before removing the old one, and stops on anything else:

  ```
  sh <<'END'
  SKILLS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
  OLD="$SKILLS/guided_coding"
  NEW="$PWD/modules/guided_coding/guided_coding"
  [ -f "$NEW/SKILL.md" ] || { echo "Not found: $NEW/SKILL.md. Clone first, and run this from the folder that contains modules."; exit 1; }
  [ -L "$OLD" ] || { echo "$OLD is not a link (or does not exist); nothing changed."; exit 1; }
  case "$(readlink "$OLD")" in
    */cctbx_project/libtbx/guided_coding|*/cctbx_project/libtbx/guided_coding/) ;;
    *) echo "$OLD points to $(readlink "$OLD"), not the cctbx_project copy; nothing changed."; exit 1;;
  esac
  if [ -e "$SKILLS/gc" ] || [ -L "$SKILLS/gc" ]; then echo "$SKILLS/gc already exists; nothing changed."; exit 1; fi
  ln -s "$NEW" "$SKILLS/gc" && rm "$OLD" && ls -l "$SKILLS"
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
