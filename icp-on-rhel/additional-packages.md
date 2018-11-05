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

The `extras` repo is important for things like Ansible and some packages that are pre-reqs for Docker.

For RHEL on `ppc64` be sure to set up at least the following repositories:
- os
- optional
- supplementary
- epel

The `epel` repo has Ansible and Docker pre-req packages in it.

TBD - Does `s390x` (zLinux) have any particular `yum` repositories that should be configured?

# Additional packages to install

This section lists some software that is needed at some time or another. These packages may not be part of a minimal RHEL server installation.

*NOTE:* Git, Ansible and Java are only needed on the boot/master node.

| **Package**    | **Install Command**         | **Comments**                     |
|:--------------:|:----------------------------|:---------------------------------|
| yum-utils      | `yum -y install yum-utils`  | for `yum-config-manager`           |    
| unzip          | `yum -y install unzip`      | zip archive extractor            |
| git            | `yum -y install git`        | source file repo management <br/>`boot` node only |
| jq             | `yum -y install jq`         | For JSON parsing in shell scripts  |
| bind-utils     | `yum -y install bind-utils` | for `nslookup`                     |
| net-tools      | `yum -y install net-tools`  | for `netstat` to see what ports are in use  |
| psmisc         | `yum -y install psmisc`     | for `fuser` to find/kill processes holding file locks     |
| lsof           | `yum -y install lsof`       | old school utility to find processes holding file locks |
| dos2unix       | `yum -y install dos2unix`   | for cleaning up files that come from Windows            |
| nano           | `yum -y install nano`       | Text editor many people prefer over `vi`   |
| vim            | yum -y install vim          | Text editor variation on `vi`   |
| ansible        | `yum -y install ansible`    | for convenient multi-host automation<br/>Ansible is in RHEL `extras` or `epel` repo.<br/>`boot` node only |
|wget            | yum -y install wget   | wget is generally useful for getting various artifacts  |
|nfs             | yum -y install nfs-utils   | Needed if you want to use NFS client or server   |
|java   | yum -y install `<java_package>`  | Where `<java_package>` is dependent on JDK/JRE version.<br/>Java may be needed for keytool or other utilities.<br/>`boot` node only   |

*NOTE:* java will be openjdk7 or openjdk8 for ppc and s390x, and will not provide a JIT. This might be perceived as a performance issue, and can be resolved by switching to the IBM JDK & JRE.
