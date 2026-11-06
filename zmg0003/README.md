# ZMG0003 — IKJCT441 for REXX

`IKJCT441` with a REXX path: the variable access routine serves the variables
of a running REXX exec as well as CLIST variables, so ISPF dialog variables
work from REXX. Design: [`internals/ZMG0003.md`](../internals/ZMG0003.md).

Status: **superseded by the rework of `ZP60038` of 2026-11-06**, which carries this module
(see "ZMG0003 or the rework of ZP60038" below). `ZMG0003` was released with BREXX/370 3.1.0
and stays usable on a system with the older `ZP60038`; the id stays spent, and this repository
is being archived. The library (`usermod.py`, `usermod/`, `jcl/`) is measured through SMP, and the
SMP-built module equals the tested one (`test/results-package.txt`). There is an open defect under ISPF:

**Open defect, in ISPF and not in this module.** A variable that first appears
after the first `ISPEXEC` call of a dialog does not get its value back from `VGET`:
`VGET` ends with RC=0, ISPF sends no `TSVEUPDT`, the variable keeps its old value.
A plain CLIST shows the same with the unchanged `IKJCT441` of `ZP60038` on TK5
(`test/ispf/lib/H1` works, `H3` does not); so does REXX (`G1` works, `G3` does not).
With variables that all exist before the first `ISPEXEC`, 30 variables and long values
work. CLISTs rarely meet this, REXX execs usually do, because `RC` alone appears after
the first call. Reported to the author of ISPF.

| File | What it is |
|---|---|
| `IKJCT441.ASM` | The module. Greg Price's public-domain source from `ZP60038` (rework 2019-07-27) with the REXX path added; his header, author line and change log are kept |
| `test/ZMGDRV.ASM` | Test driver, a TSO command processor: `C` CLIST regression, `R` REXX path, `O` which path wins inside a CLIST, `F` reading a freed chunk. It carries the stand-in REXX environment (`ENVBLOCK`, `IRXEXTE`, and `FAKEXCOM`, a variable routine over a small table that also checks how it is called) |
| `test/mktest.py` | Writes the test job: assembles both sources with IFOX00 on the target, links a private copy of the installed `IKJPTGT` with the new `IKJCT441` as `ZMGT441`, runs the driver in three batch TMP steps |
| `test/lmodcmp.py` | Compares the tested `IKJPTGT` with the SMP-built one from AMBLIST listings, per CSECT, with controls |
| `test/results-package.txt` | The SMP package measured: install, ISPF from the LPA, removal, module comparison |
| `test/results-tk5.txt` | The driver's output from TK5 |
| `test/ispf/results-after.txt` | Real BREXX/370 execs under ISPF: two screens, nesting, attention, storage |

**Also in ISPF, seen 2026-11-05.** `VPUT`, a change of the variable and `VGET` with no
`DISPLAY` between: with `INNER` then `CLOBBER` the variable keeps `CLOBBER`, with `FROMXC`
then `OLD` it gets its value back, the same in a CLIST and in REXX (`test/ispf/results-after.txt`,
`XB`, `XU`, `XC`, `XA`). Whether it is the length of the values is not isolated.

## ZMG0003 or the rework of ZP60038

Rob Prins reworked `ZP60038` on 2026-11-06 (`++USERMOD(ZP60038) REWORK(20261106)`). Its
`IKJCT441` is this module: the source differs from `IKJCT441.ASM` in five lines of comment and
in the module text (`IKJCT441 ZP60038 20261103` instead of `IKJCT441 ZMG0003 20261103`). So
**`ZMG0003` is superseded: a new install takes the rework, and a system with the rework does
not need `ZMG0003`.** `ZMG0003` stays usable where the older `ZP60038` is applied, and its id
stays spent. `ZMG03CK` cannot tell the two apart: both show as `ZP60038` applied, and so does
`LIST CDS`. `AMBLIST` of `IKJPTGT` can, by the module text above.

Measured on fresh TK5 and MVS/CE, each in a throwaway system, with the older `ZP60038` applied:

