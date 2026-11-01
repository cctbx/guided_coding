# Review folder and review.json (GuidedCoding review pages)

A review folder holds, for one job or one batch:

- `review.json`: the spec below;
- one description per change (Markdown, format below);
- `evidence/`, written by `review_pages.py packet` and `scope`;
- `out/`, written by `review_pages.py request`, `page` and `navtest`.

## review.json

```json
{
  "settings": {
    "modules": "/path/to/the folder holding the repositories",
    "python": "/path/to/the python that runs the tests (for PHENIX: libtbx.python)",
    "git_path": "optional folder added to PATH for git (for example git-lfs)",
    "repositories": ["cctbx_project", "phenix"],
    "upstream": "origin/master",
    "full_test": "the full server test (t96)",
    "author": "the git author name of the agent's commits",
    "timeout": 3600
  },
  "task": "The developer's request, word for word (or per change, below)",
  "title": "Five changes reviewed",
  "page_title": "Five Changes Reviewed",
  "result": "**All five accepted.** ... (written after the outside review)",
  "review_summary": "One or two sentences on the outside review.",
  "old_code_note": "How the old-code runs were made (any change reversed with another).",
  "baselines": {"cctbx_project": "<commit>^"},
  "excluded": {"<commit>": "why it is not part of the review"},
  "other_work": {"name of other work": ["<commit>"]},
  "others": {"#8": "name in words of a fix a description mentions that is not on this page"},
  "not_secret": ["a test's dummy value that looks like a key"],
  "changes": [
    {
      "id": "02_rename_side_chain_target",
      "ref": "#2",
      "name": "Side-chain renaming keeps its model on the map",
      "short": "Side chains",
      "description": "CARD_02_rename_side_chain_target.md",
      "task": "optional: this change's own request, in a batch",
      "parts": [
        {"repo": "phenix", "commits": ["3ba3d2aab"],
         "library_files": ["phenix/model_building/__init__.py"], "test_files": []},
        {"repo": "phenix_regression", "commits": ["f992f057"],
         "library_files": [], "test_files": ["model_building/tst_rename_side_chain_atoms.py"]}
      ],
      "also_reverse": {"cctbx_project": ["<a later commit that changed the same lines>"]},
      "runs": [
        {"repo": "phenix_regression", "test": "model_building/tst_rename_side_chain_atoms.py",
         "args": [], "new_only": false, "label": "optional: a unique run name",
         "old_fails_with": "AssertionError: 0.747"}
      ]
    }
  ],
  "findings": [
    {"found": "What the outside reviewer found", "changes": [3], "done": "What was done"}
  ]
}
```

- `commits`: a list, not a range, so that other changes' commits in between are left out.
- `"uncommitted": true` (instead of `commits`), with `"before"`: the change is still in
  the working tree, as it is during a GuidedCoding job before the developer asks for a
  commit. `before` is the folder of the job's saved copies of the files from before the
  job, at their paths in the repository (the job folder's `before/repo-<n>`; its
  `JOB.txt` lists every file the job changed or created, and `check` refuses the
  packet without it). The old
  code is those copies, so the developer's own earlier uncommitted work stays in it; the
  diff is each copy against the current file (a file without a copy is new). Use the
  baseline `HEAD` for that repository; the page then says the change is not committed.
- `"state": "saved"`: a batch candidate saved as patches and set aside; the page says it
  is saved, not applied, and `check` compares the job folder's `after/` copies, not the
  checkout, with the files that were tested.
- `not_reversed`: `{path: reason}` for a changed file that is not Python (compiled
  code, data), whose current version the old-code runs use. `check` refuses a changed
  file that is in none of `library_files`, `test_files` and `not_reversed`.
- `library_files`: the changed Python modules; the old-code runs load them with the
  change reversed. `test_files`: the tests to include in full (a file over 400 lines is
  shown only through its diff).
- `runs`: each test run on the old and the current code. `new_only`: run on the current
  code only (a test that starts a child process, which the replacement cannot reach).
  `old_fails_with`: text the old-code run must print after the test starts (at least one
  run of each change has it): the assertion message or diagnostic, not only an exception
  name, which `check` refuses as too general. Two runs of a change need different names
  (`label`). `check` also requires each old-code run to have its
  current-code run, to have used the old version of every changed module, and the
  current-code runs to import the changed modules from the checkout.
- `ref`: the change's number in the full list of the job or batch; a description may
  refer to other changes as `#N`, and the page turns those into links.

## A change's description

```
# <ref>: <what the change accomplishes>

Repo: <repositories> | Commits: <commits> | Status: <pushed / local>
Files: <principal source and test files>

## In short
Problem: <one sentence: what was wrong>
Now: <one sentence: what is true after the change>

## Problem
## Cause
## Fix: how it solves the problem
## Essential code
## What the tests show
- **Test:** ...
- **Old code:** ... (with the real failure reason)
- **New code:** ...
- **Remains uncertain:** ...
## Proof
## Other checks and remaining risks
## Changes after the review
```

Required: In short (both lines), Problem, Fix, Essential code, What the tests show;
`review_pages.py check` refuses the page otherwise. The page shows no summary of a change
except its "Problem:" and "Now:" lines. In "Changes after the review", a bullet starting
"(record only)" is shown only in the evidence, not in the explanation.
