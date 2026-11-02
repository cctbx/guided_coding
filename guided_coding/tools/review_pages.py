"""
GuidedCoding review pages: the evidence for each change, and the one page
the developer reads after the outside review.

Everything comes from one review spec, review.json, in a review folder
(format in REVIEW_SPEC.md beside this file). Run with a Python that has
the markdown package (for PHENIX: libtbx.python):

  python review_pages.py packet  <review folder> [<change id> ...]
  python review_pages.py scope   <review folder>
  python review_pages.py request <review folder> [<change id> ...]
  python review_pages.py page    <review folder>   # the developer's page
  python review_pages.py check   <review folder> [--before-review]
  python review_pages.py navtest <review folder>   # needs Google Chrome

Outputs go to <review folder>/evidence/ and <review folder>/out/.

"packet" runs each test of a change on the current code ("new") and on
the old code: the current code with only that change's commits reversed
("current minus the change"), or for a change not yet committed, the
job's saved copies of the files from before the job. The old library
files are loaded in place of the current modules in the test's own
process, so only tests that run the code in-process are suitable; a run
whose test starts a child process is marked new_only. Each run records
the command, exit code, output, and which file every changed module was
loaded from; "check" refuses runs that do not prove the change.
"""
from __future__ import print_function
import html, json, os, re, subprocess, sys

# ---------------------------------------------------------------------------
# The review spec

def load(folder):
  spec = json.load(open(os.path.join(folder, "review.json")))
  spec["folder"] = os.path.abspath(folder)
  settings = spec["settings"]
  settings.setdefault("upstream", "origin/master")
  settings.setdefault("full_test", "the full test suite")
  env = dict(os.environ)
  if settings.get("git_path"):
    env["PATH"] = env["PATH"] + os.pathsep + settings["git_path"]
  spec["git_env"] = env
  for k, c in enumerate(spec["changes"], 1):
    c["number"] = k
  return spec

def git(spec, repo, args, check = True):
  p = subprocess.run(["git"] + args, cwd = os.path.join(
    spec["settings"]["modules"], repo), env = spec["git_env"],
    stdout = subprocess.PIPE, stderr = subprocess.PIPE,
    universal_newlines = True)
  if check and p.returncode != 0:
    raise RuntimeError("git %s in %s failed: %s" %(" ".join(args), repo,
      p.stderr))
  return p

def evidence_dir(spec, change):
  return os.path.join(spec["folder"], "evidence", change["id"])

def out_dir(spec):
  d = os.path.join(spec["folder"], "out")
  os.makedirs(d, exist_ok = True)
  return d

# ---------------------------------------------------------------------------
# packet: the evidence for one change

BUILD_NOTE = ("Old-code runs replace only the changed Python modules listed "
  "under OLD CODE; compiled extensions and every other file come from the "
  "current build and checkout.")

TEST_STARTED = "TEST STARTED"  # the runner's marker: replacements loaded

RUNNER = '''
import importlib.util, os, runpy, sys
overlays = %(overlays)r   # (module name, old file, real file)
for root in %(roots)r:     # so the old modules' packages can be imported
  if root not in sys.path:
    sys.path.append(root)
for name, old_file, real_file in sorted(overlays, key = lambda x: x[0].count(".")):
  kw = {}
  if os.path.basename(real_file) == "__init__.py":
    kw["submodule_search_locations"] = [os.path.dirname(real_file)]
  spec = importlib.util.spec_from_file_location(name, old_file, **kw)
  module = importlib.util.module_from_spec(spec)
  sys.modules[name] = module
  parent, _, child = name.rpartition(".")
  spec.loader.exec_module(module)
  if parent:
    setattr(importlib.import_module(parent), child, module)
  print("OLD CODE: %%s from %%s" %%(name, old_file))
sys.argv = [%(test)r] + %(args)r
print(%(started)r, flush = True)
try:
  runpy.run_path(%(test)r, run_name = "__main__")
finally:
  # Which file each changed module was loaded from, and any module loaded
  #  from a current copy of a changed file (replacement bypassed)
  real_files = %(real_files)r
  for name in sorted(%(module_names)r):
    m = sys.modules.get(name)
    print("LOADED: %%s from %%s" %%(name, getattr(m, "__file__", None)))
  for name, m in sorted(sys.modules.items()):
    f = getattr(m, "__file__", None)
    if %(is_old)r and f and os.path.realpath(f) in real_files:
      print("WARNING: %%s loaded from the current file %%s" %%(name, f))
'''

def module_name(path):
  """Python module name of a library file (phenix/x/y.py -> phenix.x.y)"""
  parts = path[:-3].split("/")
  if parts[-1] == "__init__":
    parts = parts[:-1]
  return ".".join(parts)

NOT_COMMITTED = "0000000000"  # marks an uncommitted diff in net.diff

def is_uncommitted(change):
  return any(part.get("uncommitted") for part in change["parts"])

def sha256(path):
  import hashlib
  return hashlib.sha256(open(path, "rb").read()).hexdigest()

def before_file(part, path):
  """The job's saved copy of a file as it was before the job (None: the
     job created the file)"""
  f = os.path.join(part["before"], path)
  return f if os.path.exists(f) else None

def job_record(part):
  """(job folder, repo-<n>, {path: "changed" or "created"}) from the job's
     JOB.txt (SKILL.md section 2), for a part whose "before" is the job
     folder's before/repo-<n>; the paths are None without a JOB.txt"""
  before = os.path.normpath(part["before"])
  job, repo_id = os.path.dirname(os.path.dirname(before)), os.path.basename(
    before)
  record = os.path.join(job, "JOB.txt")
  if not os.path.exists(record):
    return job, repo_id, None
  paths = {}
  for line in open(record).read().splitlines():
    kind, _, where = line.partition(" ")
    if kind in ("changed", "created") and where.startswith(repo_id + "/"):
      paths[where[len(repo_id) + 1:]] = kind
  return job, repo_id, paths

def text_lines(path):
  """The file's lines, or None for a file that is not text"""
  data = open(path, "rb").read()
  if b"\0" in data:
    return None
  try:
    return data.decode("utf-8").splitlines(True)
  except UnicodeDecodeError:
    return None

def saved_diff(spec, part, files):
  """This job's change of these files: each saved copy (the file before
     the job, the developer's earlier uncommitted work included) against
     the current file, in git's format"""
  import difflib
  out = []
  for path in files:
    old = before_file(part, path)
    current = os.path.join(spec["settings"]["modules"], part["repo"], path)
    if not old and not os.path.exists(current):
      continue
    a = text_lines(old) if old else []
    b = text_lines(current) if os.path.exists(current) else []
    header = "diff --git a/%s b/%s\n" %(path, path)
    if not old:
      header += "new file mode 100644\n"
    elif not os.path.exists(current):
      header += "deleted file mode 100644\n"
    if a is None or b is None:
      out.append(header + "Binary files differ\n")
      continue
    lines = list(difflib.unified_diff(a, b, "a/" + path if old else
      "/dev/null", "b/" + path if os.path.exists(current) else "/dev/null"))
    if lines:
      out.append(header + "".join(x if x.endswith("\n") else
        x + "\n\\ No newline at end of file\n" for x in lines))
  return "".join(out)

def changed_paths(spec, part):
  """Every file the part changes: its commits' files, or the files the
     job's record names (with those it saved and those listed)"""
  if part.get("uncommitted"):
    paths = []
    for root, dirs, files in os.walk(part["before"]):
      for f in files:
        paths.append(os.path.relpath(os.path.join(root, f),
          part["before"]).replace(os.sep, "/"))
    recorded = job_record(part)[2]
    return sorted(set(paths + list(recorded or {}) +
      part.get("library_files", []) + part.get("test_files", [])))
  paths = []
  for c in part.get("commits", []):
    paths.extend(git(spec, part["repo"], ["show", "--name-only", "--format=",
      c]).stdout.split())
  return sorted(set(paths))

