#!/bin/sh
set -eu

EXPECTED_ORIGIN='https://github.com/Karin-Laboratory/sbat6-usb-nic.git'

TOP=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "ERROR: not inside a git repository" >&2
    exit 1
}

cd "$TOP"

ORIGIN=$(git remote get-url origin 2>/dev/null || true)

if [ "$ORIGIN" != "$EXPECTED_ORIGIN" ]; then
    echo "ERROR: wrong origin" >&2
    echo "expected: $EXPECTED_ORIGIN" >&2
    echo "actual:   $ORIGIN" >&2
    exit 1
fi

test -f docs/T6A_AUTONOMOUS_LOOP_V1.md || {
    echo "ERROR: T6A repository marker missing" >&2
    exit 1
}

for p in \
    AGENTS.md \
    ALPHA_PLAN.md \
    AUTHORITY.md \
    zen3-gnss-feeder.py \
    venue-youtube-ad-skip \
    tools/find_vm_host_clues.py
do
    if [ -e "$p" ]; then
        echo "ERROR: foreign ButlerX marker found: $p" >&2
        exit 1
    fi
done

git fetch origin main --quiet

git merge-base HEAD origin/main >/dev/null 2>&1 || {
    echo "ERROR: HEAD has no common ancestor with origin/main" >&2
    exit 1
}

echo "REPO_IDENTITY_OK=Karin-Laboratory/sbat6-usb-nic"
