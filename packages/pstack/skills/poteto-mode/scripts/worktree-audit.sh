#!/usr/bin/env bash
# PATCH-HERMES-SCRIPT-PATHS
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and the most recent chat that
# operated in it. Emits a table sorted by size with a suggested bucket. Never
# deletes anything; deletion stays a human-gated step in the playbook.
#
# Usage: worktree-audit.sh [repo-path]   (defaults to the current repo)
set -u

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

# Main worktree is the first entry; everything else is a candidate.
main_wt=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')

# Remote enrichment is bounded and non-interactive. Repositories without an
# origin stay fully local; a dead network or unauthenticated gh may not hang the
# audit indefinitely.
has_origin=no
if git remote get-url origin >/dev/null 2>&1; then
	has_origin=yes
	timeout 20s env GIT_TERMINAL_PROMPT=0 git fetch origin main --quiet 2>/dev/null \
		|| echo "warn: could not refresh origin/main; merged column may be stale" >&2
fi

# PR state by branch, fetched once. Empty if origin or gh is unavailable.
prs=$(mktemp)
if [ "$has_origin" = yes ] && command -v gh >/dev/null 2>&1; then
	GH_PROMPT_DISABLED=1 timeout 20s gh pr list --author "@me" --state all --limit 1000 \
		--json number,state,headRefName 2>/dev/null > "$prs" || echo "[]" > "$prs"
else
	echo "[]" > "$prs"
fi

# Session evidence is queried by the supervising Hermes agent through
# session_search. This shell helper deliberately has no hidden transcript path.
now=$(date +%s)

printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE\n"

git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do
	[ "$wt" = "$main_wt" ] && continue

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of main, so PR state is the
	# real signal; merge-base only catches fast-forward/rebase merges.
	git merge-base --is-ancestor "$head" origin/main 2>/dev/null && merged=YES || merged=no

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	porcelain=$(git -C "$wt" status --porcelain 2>/dev/null)
	if [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		[ "$(git -C "$wt" rev-parse "origin/$branch" 2>/dev/null)" = "$head" ] \
			&& remote=pushed \
			|| remote="ahead$(git -C "$wt" rev-list --count "origin/$branch..HEAD" 2>/dev/null)"
	else remote=no-remote; fi

	pr=$([ -n "$branch" ] && jq -r --arg b "$branch" \
		'.[] | select(.headRefName==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
	[ -z "$pr" ] && pr="-"

	# A supervising Hermes agent may inspect session evidence with session_search
	# before using this table. The shell helper never guesses or scans transcripts.
	last="-"
	recent=no

	case "$dirty" in wip:*) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=safe
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh

rm -f "$prs"