def coverage_problems(part, paths):
  """Changed files the old-code runs do not account for"""
  listed = set(part.get("library_files", []) + part.get("test_files", []))
  not_reversed = part.get("not_reversed", {})
  problems = []
  if part.get("uncommitted") and job_record(part)[2] is None:
    problems.append("%s: no JOB.txt beside %s, so the files the job created "
      "cannot be confirmed (use the job log, or REVIEW.md section 4)" %(
      part["repo"], part["before"]))
  for path in paths:
    if path in listed or path in not_reversed or os.path.basename(path) in \
        SKIP_FILES or is_test(path):
      continue
    if path.endswith(".py"):
      problems.append("%s %s: a changed module not in library_files (the "
        "old-code runs would use its current version)" %(part["repo"], path))
    else:
      problems.append("%s %s: a changed file the old-code runs cannot "
        "reverse; list it under not_reversed with the reason" %(part["repo"],
        path))
  return problems

def stop_group(p):
  """Stop a run and every process it started"""
  import signal
  try:
    os.killpg(p.pid, signal.SIGKILL)
  except (AttributeError, OSError):  # Windows, or already gone
    p.kill()

def run_label(run):
  """The run's name in the evidence: its "label", or the test's file name
     and arguments"""
  if run.get("label"):
    return run["label"]
  args = run.get("args", [])
  return "%s%s" %(os.path.basename(run["test"])[:-3],
    ("_" + "_".join(args)) if args else "")

