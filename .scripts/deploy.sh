#!/bin/bash
# ============================================================
# GitHub Pages 自动部署脚本 (v2 — 2026-06-28)
# ============================================================
# 将 hnft-site/ 目录部署到 https://2810300-bot.github.io/hnft/
#
# 用法:
#   bash deploy.sh                           # 提交所有变更并推送
#   bash deploy.sh --message "自定义提交信息"  # 自定义 commit message
#   bash deploy.sh --dry-run                 # 仅检查，不实际推送
#
# 部署策略：git push（优先）→ GitHub REST API 逐文件推送（自动回退）
# Token 来源：git remote URL > ~/.workbuddy/config/github_token.txt
# ============================================================

# 不使用 set -e，手动处理关键错误
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BRANCH="${GITHUB_PAGES_BRANCH:-main}"
COMMIT_MSG="auto: dashboard refresh $(date '+%Y-%m-%d %H:%M:%S')"
DRY_RUN=false

# GitHub 配置
OWNER="2810300-bot"
REPO="hnft"
# Token 配置文件（在 git 仓库之外，不会被提交）
TOKEN_FILE="${HOME}/.workbuddy/config/github_token.txt"
# Python 路径（避免自动化环境中 PATH 不一致）
PYTHON_BIN="/Users/mac/.workbuddy/binaries/python/envs/default/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="/usr/bin/python3"
fi

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --message|-m)
            COMMIT_MSG="$2"; shift 2 ;;
        --dry-run)
            DRY_RUN=true; shift ;;
        *)
            echo "未知参数: $1"; exit 1 ;;
    esac
done

echo "============================================"
echo "  GitHub Pages 部署: hnft-site"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

cd "$SITE_DIR"

# 检查是否为 git 仓库
if [ ! -d ".git" ]; then
    echo "🔧 初始化 Git 仓库..."
    git init
    git remote add origin "https://github.com/${OWNER}/${REPO}.git" 2>/dev/null || git remote set-url origin "https://github.com/${OWNER}/${REPO}.git"
fi

# 检测 git remote URL（必须在 cd 到 SITE_DIR 之后）
if [ -n "${GITHUB_PAGES_REPO:-}" ]; then
    REPO_URL="$GITHUB_PAGES_REPO"
elif git remote get-url origin 2>/dev/null | grep -q '@\|https'; then
    REPO_URL="$(git remote get-url origin)"
else
    REPO_URL="https://github.com/${OWNER}/${REPO}.git"
fi

echo "  目标: https://github.com/${OWNER}/${REPO}.git（token 已隐藏）"

# ------------------------------------------------------------
# 代理探测：git 的 http.proxy 可能指向一个未运行的端口（如 7891）。
# 自动探测「正在监听」的代理并改用，避免部署因死代理而失败。
# ------------------------------------------------------------
# 检查 host:port 是否可连通
port_listen() {
    local hp="$1"
    [ -z "$hp" ] && return 1
    local host port
    host=$(echo "$hp" | cut -d: -f1)
    port=$(echo "$hp" | cut -d: -f2)
    [ -z "$host" ] && return 1
    [ -z "$port" ] && return 1
    (exec 3<>/dev/tcp/$host/$port) 2>/dev/null
}

# 返回环境中第一个「正在监听」的代理（http://host:port 形式）
env_live_proxy() {
    for envvar in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy; do
        local val="${!envvar:-}"
        [ -z "$val" ] && continue
        local hp
        hp=$(echo "$val" | sed -E 's#^[a-zA-Z]+://##; s#/.*##; s#\?.*##')
        if port_listen "$hp"; then
            echo "http://$hp"
            return 0
        fi
    done
    return 1
}

GIT_PROXY=$(git config --get http.proxy 2>/dev/null || true)
GIT_PROXY_HOSTPORT=$(echo "$GIT_PROXY" | sed -E 's#^[a-zA-Z]+://##; s#/.*##')

# 选定最终代理 PROXY_URL（http://host:port）或空串（直连）
PROXY_URL=""
if [ -n "$GIT_PROXY" ] && port_listen "$GIT_PROXY_HOSTPORT"; then
    echo "   🔎 git 代理可用: $GIT_PROXY_HOSTPORT（沿用）"
elif PROXY_URL=$(env_live_proxy); then
    echo "   🔎 git 代理不可用（${GIT_PROXY_HOSTPORT:-无}），改用环境代理: ${PROXY_URL#*//}"
else
    echo "   🔎 未发现可用代理，git 将尝试直连"
fi

