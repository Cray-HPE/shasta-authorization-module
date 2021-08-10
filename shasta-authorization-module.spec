# Copyright 2019,2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)
Name: shasta-authorization-module
License: MIT
Summary: An Ansible Module that authenticates requests into the management plane
Group: System/Management
Version: %(cat .version)
Release: %(echo ${BUILD_METADATA})
BuildArch: noarch
Source: %{name}-%{version}.tar.bz2
Vendor: Hewlett Packard Enterprise Development LP
Requires: cray-crayctl
Requires: cray-python-helper-requires-crayctldeploy

# Project level defines TODO: These should be defined in a central location; DST-892
%define afd /opt/cray/crayctl/ansible_framework
%define modules %{afd}/library

%description
Provides an Ansible module that allows for interacting with Shasta JSON-based microservices
in an authenticated way. Includes required oauthlib libraries.

%prep
%setup -q

%build

%install
install -m 755 -d %{buildroot}%{modules}/
install -D -m 644 src/authorized.py %{buildroot}%{modules}/authorized.py

%clean
rm -f  %{buildroot}%{modules}/*

%files
%defattr(755, root, root)
%{modules}/authorized.py