def packet(spec, change):
  """Write <review>/evidence/<id>/packet/ for one change"""
  labels = [run_label(r) for r in change["runs"]]
  same = sorted(set(x for x in labels if labels.count(x) > 1))
  if same:
    raise ValueError("%s: two runs are both named %s; give one a \"label\""
      %(change["id"], ", ".join(same)))
  modules = spec["settings"]["modules"]
  out = os.path.join(evidence_dir(spec, change), "packet")
  for sub in ("tests", "old", "runs"):
    os.makedirs(os.path.join(out, sub), exist_ok = True)
  base_head, changed, diffs, overlays = [], [], [], []
  candidate, coverage = {}, []
  also_reverse = change.get("also_reverse", {})
  for part in change["parts"]:
    repo, commits = part["repo"], part.get("commits", [])
    uncommitted = part.get("uncommitted", False)
    files = part.get("library_files", []) + part.get("test_files", [])
    paths = changed_paths(spec, part)
    coverage.extend(coverage_problems(part, paths))
    for path in paths:
      f = os.path.join(modules, repo, path)
      candidate[repo + "/" + path] = sha256(f) if os.path.exists(f) else None
    cur = git(spec, repo, ["rev-parse", "--short", "HEAD"]).stdout.strip()
    base_head.append("%s: %s (checkout HEAD %s)" %(repo, "not committed: "
      "each file against the job's copy of it from before the job (%s)"
      %part["before"] if uncommitted else "commits " + " ".join(commits),
      cur))
    for path, reason in sorted(part.get("not_reversed", {}).items()):
      base_head.append("  NOT REVERSED in the old code: %s (%s)" %(path,
        reason))
    if uncommitted:
      diff = saved_diff(spec, part, paths)
      changed.append("%s, not committed:\n%s\n" %(repo, "\n".join("  " + p
        for p in paths)))
      diffs.append("commit %s\nAuthor: -\n\n    Not committed (%s)\n\n%s\n"
        %(NOT_COMMITTED, repo, diff))
    if also_reverse.get(repo):
      base_head.append("  ALSO REVERSED in the old code (a later change "
        "changed the same lines): %s" %" ".join(also_reverse[repo]))
    for c in commits:
      cmd = ["show", "--stat", "--format=%h %s", c]
      changed.append("$ (cd %s && git %s)\n%s" %(repo, " ".join(cmd),
        git(spec, repo, cmd).stdout))
      diffs.append(git(spec, repo, ["show", c]).stdout + "\n")
    for path in part.get("test_files", []):
      dest = os.path.join(out, "tests", repo, path)
      os.makedirs(os.path.dirname(dest), exist_ok = True)
      with open(dest, "w") as f:
        f.write(open(os.path.join(modules, repo, path)).read())
    for path in part.get("library_files", []):
      real = os.path.join(modules, repo, path)
      old = os.path.join(out, "old", repo, path)
      os.makedirs(os.path.dirname(old), exist_ok = True)
      if uncommitted:
        # The file exactly as it was before the job
        saved = before_file(part, path)
        if saved is None:
          coverage.append("%s %s: a module the job created has no old "
            "version to load" %(repo, path))
          continue
        with open(old, "w") as f:
          f.write(open(saved).read())
        with open(old + ".reverse_patches.txt", "w") as f:
          f.write("=== the job's saved copy %s\n" %saved)
        overlays.append((module_name(path), old, real))
        continue
      # The current file with only this change's commits reversed
      with open(old, "w") as f:
        f.write(open(real).read())
      applied = []
      steps = list(reversed(also_reverse.get(repo, []))) + list(
        reversed(commits))  # newest first
      for c in steps:
        patch = git(spec, repo, ["show", "--format=", c, "--", path]).stdout
        if not patch:
          continue
        p = subprocess.run(["patch", "-R", "-s", "--no-backup-if-mismatch",
          old], input = patch, universal_newlines = True,
          stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        if p.returncode != 0:
          raise RuntimeError("reverse patch of %s failed for %s: %s" %(c,
            path, p.stdout))
        applied.append("=== reversed %s (applied completely)\n%s" %(c, patch))
      with open(old + ".reverse_patches.txt", "w") as f:
        f.write("\n".join(applied))
      overlays.append((module_name(path), old, real))
  checkout = []
  for repo in spec["settings"]["repositories"]:
    head = git(spec, repo, ["rev-parse", "HEAD"]).stdout.strip()
    status = git(spec, repo, ["status", "--short"]).stdout.rstrip()
    checkout.append("%s: HEAD %s\n  git status --short:\n%s" %(repo, head,
      "\n".join("    " + x for x in status.splitlines()) or "    (clean)"))
  with open(os.path.join(out, "base_head.txt"), "w") as f:
    f.write("\n".join(base_head) + "\n\nCheckouts:\n" + "\n".join(checkout) +
      "\n\n" + BUILD_NOTE + "\n")
  with open(os.path.join(out, "changed_files.txt"), "w") as f:
    f.write("\n".join(changed))
  with open(os.path.join(out, "net.diff"), "w") as f:
    f.write("".join(diffs))
  # What the checker needs: the candidate's files, the replaced modules,
  #  what each run must show
  with open(os.path.join(out, "candidate.json"), "w") as f:
    json.dump({"files": candidate, "coverage_problems": coverage,
      "modules": overlays, "runs": dict(("%s_old" %run_label(r),
      r.get("old_fails_with")) for r in change["runs"])}, f, indent = 1)
  timeout = spec["settings"].get("timeout", 3600)
  summary = []
  for run in change["runs"]:
    test_path = os.path.join(modules, run["repo"], run["test"])
    labels = ("new",) if run.get("new_only") else ("old", "new")
    for label in labels:
      name = "%s_%s" %(run_label(run), label)
      run_dir = os.path.join(out, "runs", name)
      os.makedirs(run_dir, exist_ok = True)
      runner = os.path.join(run_dir, "runner.py")
      with open(runner, "w") as f:
        f.write(RUNNER %dict(overlays = overlays if label == "old" else [],
          test = test_path, args = list(run.get("args", [])),
          roots = sorted(set(os.path.join(modules, part["repo"])
            for part in change["parts"])), started = TEST_STARTED,
          real_files = [os.path.realpath(x[2]) for x in overlays],
          module_names = [x[0] for x in overlays],
          is_old = (label == "old")))
      command = [spec["settings"]["python"], runner]
      # In a process group of its own, so that a test stopped at the time
      #  limit is stopped with any processes it started
      p = subprocess.Popen(command, cwd = run_dir, stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT, universal_newlines = True,
        start_new_session = True)
      try:
        output = p.communicate(timeout = timeout)[0]
        code = p.returncode
      except subprocess.TimeoutExpired:
        stop_group(p)
        output = p.communicate()[0] + "\nTIMEOUT: stopped after %d s\n" %(
          timeout)
        code = 124
      with open(os.path.join(out, "runs", name + ".txt"), "w") as f:
        f.write("$ (cd %s && %s)\nexit code: %s\n\n%s" %(run_dir,
          " ".join(command), code, output))
      last = [x for x in output.splitlines() if x.strip() and not
        x.startswith(("LOADED:", "WARNING:"))][-1:] or [""]
      summary.append("%-4s exit %s  %s  last line: %s" %(label, code,
        name, last[0][:150]))
      print(change["id"] + ": " + summary[-1])
  with open(os.path.join(out, "summary.txt"), "w") as f:
    f.write("\n".join(summary) + "\n")

# ---------------------------------------------------------------------------
# scope: every commit of the review interval accounted for

def owners(spec):
  """{commit: (kind, label)}: kind is "change" (label: its number) or
     "other" (label: the other work's name)"""
  own = {}
  for c in spec["changes"]:
    for part in c["parts"]:
      for h in part.get("commits", []):
        own[h] = ("change", c["number"])
  for name, commits in spec.get("other_work", {}).items():
    for h in commits:
      own[h] = ("other", name)
  return own

def lookup(own, h):
  for c, value in own.items():
    if h.startswith(c) or c.startswith(h):
      return value
  return None

def scope(spec):
  own = owners(spec)
  excluded = spec.get("excluded", {})
  lines, problems = [], []
  for repo in spec["settings"]["repositories"]:
    base = spec["baselines"][repo]
    head = git(spec, repo, ["rev-parse", "--short", "HEAD"]).stdout.strip()
    lines.append("== %s: %s..HEAD (%s)" %(repo, base, head))
    log = git(spec, repo, ["log", "--reverse", "--format=%h%x09%an%x09%s",
      "%s..HEAD" %base]).stdout.splitlines()
    for entry in log:
      h, author, subject = entry.split("\t", 2)
      who = lookup(own, h)
      reason = lookup(dict((c, r) for c, r in excluded.items()), h)
      if who and who[0] == "change":
        tag = "change %d" %who[1]
      elif who:
        tag = "other work: %s" %who[1]
      elif reason:
        tag = "excluded: %s" %reason
      elif author != spec["settings"]["author"]:
        tag = "other author (not part of this review)"
      else:
        tag = "NOT ACCOUNTED FOR"
        problems.append("%s %s %s" %(repo, h, subject))
      files = git(spec, repo, ["show", "--name-only", "--format=", h]
        ).stdout.split()
      lines.append("%s  %-16s %-40s %s\n      files: %s" %(h, author[:16],
        tag[:40], subject[:60], " ".join(files)))
    status = git(spec, repo, ["status", "--short"]).stdout.rstrip()
    lines.append("  git status --short:\n%s" %("\n".join(
      "    " + x for x in status.splitlines()) or "    (clean)"))
  for h in own:
    found = False
    for repo in spec["settings"]["repositories"]:
      if git(spec, repo, ["rev-parse", "--verify", "-q", h + "^{commit}"],
          check = False).returncode == 0:
        found = True
    if not found:
      problems.append("commit %s (in the spec) not found" %h)
  lines.append("\nProblems: %s" %("none" if not problems else ""))
  lines.extend("  " + x for x in problems)
  d = os.path.join(spec["folder"], "evidence", "scope")
  os.makedirs(d, exist_ok = True)
  with open(os.path.join(d, "scope.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
  return problems

def unpushed(spec):
  """[(repository, commit, change number, subject)] of this review's
     commits not on the upstream branch, and [(repository, commit, other
     work's name or None, subject)] of the other unpushed commits that the
     same pushes would publish"""
  own = owners(spec)
  ours, other = [], []
  for repo in spec["settings"]["repositories"]:
    log = git(spec, repo, ["log", "--reverse", "--format=%h%x09%s",
      "%s..HEAD" %spec["settings"]["upstream"]]).stdout.splitlines()
    for entry in log:
      h, subject = entry.split("\t", 1)
      who = lookup(own, h)
      if who and who[0] == "change":
        ours.append((repo, h, who[1], subject))
      else:
        other.append((repo, h, who[1] if who else None, subject))
  return ours, other

# ---------------------------------------------------------------------------
# The descriptions (one Markdown file per change; format in REVIEW_SPEC.md)

REQUIRED = ["In short", "Problem", "Fix: how it solves the problem",
  "Essential code", "What the tests show"]
EXPLANATION = ["Problem", "Cause", "Fix: how it solves the problem",
  "Essential code", "What the tests show", "Changes after the review"]
CHECKS = "Other checks and remaining risks"
CHECKS_SHOWN = "What was checked and what remains uncertain"

def read_description(spec, change):
  """(opening block lines, [(section title, text)])"""
  lines = open(os.path.join(spec["folder"], change["description"])
    ).read().splitlines()
  first = 1
  while first < len(lines) and not lines[first].startswith("## "):
    first += 1
  header = [x for x in lines[1:first] if x.strip()]
  sections = []
  for part in re.split(r"(?m)^## ", "\n".join(lines[first:]))[1:]:
    name, _, text = part.partition("\n")
    sections.append((name.strip(), text.strip()))
  return header, sections

def section_text(sections, name):
  for title, text in sections:
    if title.startswith(name):
      return title, text
  return None, None

def in_short(sections, where):
  """The change's two summary lines, (problem, now). The page shows no
     other summary of a change, so every short statement comes from the
     description and says which it is. Without both lines the page is
     not made."""
  t, text = section_text(sections, "In short")
  problem = now = None
  for line in (text or "").splitlines():
    if line.startswith("Problem:"):
      problem = line[len("Problem:"):].strip()
    elif line.startswith("Now:"):
      now = line[len("Now:"):].strip()
  if not problem or not now:
    raise ValueError("%s: its \"In short\" part needs a \"Problem:\" and a "
      "\"Now:\" line" %where)
  return problem, now

def changes_after_review(text, record = False):
  """The bullets of "Changes after the review"; "(record only)" bullets
     only in the evidence, without the marker"""
  if text is None or text.strip().startswith("None"):
    return None
  keep = []
  for item in re.split(r"(?m)^(?=- )", text):
    if "(record only)" in item:
      if not record:
        continue
      item = item.replace("(record only) ", "")
    if item.strip():
      keep.append(item.rstrip())
  if not keep:
    return None
  return "\n".join(keep)

def anchor(k, part = None):
  return "change-%d%s" %(k, "-" + part if part else "")

def link(text, k, part = None):
  return "[%s](#%s)" %(text, anchor(k, part))

def renumber(spec, text):
  """#N references (the full list's numbers) -> links to this page's
     changes, or the name in words of work not on the page"""
  numbers = dict((c["ref"], c["number"]) for c in spec["changes"])
  others = spec.get("others", {})
  def repl(m):
    ref = m.group(0)
    if ref in numbers:
      return link("change %d" %numbers[ref], numbers[ref])
    if ref in others:
      return others[ref]
    return ref
  return re.sub(r"#\d+\b", repl, text)

def commit_lines(spec, header):
  joined = " ".join(x for x in header if not x.startswith("Review priority"))
  parts = []
  for field in re.split(r"\s*\|\s*|\s+(?=Files:)", joined):
    if field.strip():
      parts.append("- " + field.strip().replace("Repo:", "Repository:"))
  return renumber(spec, "\n".join(parts))

# ---------------------------------------------------------------------------
# Evidence in the page: the code, the tests, what they printed

SKIP_FILES = ("run_tests.py",)  # test registration only

def is_test(path):
  return os.path.basename(path).startswith("tst_") or "/regression/" in path

def split_commits(net_diff):
  """[(commit, subject, [(path, diff text)])] from git show output"""
  commits = []
  for block in re.split(r"(?m)^(?=commit [0-9a-f]{7,40}$)", net_diff):
    if not block.strip():
      continue
    m = re.match(r"commit ([0-9a-f]+)", block)
    subject = ""
    for line in block.splitlines()[1:]:
      if line.startswith("    ") and line.strip():
        subject = line.strip()
        break
    files = []
    for part in re.split(r"(?m)^(?=diff --git )", block)[1:]:
      path = part.splitlines()[0].split(" b/", 1)[-1]
      body = [x for x in part.splitlines()
        if not x.startswith(("diff --git", "index ", "--- ", "+++ ",
          "new file mode", "deleted file mode"))]
      files.append((path, "\n".join(body)))
    commits.append((m.group(1)[:10] if m else "?", subject, files))
  return commits

def run_lines(text, n = 8):
  """The last n lines a test printed, without the runner's bookkeeping and
     traceback frames (the final error line is kept)"""
  keep = []
  in_traceback = False
  for x in text.splitlines()[3:]:
    if not x.strip() or x.startswith(("OLD CODE", "LOADED", "WARNING", "$ ",
        "exit code", TEST_STARTED)):
      continue
    if x.startswith("Traceback"):
      in_traceback = True
      continue
    if in_traceback and (x.startswith(" ") or not x.strip("^~ ")):
      continue
    in_traceback = False
    keep.append(x.rstrip()[:200])
  return keep[-n:]

def listed_runs(packet_dir):
  """The runs the packet's generator made (summary.txt), each test's
     old-code run first: [(name, label, exit code)]"""
  runs = []
  for line in open(os.path.join(packet_dir, "summary.txt")).read(
      ).splitlines():
    words = line.split()
    if len(words) > 3:
      runs.append((words[3], words[0], int(words[2])))
  return sorted(runs, key = lambda r: (r[0].rsplit("_", 1)[0], r[1] != "old"))

def evidence_md(spec, change):
  packet_dir = os.path.join(evidence_dir(spec, change), "packet")
  code, tests = [], []
  for commit, subject, files in split_commits(open(os.path.join(packet_dir,
      "net.diff")).read()):
    for path, body in files:
      if os.path.basename(path) in SKIP_FILES:
        continue
      if commit == NOT_COMMITTED:
        source = "not committed"
      else:
        source = "commit %s: %s" %(commit, subject)
      entry = "**%s** (%s)\n\n```diff\n%s\n```\n" %(path, source, body)
      (tests if is_test(path) else code).append(entry)
  out = []
  if code:
    out.append("\n### The full change\n\n" + "\n".join(code))
  if tests:
    out.append("\n### The new and changed tests\n\n" + "\n".join(tests))
  outputs = []
  for name, label, code_ in listed_runs(packet_dir):
    version = ("old code (current minus the change)" if label == "old"
      else "new code (current)")
    text = open(os.path.join(packet_dir, "runs", name + ".txt")).read()
    outputs.append("**%s**, %s: %s\n\n```\n%s\n```\n" %(name.rsplit("_", 1)[0],
      version, "passed" if code_ == 0 else "failed",
      "\n".join(run_lines(text))))
  if outputs:
    out.append("\n### What the tests printed (last lines)\n\n" +
      "\n".join(outputs))
  header, sections = read_description(spec, change)
  t, text = section_text(sections, "Proof")
  if text:
    out.append("\n### The proof in full\n\n%s\n" %renumber(spec, text))
  t, text = section_text(sections, CHECKS)
  if text:
    out.append("\n### %s\n\n%s\n" %(CHECKS_SHOWN, renumber(spec, text)))
  t, text = section_text(sections, "Changes after the review")
  text = changes_after_review(text, record = True)
  if text:
    out.append("\n### Changes after the review\n\n%s\n" %renumber(spec,
      text))
  out.append("\n### Commits and files\n\n%s\n" %commit_lines(spec, header))
  return "".join(out)

# ---------------------------------------------------------------------------
# HTML

STYLE = """
:root {
  --bg: #fbfcfd; --fg: #1b2430; --muted: #5b6676; --line: #d5dbe3;
  --panel: #eef2f6; --accent: #1f5fa8; --add: #e6f3ea; --del: #f9e8e8;
  --font-body: "IBM Plex Sans", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
  --bar-h: 3.4rem; /* replaced by the bar's measured height */
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #14181d; --fg: #e3e8ee; --muted: #9aa5b3; --line: #2e3742;
  --panel: #1d232b; --accent: #8bb8f2; --add: #17301f; --del: #3a1d1f;
  color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #14181d; --fg: #e3e8ee; --muted: #9aa5b3; --line: #2e3742;
  --panel: #1d232b; --accent: #8bb8f2; --add: #17301f; --del: #3a1d1f;
  color-scheme: dark; }
body { background: var(--bg); color: var(--fg); margin: 0;
  font: 15px/1.55 var(--font-body);
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }
body::before { content: ""; position: fixed; inset: 0 0 auto;
  height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--bg); }
main { max-width: 880px; margin: 0 auto; padding-block: 28px 72px; min-width: 0; }
h1 { font-size: 1.7rem; line-height: 1.25; margin: 0 0 0.6rem; text-wrap: balance; }
h2 { font-size: 1.25rem; line-height: 1.3; margin: 2.2rem 0 0.6rem;
  padding-top: 0.9rem; border-top: 1px solid var(--line); text-wrap: balance; }
h3 { font-size: 1.02rem; margin: 1.5rem 0 0.4rem; }
[id] { scroll-margin-top: calc(var(--bar-h) + 10px); }
p, li { max-width: 72ch; }
a { color: var(--accent); text-underline-offset: 2px; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
table { border-collapse: collapse; margin: 0.8rem 0; font-size: 0.92rem;
  display: block; overflow-x: auto; max-width: 100%; }
th, td { border: 1px solid var(--line); padding: 6px 9px; text-align: left;
  vertical-align: top; }
th { background: var(--panel); font-weight: 600; }
code { background: var(--panel); padding: 1px 4px; border-radius: 3px;
  font: 0.86em/1.4 var(--font-mono); }
pre { background: var(--panel); padding: 10px 12px; border-radius: 6px;
  overflow-x: auto; max-width: 100%; font-size: 0.9rem; line-height: 1.45; }
pre code { padding: 0; background: none; font-size: inherit; }
pre .add { background: var(--add); display: inline-block; min-width: 100%; }
pre .del { background: var(--del); display: inline-block; min-width: 100%; }
hr { border: 0; border-top: 2px solid var(--line); margin: 2.4rem 0 0; }
.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5;
  background: var(--bg); border-bottom: 1px solid var(--line);
  margin-left: calc(-1 * max(16px, env(safe-area-inset-left, 0px)));
  margin-right: calc(-1 * max(16px, env(safe-area-inset-right, 0px))); }
.bar-inner { max-width: 880px; margin: 0 auto; display: flex; flex-wrap: nowrap;
  align-items: center; gap: 6px 10px; min-height: 2.6rem; padding-block: 6px;
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.bar .where { font-weight: 600; margin-right: auto; min-width: 0; flex: 1 1 auto;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar button, .bar select { flex: none; font: 0.9rem/1.2 var(--font-body);
  color: var(--fg); background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 5px 9px; cursor: pointer; }
.bar button:disabled { opacity: 0.45; cursor: default; }
.bar button[aria-current="true"] { background: var(--accent); color: var(--bg);
  border-color: var(--accent); }
.bar button:focus-visible, .bar select:focus-visible,
summary:focus-visible, .close-evidence:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }
.bar .changes { display: flex; flex-wrap: wrap; gap: 6px; }
.bar select { display: none; }
@media (max-width: 700px) {
  .bar .changes { display: none; }
  .bar select { display: inline-block; max-width: 9.5rem; } }
details.evidence { margin: 1.2rem 0 0.4rem; border: 1px solid var(--line);
  border-radius: 8px; background: var(--bg); }
details.evidence > summary { cursor: pointer; padding: 10px 14px;
  font-weight: 600; color: var(--accent); list-style-position: inside; }
details.evidence[open] > summary { border-bottom: 1px solid var(--line); }
.evidence-body { padding: 4px 14px 14px; min-width: 0; }
.close-evidence { font: 0.9rem/1.2 var(--font-body); color: var(--fg);
  background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: 5px 10px; cursor: pointer; margin-top: 10px; }
@media (max-width: 700px) {
  table.stack, table.stack tbody, table.stack tr, table.stack td {
    display: block; width: 100%; box-sizing: border-box; }
  table.stack { overflow: visible; border: 0; }
  table.stack thead { display: none; }
  table.stack tr { border: 1px solid var(--line); border-radius: 6px;
    margin: 0 0 10px; padding: 6px 10px; }
  table.stack td { border: 0; padding: 3px 0; }
  table.stack td::before { content: attr(data-label); display: block;
    font-size: 0.8rem; color: var(--muted); } }
main p, main li, main td, main strong { overflow-wrap: anywhere; }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
  'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600'
  '&display=swap">')

SCRIPT = """
(function () {
  // Back works from the page's own list of places (the browser's history
  //  is not used: the viewer's frame may not give it to the page); the
  //  address only follows along (replaceState), for reloads and copying
  var stack = [];
  var root = document.documentElement;
  var bar = document.querySelector(".bar");
  var back = document.getElementById("nav-back");
  var where = document.getElementById("nav-where");
  var select = document.getElementById("nav-select");
  var changes = Array.prototype.slice.call(
    document.querySelectorAll("section.change"));
  var buttons = Array.prototype.slice.call(
    document.querySelectorAll(".bar .changes button"));
  function measureBar() {  // headings land just below the bar
    root.style.setProperty("--bar-h", bar.getBoundingClientRect().height + "px");
  }
  function openIds() {
    return Array.prototype.slice.call(
      document.querySelectorAll("details.evidence[open]")).map(
      function (d) { return d.id; });
  }
  function setHash(hash) {
    try { history.replaceState(null, "", hash || location.pathname +
      location.search); } catch (e) {}
  }
  function remember(opened) {
    stack.push({y: window.scrollY, open: openIds(), hash: location.hash,
      opened: opened || null});
    back.disabled = false;
  }
  function restore(s) {
    document.querySelectorAll("details.evidence").forEach(function (d) {
      d.open = s.open.indexOf(d.id) >= 0;
    });
    window.scrollTo(0, s.y);
    setHash(s.hash);
    track();
  }
  function goBack() {
    var s = stack.pop();
    back.disabled = stack.length === 0;
    if (s) restore(s);
  }
  function openAncestors(el) {
    var d = el.closest("details");
    while (d) { d.open = true; d = d.parentElement.closest("details"); }
  }
  function go(id, remembering) {
    var target = document.getElementById(id);
    if (!target) return;
    if (remembering !== false) remember();
    openAncestors(target);
    measureBar();
    if (id === "top") {
      window.scrollTo(0, 0);
    } else {
      target.scrollIntoView({block: "start"});
    }
    setHash("#" + id);
    track();
  }
  // Fold evidence; if opening it was the last step, take that step back
  function closeEvidence(d) {
    var top = stack[stack.length - 1];
    if (top && top.opened === d.id) {
      goBack();
      d.open = false;
    } else {
      d.open = false;
      d.querySelector("summary").scrollIntoView({block: "nearest"});
    }
    track();
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (a) {
      var href = a.getAttribute("href") || "";
      if (href.charAt(0) === "#" && href.length > 1) {
        e.preventDefault();
        go(href.slice(1));
      }
      return;
    }
    var s = e.target.closest("details.evidence > summary");
    if (s) {
      var d = s.parentElement;
      if (d.open) { e.preventDefault(); closeEvidence(d); }
      else { remember(d.id); }
      return;
    }
    var c = e.target.closest(".close-evidence");
    if (c) closeEvidence(c.closest("details"));
  });
  back.addEventListener("click", goBack);
  document.getElementById("nav-top").addEventListener("click",
    function () { go("top"); });
  buttons.forEach(function (b) {
    b.addEventListener("click", function () { go(b.dataset.target); });
  });
  select.addEventListener("change", function () {
    if (select.value) go(select.value);
  });
  var ticking = false;
  function track() {  // which change is on screen
    var bottom = bar.getBoundingClientRect().bottom;
    var current = null;
    changes.forEach(function (sec, i) {
      if (sec.getBoundingClientRect().top <= bottom + 12) current = i;
    });
    var narrow = window.matchMedia("(max-width: 700px)").matches;
    where.textContent = current === null ? where.dataset.overview :
      narrow ? (current + 1) + " of " + changes.length :
      "Change " + (current + 1) + " of " + changes.length + ": " +
      buttons[current].dataset.name;
    buttons.forEach(function (b, i) {
      b.setAttribute("aria-current", i === current ? "true" : "false");
    });
    select.value = current === null ? "" : changes[current].id;
  }
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () { ticking = false; track(); });
  });
  window.addEventListener("resize", function () { measureBar(); track(); });
  window.addEventListener("load", function () {  // #change-3 opens there
    measureBar();
    var id = (location.hash || "").slice(1);
    if (id) go(id, false);
    track();
  });
  measureBar();
  back.disabled = true;
  track();
})();
"""

# The text that goes through Markdown comes from descriptions, the outside
#  review and test output, so it is not trusted. Python-Markdown is used
#  with only the tables and fenced_code extensions, and in this way:
#  - raw HTML in the text is escaped (its html_block and html parts are
#    switched off);
#  - attr_list is not used, so no text can add attributes; and where
#    fenced_code reads a code block's {...} header, only its first class is
#    kept, as the language (fenced_code would otherwise take an id and
#    further classes from it);
#  - the page's own anchors (#top, #review, ...) are made by the page, not
#    by Markdown;
#  - a last pass over Markdown's element tree keeps a link only to an
#    anchor on the page, an http(s) address with a host, or a plain mailto
#    address (others keep their text), turns an image into its alt text,
#    and removes any attribute but those below. Code blocks are the one
#    part fenced_code makes outside that tree: their text is escaped and
#    their only attribute is the language class.
SAFE_LINK = re.compile(r"#[\w.:-]*|https?://[A-Za-z0-9][A-Za-z0-9.-]*"
  r"(:\d+)?([/?#][^\s\\]*)?|mailto:[^\s\\/:]+@[A-Za-z0-9.-]+", re.I)
SAFE_ATTRIBUTES = {"a": {"href": SAFE_LINK},
  "th": {"style": re.compile(r"text-align: (left|right|center);")},
  "td": {"style": re.compile(r"text-align: (left|right|center);")}}
LANGUAGE = re.compile(r"[\w+-]+")

def markdown_text(text, extensions = ()):
  """Markdown to HTML, for untrusted text (above)"""
  try:
    import markdown
    from markdown.treeprocessors import Treeprocessor
  except ImportError:
    raise ImportError("review_pages.py needs the Python-Markdown package "
      "(import markdown), and this Python (%s) does not have it: run it with "
      "a Python that has it (for PHENIX: libtbx.python)" %sys.executable)
  class Safe(Treeprocessor):
    def run(self, root):
      for element in root.iter():
        allowed = SAFE_ATTRIBUTES.get(element.tag, {})
        if element.tag == "img":
          element.tag, element.text = "span", element.get("alt", "")
        elif element.tag == "a" and not SAFE_LINK.fullmatch(
            element.get("href", "")):
          element.tag = "span"
        for name in list(element.attrib):
          if element.tag == "span" or name not in allowed or \
              not allowed[name].fullmatch(element.get(name)):
            del element.attrib[name]
  def language_only(attrs):  # (id, classes, options) from a code header
    classes = [v for k, v in attrs if k == "."][:1]
    return "", [x for x in classes if LANGUAGE.fullmatch(x)], {}
  md = markdown.Markdown(extensions = list(extensions))
  if "fenced_code" in extensions:  # fails if the step has another name
    md.preprocessors["fenced_code_block"].handle_attrs = language_only
  md.preprocessors.deregister("html_block")
  md.inlinePatterns.deregister("html")
  md.treeprocessors.register(Safe(md), "safe", 0)  # after all the others
  try:
    return md.convert(text)
  except RecursionError:  # nested too deeply for Python-Markdown: as text
    return "<pre><code>%s\n</code></pre>" %html.escape(text)

def heading(level, text, anchor):
  """A heading with one of the page's own anchors"""
  return '<h%d id="%s">%s</h%d>' %(level, anchor, html.escape(text), level)

