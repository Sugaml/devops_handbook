# Day 2 — Shell Essentials, Pipes & Text Processing

**Goal:** Chain commands efficiently, filter logs and configs, and use `grep`/`sed`/`awk`/`find`—the daily toolkit of SRE and platform engineers.

**Time:** 5–7 hours

---

## 1. Redirection and pipes

```bash
# stdout redirect
echo "deploy ok" > /tmp/result.txt      # overwrite
echo "line 2" >> /tmp/result.txt        # append

# stderr redirect
ls /nonexistent 2> /tmp/errors.log
ls /nonexistent 2>> /tmp/errors.log

# combine stdout + stderr
command &> /tmp/all.log
command > /tmp/out.log 2>&1             # classic form (order matters in complex cases)

# discard output
command > /dev/null
command &> /dev/null

# pipe: stdout of left → stdin of right
dmesg | tail -20
cat /var/log/syslog | grep -i error | tail -50

# pipe stderr into pipeline
cmd 2>&1 | grep pattern

# here document (multi-line input to command)
cat <<EOF | sudo tee /etc/myapp/config
key=value
mode=production
EOF

# here string (single line, no expansion if quoted delimiter)
grep 'root' <<< "$(cat /etc/passwd)"
```

**DevOps:** CI logs are pipelines—`build.sh 2>&1 | tee build.log` preserves output for artifacts while showing on console.

---

## 2. `grep` — pattern search

```bash
grep error /var/log/syslog
grep -i error /var/log/syslog           # case insensitive
grep -v DEBUG app.log                   # invert match
grep -n "listen" /etc/nginx/nginx.conf  # line numbers
grep -c FAILED deploy.log               # count matches
grep -r "password" /etc/ 2>/dev/null    # recursive (careful!)
grep -E 'error|warn|fatal' app.log      # extended regex (egrep)
grep -F 'literal.string' file.txt       # fixed string (fgrep)
grep -A 3 -B 2 "Exception" java.log     # context after/before
grep -w "failed" status.log             # whole word

# with find
find /var/log -name "*.log" -exec grep -l "OOM" {} \;

# modern alternative (if installed)
rg "error" /var/log --glob '*.log'
```

**Practical:** Parse nginx 5xx:

```bash
awk '$9 ~ /^5/ {print}' /var/log/nginx/access.log | tail -20
# or
grep ' "5[0-9][0-9] ' /var/log/nginx/access.log | wc -l
```

---

## 3. `sed` — stream editor

```bash
# substitute first occurrence per line
sed 's/debug/info/' config.txt

# substitute all on line (g)
sed 's/localhost/127.0.0.1/g' config.txt

# in-place edit (GNU sed - backup extension optional)
sed -i.bak 's/PORT=8080/PORT=9090/' .env
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# delete lines
sed '/^#/d' config.txt                  # delete comments
sed '/^$/d' config.txt                  # delete blank lines

# print specific lines
sed -n '10,20p' large.conf
sed -n '/server_name/p' /etc/nginx/sites-enabled/default

# append after match (GNU)
sed -i '/\[Service\]/a Environment=APP_ENV=prod' unit.file
```

**DevOps:** Templating in shell before cloud-init/Ansible exists:

```bash
sed "s/{{HOST}}/$HOSTNAME/g" template.conf > /etc/app/config
```

---

## 4. `awk` — column-oriented processing

```bash
# Print columns (default whitespace separator)
ps aux | awk '{print $1, $2, $11}'      # user, pid, command
df -h | awk 'NR>1 {print $1, $5}'       # skip header, disk and use%

# Custom separator
awk -F: '{print $1, $3}' /etc/passwd    # user, uid

# Conditions
awk '$3 > 1000 {print $1}' /etc/passwd  # users with uid > 1000
netstat -tn 2>/dev/null | awk '$6=="ESTABLISHED" {print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn

# BEGIN/END blocks
awk 'BEGIN {sum=0} {sum+=$9} END {print sum}' access.log

# nginx: average response time if $NF is request_time
awk '{sum+=$NF; n++} END {if(n) print sum/n}' /var/log/nginx/access.log
```

---

## 5. `cut`, `sort`, `uniq`, `tr`

