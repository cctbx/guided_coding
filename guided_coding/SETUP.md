# GuidedCoding setup (`/gc setup`, version 1.3)

Setup saves a short notes file, `.claude/GC_NOTES.md`, that `/gc` reads at the start of every job. It changes
nothing else, runs no build or test, connects to nothing, and does not start a coding task. Expect it to take a few
minutes, once per project.

## 1. Find the project

- **The project** is the folder this session was started in, unless the developer names another.
- **Notes that already exist.** If `.claude/GC_NOTES.md` (or the older `.claude/LEAN_NOTES.md`) exists there or in a
  parent folder, show it and ask what to change, and update that file where it is. Do not start again from scratch, and do not make a second copy.

## 2. Look before asking

Read what the project and the developer already have, and fill in what you can. List each folder with one
read-only command; if a listing is refused, say so and continue:
- the project's instruction files: `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, and any project method they name.
  Team rules in `CLAUDE.md` or `AGENTS.md` (on pushing, commits, tests, environment) go into the card as found;
- its README, contributing guide and CI files, for build and test commands;
- the repositories in the folder, and the remotes they push to.

Note where each value came from. Never copy passwords, tokens or keys into the notes. The notes list the
repositories they cover (item 1); `/gc` ignores them for any other repository.

## 3. Show one card

Show the card below in one message, filled in with what you found. Mark each value "found in <file>", "default" or
"needs your answer". Ask the developer to reply with any changes, or "OK". Ask nothing else.

```
GC setup for <project folder>

1. Repositories:         <list>                               (found / default: the repositories in this folder)
2. Build and environment:
                         <environment needed (activation, or full-path commands); build command, or "none needed">
                                                              (found / default: from the project's docs)
3. Run one test:         <command and an example; any rule on where tests may run>
                                                              (found / default: from the project's docs)
4. Full suite before a push:
                         <none, or: where it runs, command, process count, log name, baseline rule, who launches it>
                                                              (default: none; rely on the project's CI)
5. Commit and push rules:
                         <the project's own: message rules, branch, how to push; or none>
                                                              (found / default: none beyond asking before a push)
6. Outside reviewer:     <which AI assistant you paste reviews into>
                                                              (default: "another AI assistant of your choice")
7. Live calls:           <allowed with safe test inputs, or ask before each one; where the keys come from>
                                                              (default: allowed with safe test inputs; ask first
                                                               for costly calls or calls with side effects;
                                                               keys never stored here)
8. Job log:              <off, or a file path>                (default: off)
9. Scratch folder:       <path>                               (default: the session's scratchpad, or /tmp/gc-<task>-<time>)
10. Exclusive use:       <is this installation used by one session at a time?>
                                                              (default: ask at each in-place swap)
11. Rebuild after a compiled change:
                         <command and folder>                 (found / default: from the project's docs)
```

**Domain defaults.** Offer these only when the project is that kind of project.

- **PHENIX / cctbx build:**
  - Build: `make` in the build folder (it runs `libtbx.scons`), after a change to compiled code.
  - Run one test: `<root>/build/bin/libtbx.python <path to test file>`, by full path, from an empty scratch folder.
    cctbx's AGENTS.md says never to source `build/setpaths.sh`.
  - Import note: `libtbx.python` puts the installation's main checkout first on the import path, so a second working
    copy is not isolated.
  - Full suite before a push: often run on a server as `phenix_regression.test_all_parallel nproc=<N> sort`, with the
    installation's `setpaths` sourced. Some developers call it "t96". Ask which server, installation, process count,
    log name and baseline rule apply, and who launches it.

## 4. Save

- **What is saved.** After the developer replies, write the card's final values, each with its source, and the date:
  into the notes file found in §1, or else into a new `.claude/GC_NOTES.md` in the project folder.
- **Keep it personal.** If a new file is inside a Git repository, add its path, relative to the repository root
  (`git rev-parse --show-prefix`), to the file that `git rev-parse --git-path info/exclude` names, so it is never
  committed. Say that you did.
- **Changing it later.** The developer can edit the file at any time, or run `/gc setup` again.
- **Then stop.** Report the file's path, and say that `/gc <task>` is ready to use.
