#!/usr/bin/env python3
"""Write the job that prepares a throwaway TK5 for the ISPF test.

    mkjob.py OUTPUT.jcl [--trace]

It links the new IKJCT441 into HERC01.ZMG4.LOAD under its own name (ISPF LOADs
IKJCT441 by name, so STEPLIB comes before the LPA and no CLPA is needed), loads
the test CLISTs, execs and the panel, and REPLACES SYS1.PROCLIB(ISPLOGON) with
a logon procedure that has those libraries and BREXX370.DEV.LINKLIB in front.
Only for a throwaway system. --trace makes IKJCT441 TPUT every request.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "..", "IKJCT441.ASM")).read().rstrip("\n").split("\n")


def members(*names):
    out = []
    for n in names:
        out.append(f"./ ADD NAME={n}")
        out += open(os.path.join(HERE, "lib", n)).read().rstrip("\n").split("\n")
    return out + ["./ ENDUP", "@@"]


if "--nofilter" in sys.argv:
    # test only: return every name, to measure what ISPF does with them
    a = [k for k, l in enumerate(src) if l.startswith("         L     R1,SHVNAML          GET THE NAME LENGTH")][0]
    b = [k for k, l in enumerate(src) if l.startswith("         L     R1,RXLCOUNT         COUNT THE VARIABLES")][0]
    del src[a:b]

if "--trace" in sys.argv:
    i = [k for k, l in enumerate(src) if l.startswith("REDRIVE  L     R7,ECT@")][0]
    src[i + 1:i + 1] = [
        "         STM   R0,R15,TRSAV",
        "         L     R1,ECT@",
        "         ICM   R2,15,X'30'(R1)",
        "         ST    R2,TRENV",
        "         MVC   TRMSG(40),TRMOD",
        "         UNPK  TRMSG+9(3),ECODE+2(2)",
        "         UNPK  TRHEX(9),TRENV(5)",
        "         TR    TRHEX(8),TRTAB-240",
        "         MVC   TRMSG+18(8),TRHEX",
        "         TPUT  TRMSG,40",
        "         LM    R0,R15,TRSAV"]
    i = [k for k, l in enumerate(src) if l.startswith("WORKEND  DS")][0]
    src[i:i] = ["TRSAV    DS    16F", "TRENV    DS    F", "TRHEX    DS    CL9", "TRMSG    DS    CL40"]
    i = [k for k, l in enumerate(src) if l.startswith("         TITLE ' CONSTANTS AND LITERALS '")][0]
    src[i:i] = ["TRMOD    DC    CL40'CT441 EC=     ENV='", "TRTAB    DC    C'0123456789ABCDEF'"]

j = ["//ZMG4SET JOB (1),'ZMG4 ISPF',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),",
     "//         REGION=8192K",
     "//DEL     EXEC PGM=IEFBR14",
     "//D1 DD DSN=HERC01.ZMG4.LOAD,DISP=(MOD,DELETE),UNIT=SYSDA,SPACE=(TRK,1)",
     "//D2 DD DSN=HERC01.ZMG4.EXEC,DISP=(MOD,DELETE),UNIT=SYSDA,SPACE=(TRK,1)",
     "//D3 DD DSN=HERC01.ZMG4.PLIB,DISP=(MOD,DELETE),UNIT=SYSDA,SPACE=(TRK,1)",
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
         "C1", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "C8", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8") + [
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
     "./ REPL NAME=ISPLOGON"] + open(os.path.join(HERE, "lib", "ISPLOGON")).read().rstrip("\n").split("\n") + ["./ ENDUP", "@@"]
open(sys.argv[1], "w").write("\n".join((x + " " * 80)[:80] for x in j) + "\n")
