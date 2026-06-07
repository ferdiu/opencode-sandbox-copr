# greywall.spec — Fedora COPR spec for greywall
#
# Repository:   https://github.com/ferdiu/opencode-sandbox-copr
# COPR project: https://copr.fedorainfracloud.org/coprs/ferdiu/opencode
#
# greywall is a container-free, deny-by-default sandbox for AI coding agents.
# It uses bubblewrap namespaces, Linux Landlock, Seccomp BPF, and eBPF to
# confine filesystem and network access without requiring root or a daemon.
#
# Part of a 3-spec COPR project (opencode.spec, greywall.spec, greyproxy.spec).
# greywall Requires: greyproxy at runtime (installed automatically).
#
# Upstream: https://github.com/GreyhavenHQ/greywall
# License:  Apache-2.0
#
# Build notes:
#   - Pure Go (CGO_ENABLED=0), statically linked — no C deps, no shared libs
#   - Built from upstream source tarball using the system Go toolchain
#   - No post-build binary downloads (all offline after %prep)
#   - The upstream .goreleaser.yaml confirms: cmd/greywall is the main package
#
# To build locally:
#   spectool -g -R greywall.spec
#   rpmbuild -bb greywall.spec
#
# Versioning: update Version + release asset URLs together.
# Upstream archive naming (from install.sh): greywall_{ver}_Linux_x86_64.tar.gz

%global debug_package %{nil}

Name:           greywall
Version:        0.3.3
Release:        2%{?dist}
Summary:        Deny-by-default kernel sandbox for AI coding agents

License:        Apache-2.0
URL:            https://github.com/GreyhavenHQ/greywall

# Source tarball: upstream GoReleaser archive
# Naming convention confirmed from install.sh:
#   greywall_{VERSION_NUM}_{OS}_{ARCH}.tar.gz
#   where OS=Linux (capital L), ARCH=x86_64 or arm64
# The tarball contains: greywall (binary), LICENSE, README.md
Source0:        https://github.com/GreyhavenHQ/greywall/releases/download/v%{version}/greywall_%{version}_Linux_x86_64.tar.gz

# Checksums file (used for verification; not used in rpmbuild but good to keep)
# Source1:      https://github.com/GreyhavenHQ/greywall/releases/download/v%%{version}/checksums.txt

# ── BuildRequires ──────────────────────────────────────────────────────────
# We download the pre-built binary (same as the install.sh approach).
# greywall is a pure Go CGO_ENABLED=0 static binary; no build-time C deps.
# If you prefer to build from source, replace Source0 with the source tarball
# and add: BuildRequires: golang >= 1.22
BuildRequires:  tar

# ── Requires ───────────────────────────────────────────────────────────────
# bubblewrap: provides bwrap — the user-namespace sandbox backend on Linux.
# socat: used by greywall for network bridging inside the sandbox.
# greyproxy: the deny-by-default SOCKS5/DNS proxy that greywall routes through.
#   'greywall setup' installs and starts it as a systemd user service.
#   greyproxy is provided by greyproxy.spec in this same COPR project.
Requires:       bubblewrap
Requires:       socat
Requires:       greyproxy
# strace is used by --learning mode to trace filesystem access
Requires:       strace

# Optional but strongly recommended:
# systemd user services for greyproxy (the %post scriptlet starts it)
Requires(post): systemd

%description
Greywall is a container-free, deny-by-default sandbox for AI coding agents
on Linux. It uses bubblewrap user namespaces, Linux Landlock (kernel 5.13+),
Seccomp BPF, and eBPF to confine what a running agent can read, write, and
connect to — without requiring root, a daemon, or Docker overhead.

Features:
  - Built-in profiles for OpenCode, Claude Code, Codex, Cursor, Aider, and more
  - Learning mode (--learning): traces filesystem access via strace and generates
    a least-privilege profile automatically
  - Deny-by-default network: all outbound traffic blocked unless routed through
    greyproxy, which provides a live allow/deny dashboard at localhost:43080
  - Command blocking: deny dangerous commands (rm -rf /, git push, etc.)
  - SSH filtering: control which hosts and commands are allowed over SSH
  - Five Linux security layers: bwrap namespaces, Landlock, Seccomp BPF,
    eBPF monitoring, TUN-based network capture

Linux kernel >= 5.13 is recommended for full Landlock support (Fedora 35+).
Fedora 44 meets this requirement.

Quick start with OpenCode:
  greywall check                         # verify all dependencies
  greywall --learning -- opencode        # learn what opencode needs
  greywall -- opencode                   # run sandboxed (learned profile applied)


##############################################################################
# %prep
##############################################################################
%prep
# The GoReleaser tarball unpacks: greywall (binary), LICENSE, README.md
%setup -q -c -T -n %{name}-%{version}
tar -xzf %{SOURCE0}
# Confirm binary is present
test -e greywall || { echo "ERROR: greywall binary not found after unpack"; exit 1; }


##############################################################################
# %build — nothing to compile (pre-built binary)
##############################################################################
%build
# Intentionally empty: the upstream binary is statically compiled.
# If building from source is preferred, replace with:
#   export CGO_ENABLED=0
#   export GOFLAGS="-mod=mod"
#   go build -ldflags="-s -w -X main.version=%{version}" ./cmd/greywall


##############################################################################
# %install
##############################################################################
%install
install -D -m 0755 greywall \
    %{buildroot}%{_bindir}/greywall


##############################################################################
# %post — set up greyproxy service
##############################################################################
%post
# greywall setup installs greyproxy as a systemd --user service.
# We do NOT call it here because:
#   1. %post runs as root; user services must be installed per-user.
#   2. The user may not have a running session at package install time.
#
# Instead, print clear instructions. The user runs 'greywall setup' once
# after install, which: downloads greyproxy (if not already installed),
# registers the systemd user service, and starts it.
#
# Since greyproxy is now provided by greyproxy.spec in this repo, the binary
# is already on PATH. 'greywall setup' will use it directly without downloading.
echo ""
echo "=== greywall installed ==="
echo ""
echo "Next step — start the greyproxy service (once, per user):"
echo "  greywall setup"
echo ""
echo "Then verify everything is working:"
echo "  greywall check"
echo ""
echo "Run OpenCode sandboxed:"
echo "  greywall --learning -- opencode   # first time: learn what it needs"
echo "  greywall -- opencode              # subsequent runs"
echo ""
if ! setcap cap_bpf+ep %{_bindir}/greywall 2>/dev/null; then
    echo "WARNING: Could not set CAP_BPF capability on greywall." >&2
    echo "         eBPF-based violation monitoring will be unavailable." >&2
    echo "         Run 'greywall --linux-features' to check what security features" >&2
    echo "         are active on this system." >&2
    echo "         See: https://docs.greywall.io/greywall/cli-reference#greywall---linux-features" >&2
fi


##############################################################################
# %files
##############################################################################
%files
%license LICENSE
%doc README.md
%{_bindir}/greywall


##############################################################################
# %changelog
##############################################################################
%changelog
* Sat May 16 2026 Federico Manzella <ferdiu@users.noreply.github.com> - 0.3.3-1
- Initial COPR package for greywall v0.3.3
- Pre-built upstream binary (pure Go, CGO_ENABLED=0, static)
- Requires: greyproxy (from greyproxy.spec in this COPR), bubblewrap, socat, strace
- %post instructs user to run 'greywall setup' (cannot run user services as root)