def convert(text):
  body = markdown_text(text, ["tables", "fenced_code"])
  def block(m):  # colour added and removed lines in diffs
    out = []
    for x in m.group(2).split("\n"):
      if x.startswith("+"):
        out.append('<span class="add">%s</span>' %x)
      elif x.startswith("-"):
        out.append('<span class="del">%s</span>' %x)
      else:
        out.append(x)
    return m.group(1) + "\n".join(out) + m.group(3)
  return re.sub(r'(<pre><code class="language-diff">)(.*?)(</code></pre>)',
    block, body, flags = re.S)

def cell(text):
  h = markdown_text(text)
  if h.startswith("<p>") and h.endswith("</p>") and h.count("<p>") == 1:
    h = h[3:-4]
  return h

def table(css_class, headers, rows):
  """A table whose cells carry their column names, so that on a narrow
     screen each row shows as a small labelled block"""
  out = ['<table class="stack %s"><thead><tr>' %css_class]
  out.extend("<th>%s</th>" %h for h in headers)
  out.append("</tr></thead><tbody>")
  for row in rows:
    out.append("<tr>" + "".join('<td data-label="%s">%s</td>' %(h, cell(c))
      for h, c in zip(headers, row)) + "</tr>")
  out.append("</tbody></table>")
  return "".join(out)

