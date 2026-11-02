"""Tests of review_pages.py check (standard library only).

A small review folder that is complete must pass; each broken version must
be refused for its own reason. Run: python3 tst_review_pages.py
"""
import json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import review_pages

DESCRIPTION = """# #1: The thing works

Repo: demo | Commit: abc1234 | Status: local

## In short
Problem: The thing failed on empty input.
Now: The thing returns an empty result for empty input.

## Problem
It failed.

## Fix: how it solves the problem
It checks for empty input first.

## Essential code
```diff
+  if not x: return []
```

## What the tests show
- **Test:** empty input.
- **Old code:** failed.
- **New code:** passed.
"""

PAGE = """<nav class="bar"></nav><main><h1 id="top">Demo</h1>
<a href="#change-1">1. The thing</a>
<section class="change" id="change-1"><h2>1. The thing</h2>
<details class="evidence" id="change-1-evidence"><summary>Show</summary></details>
</section>
<h2 id="review">The outside review</h2>
<h2 id="commits-to-push">Commits to push</h2></main><script></script>"""

def run_text(code, body, module_file):
  return "$ run\nexit code: %d\n\n%s\nLOADED: demo.thing from %s\n" %(code,
    body, module_file)

def make_folder(description = DESCRIPTION, page = PAGE, scope_ok = True,
    task = "Make the thing work on empty input.",
    old_exit = 1, old_body = None, new_exit = 0, new_loaded = None,
    old_loaded = None, warning = False, expected = "AssertionError: 7/3",
    new_run = True, coverage = (), edit_after = False, request = "",
    saved = None, change_task = None):
  folder = tempfile.mkdtemp()
  modules = os.path.join(folder, "modules")
  real = os.path.join(modules, "demo", "demo", "thing.py")
  os.makedirs(os.path.dirname(real))
  open(real, "w").write("def thing(x):\n  return x\n")
  packet = os.path.join(folder, "evidence", "01_thing", "packet")
  old = os.path.join(packet, "old", "demo", "demo", "thing.py")
  os.makedirs(os.path.dirname(old))
  open(old, "w").write("def thing(x):\n  return x[0]\n")
  spec = {"settings": {"modules": modules, "python": "python3",
      "repositories": ["demo"], "author": "me"},
    "title": "One change reviewed", "page_title": "One Change Reviewed",
    "result": "Accepted.", "review_summary": "Reviewed.",
    "old_code_note": "Old and new.", "baselines": {"demo": "x^"},
    "not_secret": ["dummydummy1234"],
    "changes": [{"id": "01_thing", "ref": "#1", "name": "The thing",
      "short": "Thing", "description": "CARD_01.md", "parts": [],
      "runs": []}]}
  if task:
    spec["task"] = task
  if change_task:
    spec["changes"][0]["task"] = change_task
  if saved is not None:
    # A batch candidate set aside: its after/ copy is the tested file
    #  ("same") or another version ("different")
    job = os.path.join(folder, "job")
    os.makedirs(os.path.join(job, "before", "repo-1", "demo"))
    os.makedirs(os.path.join(job, "after", "repo-1", "demo"))
    open(os.path.join(job, "JOB.txt"), "w").write("repo-1: %s @ abc\n"
      "changed repo-1/demo/thing.py\nafter: complete\n" %modules)
    open(os.path.join(job, "after", "repo-1", "demo", "thing.py"), "w"
      ).write(open(real).read() + ("" if saved == "same" else "# other\n"))
    spec["changes"][0]["state"] = "saved"
    spec["changes"][0]["parts"] = [{"repo": "demo", "uncommitted": True,
      "before": os.path.join(job, "before", "repo-1"),
      "library_files": ["demo/thing.py"]}]
  json.dump(spec, open(os.path.join(folder, "review.json"), "w"))
  open(os.path.join(folder, "CARD_01.md"), "w").write(description)
  os.makedirs(os.path.join(packet, "runs"))
  for name in ("base_head.txt", "changed_files.txt", "net.diff"):
    open(os.path.join(packet, name), "w").write("")
  json.dump({"files": {"demo/demo/thing.py": review_pages.sha256(real)},
    "coverage_problems": list(coverage),
    "modules": [["demo.thing", old, real]],
    "runs": {"tst_thing_old": expected}},
    open(os.path.join(packet, "candidate.json"), "w"))
  if edit_after:
    open(real, "a").write("# edited after the packet\n")
  summary = "old  exit %d  tst_thing_old  last line: x\n" %old_exit
  if old_body is None:
    old_body = "%s\nTraceback\nAssertionError: 7/3" %review_pages.TEST_STARTED
  if warning:
    old_body += "\nWARNING: demo.thing loaded from the current file " + real
  open(os.path.join(packet, "runs", "tst_thing_old.txt"), "w").write(
    run_text(old_exit, old_body, old_loaded or old))
  if new_run:
    summary += "new  exit %d  tst_thing_new  last line: OK\n" %new_exit
    open(os.path.join(packet, "runs", "tst_thing_new.txt"), "w").write(
      run_text(new_exit, "%s\nOK" %review_pages.TEST_STARTED,
      new_loaded or real))
  open(os.path.join(packet, "summary.txt"), "w").write(summary)
  os.makedirs(os.path.join(folder, "evidence", "scope"))
  open(os.path.join(folder, "evidence", "scope", "scope.txt"), "w").write(
    "Problems: none\n" if scope_ok else "Problems: \n  demo abc NOT\n")
  os.makedirs(os.path.join(folder, "out"))
  open(os.path.join(folder, "out", "page.html"), "w").write(page)
  open(os.path.join(folder, "out", "request.md"), "w").write(request)
  return folder

