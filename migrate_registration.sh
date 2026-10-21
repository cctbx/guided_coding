#!/bin/sh
# Re-point a GuidedCoding registration (the personal skill link
# skills/guided_coding) from the retiring copy in cctbx_project
# (libtbx/guided_coding) to the kit in this repository's guided_coding/ folder.
#
# Run it with sh from any shell, for example from the PHENIX folder:
#   sh modules/guided_coding/migrate_registration.sh [--config-dir DIR] [--from-other-phenix]
#
# It verifies the kit beside it before changing anything, re-points only the
# usual link to the old copy, saves a restore note, and otherwise changes
# nothing. Running it again is harmless. The link change itself is done in
# Python (os.replace), so it is atomic. See README.md.

# The release this script migrates to. CI fails when it differs from the
# label at the start of guided_coding/payload/RELEASE, so a later release
# must update it in the same commit.
EXPECTED_LABEL='guided_coding 2.0 pilot r10 rev21'

say() { printf '%s\n' "$*"; }
die() {
  printf 'migrate_registration: STOPPED, nothing was changed: %s\n' "$*" >&2
  exit 2
}

usage() {
  say "usage: sh migrate_registration.sh [--config-dir DIR] ... [--from-other-phenix]"
  say "  --config-dir DIR     also check DIR/skills/guided_coding (DIR absolute; repeatable),"
  say "                       for a configuration folder that only the Claude app uses"
  say "  --from-other-phenix  also migrate a registration whose old copy is in a"
  say "                       different PHENIX folder from this script's"
}

# Options are checked before anything else; the Python step reads them again.
expect_dir=0
for arg in "$@"; do
  if [ "$expect_dir" = 1 ]; then expect_dir=0; continue; fi
  case "$arg" in
    --config-dir) expect_dir=1 ;;
    --config-dir=*) ;;
    --from-other-phenix) ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $arg" ;;
  esac
done
[ "$expect_dir" = 0 ] || { usage >&2; die "--config-dir needs a folder"; }

# CDPATH would make cd print and choose another folder; the Git variables
# would make git read another repository.
unset CDPATH GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY

