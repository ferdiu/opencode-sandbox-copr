# opencode-sandbox-copr

RPM packaging for [opencode](https://opencode.ai) and its full security sandbox
stack, targeting Fedora via the
[ferdiu/opencode](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/) COPR.

A GitHub Actions workflow runs daily, checks all three upstream projects for new
releases, and triggers a fresh COPR build for each package that is behind.

---

## Packages

| RPM | Upstream | Description |
|-----|----------|-------------|
| `opencode` | [anomalyco/opencode](https://github.com/anomalyco/opencode) | AI coding agent (self-contained Bun binary, no Node/Bun runtime needed) |
| `opencode-selinux` | same | SELinux MAC policy module (permissive by default) |
| `opencode-sandbox` | same | Wrapper to launch opencode inside a greywall sandbox |
| `greywall` | [GreyhavenHQ/greywall](https://github.com/GreyhavenHQ/greywall) | Deny-by-default kernel sandbox (bubblewrap + Landlock + Seccomp BPF) |
| `greyproxy` | [GreyhavenHQ/greyproxy](https://github.com/GreyhavenHQ/greyproxy) | Deny-by-default SOCKS5/DNS proxy with live web dashboard |

---

## Install

```bash
sudo dnf copr enable ferdiu/opencode
sudo dnf install opencode opencode-selinux opencode-sandbox
# automatically pulls: greywall, greyproxy, bubblewrap, socat, strace

# One-time per-user setup: start greyproxy as a systemd user service
greywall setup
greywall check    # verify the full sandbox stack is operational
```

---

## COPR build status

[![opencode](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/opencode/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/opencode/)
[![greywall](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greywall/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greywall/)
[![greyproxy](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greyproxy/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greyproxy/)

## Workflow status

[![COPR CI build](https://github.com/ferdiu/opencode-sandbox-copr/actions/workflows/copr-ci.yml/badge.svg)](https://github.com/ferdiu/opencode-sandbox-copr/actions/workflows/copr-ci.yml)

---

## Repository layout

```
opencode.spec                         # opencode + -selinux + -sandbox subpackages
greywall.spec                         # greywall sandbox binary
greyproxy.spec                        # greyproxy companion proxy (systemd user service)
sources/
  opencode.te                         # SELinux type enforcement rules
  opencode.fc                         # SELinux file context definitions
  opencode-sandbox.sh                 # wrapper script → /usr/bin/opencode-sandbox
  greyproxy.service                   # systemd user unit for greyproxy
.github/
  workflows/
    copr-ci.yml                       # daily version check + COPR build trigger
```

---

## Setting up the GitHub Actions workflow

### 1. Create the COPR project

Go to https://copr.fedorainfracloud.org/coprs/ferdiu/ and create a new project
named **opencode**. Enable at least `fedora-44-x86_64` as a chroot.

### 2. Add the three packages

In the COPR project UI, add three packages manually — one per spec file —
or let the workflow trigger the first build which registers them automatically
via `copr-cli build`.

### 3. Get your COPR API token

Visit https://copr.fedorainfracloud.org/api/ while logged in. You will see a
pre-filled config block like:

```ini
[copr-cli]
login    = <your-login-token>
username = ferdiu
token    = <your-api-token>
copr_url = https://copr.fedorainfracloud.org
```

### 4. Add GitHub repository secrets

Go to **Settings → Secrets and variables → Actions** in this repository and add:

| Secret name | Value |
|-------------|-------|
| `COPR_BUILD_L` | the `login` value from the API page |
| `COPR_BUILD_T` | the `token` value from the API page |

### 5. Trigger the first run

Either push a commit or go to **Actions → COPR CI build → Run workflow**
to trigger the first build manually. After the first successful run, the
workflow runs automatically at 02:00 UTC every day.

---

## Hardening opencode after install (SELinux enforcing mode)

```bash
# Use opencode normally for a session, then collect AVC denials:
sudo ausearch -c opencode --raw | audit2allow -M opencode-local
sudo semodule -i opencode-local.pp

# Switch from permissive logging to enforcing:
sudo semanage permissive -d opencode_t

# Confirm:
sudo semanage permissive -l | grep opencode   # should be empty
```

---

## Updating package versions manually

The workflow patches the `Version:` line in each spec file automatically before
each build. If you need to bump a version manually (e.g. to pin a specific
release), edit the relevant spec file and push — the next workflow run will
detect the mismatch and build.

---

## Links

- COPR project: https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/
- opencode upstream: https://github.com/anomalyco/opencode
- greywall upstream: https://github.com/GreyhavenHQ/greywall
- greyproxy upstream: https://github.com/GreyhavenHQ/greyproxy
- Fedora packaging guidelines: https://docs.fedoraproject.org/en-US/packaging-guidelines/
