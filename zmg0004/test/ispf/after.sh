#!/bin/sh
# Stage 1 measured after the build: the cases twoscreens.sh and attention.sh do not cover.
# On a throwaway TK5 with BREXX (feature/irxexcom) deployed and ZMG0001 applied.
# after.sh ENVFILE OUTDIR [CASE...]
HERE=$(cd "$(dirname "$0")" && pwd)
ENVF=$1; OUT=$2; shift 2
CASES=${*:-CR REXXREXX REXXCLIST CLISTREXX NESTCTL ATDISPLAY REOPEN MEMORY}
mkdir -p "$OUT"; cd "$OUT" || exit 1
set -a; . "$ENVF"; set +a
AUTH="$MBT_TARGET_MVSMF_USER:$MBT_TARGET_MVSMF_PASSWORD"; URL=$MBT_TARGET_MVSMF_URL
kick() { curl -s -m 20 -u "$AUTH" -X PUT -H 'Content-Type: application/json' -d '{"cmd":"C U=HERC01"}' \
  "$URL/zosmf/restconsoles/consoles/defcn" -o /dev/null; sleep 12; }
sub() {
  r=$(curl -s -m 60 -u "$AUTH" -X PUT -H 'Content-Type: text/plain' --data-binary @"$1" "$URL/zosmf/restjobs/jobs")
  j=$(echo "$r" | python3 -c 'import json,sys;print(json.load(sys.stdin)["jobid"])') || { echo "submit failed"; return 1; }
  n=$(echo "$r" | python3 -c 'import json,sys;print(json.load(sys.stdin)["jobname"])')
  for i in $(seq 1 60); do
    s=$(curl -s -m 20 -u "$AUTH" "$URL/zosmf/restjobs/jobs/$n/$j" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("status"),d.get("retcode"))')
    case "$s" in OUTPUT*) break;; esac; sleep 3
  done
  echo "$n $j $s"
}
logon() { cat <<EOF
raw Toggle(aidWait,clear)
wait 2
string LOGON
enter
wait 4
string HERC01/CUL8TR PROC(ISPLOGON)
enter
wait 10
enter
wait 3
clear
string ISPF
enter
wait 8
string 6
enter
wait 4
EOF
}
run() { cat <<EOF
string ISPEXEC SELECT CMD(%$1)
enter
wait ${2:-8}
show $1
enter
wait 5
show $1-2
enter
wait 5
show $1-3
enter
wait 5
EOF
}
who() { cat <<EOF
string ZMGWHO
enter
wait 5
show $1
enter
wait 4
EOF
}
# screen 1 in a panel, screen 2 in a panel
two() { logon; cat <<EOF
string ISPEXEC SELECT CMD(%$1)
enter
wait 6
show s1-start
enter
wait 5
move 11 2
pf 2
wait 5
string 6
enter
wait 4
string ISPEXEC SELECT CMD(%$2)
enter
wait 12
show s2-start
enter
wait 5
show s2-screen
EOF
}
# case C the other way round: the exec of screen 2 ends first
CR() { two XS3 XS4; cat <<'EOF'
enter
wait 6
show x4-end
enter
wait 5
pf 9
wait 4
enter
wait 6
show x3-end
enter
wait 5
string ZMGWHO
enter
wait 5
show who
enter
wait 4
string ISPEXEC SELECT CMD(%XC)
enter
wait 6
show xc
EOF
}
REXXREXX() { logon; run XN1 10; who after; }
REXXCLIST() { logon; run XN3 10; who after; }
CLISTREXX() { logon; run XN4 10; who after; }
# PA1 while the exec waits in ISPF DISPLAY
ATDISPLAY() { logon; cat <<'EOF'
string ISPEXEC SELECT CMD(%XD)
enter
wait 6
show s1-start
enter
wait 5
show panel
pa 1
wait 6
show after-pa1
enter
wait 5
show enter-1
enter
wait 5
show enter-2
EOF
  who who-1; run XC 8; }
# screen 2 closed and opened again, then case A
REOPEN() { two XS1 XQ; cat <<'EOF'
pf 3
wait 4
pf 3
wait 5
show closed
move 11 2
pf 2
wait 5
string 6
enter
wait 4
string ISPEXEC SELECT CMD(%XS2)
enter
wait 12
show s2-start
enter
wait 5
pf 9
wait 4
move 2 14
string NEW1
show before-enter
enter
wait 6
show after-display
EOF
}
# controls: what ISPF does in plain CLISTs and alone
NESTCTL() { logon; run XN5 10; run XN2 8; run XU 6; run XC 6; run XB 6; run XA 6; run XV 6; run XR 6; }
# twenty dialogs in a row on one screen, and twenty ISPEXEC calls in one exec
MEMORY() { logon; who before; i=1; while [ $i -le 20 ]; do cat <<'EOF'
string ISPEXEC SELECT CMD(%XQ)
enter
wait 4
enter
wait 2
EOF
    i=$((i+1)); done; who after; run XM 8; who end; }
kick
python3 "$HERE/mkjob.py" set.jcl > /dev/null; sub set.jcl
python3 "$HERE/mkwho.py" add.jcl --add; sub add.jcl
for m in XS1 XS2 XS3 XS4 XQ XP XC XN1 XN2 XN3 XN4 XN5 XN6 XU XA XB XV XR XD XM; do
  curl -s -m 30 -u "$AUTH" -X PUT -H 'Content-Type: text/plain' --data-binary @"$HERE/lib/$m" \
    "$URL/zosmf/restfiles/ds/HERC01.ZMG4.EXEC($m)" -o /dev/null -w "$m=%{http_code} "
done; echo
for c in $CASES; do
  kick
  MBT_TARGET=env mbt target ping env --tso --wait 90 > /dev/null 2>&1
  "$c" > "$c.s"
  PYTHONUNBUFFERED=1 timeout 300 python3 "$HERE/s3.py" "$ENVF" "$c.s" 2>&1 | cut -c1-80 > "$c.res"
  echo "$c done: $(wc -l < "$c.res") lines"
done
kick
