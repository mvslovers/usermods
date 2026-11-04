#!/usr/bin/env python3
"""Write the job for the screen and stack measurements on a throwaway TK5.

    mkwho.py OUTPUT.jcl [--add]

Builds ZMGWHO (see ZMGWHO.ASM), ZMGABND (abends S0C1) and ZMGSET, loads the test CLISTs
and panel, and REPLACES SYS1.PROCLIB(ISPLOGON). Only for a throwaway system. --add only adds ZMGWHO and the panels to the
libraries mkjob.py made, for the two-screen test with real execs.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
who = open(os.path.join(HERE, "ZMGWHO.ASM")).read().rstrip("\n").split("\n")
abnd = ["ZMGABND  CSECT", "         DC    H'0'", "         END"]
# ZMGSET stores the top input stack element in ECT+X'30', to see whether ISPF swaps the word per screen
zset = ["ZMGSET   CSECT", "         L     1,12(,1)", "         L     2,4(,1)", "         L     2,0(,2)",
        "         ST    2,X'30'(,1)", "         SLR   15,15", "         BR    14", "         END"]
clists = {
    "N1": ["PROC 0", "WRITE N1", "ZMGWHO"],
    "N2": ["PROC 0", "WRITE N2 BEFORE", "ZMGWHO", "%N1", "WRITE N2 AFTER", "ZMGWHO"],
    "A1": ["PROC 0", "WRITE A1 BEFORE ABEND", "ZMGWHO", "ZMGABND", "WRITE A1 AFTER ABEND", "ZMGWHO"],
    "R1": ["PROC 0", "WRITE R1 BEFORE READ", "ZMGWHO", "READ &X", "WRITE R1 AFTER READ", "ZMGWHO"],
    "S1": ["PROC 0", "WRITE S1 BEFORE", "ZMGWHO", "ISPEXEC DISPLAY PANEL(ZMGS)",
           "WRITE S1 AFTER", "ZMGWHO"],
    "S2": ["PROC 0", "WRITE S2 BEFORE", "ZMGWHO", "ISPEXEC DISPLAY PANEL(ZMGS)",
           "WRITE S2 AFTER", "ZMGWHO"],
}
panel = [")BODY", "%ZMGWHO TEST PANEL", "%COMMAND ===>_ZCMD", "+", ")END"]
proc = [l for l in open(os.path.join(HERE, "lib", "ISPLOGON")).read().rstrip("\n").split("\n")
        if "BREXX370" not in l]
i = [k for k, l in enumerate(proc) if l.startswith("//SYSPROC")][0]
proc[i:i + 1] = ["//SYSPROC  DD  DISP=SHR,DSN=HERC01.ZMG4.EXEC", "//         DD  DISP=SHR,DSN=SYS1.CMDPROC"]


def asm(name, src):
    return [f"//A{name[3:]:<7} EXEC PGM=IFOX00,PARM='OBJECT,NODECK,NOTERM'",
            "//SYSLIB   DD DSN=SYS1.MACLIB,DISP=SHR",
            "//SYSUT1   DD UNIT=VIO,SPACE=(CYL,5)",
            "//SYSUT2   DD UNIT=VIO,SPACE=(CYL,5)",
            "//SYSUT3   DD UNIT=VIO,SPACE=(CYL,5)",
            "//SYSPRINT DD SYSOUT=*",
            "//SYSGO    DD DSN=&&OBJ,DISP=(,PASS),UNIT=VIO,SPACE=(CYL,1)",
            "//SYSIN    DD *"] + src + ["/*",
            f"//L{name[3:]:<7} EXEC PGM=IEWL,PARM='LIST,MAP,NCAL,LET'",
            "//SYSPRINT DD SYSOUT=*",
            "//SYSUT1   DD UNIT=VIO,SPACE=(CYL,1)",
            "//SYSLIN   DD DSN=&&OBJ,DISP=(OLD,DELETE)",
            f"//SYSLMOD  DD DSN=HERC01.ZMG4.LOAD({name}),DISP=SHR"]


def upd(dsn, mem):
    out = ["//UPD      EXEC PGM=IEBUPDTE,PARM=NEW", "//SYSPRINT DD SYSOUT=*",
           f"//SYSUT2   DD DSN={dsn},DISP=SHR", "//SYSIN    DD DATA,DLM=@@"]
    for n, b in mem.items():
        out.append(f"./ ADD NAME={n}")
        out += b
    return out + ["./ ENDUP", "@@"]


panels = {"ZMGS": panel,
          "ZMGT": [")BODY", "%ZMGT TEST PANEL", "%COMMAND ===>_ZCMD", "+FIELD   ===>_FLD ", "+", ")END"]}
ADD = "--add" in sys.argv
j = ["//ZMG4WHO JOB (1),'ZMG4 WHO',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),",
     "//         REGION=4096K"]
if ADD:
    j += asm("ZMGWHO", who) + upd("HERC01.ZMG4.PLIB", panels)
    open(sys.argv[1], "w").write("\n".join((x + " " * 80)[:80] for x in j) + "\n")
    sys.exit(0)
j += ["//DEL     EXEC PGM=IEFBR14"]
for k, d in (("D1", "LOAD"), ("D2", "EXEC"), ("D3", "PLIB")):
    j += [f"//{k} DD DSN=HERC01.ZMG4.{d},DISP=(MOD,DELETE),UNIT=SYSDA,", "//   SPACE=(TRK,1)"]
j += ["//ALC     EXEC PGM=IEFBR14",
      "//A1 DD DSN=HERC01.ZMG4.LOAD,DISP=(NEW,CATLG),UNIT=SYSDA,",
      "//   SPACE=(TRK,(10,5,5)),DCB=(RECFM=U,BLKSIZE=19069)",
      "//A2 DD DSN=HERC01.ZMG4.EXEC,DISP=(NEW,CATLG),UNIT=SYSDA,",
      "//   SPACE=(TRK,(5,5,5)),DCB=(RECFM=FB,LRECL=80,BLKSIZE=3120)",
      "//A3 DD DSN=HERC01.ZMG4.PLIB,DISP=(NEW,CATLG),UNIT=SYSDA,",
      "//   SPACE=(TRK,(5,5,5)),DCB=(RECFM=FB,LRECL=80,BLKSIZE=3120)"]
j += asm("ZMGWHO", who) + asm("ZMGABND", abnd) + asm("ZMGSET", zset)
j += upd("HERC01.ZMG4.EXEC", clists) + upd("HERC01.ZMG4.PLIB", panels)
j += ["//PROC    EXEC PGM=IEBUPDTE,PARM=MOD", "//SYSPRINT DD SYSOUT=*",
      "//SYSUT1   DD DSN=SYS1.PROCLIB,DISP=SHR", "//SYSUT2   DD DSN=SYS1.PROCLIB,DISP=SHR",
      "//SYSIN    DD DATA,DLM=@@", "./ REPL NAME=ISPLOGON"] + proc + ["./ ENDUP", "@@"]
open(sys.argv[1], "w").write("\n".join((x + " " * 80)[:80] for x in j) + "\n")
