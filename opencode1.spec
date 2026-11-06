# opencode1.spec — Fedora COPR spec for opencode (legacy v1 line) + SELinux policy
#
# Repository:  https://github.com/ferdiu/opencode-sandbox-copr
# COPR project: https://copr.fedorainfracloud.org/coprs/ferdiu/opencode
#
# Legacy OpenCode v1 package. The current v2 line lives in opencode.spec.
#
# Part of a 4-spec COPR project. Directory layout expected in git:
#
#   opencode.spec       (current v2.x line)
#   opencode1.spec      (this file — legacy v1.x line)
#   greywall.spec
#   greyproxy.spec
#   sources/
#     opencode.te
#     opencode.fc
#     opencode-sandbox.sh
#
# Build this package locally:
#   spectool -g -R opencode1.spec          # download Source0
#   rpmbuild -bb opencode1.spec
#
# For COPR: add each spec as a separate package in the same project.
# COPR resolves cross-package Requires (greywall, greyproxy) at install time
# because they all land in the same dnf repository.

%global debug_package %{nil}
# Following lines disable some optimizations that might make interfere
# by (almost) silently creating borken hardlinks
%define __strip /bin/true
%define __brp_strip /bin/true
%define __brp_strip_comment_note /bin/true
%define __brp_strip_lto /bin/true
%define __brp_python_hardlink /bin/true
%define __brp_linkdupes /bin/true

Name:           opencode1
# Bump Version on each upstream v1.x release (the CI workflow does this
# automatically). This spec tracks the legacy v1.x line; the current v2.x
# line lives in opencode.spec.
# Quick SHA256: curl -sL <Source0 URL> | sha256sum
Version:        1.19.5
Release:        1%{?dist}
Summary:        Open source AI coding agent for the terminal

License:        MIT
URL:            https://opencode.ai

# Upstream distributes a single self-contained binary compiled with Bun.
# The tarball for linux-x64 unpacks as a bare ./opencode ELF (no subdirectory).
# Confirm layout with: tar -tzf opencode-linux-x64.tar.gz
Source0:        https://github.com/anomalyco/opencode/releases/download/v%{version}/opencode-linux-x64.tar.gz
Source1:        https://github.com/anomalyco/opencode/releases/download/v%{version}/opencode-linux-x64-baseline.tar.gz
# SELinux policy sources — live next to this spec in git (see sources/ dir)
Source2:        opencode.te
Source3:        opencode.fc
# Best opencode version selector wrapper — installed as /usr/libexec/opencode1/opencode-launch
Source4:        opencode-launch
# Greywall wrapper — installed as /usr/bin/opencode-sandbox
Source5:        opencode-sandbox.sh

# ── BuildRequires ──────────────────────────────────────────────────────────
# The opencode binary is pre-built; no compiler needed for it.
BuildRequires:  tar
# Needed to compile the SELinux .te + .fc into a .pp.bz2 module
BuildRequires:  make
BuildRequires:  selinux-policy-devel
BuildRequires:  checkpolicy

# ── Requires (main package) ────────────────────────────────────────────────
# The binary bundles the full Bun runtime — zero Node/Bun deps at runtime.
# bubblewrap + socat are required by greywall for its namespace sandbox;
# pulling them here guarantees the sandbox layer is available.
Requires:       bubblewrap
Requires:       socat
# Legacy OpenCode v1. Mutually exclusive with the current v2 package
# (opencode): both ship /usr/bin/opencode; switch with:
#   sudo dnf swap opencode1 opencode
Conflicts:      opencode

%description
OpenCode is an open source, terminal-based AI coding agent.

It supports multiple LLM providers (Claude, OpenAI, Gemini, local Ollama models)
and features built-in LSP support, a rich TUI, and a client/server architecture.

The upstream binary is compiled with Bun and is fully self-contained —
no Bun or Node.js runtime is required on the host system.

Security hardening subpackages also provided by this COPR:
  opencode1-selinux   — SELinux MAC policy module (permissive by default)
  opencode1-sandbox   — launcher that runs opencode inside a greywall sandbox
  greywall           — kernel-level filesystem+network sandbox (bubblewrap+Landlock)
  greyproxy          — deny-by-default SOCKS5/DNS transparent proxy


