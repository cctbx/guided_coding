"""Tests of migrate_registration.sh, and the CI check that its EXPECTED_LABEL
matches the label at the start of guided_coding/payload/RELEASE.

Each test builds a scratch PHENIX-like folder (or a standalone clone) holding a
copy of the script and of the kit's listed files in a Git checkout, an old
registration under a scratch HOME, and runs the script with each POSIX shell
present: /bin/sh (dash on Debian and Ubuntu, bash 3.2 in POSIX mode on macOS)
and dash where it is installed. Python 3.10 or newer; no psutil needed.
Run: python3 tst_migrate_registration.py
"""
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "migrate_registration.sh")
KIT = os.path.join(HERE, "guided_coding")
ORIGIN = "https://github.com/cctbx/guided_coding.git"
NOTE = "guided_coding-restore-note.txt"
PREFIX = ".gc-migrate-tmp-"


def shells():
  found = []
  for path in ("/bin/sh", shutil.which("dash")):
    if path and os.path.exists(path) and os.path.realpath(path) not in \
        [os.path.realpath(p) for p in found]:
      found.append(path)
  return found


SHELLS = shells()


def read(path, mode="r"):
  with open(path, mode) as f:
    return f.read()


def expected_label(script_text):
  m = re.search(r"^EXPECTED_LABEL='([^']*)'$", script_text, re.M)
  return m.group(1) if m else None


def label_matches(label, release_text):
  """The script's own rule: the RELEASE line begins with the label and a space."""
  first = release_text.splitlines()[0] if release_text else ""
  return label is not None and first.startswith(label + " ")


def listed(kit):
  with open(os.path.join(kit, "SOURCE_MANIFEST.sha256")) as f:
    names = [line.split("  ", 1)[1].strip()[2:] for line in f]
  return names + ["SOURCE_MANIFEST.sha256"]


def write_manifest(kit):
  """Rewrite a copy's manifest after a test changed a listed file on purpose."""
  names = [n for n in listed(kit) if n != "SOURCE_MANIFEST.sha256"]
  with open(os.path.join(kit, "SOURCE_MANIFEST.sha256"), "w") as f:
    for name in names:
      with open(os.path.join(kit, name), "rb") as g:
        f.write("%s  ./%s\n" % (hashlib.sha256(g.read()).hexdigest(), name))


class Fixture(object):
  """A scratch world: root/phenix/modules/{guided_coding,cctbx_project},
  root/home/.claude/skills/guided_coding, and a bin folder for PATH."""

  def __init__(self, tmp, standalone=False, origin=ORIGIN, git=True):
    self.root = tmp
    self.phenix = os.path.join(tmp, "PHENIX install")
    self.modules = os.path.join(self.phenix, "modules")
    self.old = os.path.join(self.modules, "cctbx_project", "libtbx", "guided_coding")
    os.makedirs(self.old)
    with open(os.path.join(self.old, "SKILL.md"), "w") as f:
      f.write("old copy\n")
    if standalone:
      self.repo = os.path.join(tmp, "my clones", "guided_coding")
    else:
      self.repo = os.path.join(self.modules, "guided_coding")
    self.kit = os.path.join(self.repo, "guided_coding")
    for name in listed(KIT):
      target = os.path.join(self.kit, name)
      if not os.path.isdir(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))
      shutil.copyfile(os.path.join(KIT, name), target)
    shutil.copyfile(SCRIPT, os.path.join(self.repo, "migrate_registration.sh"))
    if git:
      self.git("init", "-q")
      if origin:
        self.git("remote", "add", "origin", origin)
    self.home = os.path.join(tmp, "home dir")
    self.config = os.path.join(self.home, ".claude")
    self.skills = os.path.join(self.config, "skills")
    self.dest = os.path.join(self.skills, "guided_coding")
    os.makedirs(self.skills)
    self.bin = os.path.join(tmp, "bin")
    os.makedirs(self.bin)
    os.symlink(sys.executable, os.path.join(self.bin, "python3"))

  def git(self, *args):
    subprocess.check_call(["git", "-C", self.repo] + list(args))

  def register_old(self, config=None, target=None):
    config = config or self.config
    skills = os.path.join(config, "skills")
    if not os.path.isdir(skills):
      os.makedirs(skills)
    dest = os.path.join(skills, "guided_coding")
    os.symlink(target or self.old, dest)
    return dest

  def fake_python(self, path, good):
    """good: a wrapper around this Python; otherwise one that answers like 3.9."""
    if not os.path.isdir(os.path.dirname(path)):
      os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
      if good:
        f.write("#!/bin/sh\nexec '%s' \"$@\"\n" % sys.executable)
      else:
        # Answers like Python 3.9: prints its version, fails the 3.10 check.
        f.write("#!/bin/sh\ncase \"$*\" in *version_info*) exit 1 ;; *) echo 3.9.6 ;; esac\n")
    os.chmod(path, 0o755)

  def env(self, **extra):
    tools = []
    for tool in ("git", "shasum", "sha256sum"):
      found = shutil.which(tool)
      if found and os.path.dirname(found) not in tools:
        tools.append(os.path.dirname(found))
    env = {"HOME": self.home, "PATH": os.pathsep.join([self.bin] + tools + ["/usr/bin", "/bin"]),
           "LC_ALL": "C", "TMPDIR": self.root}
    for key, value in extra.items():
      if value is None:
        env.pop(key, None)
      else:
        env[key] = value
    return env

  def run(self, shell, *args, **env):
    cwd = env.pop("cwd", self.phenix if os.path.isdir(self.phenix) else self.root)
    script = os.path.relpath(os.path.join(self.repo, "migrate_registration.sh"), cwd)
    p = subprocess.Popen([shell, script] + list(args), cwd=cwd, env=self.env(**env),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0].decode("utf-8", "replace")
    return p.returncode, out