# ---------------------------------------------------------------------------
# page: the developer's one page

def review_md(spec):
  """The outside review's heading and summary; a job without an outside
     review says so"""
  if "review_summary" in spec:
    summary = spec["review_summary"]
  else:
    summary = ("No outside review was run for this job; the report offers "
      "one.")
  return "<hr />" + heading(2, "The outside review", "review") + convert(
    summary)

def page(spec):
  ours, other = unpushed(spec)
  n_changes = len(spec["changes"])
  body = []
  # 1. A very brief summary: the result and what remains to do
  title = heading(1, spec["title"], "top")
  top = "%s\n" %spec["result"]
  n_uncommitted = len([c for c in spec["changes"] if is_uncommitted(c)])
  n_saved = len([c for c in spec["changes"] if c.get("state") == "saved"])
  if n_saved:
    top += ("\n**Still to do:** the fixes are saved as patches, not "
      "applied. Choose which to apply; they are applied together and their "
      "tests rerun on the combined code before anything is committed. After "
      "%s passes, push.\n" %spec["settings"]["full_test"])
  elif n_uncommitted:
    top += ("\n**Still to do:** commit %s (not committed yet); then, after "
      "%s passes, push. The commits a push would publish are listed [at the "
      "end of this page](#commits-to-push).\n" %("the change" if
      n_uncommitted == 1 else "%d changes" %n_uncommitted,
      spec["settings"]["full_test"]))
  elif ours or other:
    text = ("\n**Still to do:** after %s passes, push %d commits from "
      "these changes" %(spec["settings"]["full_test"], len(ours)))
    if other:
      text += ("; the same pushes also publish %d commits from other work "
        "(see the [complete list](#commits-to-push))" %len(other))
    top += text + ".\n"
  top += "\n## The changes\n"
  body.append(title + convert(top))
  # 2. The changes: problem and result, from each description
  rows = []
  for c in spec["changes"]:
    header, sections = read_description(spec, c)
    problem, now = in_short(sections, c["description"])
    if c.get("state") == "saved":
      state = "saved, not applied"
    elif is_uncommitted(c):
      state = "not committed"
    else:
      state = str(len([x for x in ours if x[2] == c["number"]]))
    rows.append((link("%d. %s" %(c["number"], c["name"]), c["number"]),
      renumber(spec, problem), renumber(spec, now), state))
  body.append(table("changes", ["Change", "Problem", "Now",
    "Status" if n_uncommitted else "Commits not yet pushed"], rows))
  # 3. Each change explained, its evidence folded underneath
  for c in spec["changes"]:
    k = c["number"]
    header, sections = read_description(spec, c)
    md = [convert("## %d. %s" %(k, c["name"]))]  # HTML, in order
    for name in EXPLANATION:
      t, text = section_text(sections, name)
      if text is None:
        continue
      if name == "Changes after the review":
        text = changes_after_review(text)
        if text is None:
          continue
        md.append(heading(3, "Changes after the review", anchor(k, "after")) +
          convert(renumber(spec, text)))
        continue
      md.append(convert("\n### %s\n\n%s\n" %(name if name.startswith("Fix")
        else t, renumber(spec, text))))
    body.append('<section class="change" id="%s">%s<details class="evidence" '
      'id="%s"><summary>Show the full change, tests and results</summary>'
      '<div class="evidence-body">%s<button type="button" '
      'class="close-evidence">Close the evidence</button></div></details>'
      '</section>\n' %(anchor(k), "".join(md), anchor(k, "evidence"),
      convert(evidence_md(spec, c))))
  # 4. The AI analysis: the outside review and how the tests were run
  body.append(review_md(spec))
  rows = [(f["found"], ", ".join(link("change %d" %k, k, "after")
    for k in f["changes"]), f["done"]) for f in spec.get("findings", [])]
  if rows:
    body.append(table("findings", ["Found", "Where", "What was done"], rows))
  body.append(convert("\n### How the changes were tested\n\n%s\n" %
    spec["old_code_note"]))
  # 5. The commits to push
  body.append("<hr />" + heading(2, "Commits to push", "commits-to-push") +
    convert("Pushing these repositories publishes all of the commits below."))
  if ours:
    body.append(convert("\n### From these %s (%d)\n" %("changes" if
      n_changes > 1 else "the change", len(ours))))
    body.append(table("commits", ["Repository", "Commit", "Change", "Subject"],
      [(repo, "`%s`" %h, link("change %d" %k, k), s) for repo, h, k, s in ours]))
  if other:
    body.append(convert("\n### From other work, carried by the same pushes "
      "(%d)\n" %len(other)))
    body.append(table("commits", ["Repository", "Commit", "Work", "Subject"],
      [(repo, "`%s`" %h, name or "not a change on this page", s)
      for repo, h, name, s in other]))
  body.append(convert("\nFound with `git log %s..HEAD` in each repository "
    "when this page was made.\n" %spec["settings"]["upstream"]))
  shorts = [c["short"] for c in spec["changes"]]
  buttons = "".join('<button type="button" data-target="%s" data-name="%s" '
    'aria-current="false">%d %s</button>' %(anchor(k), html.escape(s), k,
    html.escape(s)) for k, s in enumerate(shorts, 1))
  options = "".join('<option value="%s">%d %s</option>' %(anchor(k), k,
    html.escape(s)) for k, s in enumerate(shorts, 1))
  bar = ('<nav class="bar" aria-label="Page navigation"><div class="bar-inner">'
    '<span class="where" id="nav-where" data-overview="Overview">Overview'
    '</span><button type="button" id="nav-back" disabled>Back</button>'
    '<button type="button" id="nav-top">Top</button><span class="changes">%s'
    '</span><select id="nav-select" aria-label="Go to a change"><option '
    'value="">Changes</option>%s</select></div></nav>' %(buttons, options))
  text = ("<title>%s</title>\n<meta name=\"claude:viewport-fit-sides\" "
    "content=\"cover\">\n%s\n<style>%s</style>\n%s\n<main>%s</main>\n"
    "<script>%s</script>\n" %(html.escape(spec["page_title"]), FONTS, STYLE,
    bar, "".join(body), SCRIPT))
  path = os.path.join(out_dir(spec), "page.html")
  with open(path, "w") as f:
    f.write(text)
  return path

