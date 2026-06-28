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

echo "  目标: ${REPO_URL%%@*}@github.com/...（token 已隐藏）"

# 检查变更
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGES" -eq 0 ]; then
    echo "✅ 无变更，跳过部署"
    exit 0
fi

echo "📝 检测到 $CHANGES 个文件变更"

if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry-run 模式 — 变更文件:"
    git status --short
    echo "✅ Dry-run 完成（未实际推送）"
    exit 0
fi

# 先提交本地变更，再同步远程（避免 pull --rebase 因 unstaged 变更而失败）
echo "📦 提交变更..."
git add -A
git commit -m "$COMMIT_MSG" || { echo "⚠️ 无内容可提交"; exit 0; }

# 同步远程最新代码（此时工作区干净，rebase 不会冲突）
echo "📥 同步远程最新代码..."
git fetch origin "$BRANCH" 2>/dev/null && git rebase origin/"$BRANCH" 2>/dev/null || echo "   (远程仓库尚不存在或无法访问，使用本地版本)"

# 推送到 GitHub Pages
echo "🚀 推送到 GitHub Pages (git push)..."
MAX_RETRIES=2
RETRY_COUNT=0
PUSH_OK=false
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if git push origin "$BRANCH" 2>&1; then
        echo ""
        echo "✅ git push 部署成功！"
        echo "   🌐 https://${OWNER}.github.io/${REPO}/"
        PUSH_OK=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "   ⚠️ 推送失败，${RETRY_COUNT}/${MAX_RETRIES} 次重试，等待 5 秒..."
            sleep 5
        fi
    fi
done

# 若 git push 全部失败，回退到 GitHub REST API 逐文件推送
if [ "$PUSH_OK" != true ]; then
    echo ""
    echo "   ⚠️ git push 失败，切换到 GitHub REST API 方式..."

    # 提取 token：策略1 从 remote URL 提取 > 策略2 从配置文件读取
    TOKEN=$(echo "$REPO_URL" | sed -n 's|.*https://\([^@]*\)@github.com.*|\1|p')
    if [ -n "$TOKEN" ]; then
        echo "   (从 remote URL 提取 token: ${TOKEN:0:12}...)"
    elif [ -f "$TOKEN_FILE" ]; then
        TOKEN=$(cat "$TOKEN_FILE")
        echo "   (从配置文件读取 token: ${TOKEN:0:12}...)"
    else
        echo "   ❌ 无法获取 token（remote URL 无 token，配置文件不存在: $TOKEN_FILE）"
        exit 1
    fi

    # 获取变更文件列表 — 多策略 fallback
    CHANGED_FILES=""
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "")
    if [ -z "$CHANGED_FILES" ]; then
        CHANGED_FILES=$(git show --name-only --format="" HEAD 2>/dev/null || echo "")
    fi
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
