#!/bin/sh
# Attention (PA1) while a published BREXX exec runs, at READY and under ISPF, on a throwaway
# TK5 with BREXX (feature/irxexcom) deployed and ZMG0001 applied.
# attention.sh ENVFILE OUTDIR [CASE...].  ZMGWHO shows ECTENVBK (E=) before and after.
HERE=$(cd "$(dirname "$0")" && pwd)
ENVF=$1; OUT=$2; shift 2
CASES=${*:-READY ISPF}
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
EOF
}
READY() { logon; cat <<'EOF'
string ZMGWHO
enter
wait 3
show baseline
clear
string %XL
enter
wait 8
show running
pa 1
wait 6
show after-pa1
raw Query(ConnectionState)
string ZMGWHO
enter
wait 6
show who-1
raw Query(ConnectionState)
enter
wait 4
show enter-1
string ZMGWHO
enter
wait 6
show who-2
EOF
}
ISPF() { logon; cat <<'EOF'
string ISPF
enter
wait 8
string 6
enter
wait 4
string ISPEXEC SELECT CMD(%XL)
enter
wait 8
show running
pa 1
wait 6
show after-pa1
enter
wait 5
show terminated
home
string ZMGWHO                       
show typed
enter
wait 6
show who-1
enter
wait 4
string ISPEXEC SELECT CMD(%XC)
enter
wait 8
show xc
enter
wait 5
show xc-2
EOF
}
kick
python3 "$HERE/mkjob.py" set.jcl > /dev/null; sub set.jcl
python3 "$HERE/mkwho.py" add.jcl --add; sub add.jcl
for m in XL XC; do
  curl -s -m 30 -u "$AUTH" -X PUT -H 'Content-Type: text/plain' --data-binary @"$HERE/lib/$m" \
    "$URL/zosmf/restfiles/ds/HERC01.ZMG4.EXEC($m)" -o /dev/null -w "$m=%{http_code} "
done; echo
for c in $CASES; do
  kick
  MBT_TARGET=env mbt target ping env --tso --wait 90 > /dev/null 2>&1
  "$c" > "$c.s"
  PYTHONUNBUFFERED=1 timeout 200 python3 "$HERE/s3.py" "$ENVF" "$c.s" 2>&1 | cut -c1-80 > "$c.res"
  echo "$c done: $(wc -l < "$c.res") lines"
done
kick