# 1. Locate this script's own kit.
case "$0" in
  */*) script_dir=${0%/*} ;;
  *) script_dir=. ;;
esac
here=$(cd "$script_dir" 2>/dev/null && pwd -P) ||
  die "cannot open the folder that holds this script ($0)"
say "Checking the new copy in $here"

command -v git >/dev/null 2>&1 ||
  die "git is not on PATH, so the script cannot check that $here is a checkout of https://github.com/cctbx/guided_coding."
top=$(git -C "$here" rev-parse --show-toplevel 2>/dev/null) ||
  die "$here is not a Git checkout. It should be a clone of https://github.com/cctbx/guided_coding; if it is something else, move it aside and clone again (git clone https://github.com/cctbx/guided_coding.git)."
top=$(cd "$top" 2>/dev/null && pwd -P) || die "cannot open the checkout's top folder $top"
[ "$top" = "$here" ] ||
  die "$here is inside the Git checkout $top, not the top of a clone of https://github.com/cctbx/guided_coding."
origin=$(git -C "$here" config --get remote.origin.url 2>/dev/null) || origin=
case "$origin" in
  https://github.com/cctbx/guided_coding | https://github.com/cctbx/guided_coding.git | \
  git@github.com:cctbx/guided_coding | git@github.com:cctbx/guided_coding.git | \
  ssh://git@github.com/cctbx/guided_coding | ssh://git@github.com/cctbx/guided_coding.git)
    say "  origin: $origin" ;;
  "")
    say "  NOTE: this checkout has no origin remote; continuing, the checks below decide whether it holds the kit" ;;
  *)
    say "  NOTE: origin is $origin, not an address of cctbx/guided_coding; continuing, the checks below decide whether it holds the kit" ;;
esac
[ -d "$here/guided_coding" ] ||
  die "there is no guided_coding folder in $here, so this is not a complete checkout of cctbx/guided_coding."
kit=$(cd -P "$here/guided_coding" 2>/dev/null && pwd -P) || die "cannot open $here/guided_coding"
[ "$kit" = "$here/guided_coding" ] ||
  die "$here/guided_coding is a link to $kit, not the checkout's own kit folder."

# The script is inside a PHENIX installation only when its folder's parent is
# named modules; the PHENIX folder is then the one that contains modules.
inside=0
phenix=
parent=${here%/*}
case "$parent" in
  */modules) inside=1; phenix=${parent%/*} ;;
esac
if [ "$inside" = 1 ]; then
  say "  inside the PHENIX installation $phenix"
else
  say "  not inside a PHENIX modules folder (a standalone clone)"
fi

# 2. Choose a Python: the first candidate that runs and is 3.10 or newer.
python=
try_python() {
  [ -n "$python" ] && return 0
  cand=$1
  [ -n "$cand" ] || return 0
  [ -f "$cand" ] && [ -x "$cand" ] || return 0
  if "$cand" -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    python=$cand
  else
    version=$("$cand" -I -c 'import sys; print(sys.version.split()[0])' 2>/dev/null) || version=
    say "  skipped $cand: ${version:+Python $version, }not a Python 3.10 or newer"
  fi
}
if [ "$inside" = 1 ]; then
  try_python "$phenix/build/bin/libtbx.python"
  try_python "$phenix/conda_base/bin/python3"
fi
try_python "$(command -v libtbx.python 2>/dev/null)"
try_python "$(command -v python3 2>/dev/null)"
[ -n "$python" ] ||
  die "no Python 3.10 or newer was found (checked the installation's build/bin/libtbx.python and conda_base/bin/python3, then libtbx.python and python3 on PATH). Install one, for example in a venv, and put it on PATH."
say "  Python: $python"

# 3. Verify the new kit before changing anything.
cd "$kit" || die "cannot open $kit"
if command -v shasum >/dev/null 2>&1; then
  sums=$(shasum -a 256 -c SOURCE_MANIFEST.sha256 2>&1)
else
  sums=$(sha256sum -c SOURCE_MANIFEST.sha256 2>&1)
fi || {
  printf '%s\n' "$sums" | grep -v ': OK$' >&2
  die "the kit's files do not match its SOURCE_MANIFEST.sha256."
}
verify=$(GC_PAYLOAD_ROOT="$kit/payload" "$python" -I -B "$kit/payload/tools/screen_check.py" verify-source "$kit" 2>&1)
status=$?
if [ "$status" != 0 ] || ! printf '%s\n' "$verify" | grep -q '^VERIFIED complete source'; then
  printf '%s\n' "$verify" >&2
  die "the kit's source check (screen_check.py verify-source) failed."
fi
release=
IFS= read -r release < "$kit/payload/RELEASE" ||
  [ -n "$release" ] || die "cannot read $kit/payload/RELEASE"
case "$release" in
  "$EXPECTED_LABEL "*) ;;
  *) die "the kit's release line does not begin with '$EXPECTED_LABEL'. This script and the kit beside it do not match; update the checkout (git -C '$here' pull) and run it again." ;;
esac
say "  verified: listed hashes, complete source, release $EXPECTED_LABEL"
cd / || die "cannot leave $kit"

# 4-7. Find, check and migrate each registration (Python).
"$python" -I -B - "$kit" "$inside" "$phenix" "$@" <<'PYTHON'
import datetime
import os
import shlex
import signal
import sys

kit, inside, phenix = sys.argv[1], sys.argv[2] == "1", sys.argv[3]
argv = sys.argv[4:]
OLD_SUFFIX = "/cctbx_project/libtbx/guided_coding"
TEMP_PREFIX = ".gc-migrate-tmp-"
NOTE_NAME = "guided_coding-restore-note.txt"
REPOSITORY = "https://github.com/cctbx/guided_coding"

config_dirs = []
from_other_phenix = False
i = 0
while i < len(argv):
    arg = argv[i]
    if arg == "--config-dir":
        config_dirs.append(argv[i + 1])
        i += 2
        continue
    if arg.startswith("--config-dir="):
        config_dirs.append(arg[len("--config-dir="):])
    elif arg == "--from-other-phenix":
        from_other_phenix = True
    i += 1

places = []
if os.environ.get("CLAUDE_CONFIG_DIR"):
    places.append(("CLAUDE_CONFIG_DIR", os.environ["CLAUDE_CONFIG_DIR"], False))
places.append(("~/.claude", os.path.join(os.path.expanduser("~"), ".claude"), False))
for d in config_dirs:
    places.append(("--config-dir", d, True))

results = []   # (status, place, detail)
seen = {}


def q(path):
    return shlex.quote(path)


def report(status, where, detail):
    results.append((status, where, detail))
    print("  %s: %s" % (status, detail))


def is_kit_folder(path):
    """A guided_coding kit folder: named guided_coding, with its source manifest
    and release file."""
    return (os.path.basename(path) == "guided_coding" and
            os.path.isfile(os.path.join(path, "SOURCE_MANIFEST.sha256")) and
            os.path.isfile(os.path.join(path, "payload", "RELEASE")))


def remove_leftovers(config):
    """Remove leftover temporary links of this script (an interrupted run);
    report and keep anything else with the temporary-name prefix."""
    for name in sorted(os.listdir(config)):
        if not name.startswith(TEMP_PREFIX):
            continue
        path = os.path.join(config, name)
        if os.path.islink(path) and is_kit_folder(os.path.realpath(path)):
            os.unlink(path)
            print("  removed a leftover temporary link from an interrupted run: %s" % path)
        else:
            print("  NOTE: left alone %s: it has this script's temporary name but is not "
                  "its temporary link" % path)


def write_note(config, dest, text, target):
    note = os.path.join(config, NOTE_NAME)
    if os.path.lexists(note):
        print("  restore note already exists, kept unchanged: %s" % note)
        return note
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = "\n".join([
        "GuidedCoding registration restore note",
        "written: %s" % stamp,
        "registration: %s" % dest,
        "original link text: %s" % text,
        "original target: %s" % (target or "target no longer exists"),
        "replaced by: %s" % kit,
        "",
        "To restore the original registration:",
        "  rm %s && ln -s %s %s" % (q(dest), q(text), q(dest)),
        "This gives back a working revision 20 copy only while the old copy in",
        "cctbx_project still exists. After it is retired the old path is gone,",
        "and recovery means the new repository, %s." % REPOSITORY,
        "",
    ])
    fd = os.open(note, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w") as f:
        f.write(body)
    print("  restore note written: %s" % note)
    return note


def migrate(where, config, dest, text, target):
    try:
        note = write_note(config, dest, text, target)
        remove_leftovers(config)
    except OSError as e:
        report("FAILED", where, "could not write the restore note or clear leftovers in %s "
               "(%s); the registration is unchanged" % (config, e))
        return
    temp = os.path.join(config, "%s%d" % (TEMP_PREFIX, os.getpid()))
    n = 0
    while os.path.lexists(temp):
        n += 1
        temp = os.path.join(config, "%s%d-%d" % (TEMP_PREFIX, os.getpid(), n))
    try:
        os.symlink(kit, temp, target_is_directory=True)
    except OSError as e:
        report("FAILED", where, "could not make the new link in %s (%s); the registration "
               "is unchanged" % (config, e))
        return
    if os.path.realpath(temp) != kit:
        os.unlink(temp)
        report("FAILED", where, "the new link did not resolve to %s; the registration is "
               "unchanged" % kit)
        return
    if os.environ.get("GC_MIGRATE_TEST_INTERRUPT") == "after-temp-link":
        os.kill(os.getpid(), signal.SIGKILL)   # test only: an interrupted run
    if not os.path.islink(dest) or os.readlink(dest) != text:
        os.unlink(temp)
        report("FAILED", where, "%s changed while the script ran; it was left as it is now"
               % dest)
        return
    try:
        os.replace(temp, dest)
    except OSError as e:
        try:
            os.unlink(temp)
        except OSError:
            pass
        report("FAILED", where, "could not replace %s (%s). The original registration is "
               "unchanged, still pointing to %s" % (dest, e, text))
        return
    now = os.readlink(dest)
    if now != kit or os.path.realpath(dest) != kit:
        report("FAILED", where, "after the change %s reads %s, not %s; restore with the "
               "note %s" % (dest, now, kit, note))
        return
    remove_leftovers(config)
    report("MOVED", where, "%s now points to %s (it pointed to %s). To undo, see %s"
           % (dest, kit, text, note))


def examine(label, config, explicit):
    where = "%s %s" % (label, config)
    print("%s:" % where)
    if not os.path.isabs(config):
        return report("REFUSED", where, "the configuration path is relative; give an absolute path")
    if ".." in config.split(os.sep):
        return report("REFUSED", where, "the configuration path contains '..'")
    if os.path.islink(config):
        return report("REFUSED", where, "the configuration folder is a symbolic link; "
                      "the script does not follow it")
    if not os.path.lexists(config):
        if explicit:
            return report("NOT EXAMINED", where, "this folder does not exist")
        return report("NOTHING THERE", where, "no configuration folder here")
    if not os.path.isdir(config):
        return report("REFUSED", where, "this is not a folder")
    key = os.path.realpath(config)
    if os.path.basename(key) == "skills":
        return report("REFUSED", where, "this is a skills folder, not a configuration folder; "
                      "give the folder that contains skills/")
    if key in seen:
        return report("SAME FOLDER", where, "the same folder as %s, checked above" % seen[key])
    seen[key] = where
    skills = os.path.join(config, "skills")
    dest = os.path.join(skills, "guided_coding")
    if os.path.islink(skills):
        return report("REFUSED", where, "the skills folder is a symbolic link; "
                      "the script does not follow it")
    if not os.path.lexists(dest):
        return report("NOTHING THERE", where,
                      "no registration at %s; for a first-time setup, follow the User Guide "
                      "(register-skill)" % dest)
    if kit == key or key.startswith(kit + os.sep):
        return report("REFUSED", where, "the configuration folder is inside the kit")
    if not os.path.islink(dest):
        return report("REFUSED", where, "%s is a real folder or file, not a link; it was "
                      "left unchanged" % dest)
    text = os.readlink(dest)
    absolute = os.path.normpath(text if os.path.isabs(text) else os.path.join(skills, text))
    exists = os.path.exists(dest)
    target = os.path.realpath(dest) if exists else None
    if absolute.endswith(OLD_SUFFIX):
        if inside:
            old_root = absolute[:-len(OLD_SUFFIX)]
            old_phenix = os.path.dirname(old_root) if os.path.basename(old_root) == "modules" else None
            same = old_phenix is not None and (
                old_phenix == phenix or
                (os.path.exists(old_phenix) and os.path.realpath(old_phenix) == phenix))
            if not same and not from_other_phenix:
                return report(
                    "NOT MOVED", where,
                    "%s points to the old copy in a different PHENIX folder (%s), not this "
                    "one (%s). It was left unchanged. To move it to this kit anyway, run the "
                    "script again with --from-other-phenix"
                    % (dest, old_phenix or os.path.dirname(old_root), phenix))
        return migrate(where, config, dest, text, target)
    if exists and target == kit:
        return report("ALREADY MOVED", where, "%s already points to this kit; nothing changed"
                      % dest)
    if not exists:
        return report("NOT MOVED", where,
                      "%s is a broken link to %s, which is not the old cctbx_project copy. It "
                      "was left unchanged. To register this kit instead, remove that link "
                      "(rm %s) and follow the User Guide's first-time setup (register-skill)"
                      % (dest, text, q(dest)))
    return report("REFUSED", where, "%s points to %s, which is neither the old cctbx_project "
                  "copy nor this kit; it was left unchanged" % (dest, text))


print("Registrations:")
for label, config, explicit in places:
    examine(label, config, explicit)

print("")
print("Summary (every place checked):")
for status, where, detail in results:
    print("  %-13s %s" % (status, where))
moved = [r for r in results if r[0] == "MOVED"]
failed = [r for r in results if r[0] == "FAILED"]
attention = [r for r in results if r[0] in ("REFUSED", "NOT MOVED", "NOT EXAMINED")]
if not os.environ.get("CLAUDE_CONFIG_DIR"):
    print("  (CLAUDE_CONFIG_DIR is not set in this shell; if the Claude app uses its own")
    print("  configuration folder, run the script again with --config-dir and that folder.)")
print("")
if moved or any(r[0] == "ALREADY MOVED" for r in results):
    print("Next: start a new Claude Code conversation (between guided jobs, not during one).")
    print("If you use the Claude app and /gc help still shows revision 20 there, quit and")
    print("reopen the app.")
if failed:
    print("A change failed; see FAILED above. Nothing else was changed for that place.")
    sys.exit(3)
if attention:
    print("Some places were not changed; see REFUSED, NOT MOVED or NOT EXAMINED above.")
    sys.exit(1)
sys.exit(0)
PYTHON
