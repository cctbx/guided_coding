# The evidence behind GuidedCoding (version 1.4)

The full report of the replay study, with every figure traced to its source, can be downloaded:
[the final report](https://www.thomasterwilliger.org/guided_coding/GuidedCoding_study_final_report.md) (Markdown, about 185 KB). In it the earlier kit is called GuidedCoding Plus
(GC+); the cited source files are available on request.

## What the evidence says about `/gc` as now written

`/gc` version 1.4 keeps the steps the replay study found to help, drops or makes optional those that showed no clear
benefit, narrows the one that probably hurt (estimated, not tested), and keeps a few safety steps that were not measured. Figures are major errors left
in the code per run on 18 harder jobs (jobs where the earlier kit's own checks had caught errors, not a random
sample), unless stated otherwise; the study is described below.

| Step | What the study found | In `/gc` 1.4 |
|---|---|---|
| **One review pass** (Claude Code's code-review skill) | Helps: 0.90 → 0.79 major errors per run; across all 37 jobs, missed program errors fell from 0.81 to 0.47 per job | Kept, on every job |
| **An outside review by another AI assistant** | Helps on the 18 harder jobs, narrowly: 1.00 → 0.83 under `/gc` (round 6b, below); for plain Claude Code with one review, 0.85 → 0.76, not a clear difference. The net gain came from 4 of the 18 jobs, and the reviews also brought in a few new errors | Standard for hard changes (new trigger H), for triggers R, D and Q, and for consequential work; offered on any other job |
| **A proving test** (fails on the old code, passes on the new) | More runs produced a proving test: about 1 in 7 plain runs ended without one, against 1 of 37 jobs for the earlier kit, which required it. Its effect on errors left was not measured | Kept, required |
| **A second ordinary review pass** | No clear additional benefit found over one review pass | Not included |
| **The independent reviewer (`REVIEWER.md`)** | Not clearly better than a second ordinary review, at about three times the time | Optional, on request |
| **The strict scope rule** (revert every review fix beyond the literal task, ask first) | Probably cost errors: in round 6, fixes the review found were undone and left as questions, and `/gc` left more major errors than plain + review (0.97 against 0.79). Estimated from those cases, not measured directly | Narrowed: real defects in the code the job changes are fixed without asking; `/gc` asks before changing public interfaces, defaults, file formats, behaviour callers rely on, or the project's scope, and when the task leaves the intended behaviour open |

**Two scorings of the same arms.** Plain Claude Code with one review appears as 0.79 (round 6) and as 0.85 (before the
outside review, round 6b); `/gc` 1.3 appears as 0.97 and 1.00. Round 6b's instruments found further errors that the
earlier versions also had, which raised those figures. Each comparison uses figures from one scoring.

**Kept for safety and clarity, not measured:** the short final report (what changed, what was checked, what is open);
a real call to a live service where a fix depends on it; exact commands for another platform; an outside review for
changes that touch existing user files or credentials; asking before any commit, push or installation; a plan, a
checked recovery step and an outside review before an irreversible step in consequential work; `/gc batch`; the
review fallback when the code-review skill is missing.

**Not known:** `/gc` 1.4 has not itself been replayed (it was checked in a small trial, below), and the narrower scope
rule was adopted without a test. Also not known: whether `/gc` 1.4 as a whole leaves fewer errors than plain Claude
Code with one review and an outside review; how much of the developer's own time an outside review takes; and whether
an outside review helps on routine fixes (it is optional there). The effects found are small (about 0.1 to 0.2 major
errors per run) next to the variation between runs.

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
- This study's 37 jobs were not replayed with this procedure; round 6 (below) replayed it on 18 of them. Its added
  steps (live calls, platform commands, the optional reviewer) were not measured as built into it.
- 37 jobs is a small sample, from one developer's work. Every worker, scorer and checker was a Claude model; some
  outside readers were not.
- The study measured errors in code. It did not measure accidental damage to installations. For that kind of work
  this procedure requires a plan, a checked recovery step and a completed outside review.

## The replay of `/gc` itself (round 6, October 2026)

`/gc` version 1.3 was replayed on the 18 harder jobs, those where the earlier kit's layers had caught something: 38
fresh runs, with the same Claude Code versions, inputs and sandbox as the plain runs, and a fixed paragraph standing
in for the developer ("keep to the task"). In 4 runs `/gc` wrote an outside review; it was sent to a model from
another family and the session continued with the reply. Every run was scored at the same depth as the others, and
the reading rule was fixed before any result was seen.

| major errors left in the code, per run (missed or disclosed) | earlier kit | P | P+R | `/gc` with its outside reviews |
|---|---|---|---|---|
| the 18 harder jobs | 0.44 | 0.90 | 0.79 | 0.90 |

- **The result:** no clear difference between `/gc` and plain Claude Code with one review pass. The estimate was
  slightly worse for `/gc` (+0.11 major errors per run; 90% interval −0.19 to +0.42). It does not show that the two
  are equal, and `/gc` did not recover the earlier kit's lead on these jobs.
- **Questions for the developer.** `/gc` disclosed more of what it left, often as a question for the developer,
  which the replay's fixed stand-in always answered "keep to the task". Had those questions been answered as `/gc`
  recommended, the two would have been about level (an untested estimate).
- **The outside review,** which `/gc` wrote on its own trigger in 4 of 38 runs, removed 3 major errors.
- **What followed.** As decided before the results were seen, `/gc` was kept as a way of working with the developer,
  not as a claim that it produces more correct code than plain Claude Code with a review. Round 6b (below) then
  measured the outside review, and version 1.4 made it standard for hard changes and narrowed the scope rule.

The round-6 report is part of the final report above (Part F).

## What an outside review adds (round 6b, October 2026)

Every counted run of round 6, both `/gc` and plain Claude Code with one review, was resumed once with an outside
review of its final change by a model from another family (gpt-6.1-sol), built by one script for both, and scored
again at the same depth. The reading rule was fixed before any run.

| major errors left in the code, per run | before the outside review | after |
|---|---|---|
| plain Claude Code + one review (38 runs) | 0.85 | 0.76 |
| `/gc` 1.3 (38 runs) | 1.00 | 0.83 |

- **For `/gc`:** the outside review "adds something" by the rule fixed in advance: −0.17 (90% interval −0.31 to
  −0.06), also without either of the two jobs that most often drive results. The margin is thin: 9 run-level removals of a major error
  and 3 additions, a net of 6 removals, all of the net in 4 jobs (one more job had 2 of each), and a single changed ruling (for example one error's severity)
  would turn it into "no clear difference".
- **For plain Claude Code with one review:** no clear difference (−0.08), as a check made before the runs predicted:
  the reviews named few of the errors that runs had left.
- **After the review,** `/gc` was still not better than plain Claude Code with one review and the same outside review
  (+0.07 major errors per run, not a clear difference).
- **What followed:** the outside review became a standard step for hard and consequential changes in `/gc` 1.4,
  optional for other jobs. The study did not test the scope rule separately; it was narrowed on the evidence above
  rather than by a further experiment.

The round-6b report is part of the final report above (Part G).

## Use since

The procedure, as an earlier version, was used on three real jobs on 2026-10-23, and the developer judged it worked
well. Evaluation continues on 10 to 15 jobs, each checked for later defects about four weeks after the job.

## Trial of version 1.4 (2026-10-26)

An implementation check, not a measurement. Fresh `/gc` 1.4 runs on replayed jobs:

| run | result |
|---|---|
| three hard jobs (a consistency check, process polling, a model-default update) | trigger H applied in each, with a one-line reason; each wrote an outside review file with the task, why the change is hard, the full diff, and the tests on the old and new code |
| a routine one-line fix | no trigger: "one clear defect on one path"; the outside review was offered, not required |
| the three hard jobs, after the outside review came back | every finding was handled (1, 3 and 2 findings), each fix with a test; each report opened with "Ready to use: no" and named the remaining platform or live check with its commands |

One fix in the trial was narrower than it might have been: on the model-default job, the no-temperature handling
was given to the two new default models only, and the report presented this as a design choice rather than an open
point.

What the first runs changed: a session must finish (or stop) any long test before writing the review file and the
report, and leave nothing running; and the narrowed scope rule replaced the strict one before the second runs.

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
- the review-fix scope rule named what counts as a behaviour change (in 1.3; 1.4 replaced it, see the table above);
- batch patches now include new and staged files, and are checked before reverting;
- the batch report checks whether accepted patches apply together.

**Later check** (2026-10-23, after the on-request line was added to `SKILL.md` §3):

| run | result |
|---|---|
| bounded fix, with "also prepare an outside review file for a second opinion" | fixed the bug with a proving test run on the old and new code; ran the code-review skill; wrote `OUTSIDE_REVIEW.md` with the task, the diff, the tests and the standard request; reported "Ready to use: no" until the outside review comes back; committed nothing |
