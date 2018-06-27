# Yum repository configuration

It is a really good idea that all machines used for ICP have access to the RHEL yum repositories (`os`, `optional` and `extras` or `epel`) in order to install various RHEL packages that are pre-requisites for ICP.

This document is intended to provide guidance for those who need to configure a yum repository.

*NOTE:* A RHEL virtual machine provided for you will very likely already have a yum repository configured, most likely using a Red Hat Satellite (RHS) server.  

*NOTE:* You may need to provide a userid and password as part of the yum repository URL. If you are using an ID with an @ character in it, e.g., an Internet email address, use %40 in place of the @ character.  Otherwise the repository URL is misinterpreted because an @ character marks the beginning of the host name in the URL.

You need to set up the repos for yum to be able to install additional packages and get OS updates.

The yum repo definition files are in `/etc/yum.repos.d/`. Any file in that directory with a `.repo` extension will be treated as a repo definition.

Each file may have multiple repositories defined.

Each repo definition typically has at least 5 attributes:
```
[rhel-os]
name=Red Hat Enterprise Linux at my site
enabled=1
gpgcheck=0
baseurl=<protocol>://<userid>:<password>@<repo_host>/<repo_path>
```

The `<protocol>` could be ftp or http(s) for remote repos, or file for a local repo.

If the repository requires a `<userid>` and `<password>`, that is included in the URL as shown.

See the Red Hat documentation [Configuring Yum and Yum Repositories](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/sec-configuring_yum_and_yum_repositories) for more details.

The `<repo_path>` needs to point to a directory with a `repodata` sub-directory where a file named `repomd.xml` is found.  If you need to explore a repository to determine the <repo_path>, something like Filezilla is very handy to use for exploration.  You can also confirm your user ID and password in getting to the repo.  (See figure below.)

![Sample Yum Repository Directory Structure](images/YumRepoDirectoryStructure.png)

In the figure above the `<repo_path>` text would be:  `/redhat/rhs6/server/7/7Server/x86_64/extras/os/`

You may need to explore a given collection of yum repositories in order to figure out where various packages are located.  Packages are typically spread across multiple directories such as "os", "optional" and "extras".

Depending on how DNS is configured, you may need to add an entry in the `/etc/hosts` file for the `<repo_host>`.

Once you have configured the yum repository you can do a quick test to confirm the configuration file is correct:
```
> yum repolist
```
Yum caches its repository information as a performance enhancement. If you want to "clean" the cache to make sure you are not using stale information about yum repositories, use:
```
> yum clean all
```
Once you have the desired yum repositories configured, you can proceed with any RHEL configuration that requires additional packages (rpms) to be installed.

At some point while using yum, you may see "Given file does not exist" errors such as:
```
rhel-optional/updateinfo       FAILED                                          
ftp://<userid>:<password>@<repo_host>:/redhat/rhs6/server/7/7Server/x86_64/optional/os/repodata/<uuid1>-updateinfo.xml.gz: [Errno 14] FTP Error 550 - Given file does not exist
Trying other mirror.
rhel-optional/primary          FAILED                                          
ftp://<userid>:<password>@<repo_host>:/redhat/rhs6/server/7/7Server/x86_64/optional/os/repodata/<uuid2>-primary.xml.gz: [Errno 14] FTP Error 550 - Given file does not exist
Trying other mirror.
ftp://<userid>:<password>@<repo_host>:/redhat/rhs6/server/7/7Server/x86_64/optional/os/repodata/<uuid2>-primary.xml.gz: [Errno 14] FTP Error 550 - Given file does not exist
Trying other mirror.
ftp://<userid>:<password>@<repo_host>:/redhat/rhs6/server/7/7Server/x86_64/optional/os/repodata/<uuid2>-primary.xml.gz: [Errno 14] FTP Error 550 - Given file does not exist
```
If you inspect the yum repository, you will notice that the `<uuid1>-updateinfo.xml.gz` and `<uuid2>-primary.xml.gz` files have a new UUID.

A `yum clean all` will likely clean up such errors.
