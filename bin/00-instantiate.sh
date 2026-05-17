#!/bin/bash

set -euo pipefail

# Install build dependencies
echo "Installing required dependencies:"
echo "  rpm-build rpmdevtools spectool"
echo "  make checkpolicy selinux-policy-devel"
echo "  tar bzip2"
sudo dnf install -y \
  rpm-build rpmdevtools spectool \
  make checkpolicy selinux-policy-devel \
  tar bzip2

# Set up the rpmbuild tree
echo "Setting up the rpmbuild tree..."
rpmdev-setuptree
# Creates: ~/rpmbuild/{SPECS,SOURCES,BUILD,RPMS,SRPMS}

echo "done. Bye ;)"
