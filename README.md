# `shasta-authorization-module`
This is an ansible module that simplifies interacting with JSON-based 
Shasta microservices with authorization tokens. It relies on running APIs
to type check variables passed in via the request itself.

More complete documentation and examples for how to use this are included
in the [src/authorized.py](src/authorized.py) module itself.

This module requires one of the following conditions to be true in order
for automatic authorization to function:
- Kubectl on the target node, such that 'oauth-client-secret' can be obtained.
- Users passing in 'oauth-client-secret' explicitly.

## Build Helpers
This repo uses some build helpers from the 
[cms-meta-tools](https://github.com/Cray-HPE/cms-meta-tools) repo. See that repo for more details.

## Local Builds
If you wish to perform a local build, you will first need to clone or copy the contents of the
cms-meta-tools repo to `./cms_meta_tools` in the same directory as the `Makefile`. When building
on github, the cloneCMSMetaTools() function clones the cms-meta-tools repo into that directory.

For a local build, you will also need to manually write the .version, .docker_version (if this repo
builds a docker image), and .chart_version (if this repo builds a helm chart) files. When building
on github, this is done by the setVersionFiles() function.

## Copyright and License
This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.

When making any modifications to a file that has a Cray/HPE copyright header, that header
must be updated to include the current year.

When creating any new files in this repo, if they contain source code, they must have
the HPE copyright and license text in their header, unless the file is covered under
someone else's copyright/license (in which case that should be in the header). For this
purpose, source code files include Dockerfiles, Ansible files, and shell scripts. It does
**not** include Jenkinsfiles or READMEs.

When in doubt, provided the file is not covered under someone else's copyright or license, then
it does not hurt to add ours to the header.
