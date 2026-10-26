# GuidedCoding job log (version 1.4)

When the job ends (the developer has answered the open decisions, or says the job is done), append one line to the
log file the notes name. Log stopped and abandoned jobs too. Separate the fields with tabs, use no tabs inside a
field, write `?` for anything you do not know, and do not change earlier lines. If the file does not exist yet,
start it with a header line of the field names below. If an older log has 14 fields, add `outside_review` at the
end of its header line; earlier rows keep 14 fields.

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
