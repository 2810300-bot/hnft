#!/bin/bash
# ============================================================
# GitHub Pages 自动部署脚本
# ============================================================
# 将 hnft-site/ 目录部署到 https://2810300-bot.github.io/hnft/
#
# 用法:
#   bash deploy.sh                           # 提交所有变更并推送
#   bash deploy.sh --message "自定义提交信息"  # 自定义 commit message
#   bash deploy.sh --dry-run                 # 仅检查，不实际推送
#
# 由自动化任务调用，也可手动执行。
# 需要配置 GitHub 认证（SSH key 或 Personal Access Token）。
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# 优先用 env 指定，其次检测本地 git remote，最后用 HTTPS+token 兜底
if [ -n "${GITHUB_PAGES_REPO:-}" ]; then
    REPO_URL="$GITHUB_PAGES_REPO"
elif git remote get-url origin 2>/dev/null | grep -q '@\|https'; then
    REPO_URL="$(git remote get-url origin)"
else
    REPO_URL="https://github.com/2810300-bot/hnft.git"
fi
BRANCH="${GITHUB_PAGES_BRANCH:-main}"
COMMIT_MSG="auto: dashboard refresh $(date '+%Y-%m-%d %H:%M:%S')"
DRY_RUN=false

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
echo "  目标: $REPO_URL"
echo "============================================"

cd "$SITE_DIR"

# 检查是否为 git 仓库
if [ ! -d ".git" ]; then
    echo "🔧 初始化 Git 仓库..."
    git init
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
fi

# 拉取最新代码并 rebase 本地变更（保留本地文件）
echo "📥 拉取远程最新代码..."
git fetch origin "$BRANCH" 2>/dev/null && git pull --rebase origin "$BRANCH" 2>/dev/null || echo "   (远程仓库尚不存在或无法访问，使用本地版本)"

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

# 添加并提交
echo "📦 提交变更..."
git add -A
git commit -m "$COMMIT_MSG" || { echo "⚠️ 无内容可提交"; exit 0; }

# 推送到 GitHub Pages
echo "🚀 推送到 GitHub Pages..."
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if git push origin "$BRANCH" 2>&1; then
        echo ""
        echo "✅ 部署成功！"
        echo "   🌐 https://2810300-bot.github.io/hnft/"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "   ⚠️ 推送失败，${RETRY_COUNT}/${MAX_RETRIES} 次重试，等待 10 秒..."
            git pull --rebase origin "$BRANCH" 2>/dev/null || true
            sleep 10
        else
            echo "❌ 部署失败：推送 $MAX_RETRIES 次后仍失败"
            echo "   请检查 GitHub 认证配置和网络连接"
            exit 1
        fi
    fi
done

echo ""
echo "============================================"
echo "  部署摘要"
echo "  站点: https://2810300-bot.github.io/hnft/"
echo "  提交: $COMMIT_MSG"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