- **The rework over the older `ZP60038`:** its install job replaces it without a `RESTORE`.
  `APPLY` ends with RC 0; the job ends with RC 4, from its `REJECT` (`HMA4081`). `IKJCT441`
  is the only CSECT of `IKJPTGT` that changes, and it differs from the one of `ZMG0003` in that
  one line of module text only (`test/lmodcmp.py`). TSO comes up after an IPL with CLPA.
- **`ZMG0003` after the rework:** `ZMG03AP` ends with RC 0 and `IKJPTGT` carries this
  usermod's module, which gains nothing. `RESTORE` of `ZMG0003` then needs the accept of the
  requisites as described below; without it RC 12 (`HMA3022`, `ZP60038 PRE`).
- **The rework after `ZMG0003`:** `APPLY` ends with RC 12 (`HMA3190`: `ZP60038` neither
  pre-requires nor supersedes the `RMID` `ZMG0003`), and `IKJPTGT` keeps the module of
  `ZMG0003`. Remove `ZMG0003` first ("Install and removal" below), then install the rework.
- **`RESTORE` of the rework:** with the requisites only applied, RC 12 (`HMA3022`) and nothing
  changes. With the requisites accepted, RC 0, but `ZP60038` disappears from the SMP inventory
  altogether and `IKJPTGT` keeps the reworked module: there is no way back to the older
  `ZP60038` through SMP, only through a backup of `IKJPTGT`.
- **On TK5 without any `ZP60038`** (`ZP60014` and `ZP60038` taken out with the `UCLIN` way
  below, `ZP60014` applied again): the install job of the rework ends with RC 0, and the module
  is the one above.

The install job of the rework was run with its high-level qualifier changed, because a TK5
system already has a library `USERMOD.ZP60038`. Not measured: an ISPF dialog with the rework,
and its install on MVS/CE without any `ZP60038`.

## Install and removal

`python3 zmg0003/usermod.py [--xmit]` builds the library `USERMOD.ZMG0003`. Run its jobs
in this order: `ZMG03CK`, `ZMG03BK`, `$INSTALL`, `ZMG03AP`. Step `REJ` of `$INSTALL` ends
with RC 12 on a first install; that is expected. The usermod is active after the next IPL
with CLPA. On MVS/CE that means answering `IEA101A` with `r 00,clpa`: its `IEASYS00` has no
`CLPA` and a plain IPL keeps the old module without any message. The TK5 image has `CLPA` in
`IEASYS00`, so every IPL there is one. A return code does not prove the module: `test/lmodcmp.py` compares it with the
tested one (`test/results-package.txt`).

**Accept the requisites first, so that `RESTORE` can take the usermod out again.** `ZMG0003`
itself is never accepted, but `RESTORE` refuses it (RC 12, HMA3022, `ZP60038 PRE`) while
`ZP60038` is only applied. Back up `SYS1.AOST4` and `SYS1.AGENLIB`, then run this before
`$INSTALL`. It ends with RC 4 from the links into `AOST4`; `USERMODS` is required, without it
HMA3652.

| System | Procedure | `ACCEPT` |
|---|---|---|
| MVS/CE | `SMPAPP` (there is no `SMPACC`) | `SELECT(UY01186,UY01301,UY13091,UY16532,UY17021,UZ44177,UZ47575,UZ47871,UZ48384,UZ48765,UZ82014,ZP60014,ZP60038) USERMODS` |
| TK5 | `SMPACC` | `SELECT(ZP60014,ZP60038) USERMODS` |

The MVS/CE list is the whole requisite chain of `ZP60038` not yet accepted there; TK5 has
the rest accepted already. On both, measured from a fresh system: `ACCEPT` leaves `IKJPTGT`
unchanged, `$INSTALL` and `ZMG03AP` run as usual, and `ZMG03RS` ends with `RESTORE` RC 0 and
`IKJPTGT` as it was before the install, also with `RESTORE` alone, without step `COPY`. TSO
came up after an IPL with CLPA (console checked), and a second install gave the same module. No ISPF dialog ran on this path; for dialogs on MVS/CE see "Under ISPF" below.

