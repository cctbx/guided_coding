# GuidedCoding commands (version 1.4)

These commands start no coding job. Each one first finds the installation:

- **The registration** is the `gc` link in the skills folder (`$CLAUDE_CONFIG_DIR/skills`, or else
  `~/.claude/skills`).
- **The copy** is the folder above the `guided_coding/` folder that link points to. It is a Git clone (in the home
  folder, or `modules/guided_coding` in a PHENIX installation) or a ZIP copy without Git history.
- **The version** is the first heading of `SKILL.md` in the copy.

Follow SKILL.md §0 for files and steps you give the developer.

## 1. help (also `/gc` alone)

In a few lines, say what GuidedCoding does: one bounded change, a proving test, one review pass, an outside review
for hard or consequential changes, extra checks only when triggered, and a short report. Give the version and where
the copy is. List the commands in one line each:

- `/gc <task>`: do one bug fix or bounded change;
- `/gc setup`: save this project's local defaults (recommended for a project you use regularly);
- `/gc batch <tasks>`: run several tasks one at a time, supervised;
- `/gc history`: list recent jobs; `/gc undo`: undo the last job;
- `/gc update`: get the latest version; `/gc uninstall`: remove GuidedCoding.

Then ask for the task.

## 2. history and status

- **`/gc history`:** read the job log (SKILL.md §6). Show the last ten jobs, newest first: date, project, job,
  status, ready to use, and the saved report. If the developer names a project or a date, show those instead.
- **`/gc status`** when no batch is running: the last job only, with anything its report left open.
- **`stop`** when no batch is running: say that nothing is running.
- If the log is turned off or empty, say so, and that `/gc setup` (SETUP.md, item 8) turns it on.
- **Job folders** (SKILL.md §2) keep private copies of source code. `/gc history` says how much space they use, and
  offers to delete those older than 30 days; ask once. Turning the job log off also stops new job folders.

## 3. update

1. Show the installed version and the copy's folder.
2. **A Git clone:** check that it is a clone of cctbx/guided_coding, on `master` tracking `origin/master`, with no
   changes of its own (`git -C <copy> status --porcelain`). If any of these does not hold, change nothing: explain
   why, and give the commands with their consequences.
3. Run `git -C <copy> fetch`. Say how many commits the copy is behind `origin/master`, and the latest version line
   (`git -C <copy> show origin/master:guided_coding/SKILL.md`). If it is up to date, say so and stop.
4. Ask once. If the developer agrees, run `git -C <copy> pull --ff-only`, and show the new version line.
5. **A ZIP copy:** there is no Git history; give the README's ZIP update steps as commands.
6. Afterwards, say to start a new Claude Code conversation: this one still uses the old instructions.

## 4. undo

Be conservative: undo only what can be undone without losing anyone's work, and say plainly what cannot.

1. **Find the job.** Use the most recent job for this project in the job log, and its job folder (SKILL.md §2). If
   there is none, a job from this conversation; otherwise ask which job.
2. **Say what it changed,** from `JOB.txt` and the current state: repositories, files, new files, commits, and
   whether they were pushed.
3. **Automatic restoring needs complete evidence:** a job folder whose `JOB.txt` says `after: complete`. Without it,
   do not restore anything automatically: explain, and offer a manual plan (show the job's changes, for example with
   `git diff`, so the developer can remove them by hand). Never assume the starting commit holds the developer's
   original files.
4. **Changes not yet committed:** a changed file can be restored from `before/repo-<n>/<path>` only if it is still
   exactly `after/repo-<n>/<path>` (compare the contents) and has no staged changes
   (`git diff --cached --quiet -- <path>`). The `before/` copy includes changes the developer had before the job, so
   restoring it loses nothing of theirs. A file that changed since the job, or has staged changes, is not restored:
   say so, and include it in the manual plan.
5. **Files the job created:** if a file is still exactly as the job left it and has no staged changes, offer to
   delete it.
6. **A commit:** offer `git revert <commit>`, which adds a commit that undoes it. First check that the commit is in
   the current branch's history (`git merge-base --is-ancestor <commit> HEAD`), that no merge, rebase or cherry-pick
   is in progress, and that the files it touches have no uncommitted changes; if any check fails, offer a manual
   plan instead. Then check for later commits that touch the same files (`git log <commit>..HEAD -- <files>`); if
   there are any, explain and ask. If the commit was
   pushed, push the revert only when the developer asks (SKILL.md §4).
7. Show exactly what you will do, ask once, and do only what the developer agrees to. Never touch other work, and
   never use `git stash` or `git reset --hard`.
8. Run the project's tests for the restored code. Report what was undone and what was not; never call a job undone
   when part of it remains.

## 5. uninstall

Ask one plain question, naming the full path of the copy, in these words: "Uninstall GuidedCoding? This removes /gc.
Its files stay in <full path of the copy>; I'll give you the command to delete them if you want. Your project notes
are kept." If the copy is under a `modules` folder (`modules/guided_coding`), ask instead: "Uninstall GuidedCoding?
This removes /gc. Its folder <full path of the copy> is part of a larger installation (such as PHENIX) and stays.
Your project notes are kept." Offer exactly two answers: "Yes, uninstall" and "No, keep it", with no other
description. In the question and answers, say only what will happen; do not mention the README, the block or links.

If the developer says yes:
1. Run the Uninstall block from the README exactly as written. It removes /gc and deletes nothing.
2. Report in plain words: /gc is removed, where the files are, and what the block said about them.
3. Unless the copy is under a `modules` folder, give the command that deletes the folder, for the developer to run
   if they want: `rm -rf '<full path of the copy>'`, in its own block, with a `cd` line first (SKILL.md §0). If the
   block said the folder holds something of theirs, say so next to the command. Do not run it yourself.