# ---------------------------------------------------------------------------
# request: the outside reviewer's packet (task first)

REQUEST_HEAD = """# Code review of %(what)s

**Your task: review %(these)s.** Do not review the presentation format or
the review process. Answer with one section per change, in order.

## For each change

Work out the intended behaviour yourself from the problem and the code
before reading the description. Then:

- mark each important claim: supported, partly supported, unsupported,
  or not verifiable from the packet (list only those not "supported");
- check that every short summary (its "Problem:" and "Now:" lines, and
  any table built from them) says what its label says and agrees with
  the full description;
- answer under three headings:
  1. **Logic and evidence findings:** code defects, questionable
     assertions, missing tests; investigate them yourself and recommend
     a correction.
  2. **Decisions for the developer:** only genuine choices about
     scientific intent or expected behaviour that you cannot settle
     yourself, and whose answer changes what is done. Each gives the
     decision, why you cannot settle it, your recommended answer, and
     what will be done for each answer.
  3. **Not checked:** limits that do not affect the decision, briefly.
- give a verdict: use as is, fix first, or cannot determine.
%(interactions)s
"Current minus the change" is the current code with only that change's
commits reversed, loaded in place of the current modules. You cannot run
the code; say which conclusions depend on the saved outputs being
genuine. Keep the answer to about three pages; a change with nothing to
report needs only its verdict.
"""