`ZMG03RS` removes the usermod, active after the next IPL with CLPA.

**Without the accept** `RESTORE` ends with RC 12 and `ZMG0003` stays in the SMP inventory.
Step `COPY` still brings back `IKJPTGT` from the backup of `ZMG03BK`, and the system runs
without the usermod (measured on TK5: after the IPL a dialog ends as without `ZMG0003`). TK5
as distributed takes this way: it accepts no usermods, because a later SYSGEN would build
from the distribution libraries.

**Without an accept on TK5**, the usermod and its requisites can also come out and the requisites
go back, if the `REJECT` indicator in the SMPPTS system entry is switched off first:

```
 UCLIN PTS .
 DEL SYS REJECT .
 ENDUCL .
 RESTORE SELECT(ZMG0003,ZP60014,ZP60038) .
 APPLY SELECT(ZP60014,ZP60038) DIS(WRITE) .
 UCLIN PTS .
 ADD SYS REJECT .
 ENDUCL .
```

Measured on a fresh TK5 with these as separate jobs, twice in a row: `RESTORE` RC 4, `APPLY` RC 0,
`IKJPTGT` line-identical to the state before the install, TSO up after the IPL, and a second install
gave the same module. `RESTORE` and `APPLY` need the DD statements for `LPALIB`, `AOST4` and
`AGENLIB`. `EXEC` in `SYS1.CMDLIB`, which `ZP60014` also changes, came back line-identical in a run of
`RESTORE` and `APPLY` without `ZMG0003`.

**Switch it off before the `RESTORE`.** With `REJECT=YES`, as distributed, `RESTORE` deletes the
three from the SMPPTS, the `APPLY` ends with RC 12 (`HMA4012`), and `ZP60014` and `ZP60038` stay
off the system until they are received again. On MVS/CE this way is not available without the
accept: `RESTORE` stops at the requisites that are only applied, such as `UY16532` and `UY17021`.

## The REXX path

At `REDRIVE` the module looks for a routine: ECT+X'30' points to an `ENVBLOCK` of at
least 320 bytes, and its `IRXEXTE` has a variable access routine. That routine decides:
R15 = -1 means no exec is the caller and the CLIST path runs, 28 and 32 give RC=40,
otherwise `SHVRET` holds the result. Then:

| Entry code | REXX path |
|---|---|
| 2 `TSVEUPDT` | SHVBLOCK `S` |
| 3 `TSVELOC` | SHVBLOCK `N`, after one other request that restarts the `N` sequence. Names and values go into chunks chained from `ENVBLOCK`+X'134', freed when the next sequence starts if this task owns them (`ENVBLOCK`+X'138'), because ISPF copies the values only after RC=20. Names with a period are not returned; the sequence ends after 2,048 names of up to 8 bytes |
| 1 `TSVERETR` | SHVBLOCK `F`; if the variable is new, `S` with the value of the caller, then `F` again. ISPF does not use it |
| 18 `TSVNOIMP` | SHVBLOCK `F`; if the variable is new, RC=52. ISPF does not use it |

The routine is called only through the address in `IRXEXTE`, with the
`IRXEXCOM` parameter list (four entries; parameter 1 is the 8-byte string
`IRXEXCOM`, a parameter value and not a module name) and R0 -> `ENVBLOCK`.

Two changes on the CLIST side: the module identifies itself as
`IKJCT441 ZMG0003`, and without an LWA (not under a TMP) it returns RC=40
instead of reading low storage.

## Limits of ISPF that a dialog meets

Measured on TK5 with ISPF V2R2M0, for CLIST and REXX alike unless noted.

