# Copyright 2019,2021 Hewlett Packard Enterprise Development LP
Name: shasta-authorization-module
License: MIT
Summary: An Ansible Module that authenticates requests into the management plane
Group: System/Management
Version: %(cat .rpm_version)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Requires: cray-crayctl
Requires: cray-python-helper-requires-crayctldeploy

# Project level defines TODO: These should be defined in a central location; DST-892
%define afd /opt/cray/crayctl/ansible_framework
%define modules %{afd}/library

%description
Provides an Ansible module that allows for interacting with Shasta JSON based microservices
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