def problems_of(**kw):
  folder = make_folder(**kw)
  try:
    return review_pages.check(review_pages.load(folder))
  finally:
    shutil.rmtree(folder)

def request_of(**kw):
  folder = make_folder(**kw)
  try:
    return open(review_pages.request(review_pages.load(folder))).read()
  finally:
    shutil.rmtree(folder)

def saved_copy_cases():
  """An uncommitted change is the job's own change: the developer's earlier
     edit in the same file stays in the old code"""
  failures = []
  folder = tempfile.mkdtemp()
  try:
    modules = os.path.join(folder, "modules")
    before = os.path.join(folder, "job", "before", "repo-1")
    for d in (os.path.join(modules, "demo", "demo"),
        os.path.join(before, "demo")):
      os.makedirs(d)
    # Before the job: HEAD's text plus the developer's own edit (line 2)
    open(os.path.join(before, "demo", "thing.py"), "w").write(
      "def thing(x):\n  y = 1  # the developer's edit\n  return x[0]\n")
    open(os.path.join(modules, "demo", "demo", "thing.py"), "w").write(
      "def thing(x):\n  y = 1  # the developer's edit\n  return x\n")
    spec = {"settings": {"modules": modules}}
    part = {"repo": "demo", "uncommitted": True, "before": before,
      "library_files": ["demo/thing.py"], "test_files": []}
    diff = review_pages.saved_diff(spec, part, ["demo/thing.py"])
    if "the developer's edit" in [x for x in diff.splitlines()
        if x.startswith(("+", "-")) and not x.startswith(("+++", "---"))]:
      failures.append("the developer's earlier edit is in the job's diff")
    if "-  return x[0]" not in diff or "+  return x" not in diff:
      failures.append("the job's change is not in its diff: %r" %diff)
    if review_pages.before_file(part, "demo/thing.py") is None:
      failures.append("the saved copy was not found")
    # Without the job's record, the files it created cannot be confirmed
    if not [x for x in review_pages.coverage_problems(part, [])
        if "no JOB.txt" in x]:
      failures.append("a missing JOB.txt was not reported")
    # A module the job created, named only in its record, is found
    open(os.path.join(folder, "job", "JOB.txt"), "w").write(
      "changed repo-1/demo/thing.py\ncreated repo-1/demo/new.py\n")
    open(os.path.join(modules, "demo", "demo", "new.py"), "w").write("x = 1\n")
    paths = review_pages.changed_paths(spec, part)
    found = review_pages.coverage_problems(part, paths)
    if "demo/new.py" not in paths or not [x for x in found
        if "demo/new.py" in x]:
      failures.append("an unlisted created module was not reported: %s %s"
        %(paths, found))
    # A binary file and a deleted file
    open(os.path.join(before, "demo", "data.bin"), "wb").write(b"\0\1")
    open(os.path.join(modules, "demo", "demo", "data.bin"), "wb").write(
      b"\0\2")
    open(os.path.join(before, "demo", "gone.py"), "w").write("y = 2\n")
    diff = review_pages.saved_diff(spec, part, ["demo/data.bin",
      "demo/gone.py"])
    if "Binary files differ" not in diff or "deleted file mode" not in diff \
        or "-y = 2" not in diff:
      failures.append("binary or deleted file not in the diff: %r" %diff)
    # A changed module or file that the old-code runs do not account for
    found = review_pages.coverage_problems(part, ["demo/thing.py",
      "demo/other.py", "demo/ext.cpp", "demo/regression/tst_x.py"])
    if len(found) != 2 or "other.py" not in found[0] or "ext.cpp" not in \
        found[1]:
      failures.append("unlisted changed files not reported: %s" %found)
  finally:
    shutil.rmtree(folder)
  return failures

