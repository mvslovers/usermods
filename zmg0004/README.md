# ZMG0004 — IKJCT441 for REXX

`IKJCT441` with a REXX path: the variable access routine serves the variables
of a running REXX exec as well as CLIST variables, so ISPF dialog variables
work from REXX. Design: [`internals/ZMG0004.md`](../internals/ZMG0004.md).

Status: the module is written and tested against a stand-in REXX
environment. Not yet packaged as a usermod (MCS, jobs), and no REXX
implementation fulfils the contract yet.

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
| 3 `TSVELOC` | SHVBLOCK `N`; the name and value of the variable returned live in a subpool 1 block the token addresses, until the next call; RC=20 frees it and resets the token |
| 1 `TSVERETR`, 18 `TSVNOIMP` | RC=40 for now: who owns the storage of a retrieved value is not decided yet. ISPF uses neither |

The routine is called only through the address in `IRXEXTE`, with the
`IRXEXCOM` parameter list (four entries; parameter 1 is the 8-byte string
`IRXEXCOM`, a parameter value and not a module name) and R0 -> `ENVBLOCK`.

Two changes on the CLIST side: the module identifies itself as
`IKJCT441 ZMG0004`, and without an LWA (not under a TMP) it returns RC=40
instead of reading low storage.

## Tests

`python3 test/mktest.py ZMGTEST.jcl` writes the job; submit it to a
throwaway TK5 system. The test copy `ZMGT441` comes first through `STEPLIB`,
so nothing is installed and no CLPA is needed; the CLIST executor keeps
using the installed `IKJPTGT`.

Results on TK5 (`test/results-tk5.txt`):

- **CLIST regression**: the installed `IKJCT441` and `ZMGT441` give the same
  48 lines: retrieve, update and retrieve, an undefined name (RC=52), and a
  full locate-all over the CLIST's own and the system variables.
- **REXX path**: locate-all returns the stand-in's variables and ends with
  RC=20 and a zero token; an update shows in the next locate-all; a new
  variable is created; retrieve gives RC=40, a name length of 0 RC=36; with a
  stale top element the CLIST path runs (RC=40, no CLIST). The stand-in saw
  15 calls and no call that broke the contract.
- **Which path wins inside a CLIST**: with the current top element recorded
  (a REXX exec started from the CLIST) the stand-in's variable comes back;
  with another element recorded (a CLIST on top of the exec) the CLIST's
  `TESTV` does.

Measured on the base as well: before the change, IFOX00 on TK5 gives the
object `ZP60038` ships (ESD, TXT and RLD equal; only the assembly date in the
END record differs).
