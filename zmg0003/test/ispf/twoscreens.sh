#!/bin/sh
# Two ISPF logical screens with real BREXX execs, on a throwaway TK5 that has BREXX
# (feature/irxexcom) deployed and ZMG0001 applied.  twoscreens.sh ENVFILE OUTDIR [CASE...]
# Prepares the libraries with mkjob.py and mkwho.py --add, then runs each case
# in a fresh logon.  One result file per case, so an interrupted run keeps what it has.
HERE=$(cd "$(dirname "$0")" && pwd)
ENVF=$1; OUT=$2; shift 2
CASES=${*:-A C D E}
mkdir -p "$OUT"; cd "$OUT" || exit 1
set -a; . "$ENVF"; set +a
AUTH="$MBT_TARGET_MVSMF_USER:$MBT_TARGET_MVSMF_PASSWORD"; URL=$MBT_TARGET_MVSMF_URL

kick() { curl -s -m 20 -u "$AUTH" -X PUT -H 'Content-Type: application/json' -d '{"cmd":"C U=HERC01"}' \
  "$URL/zosmf/restconsoles/consoles/defcn" -o /dev/null; sleep 12; }
sub() { # JCL OUT
  r=$(curl -s -m 60 -u "$AUTH" -X PUT -H 'Content-Type: text/plain' --data-binary @"$1" "$URL/zosmf/restjobs/jobs")
  j=$(echo "$r" | python3 -c 'import json,sys;print(json.load(sys.stdin)["jobid"])') || { echo "submit failed"; return 1; }
  n=$(echo "$r" | python3 -c 'import json,sys;print(json.load(sys.stdin)["jobname"])')
  for i in $(seq 1 60); do
    s=$(curl -s -m 20 -u "$AUTH" "$URL/zosmf/restjobs/jobs/$n/$j" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("status"),d.get("retcode"))')
    case "$s" in OUTPUT*) break;; esac; sleep 3
  done
  echo "$n $j $s"
}
pre() { cat <<EOF
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
back() { cat <<EOF
pf 9
wait 4
move 2 14
string $1
show before-enter
enter
wait 6
show after-display
EOF
}
A() { pre XS1 XS2; back NEW1; printf 'enter\nwait 5\nshow next\n'; }
C() { pre XS3 XS4; cat <<'EOF'
pf 9
wait 4
enter
wait 6
show x3-end
enter
wait 5
pf 9
wait 4
enter
wait 6
show x4-end
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
enter
wait 4
string ISPEXEC SELECT CMD(%XQ)
enter
wait 6
show xq
enter
wait 4
string ZMGWHO
enter
wait 5
show who2
EOF
}
D() { pre XS3 XQ; back NEW3; }
E() { pre XS3 XP; back NEW3; printf 'enter\nwait 4\npf 9\nwait 4\npf 3\nwait 5\nshow xp-after\n'; }

kick
python3 "$HERE/mkjob.py" set.jcl > /dev/null; sub set.jcl
python3 "$HERE/mkwho.py" add.jcl --add; sub add.jcl
for m in XS1 XS2 XS3 XS4 XQ XP XC; do
  curl -s -m 30 -u "$AUTH" -X PUT -H 'Content-Type: text/plain' --data-binary @"$HERE/lib/$m" \
    "$URL/zosmf/restfiles/ds/HERC01.ZMG3.EXEC($m)" -o /dev/null -w "$m=%{http_code} "
done; echo
for c in $CASES; do
  kick
  MBT_TARGET=env mbt target ping env --tso --wait 90 > /dev/null 2>&1
  "$c" > "$c.s"
  PYTHONUNBUFFERED=1 timeout 260 python3 "$HERE/s3.py" "$ENVF" "$c.s" 2>&1 | cut -c1-80 > "$c.res"
  echo "$c done: $(wc -l < "$c.res") lines"
done
kick
