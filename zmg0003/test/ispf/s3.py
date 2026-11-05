#!/usr/bin/env python3
"""Drive a TSO session through s3270 from a small script.

    s3.py ENVFILE SCRIPT

ENVFILE holds MBT_TARGET_TN3270_HOST and _PORT. Script lines:
wait N | show TAG | string TEXT | enter | pf N | pa N | clear | tab | home | move ROW COL (from 0) | raw ACTION
run TIMEOUT TEXT: type TEXT, press Enter, print the line-mode output page by page
until the screen is the TSO command panel again ("-" types nothing and only waits). If the screen shows a panel
marked ZMG0003, it answers from the next "panel" lines: tab, string, enter.
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


def lines():
    return [x[6:].rstrip() for x in cmd("Ascii()") if x.startswith("data: ")]


def run(timeout, text):
    print(f"--- {text}")
    if text != "-":
        cmd("Reset()")
        cmd('String("%s")' % text.replace('"', '\\"'))
        cmd("Enter()")
        time.sleep(2)
    end = time.time() + timeout
    while time.time() < end:
        s = lines()
        body = [x for x in s if x.strip()]
        if any("ZMG0003" in x for x in body):
            return
        if body and body[-1].strip() == "***":
            for x in body[:-1]:
                if "COMMAND PROCESSOR" not in x and "ENTER TSO COMMAND" not in x and not x.lstrip().startswith(("=>", "===>", "Use command", "Place cursor", "/C ", "**")):
                    print(x)
            cmd("Enter()")
            time.sleep(1.5)
            continue
        if any("ENTER TSO COMMAND" in x for x in s):
            return
        time.sleep(1)
    print("--- TIMEOUT")


cmd(f"Connect({env['MBT_TARGET_TN3270_HOST']}:{env['MBT_TARGET_TN3270_PORT']})")
cmd("Wait(5,Output)")
for raw in open(sys.argv[2]):
    line = raw.rstrip("\n")
    if not line or line.startswith("#"):
        continue
    verb, _, arg = line.partition(" ")
    if verb == "run":
        to, _, text = arg.partition(" ")
        run(float(to), text)
    elif verb == "wait":
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
        cmd("Reset()")
        cmd(f"PA({arg})")
        time.sleep(1.5)
    elif verb == "clear":
        cmd("Clear()")
        time.sleep(1)
    elif verb == "tab":
        cmd("Tab()")
    elif verb == "home":
        cmd("Home()")
    elif verb == "raw":
        print("RAW", arg, cmd(arg)[-1])
    elif verb == "move":
        r, c = arg.split()
        cmd(f"MoveCursor({r},{c})")
    else:
        print("?", line)
cmd("Disconnect()")
cmd("Quit()")
