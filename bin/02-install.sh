#!/bin/bash

set -euo pipefail

rpmtopdir="$(rpm --eval %_topdir)"
arch="$(rpm --eval %_arch)"
dist="$(rpm --eval %_arch)" # Includes the dot (e.g. .fc44)

# Install greyproxy first (greywall depends on it)
echo "Installing build packages..."
sudo dnf install -y \
    "$rpmtopdir/RPMS/$arch/greyproxy-*$dist.$arch.rpm" \
    "$rpmtopdir/RPMS/$arch/greywall-*$dist.$arch.rpm" \
    "$rpmtopdir/RPMS/$arch/opencode-*$dist.$arch.rpm"

echo "done. Bye ;)"
