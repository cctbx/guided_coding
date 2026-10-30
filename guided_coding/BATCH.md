# GuidedCoding batch (`/gc batch`, version 1.4)

A batch is a **supervised sequence of ordinary `/gc` jobs**, run one at a time while the developer stays reachable.
Say these limits in one line when the batch starts:
- it is not the old unattended auto mode, and has no enforced time limits, process tracking or locks;
- a job's time cap is kept by the job itself, and a hung job can be stopped only by the developer interrupting;
- a batch does not detect or stop other sessions that use the same checkout or build.

## 1. Agree the batch

- **List the tasks** from the request, one line each. Check that each is bounded, that none is consequential work
  (SKILL.md §1), and that the request authorizes it. Leave out anything that fails these checks, and say why.
- **Dependent tasks.** A task that needs another task's change cannot run in the batch, because each job's changes
  are set aside before the next job starts. List it as "needs patch <n> applied first", for after the batch. When
  unsure whether tasks depend on each other, treat them as dependent.
- **Ask the developer to confirm, in one message:**
  - the list;
  - a stopping time;
  - a time cap per job (for example 60 minutes);
  - whether this checkout and build are used only by this batch while it runs. This settles exclusive use for any
    in-place swap. If the answer is no or unclear, jobs use isolated copies, or leave the old-code check pending.
- **Record the starting state** of every repository the batch may touch: `git rev-parse HEAD` and
  `git status --short`. A job may not change a file that was already modified at the start; such a job stops instead.
- **Make a scratch folder for the batch,** with one subfolder per job (`job-1/`, `job-2/`, and so on).

## 2. Run each job

- **One at a time, with fresh context.** Start a subagent of type general-purpose with this brief:
  - "Follow the GuidedCoding instructions in `<skill folder>/SKILL.md` for one job. The task is: <task>. It takes the
    place of `$ARGUMENTS`; `${CLAUDE_SKILL_DIR}` is `<skill folder>`. Skip the routing and session naming in
    SKILL.md §0, but read the project notes as SKILL.md §0 says. Do not write the job log."
  - the job's scratch subfolder, and the starting state;
  - the exclusive-use answer from §1;
  - these limits:
    - no commit, no push, no installation, nothing irreversible;
    - no paid live call and no outside review: mark them pending;
    - stop and return at the first decision the developer must make;
    - stop at the time cap.
- **The subagent returns:**
  - its final report (SKILL.md §5), including whether the code-review skill ran or the fallback was used;
  - its complete candidate, saved in its scratch subfolder, for each changed repository:
    - `git diff --binary HEAD`, which covers staged and unstaged changes;
    - each new untracked file as a patch (`git diff --no-index --binary /dev/null <file>`), listed from
      `git ls-files --others --exclude-standard` against the starting state;
    - copies of every changed and new file;
  - the list of processes it started, and whether they have ended;
  - whether it rebuilt compiled code.
- **After each job, before the next starts:**
  1. Check that its processes have ended.
  2. Check that any files it swapped in place were restored (hashes).
  3. Check the candidate is complete before removing anything: in a disposable copy of the starting state, apply its
     patches, and compare every changed and new file with the saved copies (`cmp`). If they differ, stop the batch.
  4. Revert its changes: restore the changed files to the starting state (unstaging them too), and remove only the
     new files it created.
  5. If it rebuilt compiled code, rebuild again from the restored sources, and say so in its entry.
  6. Confirm that HEAD and `git status --short` match the starting state.

  If any of these cannot be confirmed, stop the batch and report why.
- **Never carry approval over.** An approval or answer for one job is never permission for another.
- **Permission prompts** raised inside a job still go to the developer, as in any session.

## 3. Stopping

- **A job that needs a decision** stops and is listed. The batch continues with the next independent job.
- **A job that hangs, overruns its cap, or leaves the state uncertain** stops the whole batch.
- **When the developer types `/gc stop`, or asks to stop,** start no further job. This takes effect when the current
  job returns; to stop the current job itself, the developer interrupts it. Report any processes still
  running. **`/gc status`** reports which jobs have finished, which is running, and which remain.
- **At the stopping time,** start no new job. A running job finishes, or is stopped at its cap.

## 4. Report

- **One summary.** First copy each patch meant for the developer into the hand-over folder (SKILL.md §0),
  keeping the original in the scratch folder. Then, for each job, give:
  - its status (completed, stopped or skipped);
  - its "Ready to use" line;
  - where its patch is, as a full path in the hand-over folder (SKILL.md §0);
  - whether the review fallback was used;
  - its decisions for the developer.

  Then give all the decisions together, each with a recommendation, and list the tasks left for after the batch.
  Say that the repositories are back at their starting state, so the jobs' changes do not appear among their
  uncommitted changes until shown (below). Name any uncommitted or untracked files that were already there at the
  start, so the developer does not take them for the batch's changes.
- **Showing the changes.** Offer to show each job's changes in the repositories it changed, as ordinary uncommitted
  changes the developer can see in their editor or app. Show the job's latest candidate (if it was redone after a
  decision, the redone one) and one job at a time. Keep track of the **expected state** of every file the batch's
  jobs change: as at the start of the batch, except for files of jobs the developer has kept (below). HEAD and
  `git status --short` are not enough, because they do not show a further edit to a file that is already modified.
  1. **Before:** confirm HEAD of every repository the job changed, and compare each file the job's patches touch
     with its expected state: its contents (`cmp`) and whether it exists. Save a copy of each, with a note of the
     files that do not exist, in the scratch folder. This is the **pre-preview state**. If a file differs from its
     expected state, show nothing: the developer may have edited it. Say which file, and ask.
  2. **Apply:** check that all the job's patches apply (`git apply --check`), then apply them. If any apply fails,
     put back the pre-preview copies and remove the files that did not exist (as in step 4, with no shown state to
     compare), confirm the pre-preview state, and show nothing.
  3. **Shown:** save a copy of each shown file (the **shown state**). Say which job is shown and the files it changed.
     If it changed compiled code, say that the build has not been rebuilt for it. While a job is shown, say so in
     every reply, and that asking you to put it back restores it (step 4 checks for the developer's edits first).
  4. **Restore** when the developer moves on. First compare each shown file with the shown state. If the developer
     has changed one, ask before restoring, and keep a copy of their version. Then put back the pre-preview copies,
     remove the files that did not exist before, and confirm that every file matches the pre-preview state.

  Show two jobs together only if the developer asks and the throwaway check (below) found that they apply together;
  their pre-preview and shown states then cover both jobs' files.
- **Applying patches.** Check whether the accepted patches apply together, in a throwaway copy, and say where they
  conflict. Then offer to apply them one at a time. Each one then gets the usual checks, and
  commit or push only on request (SKILL.md §4). A shown job that the developer keeps stays applied (do not apply it
  again) and gets the same checks. Its shown state becomes the expected state of its files, and jobs shown after
  it are applied on top of it.
- **Job log.** Unless the notes turn it off, add one line per job, as `LOG.md` says.
