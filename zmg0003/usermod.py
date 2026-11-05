#!/usr/bin/env python3
"""zmg0003/usermod.py - build the library USERMOD.ZMG0003 of this usermod.

The same form as ZMG0001 (mvslovers/brexx370 tso/usermod.py), the TK5 convention:
one source library, assembled on the target system.

    python3 zmg0003/usermod.py [--xmit]
        build/zmg0003/pds/          the members, as host files
        build/zmg0003/ZMG0003.zip   the same members, for upload
        build/zmg0003/ZMG0003.xmit  with --xmit: the library as a TSO TRANSMIT
                                    file (xmit370 from the cc370 toolchain)

    @CVRLET   cover letter and MCS (usermod/ZMG0003.mcs)
    IKJCT441  the source
    $INSTALL  job: assemble with IFOX00, store the object plus the card
              IDENTIFY IKJCT441('ZMG0003') in a temporary PDS, REJECT,
              RECEIVE, APPLY CHECK
    ZMG03CK   job: check the prerequisites (jcl/)
    ZMG03BK   job: back up IKJPTGT (jcl/)
    ZMG03AP   job: assemble again and APPLY
    ZMG03RS   job: RESTORE, then copy the backup back (jcl/)

Checks, since a wrong job fails on MVS only after a RECEIVE: MCS lines fit in 72
columns, source cards in 80, all plain ASCII; no source card starts with //, /*
or ++; every ++MOD names its source in TXLIB(); one ++USERMOD and one ++VER; the
JCL cards of every job end before column 72.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
BUILD = Path("build/zmg0003")
PDS = "USERMOD.ZMG0003"
PARM = "OBJECT,NODECK,NOTERM,XREF(SHORT),RENT"
# Fixed date of this usermod level: zip member time and XMIT statistics, so
# the same sources give byte-identical ZMG0003.zip and ZMG0003.xmit.
USERMOD_DATE = (2026, 1, 1, 0, 0, 0)
JOB_CARD = "//{name:<8} JOB (USERMOD),'ZMG0003',CLASS=A,\n" \
           "//         MSGCLASS=H,MSGLEVEL=(1,1)\n"

HEAD_IN = """\
//*
//* ZMG0003 (IKJCT441 FOR REXX) - ASSEMBLE, RECEIVE, CHECK
//*
//* RUN ZMG03CK AND ZMG03BK FIRST.  THE USERMOD COMES AS SOURCE IN THE
//* LIBRARY {pds}.  THE STEPS ASSEMBLE IKJCT441 WITH IFOX00,
//* STORE THE OBJECT WITH AN IDENTIFY CARD IN THE TEMPORARY LIBRARY
//* &&TXLIB, AND LET SMP RECEIVE THE MCS (MEMBER @CVRLET) AND THE TXLIB
//* MEMBER.  THE ASSEMBLY MUST END WITH RC 0.  A STEP THAT FAILS STOPS
//* THE JOB BEFORE SMP.
//* STEP REJ REJECTS ZMG0003 FIRST, SO THE JOB CAN BE RUN AGAIN.  ITS
//* RC IS 12 WHEN ZMG0003 WAS NOT RECEIVED - EXPECTED ON THE FIRST RUN.
//* STEP SMP ENDS WITH THE RC OF RECEIVE AND APPLY CHECK.  THE APPLY
//* CHECK CHANGES NOTHING.
//*
"""

HEAD_AP = """\
//*
//* ZMG0003 (IKJCT441 FOR REXX) - ASSEMBLE AND APPLY
//*
//* RUN ZMG03CK, ZMG03BK AND $INSTALL FIRST.  SMP TAKES THE TEXT OF A
//* ++MOD FROM ITS TXLIB DD AT APPLY TIME, AND THE TEMPORARY LIBRARY OF
//* $INSTALL IS GONE WHEN THAT JOB ENDS.  SO THIS JOB ASSEMBLES
//* IKJCT441 AGAIN FROM THE LIBRARY {pds} AND THEN APPLIES.
//* THE USERMOD BECOMES ACTIVE WITH THE NEXT IPL WITH CLPA.
//* DO NOT ACCEPT ZMG0003.
//*
"""

ASM_STEP = """\
//{asm:<8} EXEC PGM=IFOX00,COND=(0,LT),
//            PARM='{parm}'
//SYSPRINT DD SYSOUT=*
//SYSUT1   DD UNIT=SYSALLDA,SPACE=(CYL,10)
//SYSUT2   DD UNIT=SYSALLDA,SPACE=(CYL,10)
//SYSUT3   DD UNIT=SYSALLDA,SPACE=(CYL,10)
//SYSLIB   DD DSN=SYS1.MACLIB,DISP=SHR
//         DD DSN=SYS1.SMPMTS,DISP=SHR
//         DD DSN=SYS1.AMODGEN,DISP=SHR
//         DD DSN=SYS1.APVTMACS,DISP=SHR
//SYSGO    DD DSN=&&OBJ,UNIT=SYSALLDA,SPACE=(TRK,(15,15)),
//            DISP=(,PASS),
//            DCB=(DSORG=PS,RECFM=FB,LRECL=80,BLKSIZE=3200)
//SYSIN    DD DSN={pds}({name}),DISP=SHR
"""

TXL_STEP = """\
//{txl:<8} EXEC PGM=IEBGENER,COND=(0,LT)
//SYSPRINT DD SYSOUT=*
//SYSIN    DD DUMMY
//SYSUT1   DD DSN=&&OBJ,DISP=(OLD,DELETE)
//         DD DDNAME=ADDREC
//SYSUT2   DD DSN=&&TXLIB({name}),{alloc}
//ADDREC   DD *
    IDENTIFY {name}('{sysmod}')
