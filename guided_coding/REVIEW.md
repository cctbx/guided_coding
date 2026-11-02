# GuidedCoding review (version 1.5)

The outside review and the developer's page (SKILL.md §3 and SKILL.md §5). Every job ends with the page (or,
where the tools do not fit, the report of §4); with an outside review, the developer first pastes one packet into
the outside reviewer and its answer back here. Keep the work proportionate: one or two focused tests per change,
the essential code only, a description as long as the change needs (a simple fix: 150 to 250 words), and no step
the developer does not need.

## 1. Prepare the review (after SKILL.md §2, before the report)

- **Do the tools fit?** They need Git, a Python with the `markdown` package (PHENIX's `libtbx.python` has it), and
  proving tests that run the changed Python code in the test's own process. If not, use §4 instead.
- **The review folder.** In the scratch folder (SKILL.md §2), `review/`. It holds `review.json`, one description per
  change, and what the tools write (`evidence/`, `out/`). Format: `${CLAUDE_SKILL_DIR}/tools/REVIEW_SPEC.md`.
- **The triggers** go into `triggers`: every reason for an outside review, including `"consequential"` for
  consequential work and `"requested"` when the developer asked for one; `[]` for none.
- **The settings** in `review.json` come from the project notes: the folder holding the repositories, the
  Python that runs the tests, a folder to add to PATH for git if any, the repositories, the upstream branch,
  the name of the full test. Without notes, find them from the project and say once that `/gc setup` would
  save them.
- **The developer's request** goes into `task` as they gave it, word for word.
- **One description per change,** in the format of REVIEW_SPEC.md: "In short" (a `Problem:` and a `Now:`
  line), Problem, Cause, Fix and how it solves the problem, Essential code, What the tests show, Proof,
  Other checks and remaining risks. Write every summary from the full description, and read each
  `Problem:` and `Now:` line once more against its label: the problem line says what was wrong, the now
  line what is true after the change.
- **The changes are not committed yet** (SKILL.md §4): each part is `"uncommitted": true`, with `before` the
  folder of the job's saved copies of the files from before the job (SKILL.md §2: the job folder's `before/repo-<n>`,
  whose `JOB.txt` gives the complete list of the job's files).
  The old code is then exactly the code before the job, the developer's own earlier changes included. A change
  made of commits lists the commits.
- **The tests.** For each change, the proving test and at most one more focused test, as `runs`. The proving test
  gives `old_fails_with`: text of the exception line that must end the old-code run (the last line of its
  traceback), distinctive enough to tell it from another failure: the assertion message, not only
  `AssertionError`. Text in the traceback's source lines does not count, so a bare `assert` with no message
  cannot be checked by the tool: give the test's assertion a message, or verify the failure by hand (§4). A test
  that starts a child process is `new_only` (the old-code replacement cannot reach it). A changed file that is
  not Python (compiled code, data) goes under `not_reversed` with the reason; if the proof needs its old version,
  use §4.
- **Run the tools** (`${CLAUDE_SKILL_DIR}/tools/review_pages.py`, with that Python): `scope`, `packet`,
  `request`, then `check --before-review`. Fix every problem `check` reports before going on. It refuses a
  run that proves nothing: an old-code run that passes, fails while loading the old code or for an import or
  syntax error, does not show its expected failure, or did not use the old modules; a current-code run that does
  not import the changed modules from the checkout; a changed module left out; files changed since `packet`;
  anything that looks like a key or password (remove it and say so; list a test's dummy value under `not_secret`).
  The scan is not a guarantee: read what goes out for keys and user data as well.
- **Give the packet to the developer.** Copy `out/request.md` to the hand-over folder (SKILL.md §0) and put it on
  the clipboard (`pbcopy` on macOS, `xclip -selection clipboard` or `wl-copy` on Linux; otherwise give its full
  path there). Say in two or three lines: the change is ready for review, its proving test fails on the old code
  and passes on the new, nothing is committed, and the packet is on the clipboard to paste into the outside
  reviewer the notes name (ChatGPT by default), with its answer pasted back here. Show nothing else yet.
  `request` warns when a packet is over 200 KB; then review fewer changes at a time.
- **No outside review** (no trigger asks for one, the work is not consequential, and the developer has not
  asked): run `scope`, `packet` (it makes the evidence for the page; nothing goes to a reviewer) and
  `check --before-review`, but not `request`, and go straight to §3. Give `"triggers": []` and leave out
  `review_summary` and `findings`; the page then says that no outside review was run and that the report offers
  one. `check` refuses a page without a review for a job with triggers. `result` says the change is ready and
  what remains.

## 2. When the answer comes back

- **Each finding,** as in SKILL.md §2: confirm it is real, then act. What it asks for decides what follows:

  | The reviewer asks for | Done | A second review |
  |---|---|---|
  | a description correction | correct the description | no |
  | a minor test change (a message, a name, an extra case) | change the test, run `packet` again | offered |
  | a code change, or a proving test that did not prove the fix | change it; rerun the tests, suites and code review; `packet` again | required |

  A second review is `request <change id>`, which makes a packet for that change alone, pasted as before.
  Nothing whose code or proving test changed is committed before its second review. Record each change made
  because of the review under "Changes after the review" in its description (a bullet starting "(record only)"
  appears only in the evidence).
- **Decisions for the developer** are only genuine choices about scientific intent or expected behaviour
  that the reviewer could not settle and whose answer changes what is done. Investigate each first; ask
  it with the decision, why it cannot be settled, a recommended answer, and what will be done for each
  answer. Ask nothing that has no action attached.
- **Fill in `review.json`:** `result` (one or two sentences: accepted or not, and whether any decision
  remains), `review_summary`, and `findings` (what was found, the changes it concerns, what was done).

## 3. The developer's page

- **Make it:** `page`, then `check` (now including the page). Fix every problem it reports. `navtest` (Google
  Chrome, at its usual macOS place) is needed only after a change to the page tools; it is a check for
  GuidedCoding's developers, and reading a page needs only a browser.
- **Deliver it** as a private claude.ai page with the Artifact tool, titled with `page_title`, and give the link;
  give it again as the very last line of the job's last message (SKILL.md §5).
  Where the session has no Artifact tool, copy `out/page.html` to the hand-over folder and give its full path,
  to open in a browser; that is an equally good route.
- **The page** opens with a very brief summary (the result, what remains to do, with every commit a push
  would publish), then the changes, each explained with its evidence folded underneath, then the outside
  review and how the tests were run, then the commits. It shows no summary of a change except its
  `Problem:` and `Now:` lines. Design for a desktop screen.
- **The process report** (SKILL.md §5) is still written and saved; the page's message gives its path. Without
  an outside review, the page's message also offers one in a line.

## 4. When the tools do not fit

No Git, a proof that needs compiled code or other non-Python files in their old version, a test that needs its
own command or working directory, a failure the tools cannot tell apart (`check` says to verify it by hand), or no
`markdown` package: make the evidence by hand, in the scratch folder. That a tool does not fit changes only how the
evidence is made, not whether there is an outside review (SKILL.md §3 decides that, as before).

- **With an outside review** (a trigger asks for one, the work is consequential, or the developer asked): write
  `OUTSIDE_REVIEW.md` and copy it to the hand-over folder. It holds the task as given, the full diff, the new tests
  and their output on the old and new code (the old code as SKILL.md §2 makes it: an isolated copy, or a swap
  where the notes allow it), for H the conditions that make the change hard, for Q the open question, and this
  request: "Review this change for correctness, unintended behaviour changes, and whether the tests prove the fix.
  List findings, most serious first." Leave out keys, tokens and user data, and name anything you removed. The
  developer pastes the file into the outside reviewer and the reply back; §2 applies.
- **Without one:** no review file. The final report (SKILL.md §5) carries the same evidence in short: the diff, the
  new tests and their output on the old and new code; it offers an outside review in one line.

Either way, say in the report which evidence was made by hand. If the old code could not be run reliably, say so;
never present it as checked. The report replaces the page.

---
Version 1.5, 2026-11-01.