# 生成 git 命令代理前缀；同时导出给 REST API 的 Python（urllib 读 HTTPS_PROXY）
if [ -n "$PROXY_URL" ]; then
    EFF_PROXY_PREFIX="GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.proxy GIT_CONFIG_VALUE_0=$PROXY_URL"
    export HTTPS_PROXY="$PROXY_URL"
    export HTTP_PROXY="$PROXY_URL"
else
    # 清空 git 代理，退回系统默认/直连（env 中可能仍有可用代理）
    EFF_PROXY_PREFIX="GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.proxy GIT_CONFIG_VALUE_0="
fi

# 统一走代理前缀执行 git 网络命令的封装
git_run() {
    if [ -n "$EFF_PROXY_PREFIX" ]; then
        eval "$EFF_PROXY_PREFIX" git "$@"
    else
        git "$@"
    fi
}

# 检查变更：未提交的文件变更 OR 已提交但未推送的 commits
# （管道脚本可能已 git commit 但 push 失败，此时 working tree 干净但远端未同步）
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
UNPUSHED=$(git log @{u}..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGES" -eq 0 ] && [ "$UNPUSHED" -eq 0 ]; then
    echo "✅ 无变更，跳过部署"
    exit 0
fi

if [ "$UNPUSHED" -gt 0 ]; then
    echo "📝 检测到 ${UNPUSHED} 个未推送的 commits（working tree 干净）"
else
    echo "📝 检测到 $CHANGES 个文件变更"
fi

if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry-run 模式 — 变更文件:"
    git status --short
    echo "✅ Dry-run 完成（未实际推送）"
    exit 0
fi

# 先同步远程最新代码（工作区可能干净——管道已 commit 但未 push；也可能有未提交变更）
echo "📥 同步远程最新代码..."
git_run fetch origin "$BRANCH" 2>/dev/null || echo "   (远程不可达，尝试本地版本)"
git_run rebase origin/"$BRANCH" 2>/dev/null || git_run rebase --abort 2>/dev/null || true

# 提交未暂存变更（仅当有未提交文件时；已 commit 未 push 场景跳过，绝不因"无新内容"而退出）
CHANGES_NOW=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGES_NOW" -gt 0 ]; then
    echo "📦 提交变更..."
    git add -A
    git commit -m "$COMMIT_MSG" || echo "   (无新内容可提交)"
fi

# 构造推送 URL：remote 不含 token 时，从配置文件注入（避免 401 后 fallback 空转）
if git remote get-url origin 2>/dev/null | grep -q '@'; then
    PUSH_URL="origin"
else
    _T="$TOKEN"
    [ -z "$_T" ] && [ -f "$TOKEN_FILE" ] && _T=$(cat "$TOKEN_FILE")
    if [ -n "$_T" ]; then
        PUSH_URL="https://${_T}@github.com/${OWNER}/${REPO}.git"
    else
        PUSH_URL="origin"
    fi
fi

# 推送到 GitHub Pages（已自动选用可用代理；非快进自动 rebase 重试）
echo "🚀 推送到 GitHub Pages (git push)..."
MAX_RETRIES=3
RETRY_COUNT=0
PUSH_OK=false
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    OUT=$(git_run push "$PUSH_URL" "$BRANCH" 2>&1)
    PUSH_RC=$?
    if [ $PUSH_RC -eq 0 ]; then
        echo "$OUT"
        echo ""
        echo "✅ git push 部署成功！"
        echo "   🌐 https://${OWNER}.github.io/${REPO}/"
        PUSH_OK=true
        break
    fi
    echo "$OUT"
    # 非快进：先同步远程再试（避免死代理之外的常见失败）
    if echo "$OUT" | grep -qiE "non-fast-forward|rejected|fetch first"; then
        echo "   ↳ 检测到非快进，拉取并 rebase 远程后重试..."
        git_run fetch origin "$BRANCH" 2>/dev/null
        git_run rebase "origin/$BRANCH" 2>/dev/null || git_run rebase --abort 2>/dev/null
    else
        echo "   ⚠️ 推送失败，等待 5 秒后重试..."
        sleep 5
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

# 若 git push 全部失败，回退到 GitHub REST API 逐文件推送
if [ "$PUSH_OK" != true ]; then
    echo ""
    echo "   ⚠️ git push 失败，切换到 GitHub REST API 方式..."

    # 提取 token：优先配置文件（remote URL 已不含明文 token）
    if [ -f "$TOKEN_FILE" ]; then
        TOKEN=$(cat "$TOKEN_FILE")
        echo "   (已从配置文件加载 token，不打印明文)"
    elif echo "$REPO_URL" | grep -q '@'; then
        TOKEN=$(echo "$REPO_URL" | sed -n 's|.*https://\([^@]*\)@github.com.*|\1|p')
        echo "   (已从 remote URL 加载 token，不打印明文)"
    else
        echo "   ❌ 无法获取 token（配置文件不存在: $TOKEN_FILE）"
        exit 1
    fi

    # 获取变更文件列表 — 多策略 fallback
    CHANGED_FILES=""
    # 策略1: 已提交但未推送的 commits（管道脚本 commit 后 push 失败的场景）
    if [ "$UNPUSHED" -gt 0 ]; then
        # 找出本地比远端多出的所有 commits 涉及的文件
        CHANGED_FILES=$(git diff --name-only origin/${BRANCH} HEAD 2>/dev/null || echo "")
    fi
    # 策略2: 最近一次 commit 的变更文件
    if [ -z "$CHANGED_FILES" ]; then
        CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "")
    fi
    if [ -z "$CHANGED_FILES" ]; then
        CHANGED_FILES=$(git show --name-only --format="" HEAD 2>/dev/null || echo "")
    fi
    # 策略3: 未提交的变更
    if [ -z "$CHANGED_FILES" ]; then
        CHANGED_FILES=$(git status --porcelain 2>/dev/null | awk '{print $NF}' || echo "")
    fi

    if [ -z "$CHANGED_FILES" ]; then
        echo "   ❌ 无法获取变更文件列表"
        exit 1
    fi

    echo "   📋 待推送文件:"
    echo "$CHANGED_FILES" | while read -r f; do echo "      - $f"; done

    # 写 Python 推送脚本到临时文件（避免 inline 引号问题）
    PY_SCRIPT=$(mktemp /tmp/deploy_gh_XXXXXX.py)
    cat > "$PY_SCRIPT" << 'PYEOF'
