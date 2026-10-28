# GuidedCoding job log (version 1.4)

When the job ends (the developer has answered the open decisions, or says the job is done), append one line to the
job log (SKILL.md §6). Log stopped and abandoned jobs too. Separate the fields with tabs, use no tabs inside a
field, write `?` for anything you do not know, and do not change earlier lines. If the file does not exist yet,
start it with a header line of the field names below. If an older log has fewer fields, add the missing names at
the end of its header line; earlier rows keep their fields.

1. `date` (YYYY-MM-DD)
2. `job` (a few words)
3. `status`: completed, stopped or abandoned
4. `repositories` touched
5. `triggers`
6. `claude_minutes`: your session minutes (approximate)
7. `developer_minutes`: write `?`; the developer fills this in
8. `decisions_asked`: decisions put to the developer (a number)
9. `steps_skipped_or_changed`: steps skipped or done differently from these instructions, or `none`
10. `problems_caught`: step: what, or `none`
11. `ready_to_use`: yes, no, or accepted (something open was accepted or skipped by the developer)
12. `later_check_date`: about four weeks after the job (YYYY-MM-DD)
13. `later_defects`: write `?`; the developer fills this in at the later check, with date, severity and who found it
14. `notes`
15. `outside_review`: none, offered, done, pending or skipped; if done, add the developer's minutes on it and whether
    it was worth it (yes, no or `?`)
16. `project`: the folder the session was started in (full path)
17. `start_commits`: for each repository, `<path>@<starting commit>` (`<path>@none` for a folder not in Git),
    separated by ` ; `
18. `files_changed`: the files the job changed or added, with paths from the repository root, separated by ` ; `
    (for reading only; `/gc undo` works from the job folder and the current state, not from this field)
19. `commits`: the commits the job made (`<path>@<commit>`), or `none`
20. `pushed`: yes, no, or `none`
21. `report`: the full path of the saved report
22. `job_folder`: the full path of the job's folder of copies (SKILL.md §2), or `none`

Never write keys, passwords, tokens or other secrets in the log.