```bash
cut -d: -f1 /etc/passwd                 # usernames
cut -c1-10 file.txt                     # characters 1-10

sort file.txt
sort -t: -k3 -n /etc/passwd             # numeric sort by uid field
sort -u file.txt                        # unique lines

uniq file.txt                           # adjacent duplicates only
sort file.txt | uniq -c                 # count occurrences
sort file.txt | uniq -d                 # only duplicated lines

tr 'a-z' 'A-Z' < file.txt
tr -d '\r' < windows.txt > unix.txt     # strip CR (common CI issue)
cat file | tr -s ' '                    # squeeze repeated spaces
```

---

## 6. `find` — locate files by criteria

```bash
find /var/log -name "*.log"
find /tmp -type f -mtime +7             # older than 7 days
find /home -type f -size +100M
find . -type f -perm 0777               # world-writable files (audit)
find /etc -name "*.conf" -exec ls -l {} \;
find /var/log -name "*.gz" -delete      # dangerous — test without -delete first

# -print0 + xargs for filenames with spaces
find . -type f -name "*.sh" -print0 | xargs -0 chmod +x

# Prune directories
find / -path /proc -prune -o -name "core" -print 2>/dev/null

# newer than reference file
find /etc -newer /etc/passwd
```

`locate` uses a database (fast, may be stale):

```bash
sudo updatedb
locate nginx.conf
```

---

## 7. `xargs` — build command lines from input

```bash
echo {1..5} | xargs -I{} touch /tmp/file{}
find . -name "*.bak" | xargs rm
find . -name "*.log" -print0 | xargs -0 gzip

# parallel (GNU)
find . -name "*.json" | xargs -P 4 -I{} jq . {} > /dev/null

# avoid xargs when possible — use find -exec or while read
find . -name "*.sh" -exec shellcheck {} +
```

---

## 8. Variables, quoting, and simple scripting

```bash
NAME="api-server"
echo "Host: $NAME"
echo 'Literal $NAME not expanded'

# Command substitution
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
FILES=$(ls /etc/*.conf 2>/dev/null | wc -l)

# Arrays (bash)
SERVERS=(web1 web2 web3)
echo "${SERVERS[1]}"
for s in "${SERVERS[@]}"; do echo "Checking $s"; done

# Test constructs
[ -f /etc/os-release ] && echo "exists"
[ -d /var/log ] || echo "missing"
[[ "$ENV" == "prod" ]] && echo "careful"

# Short-circuit
command1 && command2    # run command2 if command1 succeeds
command1 || command2    # run command2 if command1 fails
```

---

## 9. `jq` for JSON (DevOps staple)

```bash
curl -s https://api.github.com/repos/torvalds/linux | jq '.name, .stargazers_count'
kubectl get pod -o json | jq '.items[].metadata.name'
echo '{"hosts":["a","b"]}' | jq -r '.hosts[]'
```

---

## 10. Lab — Day 2

1. From `/var/log`, list files larger than 1MB, sorted by size (hint: `find` + `ls -l` or `du`).
2. Extract unique client IPs from a sample access log (or create one with 10 lines); output sorted by count descending.
3. Use `sed` to comment out every line containing `password` in a test file (prefix `#`).
4. Use `awk` to print only usernames with UID ≥ 1000 from `/etc/passwd`.
5. Pipeline: `find /etc -name '*.conf' 2>/dev/null | wc -l`

**Stretch:** Write a one-liner that reports the top 5 most common words in `/etc/services` (hint: `tr`, `sort`, `uniq`).

---

## 11. DevOps connections

- **Log aggregation:** Fluent Bit/Filebeat ship parsed fields—understanding `grep`/`awk` helps write parser rules and emergency queries.
- **CI:** Exit codes propagate through `&&` chains; failed stage = non-zero exit from any command in pipeline unless `set +e`.
- **Kubernetes:** `kubectl ... | jq` is the standard inspection pattern.

---

## Quick reference

| Task | Tool |
|------|------|
| Search text | `grep -E` |
| Replace in file | `sed -i 's/a/b/'` |
| Columns / sums | `awk` |
| Find files | `find` |
| Count unique | `sort \| uniq -c` |
| JSON | `jq` |

**Previous:** [Day 1](../day1/) · **Next:** [Day 3 — Processes & systemd](../day3/)
