import os,sys
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")+"/"
def src(p): return open(R+p).read().rstrip("\n").split("\n")
def c(s): return (s+" "*80)[:80]
asmstep=lambda name,obj,s: [
f"//{name:<8}EXEC PGM=IFOX00,PARM='OBJECT,NODECK,NOTERM,XREF(SHORT),RENT'",
"//SYSLIB   DD DSN=SYS1.MACLIB,DISP=SHR",
"//         DD DSN=SYS1.SMPMTS,DISP=SHR",
"//         DD DSN=SYS1.AMODGEN,DISP=SHR",
"//         DD DSN=SYS1.APVTMACS,DISP=SHR",
"//SYSUT1   DD UNIT=VIO,SPACE=(CYL,10)",
"//SYSUT2   DD UNIT=VIO,SPACE=(CYL,10)",
"//SYSUT3   DD UNIT=VIO,SPACE=(CYL,10)",
"//SYSPRINT DD SYSOUT=*",
f"//SYSGO    DD DSN=&&{obj},DISP=(,PASS),UNIT=VIO,SPACE=(CYL,1)",
"//SYSIN    DD *"]+s+["/*"]
j=["//ZMG4T1 JOB (1),'ZMG4 TEST',CLASS=A,MSGCLASS=H,MSGLEVEL=(1,1),",
"//         REGION=8192K"]
j+=asmstep("ASM441","O441",src("IKJCT441.ASM"))
j+=["//LKD441  EXEC PGM=IEWL,PARM='LIST,MAP,XREF,NCAL,LET,RENT,REUS',",
"//         COND=(0,NE)",
"//SYSPRINT DD SYSOUT=*",
"//SYSUT1   DD UNIT=VIO,SPACE=(CYL,1)",
"//SYSLPA   DD DSN=SYS1.LPALIB,DISP=SHR",
"//OBJ      DD DSN=&&O441,DISP=(OLD,DELETE)",
"//SYSLMOD  DD DSN=&&LOAD(ZMGT441),DISP=(,PASS),UNIT=VIO,",
"//            SPACE=(CYL,(2,1,5))",
"//SYSLIN   DD *",
"  INCLUDE OBJ",
"  REPLACE IKJCT441",
"  INCLUDE SYSLPA(IKJPTGT)",
"  ENTRY IKJCT441",
"  NAME ZMGT441(R)",
"/*"]
s=asmstep("ASMDRV","ODRV",src("test/ZMGDRV.ASM"))
s[0]=s[0].replace(",RENT'","'")
j+=s
j+=["//LKDDRV  EXEC PGM=IEWL,PARM='LIST,MAP,LET',COND=(0,NE)",
"//SYSPRINT DD SYSOUT=*",
"//SYSUT1   DD UNIT=VIO,SPACE=(CYL,1)",
"//SYSLMOD  DD DSN=&&LOAD(ZMGDRV),DISP=(OLD,PASS)",
"//SYSLIN   DD DSN=&&ODRV,DISP=(OLD,DELETE)",
"//CLIST   EXEC PGM=IEBUPDTE,PARM=NEW,COND=(0,NE)",
"//SYSPRINT DD SYSOUT=*",
"//SYSUT2   DD DSN=&&PROC,DISP=(,PASS),UNIT=VIO,SPACE=(TRK,(2,1,2)),",
"//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=800)",
"//SYSIN    DD DATA",
"./ ADD NAME=TESTC","PROC 1 OP","SET &TESTV = HELLOWORLD","SET &X1 = ONE","ZMGDRV &OP",
"./ ADD NAME=TESTO","PROC 0","SET &TESTV = HELLOWORLD","ZMGDRV O",
"./ ENDUP","/*"]
for step,inp in (("TMPC","%TESTC C"),("TMPD","%TESTC D"),("TMPR","ZMGDRV R"),("TMPO","%TESTO")):
    j+=[f"//{step:<8}EXEC PGM=IKJEFT01,COND=EVEN",
    "//STEPLIB  DD DSN=&&LOAD,DISP=(OLD,PASS)",
    "//SYSPROC  DD DSN=&&PROC,DISP=(OLD,PASS)",
    "//SYSTSPRT DD SYSOUT=*",
    "//SYSUDUMP DD SYSOUT=*",
    "//SYSTSIN  DD *",inp,"/*"]
open(sys.argv[1] if len(sys.argv)>1 else "ZMGTEST.jcl","w").write("\n".join(c(x) for x in j)+"\n")