import json, base64, urllib.request, sys, os

TOKEN = os.environ.get('GH_TOKEN', '')
OWNER = os.environ.get('GH_OWNER', '2810300-bot')
REPO = os.environ.get('GH_REPO', 'hnft')
BRANCH = os.environ.get('GH_BRANCH', 'main')
FILE = os.environ.get('GH_FILE', '')
MSG = os.environ.get('GH_MSG', 'auto: dashboard refresh')

if not FILE:
    print('ERR: no file specified', file=sys.stderr)
    sys.exit(1)

if not os.path.isfile(FILE):
    print(f'ERR: file not found: {FILE}', file=sys.stderr)
    sys.exit(1)

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

api_url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE}'
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'WorkBuddy'
}

# 获取已有文件的 SHA（用于更新而非创建）
sha = None
try:
    req = urllib.request.Request(api_url)
    for k, v in headers.items():
        req.add_header(k, v)
    resp = urllib.request.urlopen(req, timeout=15)
    sha = json.loads(resp.read()).get('sha')
except Exception:
    pass

# 上传/更新文件
encoded = base64.b64encode(content.encode('utf-8')).decode()
body_dict = {'message': MSG, 'content': encoded, 'branch': BRANCH}
if sha:
    body_dict['sha'] = sha

req2 = urllib.request.Request(api_url, data=json.dumps(body_dict).encode('utf-8'), method='PUT')
for k, v in headers.items():
    req2.add_header(k, v)

resp2 = urllib.request.urlopen(req2, timeout=30)
result = json.loads(resp2.read())
commit_sha = result.get('commit', {}).get('sha', 'unknown')[:12]
print(f'OK: {FILE} -> commit {commit_sha}')
PYEOF

    API_OK=true
    FILE_COUNT=0
    for FILE in $CHANGED_FILES; do
        if [ ! -f "$FILE" ]; then
            echo "   ⏭️ 跳过不存在的文件: $FILE"
            continue
        fi
        echo "   📤 推送: $FILE"
        GH_TOKEN="$TOKEN" GH_FILE="$FILE" GH_MSG="$COMMIT_MSG" \
            "$PYTHON_BIN" "$PY_SCRIPT" 2>&1 || { echo "   ❌ 推送失败: $FILE"; API_OK=false; }
        FILE_COUNT=$((FILE_COUNT + 1))
    done

    rm -f "$PY_SCRIPT"

    # 同步本地 git 状态
    git fetch origin "$BRANCH" 2>/dev/null && git reset --hard origin/"$BRANCH" 2>/dev/null || true

    if [ "$API_OK" = true ] && [ "$FILE_COUNT" -gt 0 ]; then
        echo ""
        echo "✅ REST API 部署成功！($FILE_COUNT 个文件)"
        echo "   🌐 https://${OWNER}.github.io/${REPO}/"
    else
        echo ""
        echo "❌ REST API 部署失败"
        exit 1
    fi
fi

echo ""
echo "============================================"
echo "  部署摘要"
echo "  站点: https://${OWNER}.github.io/${REPO}/"
echo "  提交: $COMMIT_MSG"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