##############################################################################
# Subpackage: opencode1-selinux
##############################################################################
%package selinux
Summary:        SELinux policy module for opencode
Requires:       %{name} = %{version}-%{release}
Requires:       selinux-policy-targeted
Requires(post): policycoreutils
Requires(postun): policycoreutils

%description selinux
SELinux type enforcement module for the opencode AI coding agent.

Installed in PERMISSIVE mode by default: AVC denials are logged but nothing
is blocked. This lets you verify that legitimate tool access is allowed before
switching to enforcing mode.

Hardening workflow (run after a normal opencode session):
  sudo ausearch -c opencode --raw | audit2allow -M opencode-local
  sudo semodule -i opencode-local.pp
  sudo semanage permissive -d opencode_t    # enforce

Policy allows opencode to:
  - Read/write files in user_home_t (current project directory)
  - Execute /usr/bin/* binaries (git, LSP servers, compilers)
  - Create files/symlinks under /tmp (required for PATH shimming)
  - Connect outbound TCP 443 (HTTPS to LLM APIs)
  - Bind TCP on localhost (internal HTTP server / desktop client mode)

Policy denies (neverallow):
  - Write to ~/.ssh/ (ssh_home_t) or ~/.gnupg/ (gpg_home_t)
  - Load kernel modules (sys_module capability)
  - ptrace processes outside the opencode_t domain


##############################################################################
# Subpackage: opencode1-sandbox
##############################################################################
%package sandbox
Summary:        Run opencode inside a greywall deny-by-default sandbox
Requires:       %{name} = %{version}-%{release}
# greywall is built by greywall.spec in the same COPR project.
# Installing this subpackage will automatically pull in greywall, greyproxy,
# bubblewrap, and socat — the complete sandbox stack.
Requires:       greywall
Requires:       bubblewrap
Requires:       socat

%description sandbox
Thin wrapper script that invokes opencode through greywall, which enforces
a deny-by-default sandbox using bubblewrap user namespaces, Linux Landlock,
Seccomp BPF, and eBPF monitoring.

The opencode built-in greywall profile restricts filesystem access to the
current project directory and routes all outbound TCP/UDP through greyproxy.
Visit http://localhost:43080 to review and approve/deny network requests.

Usage:
  opencode-sandbox                    # sandboxed run using the learned profile
  GREYWALL_LEARN=1 opencode-sandbox   # learning mode: trace and build a profile
  opencode-sandbox --help             # passes flags through to opencode

On first run without a saved profile, greywall will prompt you to apply the
built-in opencode profile (covers ~/.config/opencode, ~/.local/share/opencode,
the working directory, and necessary system paths).


##############################################################################
# %prep
##############################################################################
%prep
# -c creates the named build dir; -T suppresses auto-unpack
%setup -q -c -T -n %{name}-%{version}
# ------------------ PLAIN ------------------
# Unpack the upstream tarball (bare binary layout, no subdirectory)
tar -xzf %{SOURCE0}
# Tolerate rare layout where upstream wraps inside a subdir
if [ -d opencode-linux-x64 ]; then
    mv opencode-linux-x64/opencode .
fi
mv opencode opencode-plain
# ------------------ BASELINE ------------------
# Unpack the upstream tarball (bare binary layout, no subdirectory)
tar -xzf %{SOURCE1}
# Tolerate rare layout where upstream wraps inside a subdir
if [ -d opencode-linux-x64-baseline ]; then
    mv opencode-linux-x64-baseline/opencode .
fi
mv opencode opencode-baseline

# Fail loudly if the binary is missing rather than producing a broken RPM
test -e opencode-plain || { echo "ERROR: opencode-plain binary not found after unpack"; exit 1; }
# Fail loudly if the binary is missing rather than producing a broken RPM
test -e opencode-baseline || { echo "ERROR: opencode-baseline binary not found after unpack"; exit 1; }


##############################################################################
# %build — compile SELinux policy module only
##############################################################################
%build
cp %{SOURCE2} opencode.te
cp %{SOURCE3} opencode.fc
make -f %{_datadir}/selinux/devel/Makefile opencode.pp
bzip2 -9 opencode.pp


##############################################################################
# %install
##############################################################################
%install
# Install the Bun-compiled binaries to libexecdir, NOT directly to bindir.
# The binaries use argv[0] (specifically basename(argv[0])) to decide whether
# to activate the opencode CLI or the raw Bun CLI. Installing it under
# libexecdir keeps it off PATH entirely, preventing the /tmp/bun-node-<hash>/
# shim mechanism from ever shadowing it with a stale "bun" symlink.
install -D -m 0755 opencode-plain \
    %{buildroot}%{_libexecdir}/opencode1/opencode
install -D -m 0755 opencode-baseline \
    %{buildroot}%{_libexecdir}/opencode1/opencode-baseline
# Install the default launch script
install -D -m 0755 %{SOURCE4} \
    %{buildroot}%{_libexecdir}/opencode1/opencode-launch

# SELinux .pp module
install -D -m 0644 opencode.pp.bz2 \
    %{buildroot}%{_datadir}/selinux/packages/opencode.pp.bz2

# Sandbox wrapper
install -D -m 0755 %{SOURCE5} \
    %{buildroot}%{_bindir}/opencode-sandbox

# Make sure the bindir exists since update-alternatives will create a link in it
install -d %{buildroot}%{_bindir}

##############################################################################
# %post — main
##############################################################################
%post
# Legacy line notice
echo "NOTE: opencode1 is the legacy OpenCode v1 line." >&2
echo "      For OpenCode v2: sudo dnf swap opencode1 opencode" >&2


##############################################################################
# %files — main
##############################################################################
%files
%{_libexecdir}/opencode1/opencode
%{_libexecdir}/opencode1/opencode-baseline
%{_libexecdir}/opencode1/opencode-launch


##############################################################################
# %files / scriptlets — opencode1-selinux
##############################################################################
%files selinux
%{_datadir}/selinux/packages/opencode.pp.bz2

%post selinux
semodule -i %{_datadir}/selinux/packages/opencode.pp.bz2 2>/dev/null || :
semanage permissive -a opencode_t 2>/dev/null || :
echo ""
echo "=== opencode SELinux module installed (PERMISSIVE mode) ==="
echo "Denials are logged but not enforced. After normal use, run:"
echo "  sudo ausearch -c opencode --raw | audit2allow -M opencode-local"
echo "  sudo semodule -i opencode-local.pp"
echo "  sudo semanage permissive -d opencode_t   # enable enforcement"
echo ""

# Register alternatives for /usr/bin/opencode. Higher priority means preferred by auto mode.
# Priorities: non-baseline (default opencode) = 100, baseline = 90
update-alternatives --install \
    /usr/bin/opencode opencode \
    %{_libexecdir}/opencode1/opencode-launch 50
# Individual candidates as slave entries (not replacing launcher); we register them too so admin can switch to them*

update-alternatives --install \
    /usr/bin/opencode opencode \
    %{_libexecdir}/opencode1/opencode 100
update-alternatives --install \
    /usr/bin/opencode opencode \
    %{_libexecdir}/opencode1/opencode-baseline 90

# Ensure /usr/bin/opencode points to the launcher (we installed launcher as the primary*
update-alternatives --set \
    opencode %{_libexecdir}/opencode1/opencode-launch >/dev/null 2>&1 || :

%postun selinux
if [ "$1" -eq 0 ]; then
    # Unload SELinux policy
    semodule -r opencode 2>/dev/null || :
    semanage permissive -d opencode_t 2>/dev/null || :
    # Remove alternatives entries on package removal
    update-alternatives --remove opencode %{_libexecdir}/opencode1/opencode-launch >/dev/null 2>&1 || :
    update-alternatives --remove opencode %{_libexecdir}/opencode1/opencode >/dev/null 2>&1 || :
    update-alternatives --remove opencode %{_libexecdir}/opencode1/opencode-baseline >/dev/null 2>&1 || :
fi


##############################################################################
# %files — opencode1-sandbox
##############################################################################
%files sandbox
%{_bindir}/opencode-sandbox


##############################################################################
# %changelog
##############################################################################
%changelog
* Fri Nov 06 2026 ferdiu - 1.19.5-1
- Split out as legacy v1 package; conflicts with opencode (v2)
