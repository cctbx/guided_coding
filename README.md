# Guided Coding

Guided Coding is a Claude Code skill (`/guided_coding`, short name `/gc`) for
making careful, reviewed changes to a project: a short plan, a tested change
with its full diff for your decision, and publication as a separate choice.

The kit is the [`guided_coding/`](guided_coding) folder. Start with its
[User Guide](guided_coding/docs/GUIDED_CODING_USER_GUIDE.md); exact
registration commands are in the
[command reference](guided_coding/docs/GUIDED_CODING_COMMAND_REFERENCE.md),
and what the checks establish is in
[Verification and limits](guided_coding/docs/GUIDED_CODING_VERIFICATION.md).

Earlier releases, up to revision 20, were developed in cctbx_project, in
`libtbx/guided_coding`.
This repository carries that history; revision 21 is the first release here.

## Requirements

macOS or Linux, Claude Code, Git, and Python 3.10 or newer. Auto mode also
needs psutil. Windows is not supported.

## In a PHENIX installation

From your PHENIX folder (the one that contains `modules` and `build`):

```
git clone https://github.com/cctbx/guided_coding.git modules/guided_coding
```

If `modules/guided_coding` already exists, use it; do not delete it or clone
over it. The kit is then `modules/guided_coding/guided_coding`. Register it
once with the guarded block in the command reference ("One-time
registration"), using that path. `libtbx.python` is the installation's Python;
when it is not on your PATH, use `build/bin/libtbx.python` or
`conda_base/bin/python3` by absolute path.

### Moving from the copy in cctbx_project

If your registration points to `cctbx_project/libtbx/guided_coding`, clone as
above, then run, from your PHENIX folder:

```
sh modules/guided_coding/migrate_registration.sh
```

It checks the new copy (listed hashes, complete source and release label), and
re-points your registration (the link `~/.claude/skills/guided_coding`, and
`$CLAUDE_CONFIG_DIR/skills/guided_coding` when that is set) only if it is the
usual link to the old copy. It saves a restore note in the configuration
folder and removes its own leftover temporary links from an interrupted run;
otherwise it changes nothing, and it reports every place it checked. Running
it again is harmless. If the Claude app uses its own configuration folder, add
`--config-dir` and that folder. Then start a new Claude Code conversation,
between guided jobs rather than during one.

A PHENIX binary installation keeps its own copy, which keeps working. To move
anyway, clone into a folder you can write to that is not part of the
installation, for example `~/guided_coding`, and run the script from there.

## Without PHENIX

```
git clone https://github.com/cctbx/guided_coding.git ~/guided_coding
python3 -m venv ~/gc-python
~/gc-python/bin/python -m pip install psutil
```

`python3` must be 3.10 or newer. Use `~/gc-python/bin/python` wherever the
kit's commands say `libtbx.python`. Not `pip install --user`: the kit runs
Python with `-I`, which ignores the user site folder. Then register
`~/guided_coding/guided_coding` as the command reference describes.

## Tests

```
python3 tst_guided_coding.py
python3 tst_migrate_registration.py
```

`tst_guided_coding.py` copies the kit's listed files to a scratch folder and
runs the kit's own tests there. With libtbx available (for example with a
PHENIX installation's `libtbx.python`) it also checks the installer's
precompile step; otherwise it prints a skip for that part.
`tst_migrate_registration.py` tests `migrate_registration.sh` under `/bin/sh`
and, where it is installed, `dash`, and checks that the script's `EXPECTED_LABEL` matches the label in
`guided_coding/payload/RELEASE`; a new release must update both in the same
commit. CI runs both on Linux and macOS.

## Licence

The cctbx licence; see [LICENSE.txt](LICENSE.txt).
