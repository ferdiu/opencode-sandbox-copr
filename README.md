# opencode-sandbox-copr

RPM packaging for [opencode](https://opencode.ai) and its full security sandbox stack,
targeting Fedora via [COPR](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/).

A GitHub Actions workflow runs daily to detect new upstream releases
and trigger fresh COPR builds automatically.

## Packages

| Package | Upstream | Description |
|---------|----------|-------------|
| `opencode` | [anomalyco/opencode](https://github.com/anomalyco/opencode) | AI coding agent (self-contained Bun binary) |
| `opencode-selinux` | same | SELinux MAC policy module (permissive by default) |
| `opencode-sandbox` | same | Wrapper to launch opencode via greywall |
| `greywall` | [GreyhavenHQ/greywall](https://github.com/GreyhavenHQ/greywall) | Kernel-level sandbox (bubblewrap + Landlock + Seccomp) |
| `greyproxy` | [GreyhavenHQ/greyproxy](https://github.com/GreyhavenHQ/greyproxy) | Deny-by-default SOCKS5/DNS proxy with live dashboard |

## Install

```bash
sudo dnf copr enable ferdiu/opencode
sudo dnf install opencode opencode-selinux opencode-sandbox
# pulls greywall, greyproxy, bubblewrap, socat, strace automatically

greywall setup    # once per user: start greyproxy as a systemd user service
greywall check    # verify the sandbox stack is operational
```

## COPR build status

[![opencode build](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/opencode/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/opencode/)
[![greywall build](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greywall/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greywall/)
[![greyproxy build](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greyproxy/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/ferdiu/opencode/package/greyproxy/)

## Workflow status

[![COPR CI build](https://github.com/ferdiu/opencode-sandbox-copr/actions/workflows/copr-ci.yml/badge.svg)](https://github.com/ferdiu/opencode-sandbox-copr/actions/workflows/copr-ci.yml)

## Tracked versions

| Package | Upstream latest |
|---------|----------------|
| opencode | [![opencode](https://img.shields.io/badge/opencode-1.15.4-blue)](https://github.com/anomalyco/opencode/releases) |
| greywall | [![greywall](https://img.shields.io/badge/greywall-0.3.3-blue)](https://github.com/GreyhavenHQ/greywall/releases) |
| greyproxy | [![greyproxy](https://img.shields.io/badge/greyproxy-0.4.3-blue)](https://github.com/GreyhavenHQ/greyproxy/releases) |