def task_of(spec, change):
  """The developer's request for this change, as they gave it"""
  return change.get("task") or spec.get("task")

LARGE_REQUEST = 200000  # bytes: about 50,000 tokens

def request(spec, wanted = None):
  """The reviewer's packet; wanted: only these change ids (a second review)"""
  changes = [c for c in spec["changes"] if not wanted or c["id"] in wanted]
  n = len(changes)
  parts = [REQUEST_HEAD %dict(
    what = "%d changes" %n if n > 1 else "one change",
    these = "these %d changes" %n if n > 1 else "this change",
    interactions = ("\nAlso look for interactions between the changes (files "
      "or functions they share).\n" if n > 1 else ""))]
  if spec.get("task"):
    parts.append("\n## The developer's request (as given)\n\n%s\n" %
      spec["task"])
  if wanted:
    parts.append("\nThis is a second review, after the corrections listed "
      "under \"Changes after the review\".\n")
  scope_file = os.path.join(spec["folder"], "evidence", "scope", "scope.txt")
  if os.path.exists(scope_file) and not wanted:
    lines = [x for x in open(scope_file).read().splitlines()
      if not x.startswith("      files:")]
    parts.append("\n## Scope check of the review interval (generated)\n\n"
      "```\n%s\n```\n" %"\n".join(lines))
  for c in changes:
    p = os.path.join(evidence_dir(spec, c), "packet")
    text = open(os.path.join(spec["folder"], c["description"])).read()
    text = text.replace("\n## ", "\n### ").replace("# ", "## Change %d: " %
      c["number"], 1)
    title, _, rest = text.partition("\n")
    parts.append("\n---\n\n" + title + "\n")
    if c.get("task"):
      parts.append("\n### The developer's request (as given)\n\n%s\n" %
        c["task"])
    parts.append(rest)
    parts.append("\n### Generated evidence\n\n#### Commits, checkouts, build\n"
      "```\n%s```\n#### Files changed\n```\n%s```\n"
      "#### Test runs (summary)\n```\n%s```\n" %(
      open(os.path.join(p, "base_head.txt")).read(),
      open(os.path.join(p, "changed_files.txt")).read(),
      open(os.path.join(p, "summary.txt")).read()))
    for name, label, code_ in listed_runs(p):
      t = open(os.path.join(p, "runs", name + ".txt")).read()
      tl = [x for x in t.splitlines() if x.strip()]
      keep = tl[:2] + ["..."] + [x for x in tl if x.startswith(("OLD CODE",
        "LOADED", "WARNING", TEST_STARTED))] + ["..."] + [x[:220]
        for x in tl[-10:] if not x.startswith(("LOADED", "WARNING"))]
      parts.append("#### %s: first lines, load records, last lines\n```\n%s\n"
        "```\n" %(name, "\n".join(keep)))
    parts.append("#### Full diff of each commit (test files: diffs only; ask "
      "for a whole file if you need it)\n```diff\n%s```\n" %open(
      os.path.join(p, "net.diff")).read())
  name = "request.md" if not wanted else "request_%s.md" %"_".join(wanted)
  path = os.path.join(out_dir(spec), name)
  text = "".join(parts)
  with open(path, "w") as f:
    f.write(text)
  if len(text) > LARGE_REQUEST:
    print("NOTE: the packet is %d KB, large for one review; review fewer "
      "changes at a time" %(len(text) // 1000))
  return path

# ---------------------------------------------------------------------------
# check: refuse an incomplete or inconsistent page

WRONG_REASON = (r"(ModuleNotFoundError|ImportError|SyntaxError|"
  r"IndentationError|NameError|TIMEOUT)\b")

def loaded(text):
  """{module name: file} from a run's LOADED lines"""
  out = {}
  for x in text.splitlines():
    if x.startswith("LOADED: "):
      name, _, f = x[len("LOADED: "):].partition(" from ")
      out[name] = f
  return out

def run_problems(spec, change, p):
  """Why the runs of one change might not prove it"""
  problems = []
  info_file = os.path.join(p, "candidate.json")
  if not os.path.exists(info_file):
    return ["the packet is from an older tool (run: packet)"]
  info = json.load(open(info_file))
  problems.extend(info["coverage_problems"])
  # The candidate tested is the one in place now (a saved batch candidate
  #  is set aside, so it is not compared)
  if change.get("state") != "saved":
    for f, h in sorted(info["files"].items()):
      real = os.path.join(spec["settings"]["modules"], f)
      if (sha256(real) if os.path.exists(real) else None) != h:
        problems.append("%s changed after the packet was made (run: packet)"
          %f)
  else:
    # The saved candidate (the job folder's after/ copies, which the batch
    #  compares with its patches) is the one tested
    for part in change["parts"]:
      if not part.get("uncommitted"):
        continue
      job, repo_id, recorded = job_record(part)
      if recorded is None or "after: complete" not in open(os.path.join(
          job, "JOB.txt")).read():
        problems.append("%s: the saved candidate has no complete after/ "
          "copies in %s" %(part["repo"], job))
        continue
      for f, h in sorted(info["files"].items()):
        if not f.startswith(part["repo"] + "/"):
          continue
        saved = os.path.join(job, "after", repo_id, f[len(part["repo"]) + 1:])
        if (sha256(saved) if os.path.exists(saved) else None) != h:
          problems.append("%s: the saved candidate differs from the version "
            "tested (run packet with it applied)" %f)
  runs = listed_runs(p)
  names = set(r[0] for r in runs)
  proving = 0
  imported = set()
  for name, label, code_ in runs:
    t = open(os.path.join(p, "runs", name + ".txt")).read()
    test = name.rsplit("_", 1)[0]
    found = loaded(t)
    if label == "new":
      if code_ != 0:
        problems.append("%s failed on the current code" %name)
      for m, old, real in info["modules"]:
        f = found.get(m, "None")
        if f == "None":
          continue
        imported.add(m)
        if os.path.realpath(f) != os.path.realpath(real):
          problems.append("%s loaded %s from %s, not from the checkout (%s)"
            %(name, m, f, real))
      continue
    # An old-code run proves something only if the test itself ran, with
    #  every replacement in place, and failed in the way expected
    if test + "_new" not in names:
      problems.append("%s has no run on the current code" %name)
    if code_ == 0:
      problems.append("%s passed on the old code (it must fail)" %name)
      continue
    before, started, after = t.partition("\n" + TEST_STARTED + "\n")
    if not started:
      problems.append("%s failed before the test started (loading the old "
        "code): %s" %(name, (run_lines(t, 1) or [""])[0][:80]))
      continue
    last = [x for x in after.splitlines() if x.strip() and not x.startswith(
      ("LOADED:", "WARNING:"))][-1:] or [""]
    if re.match(WRONG_REASON, last[0]):
      problems.append("%s failed on the old code for the wrong reason (%s), "
        "not on the test" %(name, last[0][:80]))
    if "\nWARNING:" in t:
      problems.append("%s loaded a current file in the old-code run" %name)
    for m, old, real in info["modules"]:
      if os.path.realpath(found.get(m, "None")) != os.path.realpath(old):
        problems.append("%s did not use the old version of %s" %(name, m))
    expected = info["runs"].get(name)
    if expected and re.match(r"^\s*\w*(Error|Exception|Failure)?:?\s*$",
        expected):
      problems.append("%s: old_fails_with \"%s\" is too general; give the "
        "assertion message or diagnostic" %(name, expected))
    elif expected:
      if expected not in after:
        problems.append("%s did not fail with the expected \"%s\"" %(name,
          expected))
      else:
        proving += 1
  if not proving:
    problems.append("no proving run: a test run on the old and the current "
      "code, with the failure it must show on the old code (old_fails_with)")
  for m, old, real in info["modules"]:
    if m not in imported:
      problems.append("no test imports %s on the current code" %m)
  return problems

SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|"
  r"gh[pousr]_[A-Za-z0-9]{30,}|xox[abpr]-[A-Za-z0-9-]{10,}|"
  r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
  r"(api[_-]?key|token|password|passwd|secret)[\"']?\s*[:=]\s*[\"']"
  r"[A-Za-z0-9_\-/+=.]{12,}[\"'])", re.I)

def secrets(text, where, allowed = ()):
  """Something that looks like a key or password in what is handed over
     (allowed: text the agent has checked is not one, such as a test's
     dummy value)"""
  out = []
  for k, line in enumerate(text.splitlines(), 1):
    found = [m for m in SECRET.finditer(line)
      if not [a for a in allowed if a in m.group(0)]]
    for m in found[:1]:
      out.append("%s line %d: looks like a key or password (%s...); remove "
        "it, and say what was removed" %(where, k, m.group(0)[:6]))
  return out

def check(spec, before_review = False):
  """Problems that stop the review (before_review: everything except the
     developer's page, which is made after the review) or the page"""
  problems = []
  for c in spec["changes"]:
    where = "change %d (%s)" %(c["number"], c["description"])
    try:
      header, sections = read_description(spec, c)
    except IOError:
      problems.append("%s: description not found" %where)
      continue
    for name in REQUIRED:
      if section_text(sections, name)[1] is None:
        problems.append("%s: no \"%s\" section" %(where, name))
    try:
      in_short(sections, where)
    except ValueError as e:
      problems.append(str(e))
    if not c.get("short"):
      problems.append("%s: no short name for the bar" %where)
    p = os.path.join(evidence_dir(spec, c), "packet")
    if not os.path.exists(os.path.join(p, "summary.txt")):
      problems.append("%s: no evidence packet (run: packet)" %where)
      continue
    if not task_of(spec, c):
      problems.append("%s: no developer's request (\"task\")" %where)
    problems.extend(where + ": " + x for x in run_problems(spec, c, p))
  scope_file = os.path.join(spec["folder"], "evidence", "scope", "scope.txt")
  if not os.path.exists(scope_file):
    problems.append("no scope check (run: scope)")
  elif "Problems: none" not in open(scope_file).read():
    problems.append("the scope check found problems (evidence/scope/scope.txt)")
  for name in sorted(os.listdir(out_dir(spec))):
    if name.startswith("request") and name.endswith(".md"):
      problems.extend(secrets(open(os.path.join(out_dir(spec), name)).read(),
        name, spec.get("not_secret", [])))
  if before_review:
    return problems
  # A page without an outside review only for a job that said it needs none
  if "review_summary" not in spec:
    if spec.get("triggers") != []:
      problems.append("no review_summary: a job without an outside review "
        "must give \"triggers\": [] (triggers: %s)" %spec.get("triggers"))
  elif not isinstance(spec["review_summary"], str) or \
      not spec["review_summary"].strip():
    problems.append("an empty review_summary (leave it out when there was "
      "no outside review)")
  path = os.path.join(out_dir(spec), "page.html")
  if os.path.exists(path):
    t = open(path).read()
    problems.extend(secrets(t, "page", spec.get("not_secret", [])))
    # Only the page's own script and links
    if t.count("<script") != 1:
      problems.append("page: %d scripts (only its own is allowed)" %
        t.count("<script"))
    if re.search(r"<[^>]+\son[a-z]+\s*=", t) or re.search(
        r"(href|src)\s*=\s*[\"']?\s*(javascript|data):", t, re.I):
      problems.append("page: an event handler or a javascript: link")
    ids = re.findall(r'id="([^"]+)"', t)
    for h in sorted(set(re.findall(r'href="#([^"]+)"', t))):
      if h not in ids:
        problems.append("page: link to #%s has no target" %h)
    dup = sorted(set(i for i in ids if ids.count(i) > 1))
    if dup:
      problems.append("page: duplicate ids %s" %", ".join(dup))
    # Each change's section holds only that change: its explanation, then
    #  its evidence, and no other part of the page
    for m in re.finditer(r'<section class="change" id="(change-\d+)">(.*?)'
        r'</section>', t, re.S):
      inside = m.group(2)
      for other in ("review", "commits-to-push"):
        if 'id="%s"' %other in inside:
          problems.append("page: the #%s part is inside %s" %(other,
            m.group(1)))
      if 'id="%s-evidence"' %m.group(1) not in inside:
        problems.append("page: %s has no evidence" %m.group(1))
    for name in ("review", "commits-to-push"):
      if 'id="%s"' %name not in t:
        problems.append("page: no #%s part" %name)
  else:
    problems.append("no page (run: page)")
  return problems

# ---------------------------------------------------------------------------
# navtest: click through the page's navigation in headless Chrome

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def navtest(spec):
  here = os.path.dirname(os.path.abspath(__file__))
  test = open(os.path.join(here, "nav_test_script.html")).read()
  page_text = open(os.path.join(out_dir(spec), "page.html")).read()
  wrapped = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<style>:root{color-scheme:light}body{margin:0}</style>' + page_text +
    test + "</html>")
  path = os.path.join(out_dir(spec), "navtest.html")
  with open(path, "w") as f:
    f.write(wrapped)
  if not os.path.exists(CHROME):
    return ["navtest: Google Chrome not found; navigation not tested"]
  results = []
  for size in ("1280,900", "700,900"):
    p = subprocess.run([CHROME, "--headless=new", "--disable-gpu",
      "--user-data-dir=" + os.path.join(out_dir(spec), "chrome-profile"),
      "--window-size=" + size, "--virtual-time-budget=20000", "--dump-dom",
      "file://" + path], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL,
      universal_newlines = True)
    m = re.search(r'data-navtest="([^"]*)"', p.stdout)
    verdict = html.unescape(m.group(1)) if m else "no result"
    print("navtest %s: %s" %(size, verdict.split(" || ")[0]))
    if not verdict.startswith("ALL PASSED"):
      results.append("navtest %s: %s" %(size, verdict))
  return results

# ---------------------------------------------------------------------------

def main(argv):
  what, folder = argv[0], argv[1]
  spec = load(folder)
  if what == "packet":
    wanted = argv[2:]
    for c in spec["changes"]:
      if not wanted or c["id"] in wanted:
        packet(spec, c)
  elif what == "scope":
    problems = scope(spec)
    print("scope: %s" %("no problems" if not problems else
      "; ".join(problems)))
  elif what == "request":
    print(request(spec, argv[2:]))
  elif what == "page":
    print(page(spec))
  elif what == "check":
    problems = check(spec, before_review = "--before-review" in argv[2:])
    for x in problems:
      print("PROBLEM: " + x)
    print("check: %s" %("passed" if not problems else "%d problems" %len(
      problems)))
    return 1 if problems else 0
  elif what == "navtest":
    problems = navtest(spec)
    for x in problems:
      print("PROBLEM: " + x)
    return 1 if problems else 0
  else:
    raise SystemExit(__doc__)
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
