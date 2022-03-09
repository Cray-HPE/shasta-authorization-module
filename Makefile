#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# If you wish to perform a local build, you will need to clone or copy the contents of the
# cms-meta-tools repo to ./cms_meta_tools

NAME ?= shasta-authorization-module
RPM_VERSION ?= $(shell head -1 .version)

SPEC_NAME ?= ${NAME}
SPEC_FILE ?= ${SPEC_NAME}.spec
BUILD_METADATA ?= "1~development~$(shell git rev-parse --short HEAD)"
SOURCE_NAME ?= ${SPEC_NAME}-${RPM_VERSION}
BUILD_DIR ?= $(PWD)/dist/rpmbuild
SOURCE_PATH := ${BUILD_DIR}/SOURCES/${SOURCE_NAME}.tar.bz2

all : runbuildprep lint prepare rpm
rpm: rpm_package_source rpm_build_source rpm_build

runbuildprep:
		./cms_meta_tools/scripts/runBuildPrep.sh

lint:
		./cms_meta_tools/scripts/runLint.sh

prepare:
		rm -rf dist
		mkdir -p $(BUILD_DIR)/SPECS $(BUILD_DIR)/SOURCES
		cp $(SPEC_FILE) $(BUILD_DIR)/SPECS/

rpm_package_source:
		tar --transform 'flags=r;s,^,/$(SOURCE_NAME)/,' \
				-cvjf $(SOURCE_PATH) \
				src \
				.version \
				LICENSE \
				Makefile \
				${SPEC_FILE} \
				gitInfo.txt \
				README.md

rpm_build_source:
		BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ts $(SOURCE_PATH) --define "_topdir $(BUILD_DIR)"

rpm_build:
		BUILD_METADATA=$(BUILD_METADATA) rpmbuild -ba $(SPEC_FILE) --define "_topdir $(BUILD_DIR)"