class MigrateTests(unittest.TestCase):

  def setUp(self):
    self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="tst migrate "))

  def tearDown(self):
    for dirpath, dirnames, filenames in os.walk(self.tmp):
      for d in dirnames:
        p = os.path.join(dirpath, d)
        if not os.path.islink(p):
          os.chmod(p, 0o755)
    shutil.rmtree(self.tmp, ignore_errors=True)

  def each_shell(self, test, **fixture_args):
    self.assertTrue(SHELLS, "no POSIX shell found")
    for shell in SHELLS:
      with self.subTest(shell=shell):
        world = os.path.join(self.tmp, os.path.basename(shell))
        os.makedirs(world)
        test(shell, Fixture(world, **fixture_args))

  # --- the table in step 5 ---------------------------------------------------

  def test_old_link_is_migrated(self):
    def t(sh, fx):
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("MOVED", out)
      self.assertEqual(os.readlink(fx.dest), fx.kit)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      note = read(os.path.join(fx.config, NOTE))
      self.assertIn("original link text: %s" % fx.old, note)
      self.assertIn("original target: %s" % fx.old, note)
      self.assertIn("only while the old copy", note)
      self.assertEqual(sorted(os.listdir(fx.skills)), ["guided_coding"])
      self.assertFalse([n for n in os.listdir(fx.config) if n.startswith(PREFIX)])
      self.assertIn("start a new Claude Code conversation", out)
      self.assertIn("Python: %s" % os.path.join(fx.bin, "python3"), out)
    self.each_shell(t)

  def test_broken_old_link_after_retirement_is_migrated(self):
    def t(sh, fx):
      fx.register_old()
      shutil.rmtree(os.path.join(fx.modules, "cctbx_project"))
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      self.assertIn("original target: target no longer exists",
                    read(os.path.join(fx.config, NOTE)))
    self.each_shell(t)

  def test_already_moved_and_second_run(self):
    def t(sh, fx):
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      note = read(os.path.join(fx.config, NOTE), "rb")
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("ALREADY MOVED", out)
      self.assertNotIn("MOVED ", out.replace("ALREADY MOVED", ""))
      self.assertEqual(os.readlink(fx.dest), fx.kit)
      self.assertEqual(read(os.path.join(fx.config, NOTE), "rb"), note)
    self.each_shell(t)

  def test_real_directory_is_refused(self):
    def t(sh, fx):
      os.makedirs(fx.dest)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 1, out)
      self.assertIn("REFUSED", out)
      self.assertTrue(os.path.isdir(fx.dest) and not os.path.islink(fx.dest))
      self.assertFalse(os.path.exists(os.path.join(fx.config, NOTE)))
    self.each_shell(t)

  def test_link_to_something_else_is_refused(self):
    def t(sh, fx):
      other = os.path.join(fx.root, "other kit")
      os.makedirs(other)
      os.symlink(other, fx.dest)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 1, out)
      self.assertIn("REFUSED", out)
      self.assertEqual(os.readlink(fx.dest), other)
    self.each_shell(t)

  def test_broken_link_to_something_else_is_reported(self):
    def t(sh, fx):
      gone = os.path.join(fx.root, "gone", "guided_coding")
      os.symlink(gone, fx.dest)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 1, out)
      self.assertIn("broken link to %s" % gone, out)
      self.assertIn("register-skill", out)
      self.assertEqual(os.readlink(fx.dest), gone)
    self.each_shell(t)

  def test_nothing_there(self):
    def t(sh, fx):
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("NOTHING THERE", out)
      self.assertIn("register-skill", out)
      self.assertFalse(os.path.lexists(fx.dest))
    self.each_shell(t)

  # --- places ------------------------------------------------------------------

  def test_both_places_with_and_without_config_dir(self):
    def t(sh, fx):
      app = os.path.join(fx.root, "app config")
      fx.register_old()
      app_dest = fx.register_old(config=app)
      # A shell without CLAUDE_CONFIG_DIR sees only ~/.claude.
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      self.assertEqual(os.readlink(app_dest), fx.old)
      self.assertIn("CLAUDE_CONFIG_DIR is not set", out)
      # A shell with it set finds the other one; ~/.claude is already moved.
      rc, out = fx.run(sh, CLAUDE_CONFIG_DIR=app)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(app_dest), fx.kit)
      self.assertIn("ALREADY MOVED ~/.claude", out)
      self.assertTrue(os.path.exists(os.path.join(app, NOTE)))
    self.each_shell(t)

  def test_custom_config_dir_option(self):
    def t(sh, fx):
      app = os.path.join(fx.root, "app only config")
      app_dest = fx.register_old(config=app)
      rc, out = fx.run(sh, "--config-dir", app)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(app_dest), fx.kit)
      self.assertIn("--config-dir %s" % app, out)
      rc, out = fx.run(sh, "--config-dir=" + app)
      self.assertEqual(rc, 0, out)
      self.assertIn("ALREADY MOVED --config-dir", out)
    self.each_shell(t)

  def test_refused_place_alongside_good_one(self):
    def t(sh, fx):
      fx.register_old()
      real = os.path.join(fx.root, "real config")
      fx.register_old(config=real)
      linked = os.path.join(fx.root, "linked config")
      os.symlink(real, linked)
      rc, out = fx.run(sh, CLAUDE_CONFIG_DIR=linked)
      self.assertEqual(rc, 1, out)
      self.assertIn("REFUSED", out)
      self.assertIn("symbolic link", out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      self.assertEqual(os.readlink(os.path.join(real, "skills", "guided_coding")), fx.old)
    self.each_shell(t)

  def test_linked_skills_folder_relative_and_dotdot_paths_refused(self):
    def t(sh, fx):
      app = os.path.join(fx.root, "app")
      os.makedirs(app)
      os.symlink(fx.skills, os.path.join(app, "skills"))
      fx.register_old()
      rc, out = fx.run(sh, "--config-dir", app, "--config-dir", "relative/config",
                       "--config-dir", os.path.join(fx.root, "a", "..", "app"))
      self.assertEqual(rc, 1, out)
      self.assertIn("the skills folder is a symbolic link", out)
      self.assertIn("the configuration path is relative", out)
      self.assertIn("contains '..'", out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)   # ~/.claude was still moved
    self.each_shell(t)

  def test_missing_config_dir_reported(self):
    def t(sh, fx):
      rc, out = fx.run(sh, "--config-dir", os.path.join(fx.root, "no such folder"))
      self.assertEqual(rc, 1, out)
      self.assertIn("NOT EXAMINED", out)
    self.each_shell(t)

  # --- paths, PHENIX folders, checkouts --------------------------------------

  def test_paths_with_spaces(self):
    def t(sh, fx):
      self.assertIn(" ", fx.kit)
      self.assertIn(" ", fx.dest)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      note = read(os.path.join(fx.config, NOTE))
      restore = [l for l in note.splitlines() if l.startswith("  rm ")][0].strip()
      subprocess.check_call(["/bin/sh", "-c", restore])
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_old_copy_in_other_phenix_needs_option(self):
    def t(sh, fx):
      other = os.path.join(fx.root, "other phenix", "modules", "cctbx_project", "libtbx",
                           "guided_coding")
      os.makedirs(other)
      fx.register_old(target=other)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 1, out)
      self.assertIn("different PHENIX folder", out)
      self.assertIn("--from-other-phenix", out)
      self.assertEqual(os.readlink(fx.dest), other)
      rc, out = fx.run(sh, "--from-other-phenix")
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  def test_standalone_clone_migrates_directly(self):
    def t(sh, fx):
      fx.register_old()   # the old copy is in a PHENIX folder; the clone is not
      fx.fake_python(os.path.join(fx.phenix, "build", "bin", "libtbx.python"), good=True)
      rc, out = fx.run(sh, cwd=fx.root)
      self.assertEqual(rc, 0, out)
      self.assertIn("standalone clone", out)
      self.assertIn("Python: %s" % os.path.join(fx.bin, "python3"), out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t, standalone=True)

  def test_installation_python_is_preferred(self):
    def t(sh, fx):
      libtbx = os.path.join(fx.phenix, "build", "bin", "libtbx.python")
      fx.fake_python(libtbx, good=True)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("Python: %s" % libtbx, out)
    self.each_shell(t)

  def test_old_python_skipped(self):
    def t(sh, fx):
      libtbx = os.path.join(fx.phenix, "build", "bin", "libtbx.python")
      fx.fake_python(libtbx, good=False)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("skipped %s: Python 3.9.6" % libtbx, out)
      self.assertIn("Python: %s" % os.path.join(fx.bin, "python3"), out)
    self.each_shell(t)

  def test_real_old_python_skipped(self):
    old = "/usr/bin/python3"
    try:
      out = subprocess.check_output([old, "-c", "import sys; print(sys.version_info < (3, 10))"])
    except (OSError, subprocess.CalledProcessError):
      self.skipTest("no %s" % old)
    if out.strip() != b"True":
      self.skipTest("%s is 3.10 or newer here" % old)
    def t(sh, fx):
      libtbx = os.path.join(fx.phenix, "build", "bin", "libtbx.python")
      os.makedirs(os.path.dirname(libtbx))
      with open(libtbx, "w") as f:   # macOS /usr/bin/python3 picks its tool by name
        f.write("#!/bin/sh\nexec %s \"$@\"\n" % old)
      os.chmod(libtbx, 0o755)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertRegex(out, r"skipped .*libtbx.python: Python 3\.[0-9]\.")
      self.assertIn("Python: %s" % os.path.join(fx.bin, "python3"), out)
    self.each_shell(t)

  def test_old_libtbx_python_on_path_ahead_of_good_python3(self):
    def t(sh, fx):
      on_path = os.path.join(fx.bin, "libtbx.python")
      fx.fake_python(on_path, good=False)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("skipped %s" % on_path, out)
      self.assertIn("Python: %s" % os.path.join(fx.bin, "python3"), out)
    self.each_shell(t, standalone=True)

  def test_no_good_python(self):
    def t(sh, fx):
      os.unlink(os.path.join(fx.bin, "python3"))
      fx.fake_python(os.path.join(fx.bin, "python3"), good=False)
      fx.register_old()
      env = {"PATH": os.pathsep.join([fx.bin, os.path.dirname(shutil.which("git")), "/bin"])}
      rc, out = fx.run(sh, **env)
      self.assertEqual(rc, 2, out)
      self.assertIn("no Python 3.10 or newer", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_not_a_git_checkout(self):
    def t(sh, fx):
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("is not a Git checkout", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t, git=False)

  def test_checkout_of_something_else_without_kit(self):
    def t(sh, fx):
      fx.git("remote", "set-url", "origin", "https://github.com/someone/other.git")
      shutil.rmtree(fx.kit)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("not an address of cctbx/guided_coding", out)
      self.assertIn("no guided_coding folder", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_ssh_and_unrecognized_origin(self):
    def t(sh, fx):
      fx.register_old()
      fx.git("remote", "set-url", "origin", "git@github.com:cctbx/guided_coding.git")
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("origin: git@github.com:cctbx/guided_coding.git", out)
      self.assertNotIn("NOTE: origin", out)
      os.unlink(fx.dest)
      fx.register_old()
      fx.git("remote", "set-url", "origin", "https://example.org/mirror/guided_coding.git")
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("NOTE: origin is https://example.org/mirror/guided_coding.git", out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  # --- verification before any change -----------------------------------------

  def test_missing_kit(self):
    def t(sh, fx):
      shutil.rmtree(fx.kit)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("no guided_coding folder", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_failed_hash_check(self):
    def t(sh, fx):
      with open(os.path.join(fx.kit, "payload", "GUIDE.md"), "a") as f:
        f.write("changed\n")
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("do not match its SOURCE_MANIFEST.sha256", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_failed_source_check(self):
    def t(sh, fx):
      with open(os.path.join(fx.kit, "payload", "tools", "extra.py"), "w") as f:
        f.write("print('unlisted')\n")
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("verify-source", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_other_release_label_refused(self):
    def t(sh, fx):
      release = os.path.join(fx.kit, "payload", "RELEASE")
      text = read(release)
      with open(release, "w") as f:
        f.write(text.replace(" r10 rev21 ", " r10 rev22 ", 1))
      write_manifest(fx.kit)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("release line does not begin with", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_later_release_with_matching_label_accepted(self):
    def t(sh, fx):
      release = os.path.join(fx.kit, "payload", "RELEASE")
      text = read(release)
      with open(release, "w") as f:
        f.write(text.replace(" r10 rev21 ", " r10 rev22 ", 1))
      write_manifest(fx.kit)
      script = os.path.join(fx.repo, "migrate_registration.sh")
      body = read(script)
      with open(script, "w") as f:
        f.write(body.replace("EXPECTED_LABEL='guided_coding 2.0 pilot r10 rev21'",
                             "EXPECTED_LABEL='guided_coding 2.0 pilot r10 rev22'", 1))
      self.assertTrue(label_matches(expected_label(read(script)), read(release)))
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  # --- interruption, temporary names and failed replacement -------------------

  def test_interrupted_run_then_rerun(self):
    def t(sh, fx):
      fx.register_old()
      rc, out = fx.run(sh, GC_MIGRATE_TEST_INTERRUPT="after-temp-link")
      self.assertNotEqual(rc, 0, out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
      self.assertEqual(sorted(os.listdir(fx.skills)), ["guided_coding"])
      leftovers = [n for n in os.listdir(fx.config) if n.startswith(PREFIX)]
      self.assertEqual(len(leftovers), 1)
      self.assertEqual(os.readlink(os.path.join(fx.config, leftovers[0])), fx.kit)
      note = read(os.path.join(fx.config, NOTE))
      self.assertIn("original link text: %s" % fx.old, note)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("removed a leftover temporary link", out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      self.assertFalse([n for n in os.listdir(fx.config) if n.startswith(PREFIX)])
      self.assertEqual(read(os.path.join(fx.config, NOTE)), note)
    self.each_shell(t)

  def test_unrelated_entries_with_temporary_name_left_alone(self):
    def t(sh, fx):
      fx.register_old()
      plain = os.path.join(fx.config, PREFIX + "999")
      with open(plain, "w") as f:
        f.write("not ours\n")
      elsewhere = os.path.join(fx.config, PREFIX + "998")
      os.symlink(os.path.join(fx.root, "somewhere"), elsewhere)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("left alone %s" % plain, out)
      self.assertIn("left alone %s" % elsewhere, out)
      self.assertEqual(read(plain), "not ours\n")
      self.assertTrue(os.path.islink(elsewhere))
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  def test_existing_restore_note_never_overwritten(self):
    def t(sh, fx):
      fx.register_old()
      with open(os.path.join(fx.config, NOTE), "w") as f:
        f.write("an earlier note\n")
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("restore note already exists, kept unchanged", out)
      self.assertEqual(read(os.path.join(fx.config, NOTE)), "an earlier note\n")
    self.each_shell(t)

  @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0,
                   "root ignores the folder permission that makes the rename fail")
  def test_failed_replacement_leaves_original(self):
    def t(sh, fx):
      fx.register_old()
      os.chmod(fx.skills, stat.S_IRUSR | stat.S_IXUSR)
      try:
        rc, out = fx.run(sh)
      finally:
        os.chmod(fx.skills, 0o755)
      self.assertEqual(rc, 3, out)
      self.assertIn("FAILED", out)
      self.assertIn("original registration is unchanged", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
      self.assertFalse([n for n in os.listdir(fx.config) if n.startswith(PREFIX)])
    self.each_shell(t)

  # --- boundaries found by the pre-freeze review ----------------------------

  def test_cdpath_ignored(self):
    def t(sh, fx):
      fx.register_old()
      other = os.path.join(fx.root, "other place", "modules")
      os.makedirs(os.path.join(other, "guided_coding"))
      rc, out = fx.run(sh, CDPATH=other)
      self.assertEqual(rc, 0, out)
      self.assertIn("Checking the new copy in %s\n" % fx.repo, out)
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  def test_leftover_link_to_a_non_kit_left_alone(self):
    def t(sh, fx):
      fx.register_old()
      named_like_kit = os.path.join(fx.root, "elsewhere", "guided_coding")
      os.makedirs(named_like_kit)
      odd = os.path.join(fx.config, PREFIX + "777")
      os.symlink(named_like_kit, odd)
      old_copy = os.path.join(fx.config, PREFIX + "778")
      os.symlink(fx.old, old_copy)
      rc, out = fx.run(sh)
      self.assertEqual(rc, 0, out)
      self.assertIn("left alone %s" % odd, out)
      self.assertIn("left alone %s" % old_copy, out)
      self.assertTrue(os.path.islink(odd) and os.path.islink(old_copy))
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
    self.each_shell(t)

  def test_skills_folder_given_as_config_dir_refused(self):
    def t(sh, fx):
      rc, out = fx.run(sh, "--config-dir", fx.skills)
      self.assertEqual(rc, 1, out)
      self.assertIn("this is a skills folder", out)
      self.assertEqual(os.listdir(fx.skills), [])
    self.each_shell(t)

  def test_linked_kit_folder_refused(self):
    def t(sh, fx):
      moved = os.path.join(fx.root, "kit elsewhere")
      os.rename(fx.kit, moved)
      os.symlink(moved, fx.kit)
      fx.register_old()
      rc, out = fx.run(sh)
      self.assertEqual(rc, 2, out)
      self.assertIn("is a link to %s" % moved, out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)

  def test_relative_and_dotdot_config_dirs_examined_nothing(self):
    def t(sh, fx):
      # Each would hold an old registration if it were followed.
      rel = os.path.join(fx.phenix, "relative config")
      dest_rel = fx.register_old(config=rel)
      dotdot = os.path.join(fx.root, "x", "..", "dotdot config")
      dest_dotdot = fx.register_old(config=os.path.join(fx.root, "dotdot config"))
      rc, out = fx.run(sh, "--config-dir", "relative config", "--config-dir", dotdot)
      self.assertEqual(rc, 1, out)
      self.assertEqual(os.readlink(dest_rel), fx.old)
      self.assertEqual(os.readlink(dest_dotdot), fx.old)
      self.assertFalse(os.path.exists(os.path.join(rel, NOTE)))
    self.each_shell(t)

  # --- calling shells and options ------------------------------------------------

  def test_run_from_other_login_shells(self):
    ran = []
    for caller in ("bash", "zsh", "csh", "tcsh"):
      path = shutil.which(caller)
      if not path:
        continue
      world = os.path.join(self.tmp, caller)
      os.makedirs(world)
      fx = Fixture(world)
      fx.register_old()
      script = os.path.join(fx.repo, "migrate_registration.sh")
      p = subprocess.Popen([path, "-c", "sh '%s'" % script], cwd=fx.phenix, env=fx.env(),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      out = p.communicate()[0].decode("utf-8", "replace")
      self.assertEqual(p.returncode, 0, (caller, out))
      self.assertEqual(os.path.realpath(fx.dest), fx.kit)
      ran.append(caller)
    print("calling shells exercised: %s" % (", ".join(ran) or "none present"))

  def test_unknown_option(self):
    def t(sh, fx):
      fx.register_old()
      rc, out = fx.run(sh, "--force")
      self.assertEqual(rc, 2, out)
      self.assertIn("unknown option: --force", out)
      self.assertEqual(os.readlink(fx.dest), fx.old)
    self.each_shell(t)


class LabelCheck(unittest.TestCase):
  """The CI check: the script's EXPECTED_LABEL is the label in payload/RELEASE."""

  def test_expected_label_matches_release(self):
    script = read(SCRIPT)
    release = read(os.path.join(KIT, "payload", "RELEASE"))
    self.assertIsNotNone(expected_label(script))
    self.assertTrue(label_matches(expected_label(script), release))

  def test_check_fails_for_a_different_label(self):
    script = read(SCRIPT)
    release = read(os.path.join(KIT, "payload", "RELEASE"))
    later = release.replace(" r10 rev21 ", " r10 rev22 ", 1)
    self.assertNotEqual(later, release)
    self.assertFalse(label_matches(expected_label(script), later))
    # A bare label with nothing after it fails here, as the script refuses it.
    self.assertFalse(label_matches(expected_label(script), expected_label(script) + "\n"))


if __name__ == "__main__":
  print("shells: %s" % ", ".join(SHELLS))
  unittest.main(verbosity=2)