def markdown_cases():
  """Raw HTML in a description or review comes out as text"""
  try:
    import markdown
  except ImportError:
    print("Note: no markdown package here, so the HTML escaping is not "
      "tested; run this with a Python that has it (libtbx.python)")
    return []
  h = review_pages.convert("A <script>alert(1)</script> and <b>x</b>")
  if "<script" in h or "<b>" in h:
    return ["raw HTML was kept: %s" %h]
  return []

def run():
  failures = []
  ok = problems_of()
  if ok:
    failures.append("a complete review was refused: %s" %ok)
  cases = [
    ("a description without its Now: line",
     dict(description = DESCRIPTION.replace(
       "Now: The thing returns an empty result for empty input.\n", "")),
     "\"Now:\""),
    ("no developer's request", dict(task = None), "no developer's request"),
    ("a test that passed on the old code", dict(old_exit = 0),
     "passed on the old code"),
    ("an old-code run that failed on an import, not on the test",
     dict(old_body = review_pages.TEST_STARTED +
       "\nModuleNotFoundError: No module named 'demo'"),
     "failed on the old code for the wrong reason"),
    ("an old-code run that failed loading the old code (ValueError)",
     dict(old_body = "Traceback\nValueError: bad"),
     "failed before the test started"),
    ("an old-code run that failed on another assertion",
     dict(old_body = review_pages.TEST_STARTED + "\nAssertionError: 1/2"),
     "did not fail with the expected"),
    ("no run with an expected old-code failure", dict(expected = None),
     "no proving run"),
    ("an old-code run without its run on the current code",
     dict(new_run = False), "has no run on the current code"),
    ("an old-code run that loaded a current file", dict(warning = True),
     "loaded a current file"),
    ("an old-code run that did not use the old module",
     dict(old_loaded = "/elsewhere/demo/thing.py"),
     "did not use the old version of demo.thing"),
    ("a current-code run that loaded another checkout",
     dict(new_loaded = "/other/install/demo/thing.py"),
     "not from the checkout"),
    ("no test imports the changed module", dict(new_loaded = "None"),
     "no test imports demo.thing"),
    ("a changed module not accounted for",
     dict(coverage = ["demo demo/other.py: a changed module not in "
       "library_files"]), "demo/other.py"),
    ("a file changed after the packet", dict(edit_after = True),
     "changed after the packet"),
    ("a key in the reviewer's packet",
     dict(request = 'api_key = "abcdefghijklmnop1234"\n'),
     "looks like a key or password"),
    ("a second script in the page",
     dict(page = PAGE + "<script>alert(1)</script>"), "2 scripts"),
    ("a link without a target",
     dict(page = PAGE.replace('href="#change-1"', 'href="#change-9"')),
     "#change-9 has no target"),
    ("the outside review inside a change",
     dict(page = PAGE.replace(
       '</details>\n</section>\n<h2 id="review">The outside review</h2>',
       '</details>\n<h2 id="review">The outside review</h2>\n</section>')),
     "#review part is inside change-1"),
    ("a scope check with problems", dict(scope_ok = False),
     "scope check found problems"),
    ("a saved candidate that differs from the one tested",
     dict(saved = "different"), "differs from the version tested"),
    ("an expected failure that is only an exception name",
     dict(expected = "AssertionError"), "too general"),
    ("a key on the same line as an allowed dummy value",
     dict(request = 'password = "dummydummy1234" api_key = '
       '"realrealreal5678"\n'), "looks like a key or password"),
  ]
  for what, kw, expected in cases:
    found = problems_of(**kw)
    if not [p for p in found if expected in p]:
      failures.append("not refused: %s (problems: %s)" %(what, found))
  found = problems_of(request = 'password = "dummydummy1234"\n')
  if found:
    failures.append("an allowed dummy value was refused: %s" %found)
  found = problems_of(saved = "same")
  if found:
    failures.append("a saved candidate that matches was refused: %s" %found)
  # The overall request and a change's own request both reach the reviewer
  text = request_of(change_task = "Also keep the old name working.")
  if "Make the thing work" not in text or "keep the old name" not in text:
    failures.append("a request is missing from the packet")
  # Two runs with the same name are refused before anything runs
  folder = make_folder()
  try:
    spec = review_pages.load(folder)
    spec["changes"][0]["runs"] = [{"repo": "a", "test": "x/tst_s.py"},
      {"repo": "b", "test": "y/tst_s.py"}]
    review_pages.packet(spec, spec["changes"][0])
    failures.append("two runs named tst_s were not refused")
  except ValueError as e:
    if "tst_s" not in str(e):
      failures.append("wrong refusal for two runs named alike: %s" %e)
  finally:
    shutil.rmtree(folder)
  # A job without an outside review still gets the review part, saying so
  folder = make_folder()
  try:
    spec = review_pages.load(folder)
    del spec["review_summary"]
    md = review_pages.review_md(spec)
    if "{#review}" not in md or "No outside review" not in md:
      failures.append("a page without an outside review: %s" %md)
    # Allowed only when the job named no triggers; refused for H, for no
    #  triggers given, and for an empty review_summary
    spec["triggers"] = []
    found = review_pages.check(spec)
    if found:
      failures.append("a job with no triggers and no review was refused: %s"
        %found)
    for triggers in (["H"], None):
      spec["triggers"] = triggers
      if triggers is None:
        del spec["triggers"]
      if not [p for p in review_pages.check(spec) if "triggers" in p]:
        failures.append("no outside review with triggers %s was not refused"
          %triggers)
      # Before the review, a job with a trigger has no review yet: allowed
      found = review_pages.check(spec, before_review = True)
      if found:
        failures.append("check --before-review refused a job with triggers "
          "%s that has no review yet: %s" %(triggers, found))
    for empty in (" ", None):
      spec["review_summary"] = empty
      if not [p for p in review_pages.check(spec)
          if "empty review_summary" in p]:
        failures.append("an empty review_summary (%r) was not refused" %empty)
  finally:
    shutil.rmtree(folder)
  failures.extend(saved_copy_cases())
  failures.extend(markdown_cases())
  return failures

if __name__ == "__main__":
  failures = run()
  for f in failures:
    print("FAIL: " + f)
  print("OK" if not failures else "%d failures" %len(failures))
  sys.exit(1 if failures else 0)
