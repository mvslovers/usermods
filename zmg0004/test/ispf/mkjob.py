#!/usr/bin/env python3
"""Write the job that prepares a throwaway TK5 for the ISPF test.

    mkjob.py OUTPUT.jcl [--trace] [--nofilter] [--mvsce]

It links the new IKJCT441 into HERC01.ZMG4.LOAD under its own name (ISPF LOADs
IKJCT441 by name, so STEPLIB comes before the LPA and no CLPA is needed), loads
the test CLISTs, execs and the panel, and REPLACES SYS1.PROCLIB(ISPLOGON) with
a logon procedure that has those libraries and BREXX370.DEV.LINKLIB in front.
--mvsce targets MVS/CE: user IBMUSER, ISPF in SYSGEN.ISPF.*, the logon procedure
IKJACCNT, and ISPF started with EX 'IBMUSER.ZMG4.EXEC(ISPZ)' so that the test
libraries come first. Only for a throwaway system. --trace makes IKJCT441 TPUT the start and end of
each locate-all sequence and every update.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "..", "IKJCT441.ASM")).read().rstrip("\n").split("\n")


CE = "--mvsce" in sys.argv
HLQ = "IBMUSER" if CE else "HERC01"


def lib(name):
    return open(os.path.join(HERE, "lib", name)).read().replace("HERC01", HLQ).rstrip("\n").split("\n")


def members(*names):
    out = []
    for n in names:
        out.append(f"./ ADD NAME={n}")
        out += lib(n)
    return out + ["./ ENDUP", "@@"]


if "--nofilter" in sys.argv:
    # test only: return every name, to measure what ISPF does with them
    a = [k for k, l in enumerate(src) if l.startswith("         L     R1,SHVNAML          GET THE NAME LENGTH")][0]
    b = [k for k, l in enumerate(src) if l.startswith("         L     R1,RXLCOUNT         COUNT THE VARIABLES")][0]
    del src[a:b]

if "--nofree" in sys.argv:
    # test only: never free the chunks of a sequence nor the work block
    i = [k for k, l in enumerate(src) if l.startswith("         BAL   R14,RXCFREE ")][0]
    del src[i]
    i = [k for k, l in enumerate(src) if l.startswith("         FREEMAIN RU,LV=(0),A=(R8),SP=1")][0]
    del src[i]

if "--trace" in sys.argv:
    # test only: TPUT the start and end of a locate-all sequence and every update
    def trace(label, text):
        i = [k for k, l in enumerate(src) if l.startswith(label)][0]
        src[i:i] = ["         STM   R0,R15,TRSAV",
                    f"         TPUT  {text},8",
                    "         LM    R0,R15,TRSAV"]
    trace("         BAL   R14,RXCFREE ", "=CL8'LOC-BEG '")
    # RXUPDT and RXLOCEND carry a label on their first statement: put the trace behind it
    for label, text in (("RXUPDT   L", "=CL8'UPDATE  '"), ("RXLOCEND BAL", "=CL8'LOC-END '")):
        i = [k for k, l in enumerate(src) if l.startswith(label)][0]
        src[i + 1:i + 1] = ["         STM   R0,R15,TRSAV", f"         TPUT  {text},8", "         LM    R0,R15,TRSAV"]
    def show(label, tag):
        # one line per variable: tag, name, value, SHVRET
        i = [k for k, l in enumerate(src) if l.startswith(label)][0]
        src[i:i] = [
            "         STM   R0,R15,TRSAV",
            "         MVI   TRMSG,C' '",
            "         MVC   TRMSG+1(39),TRMSG",
            f"         MVC   TRMSG(4),=CL4'{tag}'",
            "         L     R1,SHVNAML",
            "         CH    R1,=H'12'",
            "         BNH   *+8",
            "         LA    R1,12",
            "         BCTR  R1,0",
            "         L     R2,SHVNAMA",
            "         EX    R1,TRMVN",
            "         MVI   TRMSG+17,C'='",
            "         ICM   R1,15,SHVVALL",
            "         BNP   *+24",
            "         CH    R1,=H'16'",
            "         BNH   *+8",
            "         LA    R1,16",
            "         BCTR  R1,0",
            "         L     R2,SHVVALA",
            "         EX    R1,TRMVV",
            "         TPUT  TRMSG,40",
            "         LM    R0,R15,TRSAV"]
    show("         B     EXIT00              VARIABLE SET", "UPD ")
    show("RXLOCPUT BAL", "LOC ")
    i = [k for k, l in enumerate(src) if l.startswith("WORKEND  DS")][0]
    src[i:i] = ["TRSAV    DS    16F", "TRMSG    DS    CL40"]
    i = [k for k, l in enumerate(src) if l.startswith("         TITLE ' CONSTANTS AND LITERALS '")][0]
    src[i:i] = ["         USING WORKAREA,R13", "TRMVN    MVC   TRMSG+4(0),0(R2)", "TRMVV    MVC   TRMSG+18(0),0(R2)", "         DROP  R13"]

j = ["//ZMG4SET JOB (1),'ZMG4 ISPF',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),",
     "//         REGION=8192K",
     "//DEL     EXEC PGM=IEFBR14",
     "//D1 DD DSN=HERC01.ZMG4.LOAD,DISP=(MOD,DELETE),UNIT=SYSDA,",
     "//   SPACE=(TRK,1)",
     "//D2 DD DSN=HERC01.ZMG4.EXEC,DISP=(MOD,DELETE),UNIT=SYSDA,",
     "//   SPACE=(TRK,1)",
     "//D3 DD DSN=HERC01.ZMG4.PLIB,DISP=(MOD,DELETE),UNIT=SYSDA,",
     "//   SPACE=(TRK,1)",
     "//ASM     EXEC PGM=IFOX00,PARM='OBJECT,NODECK,NOTERM,XREF(SHORT),RENT'",
     "//SYSLIB   DD DSN=SYS1.MACLIB,DISP=SHR",
     "//         DD DSN=SYS1.SMPMTS,DISP=SHR",
     "//         DD DSN=SYS1.AMODGEN,DISP=SHR",
     "//         DD DSN=SYS1.APVTMACS,DISP=SHR",
     "//SYSUT1   DD UNIT=VIO,SPACE=(CYL,10)",
     "//SYSUT2   DD UNIT=VIO,SPACE=(CYL,10)",
     "//SYSUT3   DD UNIT=VIO,SPACE=(CYL,10)",
     "//SYSPRINT DD SYSOUT=*",
     "//SYSGO    DD DSN=&&O441,DISP=(,PASS),UNIT=VIO,SPACE=(CYL,1)",
     "//SYSIN    DD *"] + src + ["/*",
     "//LKED    EXEC PGM=IEWL,PARM='LIST,MAP,NCAL,LET,RENT,REUS',COND=(0,NE)",
     "//SYSPRINT DD SYSOUT=*",
     "//SYSUT1   DD UNIT=VIO,SPACE=(CYL,1)",
     "//SYSLPA   DD DSN=SYS1.LPALIB,DISP=SHR",
     "//OBJ      DD DSN=&&O441,DISP=(OLD,DELETE)",
     "//SYSLMOD  DD DSN=HERC01.ZMG4.LOAD(IKJCT441),DISP=(NEW,CATLG),",
     "//            UNIT=SYSDA,SPACE=(CYL,(2,1,5)),",
     "//            DCB=(RECFM=U,BLKSIZE=19069)",
     "//SYSLIN   DD *",
     "  INCLUDE OBJ",
     "  REPLACE IKJCT441",
     "  INCLUDE SYSLPA(IKJPTGT)",
     "  ENTRY IKJCT441",
     "  NAME IKJCT441(R)",
     "/*",
     "//EXEC    EXEC PGM=IEBUPDTE,PARM=NEW,COND=(0,NE)",
     "//SYSPRINT DD SYSOUT=*",
     "//SYSUT2   DD DSN=HERC01.ZMG4.EXEC,DISP=(NEW,CATLG),UNIT=SYSDA,",
     "//            SPACE=(TRK,(5,5,5)),DCB=(RECFM=FB,LRECL=80,BLKSIZE=3120)",
     "//SYSIN    DD DATA,DLM=@@"] + members(
         "C1", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "C8", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "TA", "TB", "TC", "TD", "F1", "F5", "TE4", "CW", "ISPZ") + [
     "//PANEL   EXEC PGM=IEBUPDTE,PARM=NEW,COND=(0,NE)",
     "//SYSPRINT DD SYSOUT=*",
     "//SYSUT2   DD DSN=HERC01.ZMG4.PLIB,DISP=(NEW,CATLG),UNIT=SYSDA,",
     "//            SPACE=(TRK,(5,5,5)),DCB=(RECFM=FB,LRECL=80,BLKSIZE=3120)",
     "//SYSIN    DD DATA,DLM=@@"] + members("ZMGP", "ZMGQ") + [
     "//PROC    EXEC PGM=IEBUPDTE,PARM=MOD,COND=(0,NE)",
     "//SYSPRINT DD SYSOUT=*",
     "//SYSUT1   DD DSN=SYS1.PROCLIB,DISP=SHR",
     "//SYSUT2   DD DSN=SYS1.PROCLIB,DISP=SHR",
     "//SYSIN    DD DATA,DLM=@@",
     "./ REPL NAME=" + ("IKJACCNT" if CE else "ISPLOGON")] + lib("IKJACCNT" if CE else "ISPLOGON") + ["./ ENDUP", "@@"]
j = [x.replace("DSN=HERC01.", "DSN=" + HLQ + ".") for x in j]
open(sys.argv[1], "w").write("\n".join((x + " " * 80)[:80] for x in j) + "\n")
