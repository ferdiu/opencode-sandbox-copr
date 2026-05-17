#!/bin/bash

set -euo pipefail

rpmtopdir="$(rpm --eval %_topdir)"
arch="$(rpm --eval %_arch)"
dist="$(rpm --eval %dist)" # Includes the dot (e.g. .fc44)

installable=(
    $(find "$rpmtopdir/RPMS/$arch/" -name "greyproxy-*$dist.$arch.rpm")
    $(find "$rpmtopdir/RPMS/$arch/" -name "greywall-*$dist.$arch.rpm")
    $(find "$rpmtopdir/RPMS/$arch/" -name "opencode-*$dist.$arch.rpm")
)

# Install greyproxy first (greywall depends on it)
echo "Installing build packages ${installable[@]}..."
sudo rpm -Uvh --force "${installable[@]}"

echo "done. Bye ;)"