| Limit | What happens |
|---|---|
| A dialog variable name has at most 8 characters | `VPUT` with a 9-character name ends with RC=20. Longer names can exist in the CLIST or exec; ISPF skips them when it collects the variables, and they do not use up its table (2,100 long names in a CLIST, 3,000 in an exec: RC=0) |
| ISPF collects at most 2,048 variables per `ISPEXEC` call | A table of 32 KB with 16 bytes per entry and no check of its end. A CLIST with 2,000 short names works; with 2,100 the process abends, also with the unchanged `IKJCT441` of `ZP60038`. On the REXX path `IKJCT441` stops at 2,048 names |
| Variables reach ISPF only in a dialog started with `SELECT CMD(%name)` | Started as `EX` or `RX` from option 6, or as `SELECT CMD(EX ...)`, `VPUT` ends with RC=8, also for a plain CLIST. A REXX exec needs `%name` through `ZMG0001`, or a CLIST started that way which calls it |
| Stems and compound variables | On the REXX path `IKJCT441` does not return names with a period. Otherwise 2,048 stem entries would fill the table and hide the simple variables |

## Tests

`python3 test/mktest.py ZMGTEST.jcl` writes the job; submit it to a
throwaway TK5 system. The test copy `ZMGT441` comes first through `STEPLIB`,
so nothing is installed and no CLPA is needed; the CLIST executor keeps
using the installed `IKJPTGT`.

Results on TK5 (`test/results-tk5.txt`):

- **CLIST regression** (TK5 and MVS/CE, `results-tk5.txt`, `results-mvsce.txt`):
  the same CLIST runs the same sequence twice, in two TMP steps, once against the
  installed `IKJCT441` and once against `ZMGT441`. Of the 53 lines, 52 are equal;
  the one that differs is the CLIST's own parameter `OP` (`C` or `D`), which selects
  the module. The sequence: retrieve, update and retrieve, an undefined name (RC=52),
  retrieve/create of a new name (the 2019 rework, re-driven through `REDRIVE`), an
  update with a value longer than the original (a new value element through
  `IKJINIT` in the private copy), and a full locate-all.
- **REXX path**: locate-all returns the stand-in's variables and ends with
  RC=20 and a zero token; an update shows in the next locate-all; a new
  variable is created; a name length of 0 gives RC=36. Retrieve returns the value
  (`R4`), an undefined name RC=52 (`R8`), retrieve/create takes the caller's value
  only for a new variable (`R9`, `RA`), and a retrieved value survives the next
  retrieve (`RB`). With -1 from the routine the CLIST path runs (`R6`: RC=40, no
  CLIST; `O2` to `O4`: the CLIST is served, a whole locate-all included); 28 and 32
  give RC=40 (`RE`, `RF`). Chunks owned by another task are not touched, even freed
  ones (`RC`), and reading a freed chunk does abend, S0C4-11 (step `TMPF`). `R7` reads the first
  located value after RC=20; the first version of this module abends there. The
  stand-in counted no call that broke the contract.
- **Which path wins inside a CLIST**: with the current top element recorded
  (a REXX exec started from the CLIST) the stand-in's variable comes back;
  with another element recorded (a CLIST on top of the exec) the CLIST's
  `TESTV` does.

- **Under ISPF** (`test/ispf`, on TK5; this harness does not yet drive the
  command panel of MVS/CE): `VPUT` and `VGET` from a REXX dialog started with
  `%name` (through `ZMG0001`) and from a CLIST that calls the exec, a panel with
  input read back, 300 `ISPEXEC` calls in a row, 10,000 stem entries, for variables
  that exist before the first `ISPEXEC`; see the open defect above. ISPF sends no `TSVEUPDT` inside a `TSVELOC` sequence (traced
  for `VPUT`, `VGET`, `DISPLAY`).
- **Under ISPF on MVS/CE**, seen 2026-11-05 on a system with `ZMG0003` applied and an IPL
  with CLPA, by hand and with interactive tests rather than with `test/ispf`: a REXX dialog
  started from option 6 with `SELECT CMD(%name)` shows its panels with the variables of the
  exec, and `VPUT` and `VGET` with `PROFILE` keep its values from one run to the next
  (first run `VGET` RC 8, `VPUT` RC 0, next run `VGET` RC 0 with the saved values).

Measured on the base as well: before the change, IFOX00 on TK5 gives the
object `ZP60038` ships (ESD, TXT and RLD equal; only the assembly date in the
END record differs).
