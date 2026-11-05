#!/usr/bin/env python3
"""zmg0003/test/lmodcmp.py - compare two load modules from AMBLIST listings.

    python3 zmg0003/test/lmodcmp.py TESTED.lst SMPBUILT.lst [BEFORE.lst]

Each file holds one LISTLOAD OUTPUT=MODLIST listing (the spool of an AMBLIST step).
TESTED is IKJPTGT linked the way test/mktest.py does it, before APPLY, into a test
library. SMPBUILT is SYS1.LPALIB(IKJPTGT) after APPLY. BEFORE, if given, is
SYS1.LPALIB(IKJPTGT) before APPLY.

The test link puts IKJCT441 first and SMP keeps it in its place, so the same CSECT
sits at another address and every address constant holds another value. A byte
comparison of the two modules therefore differs almost everywhere. The comparison is
per CSECT: the text outside relocated fields must be equal, and every relocated field
must name the same target CSECT and offset. The continuation bit of an RLD flag is
ignored, since it only says how entries were grouped into records.

Two controls run on the data itself: a flipped text byte and a changed address
constant in the SMP-built module must both be reported. With BEFORE, the only changed
CSECT must be IKJCT441. Exit 0 only when all of this holds.
"""
import re
import sys
from pathlib import Path

TARGET = "IKJCT441"
TEXT = re.compile(r"\s+([0-9A-F]{6})\s+((?:[0-9A-F]{2,8}\s*)+)")
CESD = re.compile(r"^\s+\d+\s+(\S+)\s+[0-9A-F]{2}\(SD\)\s+([0-9A-F]{6})\s+\d+\s+\d+\s+([0-9A-F]+)", re.M)
ENTRIES = r"((?:[0-9A-F]{2} [0-9A-F]{6}\s*)+)$"
# A continuation line first: "09 001895  09 00189D" also matches two decimal pointers.
RLD_NEXT = re.compile(r"\s+" + ENTRIES)
RLD_FIRST = re.compile(r"\s+\d+\s+\d+\s+" + ENTRIES)


class Module:
    def __init__(self, listing):
        self.image = {}
        self.rld = []
        kind = None
        for line in listing.splitlines():
            if line.startswith("RECORD#"):
                kind = "text" if "T E X T" in line else "rld" if "RLD" in line else None
            elif kind == "text":
                m = TEXT.match(line)
                if m:
                    data = bytes.fromhex("".join(m.group(2).split()))
                    for i, b in enumerate(data):
                        self.image[int(m.group(1), 16) + i] = b
            elif kind == "rld" and "R-PTR" not in line:
                m = RLD_NEXT.match(line) or RLD_FIRST.match(line)
                if m:
                    for fl, addr in re.findall(r"([0-9A-F]{2}) ([0-9A-F]{6})", m.group(1)):
                        self.rld.append((int(fl, 16), int(addr, 16)))
        self.csects = sorted(((n, int(o, 16), int(z, 16)) for n, o, z in CESD.findall(listing)),
                             key=lambda c: c[1])
        if not self.image or not self.csects or not self.rld:
            sys.exit("a listing without text, CESD or RLD: not an AMBLIST MODLIST")

    def where(self, addr):
        for name, off, size in self.csects:
            if off <= addr < off + size:
                return name, addr - off
        return None, addr

    def normal(self):
        """{csect: text with relocated fields blanked}, sorted relocations."""
        text = {n: bytearray(self.image.get(o + i, 0) for i in range(z))
                for n, o, z in self.csects}
        rel = []
        for fl, addr in self.rld:
            size = ((fl >> 2) & 3) + 1
            name, off = self.where(addr)
            if name is None:
                sys.exit(f"RLD address {addr:06X} outside every CSECT")
            value = int.from_bytes(bytes(self.image.get(addr + i, 0) for i in range(size)), "big")
            rel.append((name, off, fl & 0xFE, self.where(value)))
            text[name][off:off + size] = bytes(size)
        return {n: bytes(t) for n, t in text.items()}, sorted(rel, key=str)


def changed(a, b):
    return [n for n in sorted(set(a) | set(b)) if a.get(n) != b.get(n)]


def main(argv):
    if len(argv) not in (3, 4):
        sys.exit(__doc__)
    tested = Module(Path(argv[1]).read_text(errors="replace"))
    built = Module(Path(argv[2]).read_text(errors="replace"))
    text_t, rel_t = tested.normal()
    text_b, rel_b = built.normal()
    bad = changed(text_t, text_b)
    print(f"text bytes {len(tested.image)} / {len(built.image)}, CSECTs {len(text_t)} / {len(text_b)}, "
          f"relocations {len(rel_t)} / {len(rel_b)}")
    print("text outside relocated fields:", bad or "identical")
    print("relocations:", "identical" if rel_t == rel_b else "DIFFER")
    ok = not bad and rel_t == rel_b and len(tested.image) == len(built.image)

    off = dict((n, o) for n, o, _ in built.csects)[TARGET]
    fields = {a + i for fl, a in built.rld for i in range(((fl >> 2) & 3) + 1)}
    byte = next(off + i for i in range(100) if off + i not in fields)
    flipped = Module.__new__(Module)
    flipped.__dict__.update(built.__dict__, image=dict(built.image))
    flipped.image[byte] ^= 1
    seen = changed(text_t, flipped.normal()[0]) == [TARGET]
    print("control, flipped text byte reported:", seen)
    ok &= seen

    addr = next(a for fl, a in built.rld if fl & 0xFE == 0x0C)
    moved = Module.__new__(Module)
    moved.__dict__.update(built.__dict__, image=dict(built.image))
    moved.image[addr + 2] = (moved.image[addr + 2] + 0x20) & 0xFF
    seen = moved.normal()[1] != rel_t
    print("control, changed address constant reported:", seen)
    ok &= seen

    if len(argv) == 4:
        before = Module(Path(argv[3]).read_text(errors="replace")).normal()[0]
        diff = changed(before, text_b)
        print("before against SMP-built, changed CSECTs:", diff)
        ok &= diff == [TARGET]
    print("RESULT", "EQUAL" if ok else "NOT PROVEN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
