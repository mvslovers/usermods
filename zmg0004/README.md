# ZMG0004 — IKJCT441 for REXX

`IKJCT441` with a REXX path: the variable access routine serves the variables
of a running REXX exec as well as CLIST variables, so ISPF dialog variables
work from REXX. Design: [`internals/ZMG0004.md`](../internals/ZMG0004.md).

Status: written and tested, **not ready**. No usermod packaging yet (MCS, jobs),
and there is an open defect under ISPF:

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
| `test/ZMGDRV.ASM` | Test driver, a TSO command processor: `C` CLIST regression, `R` REXX path, `O` which path wins inside a CLIST. It carries the stand-in REXX environment (`ENVBLOCK`, `IRXEXTE`, and `FAKEXCOM`, a variable routine over a small table that also checks how it is called) |
| `test/mktest.py` | Writes the test job: assembles both sources with IFOX00 on the target, links a private copy of the installed `IKJPTGT` with the new `IKJCT441` as `ZMGT441`, runs the driver in three batch TMP steps |
| `test/results-tk5.txt` | The driver's output from TK5 |

## The REXX path

At `REDRIVE` the module checks whether a REXX exec is the caller: ECT+X'30'
points to an `ENVBLOCK` of at least 320 bytes, its `IRXEXTE` has a variable
access routine, and `ENVBLOCK`+X'130' holds the input stack element that is
still on top. Then:

| Entry code | REXX path |
|---|---|
| 2 `TSVEUPDT` | SHVBLOCK `S` |
| 3 `TSVELOC` | SHVBLOCK `N`, after one other request that restarts the `N` sequence. Names and values go into chunks chained from `ENVBLOCK`+X'134', freed when the next sequence starts, because ISPF copies the values only after RC=20. Names with a period are not returned; the sequence ends after 2,048 names of up to 8 bytes |
| 1 `TSVERETR`, 18 `TSVNOIMP` | RC=40 for now: who owns the storage of a retrieved value is not decided yet. ISPF uses neither |

The routine is called only through the address in `IRXEXTE`, with the
`IRXEXCOM` parameter list (four entries; parameter 1 is the 8-byte string
`IRXEXCOM`, a parameter value and not a module name) and R0 -> `ENVBLOCK`.

Two changes on the CLIST side: the module identifies itself as
`IKJCT441 ZMG0004`, and without an LWA (not under a TMP) it returns RC=40
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
  variable is created; retrieve gives RC=40, a name length of 0 RC=36; with a
  stale top element the CLIST path runs (RC=40, no CLIST). `R7` reads the first
  located value after RC=20; the first version of this module abends there. The
  stand-in counted no call that broke the contract.
- **Which path wins inside a CLIST**: with the current top element recorded
  (a REXX exec started from the CLIST) the stand-in's variable comes back;
  with another element recorded (a CLIST on top of the exec) the CLIST's
  `TESTV` does.

- **Under ISPF** (`test/ispf`, TK5 only so far; the harness does not yet drive the
  command panel of MVS/CE): `VPUT` and `VGET` from a REXX dialog started with
  `%name` (through `ZMG0001`) and from a CLIST that calls the exec, a panel with
  input read back, 300 `ISPEXEC` calls in a row, 10,000 stem entries, for variables
  that exist before the first `ISPEXEC`; see the open defect above. ISPF sends no `TSVEUPDT` inside a `TSVELOC` sequence (traced
  for `VPUT`, `VGET`, `DISPLAY`).

Measured on the base as well: before the change, IFOX00 on TK5 gives the
object `ZP60038` ships (ESD, TXT and RLD equal; only the assembly date in the
END record differs).
