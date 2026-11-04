#!/usr/bin/env python3
"""Drive a TSO session through s3270 from a small script.

    s3.py ENVFILE SCRIPT

ENVFILE holds MBT_TARGET_TN3270_HOST and _PORT. Script lines:
wait N | show TAG | string TEXT | enter | pf N | pa N | clear | tab | home
"""
import subprocess
import sys
import time

env = dict(l.strip().split("=", 1) for l in open(sys.argv[1]) if "=" in l)
p = subprocess.Popen(["s3270", "-model", "3279-2"], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                     text=True, bufsize=1)


def cmd(c):
    p.stdin.write(c + "\n")
    p.stdin.flush()
    out = []
    while True:
        line = p.stdout.readline()
        if not line:
            return out
        line = line.rstrip("\n")
        out.append(line)
        if line in ("ok", "error"):
            return out


def show(tag):
    print(f"--- {tag}")
    for x in cmd("Ascii()"):
        if x.startswith("data: ") and x[6:].strip():
            print(x[6:].rstrip())


cmd(f"Connect({env['MBT_TARGET_TN3270_HOST']}:{env['MBT_TARGET_TN3270_PORT']})")
cmd("Wait(5,Output)")
for raw in open(sys.argv[2]):
    line = raw.rstrip("\n")
    if not line or line.startswith("#"):
        continue
    verb, _, arg = line.partition(" ")
    if verb == "wait":
        time.sleep(float(arg))
    elif verb == "show":
        show(arg)
    elif verb == "string":
        cmd("Reset()")
        cmd('String("%s")' % arg.replace("\\", "\\\\").replace('"', '\\"'))
    elif verb == "enter":
        cmd("Enter()")
        time.sleep(2)
    elif verb == "pf":
        cmd(f"PF({arg})")
        time.sleep(1.5)
    elif verb == "pa":
        cmd(f"PA({arg})")
        time.sleep(1.5)
    elif verb == "clear":
        cmd("Clear()")
        time.sleep(1)
    elif verb == "tab":
        cmd("Tab()")
    elif verb == "home":
        cmd("Home()")
    else:
        print("?", line)
cmd("Disconnect()")
cmd("Quit()")
