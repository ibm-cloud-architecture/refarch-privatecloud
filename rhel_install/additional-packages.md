Additional Packages to Install
=====================================================
# Introduction

This document provides a list of packages that are convenient to have on ICP machines.

# Yum Repositories

For RHEL on `x86` be sure to set up at least the following repositories or subscriptions (if using RHS)
- os
- optional
- supplementary
- extras

The `extras` repo is important for things like ansible and some packages that are pre-reqs for Docker.

For RHEL on `ppc64` be sure to set up at least the following repositories:
- os
- optional
- supplementary
- epel

The `epel` repo has ansible and docker pre-req packages in it.

# Additional packages to install

This section lists some software that is needed at some time or another and it is not part of a minimal RHEL server installation.

*NOTE:* Git and Ansible are only needed on the boot/master node.

| **Package**    | **Install Command**         | **Comments**                     |
|:--------------:|:----------------------------|:---------------------------------|
| yum-utils      | `yum -y install yum-utils`  | for `yum-config-manager`           |    
| unzip          | `yum -y install unzip`      | zip archive extractor            |
| git            | `yum -y install git`        | source file repo management <br/>`boot` node only |
| bind-utils     | `yum -y install bind-utils` | for `nslookup`                     |
| net-tools      | `yum -y install net-tools`  | for `netstat` to see what ports are in use  |
| psmisc         | `yum -y install psmisc`     | for `fuser` to find/kill processes holding file locks     |
| lsof           | `yum -y install lsof`       | old school utility to find processes holding file locks |
| dos2unix       | `yum -y install dos2unix`   | for cleaning up files that come from Windows            |
| nano           | `yum -y install nano`       | Text editor many people prefer over `vi`   |
| ansible        | `yum -y install ansible`    | for convenient multi-host automation<br/>Ansible is in RHEL `extras` or `epel` repo.<br/>`boot` node only |
|wget   | yum -y install wget   | wget is generally useful for getting various artifacts  |
|java   | TBD  | Java may be needed for keytool or other utilities   |
