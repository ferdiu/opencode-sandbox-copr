#!/bin/bash

set -euo pipefail

rpmtopdir="$(rpm --eval %_topdir)"
arch="$(rpm --eval %_arch)"
dist="$(rpm --eval %_arch)" # Includes the dot (e.g. .fc44)

# Copy your spec files and sources into place
echo "Copying spec files in rpm SOURCES topdir..."
cp opencode.spec  "$rpmtopdir/SPECS/"
cp greywall.spec  "$rpmtopdir/SPECS/"
cp greyproxy.spec "$rpmtopdir/SPECS/"

# Sources that are local files (not downloaded)
echo "Copying source files in rpm SOURCES topdir..."
cp sources/opencode.te          "$rpmtopdir/SOURCES/"
cp sources/opencode.fc          "$rpmtopdir/SOURCES/"
cp sources/opencode-sandbox.sh  "$rpmtopdir/SOURCES/"
cp sources/greyproxy.service    "$rpmtopdir/SOURCES/"

# Download the remote Source0 tarballs for each spec
echo "Downloading additional source files from spec files..."
spectool -g -C "$rpmtopdir/SOURCES/" "$rpmtopdir/SPECS/opencode.spec"
spectool -g -C "$rpmtopdir/SOURCES/" "$rpmtopdir/SPECS/greywall.spec"
spectool -g -C "$rpmtopdir/SOURCES/" "$rpmtopdir/SPECS/greyproxy.spec"

# Build pacakges using spec file
echo "Starting actual build of the packages..."
rpmbuild -bb "$rpmtopdir/SPECS/greyproxy.spec" 2>&1 | tee /tmp/greyproxy-build.log
rpmbuild -bb "$rpmtopdir/SPECS/greywall.spec"  2>&1 | tee /tmp/greywall-build.log
rpmbuild -bb "$rpmtopdir/SPECS/opencode.spec"  2>&1 | tee /tmp/opencode-build.log

# Show results
echo "Built following packages:"
find "$rpmtopdir/RPMS/$arch/" -name "greyproxy-*$dist.$arch.rpm"
find "$rpmtopdir/RPMS/$arch/" -name "greywall-*$dist.$arch.rpm"
find "$rpmtopdir/RPMS/$arch/" -name "opencode-*$dist.$arch.rpm"

echo "done. Bye ;)"
