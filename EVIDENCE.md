# The evidence behind GuidedCoding (revision 22)

## What the evidence says about `/gc` as now written

GuidedCoding as now written (`/gc`, version 1.3) has not been measured as a whole. Its main parts have different
support. The study and the checks behind this list are described below it. Behaviour checks show what happened in
particular examples; they do not establish reliability across jobs or measure how many defects a rule prevents.

- **One review pass with Claude Code's code-review skill, on every job where the skill is available.** Measured. In
  the replay study, adding this pass to plain Claude Code cut missed program errors per job from 0.81 to 0.47, and
  missed major errors from 0.33 to 0.24. This is the main support for `/gc`.
- **The review fallback (Claude reviews the change itself when the code-review skill is missing).** Not measured. The
  report says when it was used.
- **A proving test that fails on the old code and passes on the new.** The earlier kit also called for this kind of
  test where there was one, but the study did not measure its separate contribution.
- **Checking each fix the review makes, and reverting fixes that change behaviour beyond the task.** Not measured. It
  was added because review passes in the study sometimes caused problems: one brought back a major error, and two
  changed behaviour the task did not ask for. A behaviour check below shows it working in one test case.
- **Added steps for the triggers (live calls, commands for another platform, outside review).** Not measured as built
  into `/gc`. In the study, the earlier kit's outside reviewers and live checks made some major catches that no
  in-session step recovered.
- **An outside review on request, on any job.** Not measured. One behaviour check below shows it working.
- **The optional independent reviewer (`REVIEWER.md`).** Measured as an extra step after a review pass, on the 18
  harder jobs. It left fewer major errors than the review pass alone (0.63 against 0.74 per run), but not clearly
  fewer than simply running a second ordinary review (0.71), and it took about three times as long; most of its runs
  reached their time limit.
- **Consequential work (plan, checked recovery step, outside review before an irreversible step).** Not measured; the
  study did not cover damage to installations. The rule is a precaution set by the developer, not a finding of the
  study.
- **`/gc batch`.** Not measured as a procedure. The behaviour checks below show its patch handling and checkout
  restoration working in specific test cases.

**In short:** the strongest measured support for `/gc` is the review pass, used on every job where the code-review
skill is available; the fallback has not been measured. The earlier, larger kit left fewer major errors in the
37-job study, although over all jobs that difference depended on one job; a closer look at the jobs where its extra
layers caught something suggested they could add further benefit (below). How much of that advantage `/gc` keeps is
not known. The other parts of `/gc` either come from the earlier kit or are new; their individual effect has not
been established, and the complete procedure is being evaluated in real use.

## The replay study (October 2026)

37 past bug-fix jobs in PHENIX and cctbx, done with the earlier GuidedCoding kit, were replayed with plain Claude
Code: alone (P), and with one review pass using Claude Code's code-review skill (P+R). Every result was scored for
program errors left, with errors tagged major or minor without knowing which method produced them.

| per job, over all 37 jobs | earlier kit | P | P+R |
|---|---|---|---|
| program errors left (missed) | 0.51 | 0.81 | 0.47 |
| major errors left (missed) | 0.16 | 0.33 | 0.24 |

**What it shows:**
- One review pass after plain Claude Code made a large difference, at about half the plain run's time.
- The earlier kit and P+R were level on all errors.
- The earlier kit led on major errors (0.16 against 0.24). Over all 37 jobs that lead rests on one job; without it,
  the two are level (0.167 against 0.160).
- A deeper search of the 18 jobs where the kit's layers caught something told a different story. On major errors
  left in the code (missed plus disclosed), the kit's lead there was 0.19 per run, leaving out the same job (0.35
  against 0.54). Part of that increase is an artefact of the deeper search, which started from errors in the plain
  runs. On the round-4 measure (missed only) the lead in those jobs was 0.05. This is unresolved, and is the main
  evidence against the change to this procedure.
- The earlier kit's outside reviewers and live checks made some major catches that no in-session step recovered.
  This procedure keeps outside review and live checks, as steps triggered by the kind of change.
- A GC-style second reviewer, run after the review pass on the 18 harder jobs, left fewer major errors than the
  review pass alone, but not clearly fewer than a second ordinary review, and took about three times as long. It is
  offered here as an optional step (`REVIEWER.md`).

**What it does not show:**
- This procedure was not replayed. Its added steps (live calls, platform commands, outside review, the optional
  reviewer) were not measured as built into it.
- 37 jobs is a small sample, from one developer's work. Every worker, scorer and checker was a Claude model; some
  outside readers were not.
- The study measured errors in code. It did not measure accidental damage to installations. For that kind of work
  this procedure requires a plan, a checked recovery step and a completed outside review.

## Use since

The procedure, as an earlier version, was used on three real jobs on 2026-10-23, and the developer judged it worked
well. Evaluation continues on 10 to 15 jobs, each checked for later defects about four weeks after the job.

## Behaviour checks of revision 22

Before release, each of these was run in Claude Code (`claude -p`) against a scratch repository, and the output was
kept: the final message, and for the runs that change things, the Git state, the diff and file hashes before and
after.

**First round** (version 1.2, 2026-10-23):

| run | result |
|---|---|
| `/gc` | an introduction; no job started |
| `/gc setup` | looked first, showed the card, saved nothing |
| `/gc stop`, `/gc help`, `/gc auto resume` | no job started |
| bounded fix (`clamp` upper bound) | proving test failed on the old code and passed on the new; code-review skill ran; short report |
| installation task | edited the script but did not run it: asked for a plan, a checked backup and an outside review first. But it kept a review fix (`set -e`) that changed the script's failure behaviour, and only reported it |
| two-task batch | separate patches; checkout restored after each job; reported that the patches conflict when combined |
| batch with a file already modified | stopped before either job; nothing changed |

**Second round** (version 1.3, after the outside reviews). The first runs below used an intermediate 1.3 text; the
final rows (marked *final*) used the published text:

| run | result |
|---|---|
| `/gc autosol GUI: ...` | a normal job started; only `auto` as a word is an old-kit command |
| `/gc stop` with no earlier kit installed | no job started, but it called `/gc batch` "unattended". The wording was fixed |
| `/gc stop` and `/gc auto resume` (*final*) | "the earlier GuidedCoding kit ... has been retired"; no job started; `/gc batch` described as supervised, not unattended |
| installation task, with an existing shared folder (*final* on the second try) | the folder stayed byte-identical (hashes before and after); a backup was made; it asked for a plan, an outside review and a go. On the first try it still kept `set -e`; after the rule was made concrete, it reverted `set -e` and a working-directory change as behaviour changes, raised them as a decision, and kept only a refactor with no behaviour change |
| batch, one job adding a new test file | the new file was in that job's patch; each patch was re-applied in a fresh copy and compared byte for byte before reverting; out-of-scope review fixes were reverted; the checkout ended where it started; the two patches apply together |

**What these runs changed:**
- the `auto` guard became a whole-word match, and the retired-command answer says that `/gc batch` is supervised;
- the review-fix scope rule now names what counts as a behaviour change;
- batch patches now include new and staged files, and are checked before reverting;
- the batch report checks whether accepted patches apply together.

**Later check** (2026-10-23, after the on-request line was added to `SKILL.md` §3):

| run | result |
|---|---|
| bounded fix, with "also prepare an outside review file for a second opinion" | fixed the bug with a proving test run on the old and new code; ran the code-review skill; wrote `OUTSIDE_REVIEW.md` with the task, the diff, the tests and the standard request; reported "Ready to use: no" until the outside review comes back; committed nothing |
