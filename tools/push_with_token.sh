#!/usr/bin/env bash
# GitHub 推送兜底脚本：token 从环境变量读（仅内存），不落盘、不打印、不入 git 历史。
# 用法：GITHUB_TOKEN=<PAT> bash tools/push_with_token.sh "<commit message>"
# 前提：本工作区为 tarball 快照（无 .git），脚本临时 git init 后推送。
set -euo pipefail

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "ERROR: 需先注入 GITHUB_TOKEN（仅内存，不落盘）；无 token 不推送、不伪造。" >&2
  exit 2
fi
MSG="${1:-Safari §4ge: aggregation independence premise refined}"
REPO="https://github.com/jsyzc2019/svl-agent.git"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"
if [[ ! -d .git ]]; then
  git init -q
  git remote add origin "$REPO"
fi
# basic auth：用户名 x-access-token，token 仅经 http.extraHeader 内存传递
AUTH="basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 | tr -d '\n')"
git add -A
git -c http.extraHeader="AUTHORIZATION: $AUTH" \
    -c http.version=HTTP/1.1 \
    -c http.postBuffer=524288000 \
    commit -m "$MSG"
git -c http.extraHeader="AUTHORIZATION: $AUTH" \
    -c http.version=HTTP/1.1 \
    -c http.postBuffer=524288000 \
    push -u origin HEAD:main

echo "PUSH_DONE; 现场复核远端 HEAD："
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/jsyzc2019/svl-agent/commits/main" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sha','?')[:12], d.get('commit',{}).get('message','').splitlines()[0][:80])"
# 不打印 token；extraHeader 仅进程级，不写 config
