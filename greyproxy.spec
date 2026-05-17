# greyproxy.spec — Fedora COPR spec for greyproxy
#
# Repository:   https://github.com/ferdiu/opencode-sandbox-copr
# COPR project: https://copr.fedorainfracloud.org/coprs/ferdiu/opencode
#
# greyproxy is a managed SOCKS5/DNS/HTTP proxy with a live web dashboard.
# It is the network-control companion to greywall: greywall routes all
# sandboxed traffic through greyproxy, which enforces allow/deny rules and
# lets you inspect, approve, or block individual outbound connections.
#
# Part of a 3-spec COPR project (opencode.spec, greywall.spec, greyproxy.spec).
#
# Upstream: https://github.com/GreyhavenHQ/greyproxy
# License:  MIT (fork of GOST v3, also MIT)
#
# Build notes:
#   - Pure Go (CGO_ENABLED=0), statically linked — no C deps or shared libs
#   - Built from upstream release binary (same strategy as greywall.spec)
#   - Runs as a systemd --user service (not a system service; no root needed)
#   - Default ports: 43052 (SOCKS5), 43053 (DNS), 43080 (dashboard/API)
#   - Generates a CA certificate for TLS inspection; installs into user trust store
#
# IMPORTANT: greyproxy installs itself as a *user* systemd service.
# The RPM %post can only enable/start it via 'systemctl --user' which requires
# a running user session. We ship a systemd user unit file and use the
# recommended %systemd_user_post macros. Users must run:
#   systemctl --user enable --now greyproxy
# or simply run 'greywall setup' which handles this automatically.

%global debug_package %{nil}

Name:           greyproxy
# Latest release: v0.2.3 (March 5, 2026) — update Version + Source0 together
Version:        0.2.3
Release:        1%{?dist}
Summary:        Deny-by-default SOCKS5/DNS proxy with live dashboard for greywall

License:        MIT
URL:            https://github.com/GreyhavenHQ/greyproxy

# Upstream uses GoReleaser. Release asset naming convention:
#   greyproxy_{VERSION}_{OS}_{ARCH}.tar.gz  (OS=Linux capital, ARCH=x86_64)
# Tarball contents: greyproxy (binary), LICENSE, README.md
Source0:        https://github.com/GreyhavenHQ/greyproxy/releases/download/v%{version}/greyproxy_%{version}_Linux_x86_64.tar.gz

# Systemd user unit file (greyproxy registers itself; we ship a pre-written unit
# so rpm can use the standard %systemd_user_post macros)
Source1:        greyproxy.service

# ── BuildRequires ──────────────────────────────────────────────────────────
BuildRequires:  tar
BuildRequires:  systemd-rpm-macros

# ── Requires ───────────────────────────────────────────────────────────────
# nss-tools provides update-ca-trust (used by greyproxy cert install)
Requires:       ca-certificates
Requires:       nss-tools
# systemd --user support
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Greyproxy is a deny-by-default SOCKS5/DNS/HTTP transparent proxy used by
greywall to provide kernel-level network isolation for AI coding agents.

All outbound TCP and UDP traffic from a greywall sandbox is routed through
greyproxy. Network requests are blocked by default unless explicitly allowed
via the live web dashboard at http://localhost:43080 or by defining allow/deny
rules in the rule engine.

Default service ports (localhost only):
  43051 — HTTP proxy
  43052 — SOCKS5 proxy  (greywall's default outbound route)
  43053 — DNS proxy
  43080 — Dashboard, REST API, and WebSocket live updates

Features:
  - Web dashboard: real-time traffic overview, rule management, pending requests
  - Rule engine: pattern matching on destination, port, and container
  - TLS inspection: MITM CA auto-generated; installed into the system trust store
  - Sensitive header redaction: strips Authorization, Cookie, API keys from logs
  - Single self-contained binary: dashboard assets embedded, no frontend deploy
  - systemd user service: runs without root, per-user process

This package is automatically installed as a dependency of greywall.
After installing, activate the service (once per user):
  systemctl --user enable --now greyproxy
Or let greywall handle it:
  greywall setup


##############################################################################
# %prep
##############################################################################
%prep
%setup -q -c -T -n %{name}-%{version}
tar -xzf %{SOURCE0}
test -e greyproxy || { echo "ERROR: greyproxy binary not found after unpack"; exit 1; }


##############################################################################
# %build — nothing to compile
##############################################################################
%build
# Pre-built static binary; no compilation needed.


##############################################################################
# %install
##############################################################################
%install
# Binary
install -D -m 0755 greyproxy \
    %{buildroot}%{_bindir}/greyproxy

# systemd user unit
# We install into the system-wide user unit dir so it's available for all users.
# Each user enables/starts it independently with 'systemctl --user enable greyproxy'
install -D -m 0644 %{SOURCE1} \
    %{buildroot}%{_userunitdir}/greyproxy.service


##############################################################################
# %post / %preun / %postun — systemd user service lifecycle
##############################################################################
%post
%systemd_user_post greyproxy.service
echo ""
echo "=== greyproxy installed ==="
echo ""
echo "Enable and start the greyproxy user service:"
echo "  systemctl --user enable --now greyproxy"
echo ""
echo "Dashboard available at: http://localhost:43080"
echo ""
echo "Or simply run 'greywall setup' which handles this automatically."
echo ""

%preun
%systemd_user_preun greyproxy.service

%postun
%systemd_user_postun_with_restart greyproxy.service


##############################################################################
# %files
##############################################################################
%files
%license LICENSE
%doc README.md
%{_bindir}/greyproxy
%{_userunitdir}/greyproxy.service


##############################################################################
# %changelog
##############################################################################
%changelog
* Sat May 16 2026 Federico Manzella <ferdiu@users.noreply.github.com> - 0.2.3-1
- Initial COPR package for greyproxy v0.2.3
- Pre-built upstream binary (pure Go, CGO_ENABLED=0, static)
- Ships systemd user unit; uses %%systemd_user_post macros per Fedora guidelines
- Requires: ca-certificates, nss-tools (for greyproxy cert install / update-ca-trust)
