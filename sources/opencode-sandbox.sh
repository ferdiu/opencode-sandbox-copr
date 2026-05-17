#!/usr/bin/env bash
# opencode-sandbox — run opencode inside a greywall deny-by-default sandbox
#
# Installed by the opencode-sandbox subpackage from opencode.spec.
# Requires: greywall (from greywall.spec) + greyproxy (from greyproxy.spec)
#
# Usage:
#   opencode-sandbox                    # sandboxed run (greywall profile applied)
#   GREYWALL_LEARN=1 opencode-sandbox   # learning mode: trace and build profile
#   opencode-sandbox --help             # pass flags directly to opencode
#
# Network:
#   All outbound traffic is routed through greyproxy (localhost:43052).
#   Visit http://localhost:43080 to approve or deny connection requests.
#
# First run:
#   greywall --learning -- opencode     # run once to trace filesystem access
#   greywall templates show opencode    # inspect the generated profile
#   opencode-sandbox                    # subsequent runs use the saved profile

set -euo pipefail

# ── Locate greywall ────────────────────────────────────────────────────────
GREYWALL=$(command -v greywall 2>/dev/null || true)

if [[ -z "$GREYWALL" ]]; then
    echo "ERROR: greywall not found in PATH." >&2
    echo "Install it with: sudo dnf install greywall" >&2
    echo "(greywall is provided by the greywall package in this COPR repository)" >&2
    exit 1
fi

# ── Check greyproxy is running ─────────────────────────────────────────────
if ! systemctl --user is-active --quiet greyproxy 2>/dev/null; then
    echo "NOTICE: greyproxy user service is not running." >&2
    echo "Starting greyproxy setup (this only needs to happen once)..." >&2
    echo "" >&2
    systemctl --user enable --now greyproxy
    echo "" >&2
fi

# ── Run opencode via greywall ──────────────────────────────────────────────
if [[ "${GREYWALL_LEARN:-0}" == "1" ]]; then
    echo "[opencode-sandbox] Learning mode: tracing filesystem access with strace."
    echo "[opencode-sandbox] A greywall profile will be saved automatically."
    echo "[opencode-sandbox] Re-run without GREYWALL_LEARN=1 to apply the profile."
    echo ""
    exec "$GREYWALL" --learning -- opencode "$@"
else
    exec "$GREYWALL" -- opencode "$@"
fi
