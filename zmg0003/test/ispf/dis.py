#!/usr/bin/env python3
"""Rough S/370 listing of a byte range of a load module: dis.py FILE START END (hex)."""
import sys

d = open(sys.argv[1], "rb").read()
s = int(sys.argv[2], 16)
e = int(sys.argv[3], 16)
L = {0: 2, 1: 4, 2: 6, 3: 6}
O = {0x05: "BALR", 0x06: "BCTR", 0x07: "BCR", 0x0A: "SVC", 0x0D: "BASR", 0x0E: "MVCL", 0x0F: "CLCL",
     0x10: "LPR", 0x12: "LTR", 0x13: "LCR", 0x14: "NR", 0x15: "CLR", 0x16: "OR", 0x17: "XR", 0x18: "LR",
     0x19: "CR", 0x1A: "AR", 0x1B: "SR", 0x1E: "ALR", 0x1F: "SLR", 0x40: "STH", 0x41: "LA", 0x42: "STC",
     0x43: "IC", 0x44: "EX", 0x45: "BAL", 0x46: "BCT", 0x47: "BC", 0x48: "LH", 0x49: "CH", 0x4A: "AH",
     0x4B: "SH", 0x4C: "MH", 0x50: "ST", 0x54: "N", 0x55: "CL", 0x56: "O", 0x57: "X", 0x58: "L", 0x59: "C",
     0x5A: "A", 0x5B: "S", 0x90: "STM", 0x91: "TM", 0x92: "MVI", 0x94: "NI", 0x95: "CLI", 0x96: "OI",
     0x98: "LM", 0xBD: "CLM", 0xBE: "STCM", 0xBF: "ICM", 0xD2: "MVC", 0xD4: "NC", 0xD5: "CLC", 0xD6: "OC",
     0xD7: "XC", 0xDC: "TR"}
SI = (0x91, 0x92, 0x94, 0x95, 0x96)
i = s
while i < e:
    b = d[i]
    n = L[b >> 6]
    h = d[i:i + n]
    nm = O.get(b, "?%02X" % b)
    if b >> 6 == 0:
        a = f"{h[1] >> 4},{h[1] & 15}"
    elif b >> 6 == 1:
        a = f"{h[1] >> 4},{((h[2] & 15) << 8) | h[3]}({h[1] & 15},{h[2] >> 4})"
    elif b >> 6 == 2:
        a = (f"{((h[2] & 15) << 8) | h[3]}({h[2] >> 4}),X'{h[1]:02X}'" if b in SI
             else f"{h[1] >> 4},{h[1] & 15},{((h[2] & 15) << 8) | h[3]}({h[2] >> 4})")
    else:
        a = f"{((h[2] & 15) << 8) | h[3]}({h[1] + 1},{h[2] >> 4}),{((h[4] & 15) << 8) | h[5]}({h[4] >> 4})"
    print(f"{i:06X} {h.hex():12} {nm:5} {a}")
    i += n
