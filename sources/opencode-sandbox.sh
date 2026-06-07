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
#   opencode-sandbox serve [ARGS]       # run opencode web server, adds --port to
#                                       # greywall from config or default (4096)
#   opencode-sandbox web [ARGS]         # alias for serve; also opens browser at
#                                       # http://localhost:<PORT> after launch
#
# Network:
#   All outbound traffic is routed through greyproxy (localhost:43052).
#   Visit http://localhost:43080 to approve or deny connection requests.
#
# First run:
#   greywall --learning -- opencode     # run once to trace filesystem access
#   greywall templates show opencode    # inspect the generated profile
#   opencode-sandbox                    # subsequent runs use the saved profile
#
# serve / web mode:
#   greywall's deny-by-default sandbox blocks opencode from opening a browser
#   window automatically. The `web` subcommand works around this by translating
#   to `serve` (the real opencode subcommand) and then opening the browser from
#   *outside* the sandbox, where it has access to the desktop environment.
#
#   The port is resolved in this order:
#     1. server.port key in ~/.config/opencode/config.json  (parsed with jq)
#     2. Hard-coded fallback: 4096  (opencode's own default)
#
#   greywall needs the port at launch time so it can add the corresponding
#   --port allow-rule before the sandbox is locked down.
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

# ── Detect serve / web subcommands ────────────────────────────────────────
# `web` is a sandbox-friendly alias for `serve`: it runs the opencode web
# server and then opens the browser from outside the sandbox (greywall blocks
# opencode itself from spawning a browser process).
OPEN_BROWSER=0
FIRST_ARG="${1:-}"

if [[ "$FIRST_ARG" == "web" || "$FIRST_ARG" == "serve" ]]; then
    [[ "$FIRST_ARG" == "web" ]] && OPEN_BROWSER=1

    # Replace the first argument with the real opencode subcommand `serve`,
    # then shift it off — we pass it explicitly in the exec call below.
    shift
    OPENCODE_SUBCMD="serve"

    # Resolve the port: prefer server.port from the opencode config file;
    # fall back to 4096 (opencode's built-in default) if the key is absent,
    # the file doesn't exist, or jq is not installed.
    OPENCODE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/config.json"
    OPENCODE_DEFAULT_PORT=4096
    PORT=$OPENCODE_DEFAULT_PORT

    if command -v jq &>/dev/null && [[ -f "$OPENCODE_CONFIG" ]]; then
        _port=$(jq -r '.server.port // empty' "$OPENCODE_CONFIG" 2>/dev/null || true)
        [[ -n "$_port" ]] && PORT=$_port
    fi

    # ── Run serve mode ─────────────────────────────────────────────────────
    if [[ "${GREYWALL_LEARN:-0}" == "1" ]]; then
        echo "[opencode-sandbox] Learning mode: tracing filesystem access with strace."
        echo "[opencode-sandbox] A greywall profile will be saved automatically."
        echo "[opencode-sandbox] Re-run without GREYWALL_LEARN=1 to apply the profile."
        echo ""
        exec "$GREYWALL" --learning --port "$PORT" -- opencode "$OPENCODE_SUBCMD" "$@"
    else
        if (( OPEN_BROWSER )); then
            # Open the browser *before* exec so this process can still run
            # xdg-open. After exec, the shell is replaced by greywall and
            # the sandbox would block any attempt to launch a browser.
            echo "[opencode-sandbox] Opening browser at http://localhost:${PORT} ..."
            sleep 3 && xdg-open "http://localhost:${PORT}" &>/dev/null &
        fi

        exec "$GREYWALL" --port "$PORT" -- opencode "$OPENCODE_SUBCMD" "$@"
    fi
fi

# ── Default: run opencode via greywall ────────────────────────────────────
if [[ "${GREYWALL_LEARN:-0}" == "1" ]]; then
    echo "[opencode-sandbox] Learning mode: tracing filesystem access with strace."
    echo "[opencode-sandbox] A greywall profile will be saved automatically."
    echo "[opencode-sandbox] Re-run without GREYWALL_LEARN=1 to apply the profile."
    echo ""
    exec "$GREYWALL" --learning -- opencode "$@"
else
    exec "$GREYWALL" -- opencode "$@"
fi