/*
"""

TXL_NEW = """UNIT=SYSALLDA,
//            SPACE=(TRK,(10,10,2)),DISP=(,PASS),
//            DCB=(DSORG=PO,RECFM=FB,LRECL=80,BLKSIZE=3200)"""
TXL_ADD = "DISP=(MOD,PASS)"

REJ = """\
//REJ      EXEC SMPAPP,COND=({cond})
//HMASMP.SMPCNTL  DD *
 REJECT S({sysmod}) .
/*
"""

SMP = """\
//SMP      EXEC SMPAPP,COND=({cond})
//HMASMP.LPALIB   DD DSN=SYS1.LPALIB,DISP=SHR
//HMASMP.AOST4    DD DSN=SYS1.AOST4,DISP=SHR
{txdd}{ptfin}//HMASMP.SMPCNTL  DD *
{cntl}/*
//
"""
SMP_IN = (" RECEIVE SELECT({sysmod}) .\n"
          " APPLY SELECT({sysmod}) CHECK .\n")
SMP_AP = " APPLY SELECT({sysmod}) .\n"
PTFIN = "//HMASMP.SMPPTFIN DD DSN={pds}(@CVRLET),DISP=SHR\n"
TXDD_FIRST = "//HMASMP.{name:<8} DD DSN=&&TXLIB,DISP=(OLD,PASS)\n"
TXDD_NEXT = ("//HMASMP.{name:<8} DD DSN=*.{first},VOL=REF=*.{first},\n"
            "//            DISP=(OLD,PASS)\n")


def read_cards(path):
    """File text as cards; only a newline ends one (a form feed does not)."""
    cards = path.read_text(encoding="ascii").split("\n")
    if cards and cards[-1] == "":
        cards.pop()
    return cards


def ascii_line(text, what, limit):
    if len(text) > limit:
        raise SystemExit(f"{what}: longer than {limit} columns: {text!r}")
    if not text.isascii() or any(ord(ch) < 32 for ch in text):
        raise SystemExit(f"{what}: not plain ASCII: {text!r}")


def source(name):
    """The cards of <name>.ASM, checked."""
    cards = read_cards(HERE / f"{name}.ASM")
    for i, c in enumerate(cards, 1):
        what = f"{name}.ASM card {i}"
        ascii_line(c, what, 80)
        if c[:2] in ("//", "/*", "++"):
            raise SystemExit(f"{what} starts with {c[:2]!r}: {c!r}")
    return cards


def check_statements(lines):
    for stmt in ("++USERMOD", "++VER"):
        n = sum(1 for ln in lines if ln.startswith(stmt))
        if n != 1:
            raise SystemExit(f"{n} {stmt} statements, expected exactly 1")


def modules(lines):
    """The ++MOD names, in order; each must carry TXLIB(name)."""
    out = []
    for i, ln in enumerate(lines, 1):
        ascii_line(ln, f"MCS line {i}", 72)
        m = re.match(r"\+\+MOD\((\w+)\)", ln)
        if m:
            name = m.group(1)
            if f"TXLIB({name})" not in ln:
                raise SystemExit(f"++MOD({name}) has no TXLIB({name}): {ln!r}")
            out.append(name)
    if not out:
        raise SystemExit("no ++MOD statement")
    return out


def job(kind, sysmod, mods):
    """Job text for kind "IN" ($INSTALL: assemble, REJECT, RECEIVE, APPLY
    CHECK) or "AP" (ZMG03AP: assemble, APPLY)."""
    name = "ZMG03IN" if kind == "IN" else "ZMG03AP"
    text = [JOB_CARD.format(name=name),
            (HEAD_IN if kind == "IN" else HEAD_AP).format(pds=PDS)]
    txdd = ""
    for n, mod in enumerate(mods):
        text.append(ASM_STEP.format(asm=f"ASM{mod[-3:]}", parm=PARM,
                                    pds=PDS, name=mod))
        text.append(TXL_STEP.format(txl=f"TXL{mod[-3:]}", name=mod,
                                    sysmod=sysmod,
                                    alloc=TXL_ADD if n else TXL_NEW))
        txdd += (TXDD_NEXT.format(name=mod, first=mods[0]) if n
                 else TXDD_FIRST.format(name=mod))
    steps = [f"{p}{m[-3:]}" for m in mods for p in ("ASM", "TXL")]
    cond = ",\n//            ".join(f"(0,LT,{x})" for x in steps)
    if kind == "IN":
        text.append(REJ.format(sysmod=sysmod, cond=cond))
    text.append(SMP.format(
        cond=cond, txdd=txdd,
        ptfin=PTFIN.format(pds=PDS) if kind == "IN" else "",
        cntl=(SMP_IN if kind == "IN" else SMP_AP).format(sysmod=sysmod)))
    return "".join(text)


def check_job(member, text):
    for i, ln in enumerate(text.splitlines(), 1):
        ascii_line(ln, f"{member} line {i}", 80)
        if ln.startswith("//") and len(ln) > 71:
            raise SystemExit(f"{member} line {i}: JCL card over column 71: "
                             f"{ln!r}")


def members(sysmod, mcs):
    """[(member, host name, zip name, text)] in the order of the library."""
    mods = modules(mcs)
    check_statements(mcs)
    out = [("@CVRLET", "CVRLET", "@CVRLET.mcs",
            "".join(c + "\n" for c in mcs))]
    for mod in mods:
        cards = source(mod)
        out.append((mod, mod, f"{mod}.asm", "".join(c + "\n" for c in cards)))
        print(f"  {mod}: {len(cards)} source cards")
    out.append(("$INSTALL", "INSTALL", "$INSTALL.jcl",
                job("IN", sysmod, mods)))
    for m in ("ZMG03CK", "ZMG03BK"):
        out.append((m, m, f"{m}.jcl",
                    (HERE / "jcl" / f"{m}.jcl").read_text(encoding="ascii")))
    out.append(("ZMG03AP", "ZMG03AP", "ZMG03AP.jcl",
                job("AP", sysmod, mods)))
    out.append(("ZMG03RS", "ZMG03RS", "ZMG03RS.jcl",
                (HERE / "jcl" / "ZMG03RS.jcl").read_text(encoding="ascii")))
    for member, _, _, text in out:
        if member.startswith(("$", "ZMG")):
            check_job(member, text)
    return out


def write_zip(path, items):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for _, _, zname, text in items:
            z.writestr(zipfile.ZipInfo(zname, USERMOD_DATE), text,
                       zipfile.ZIP_DEFLATED)


def write_xmit(path, items, pds):
    exe = shutil.which("xmit370")
    if exe is None:
        raise SystemExit("xmit370 not on PATH (cc370 toolchain: "
                         "make xmit370/xmit370 in mvslovers/cc370)")
    cmd = [exe, "create", "-o", str(path), "--dsn", pds, "--lrecl", "80",
           "--blocksize", "3120", "--tabs", "0",
           "--stats-date", "%04d-%02d-%02dT%02d:%02d:%02d" % USERMOD_DATE]
    for member, host, _, _ in items:
        cmd += ["--member", f"{member}={BUILD / 'pds' / host}"]
    empty = BUILD / "nomembers"
    empty.mkdir(exist_ok=True)
    subprocess.run(cmd + [str(empty)], check=True)
    empty.rmdir()
    subprocess.run([exe, "list", str(path)], check=True)


def main():
    sysmod = "ZMG0003"
    mcs = read_cards(HERE / "usermod" / f"{sysmod}.mcs")
    items = members(sysmod, mcs)
    pds = BUILD / "pds"
    shutil.rmtree(pds, ignore_errors=True)
    pds.mkdir(parents=True)
    for _, host, _, text in items:
        (pds / host).write_text(text, encoding="ascii", newline="\n")
    write_zip(BUILD / f"{sysmod}.zip", items)
    print(f"wrote {pds}/ ({len(items)} members) and {BUILD}/{sysmod}.zip")
    if "--xmit" in sys.argv:
        write_xmit(BUILD / f"{sysmod}.xmit", items, PDS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
