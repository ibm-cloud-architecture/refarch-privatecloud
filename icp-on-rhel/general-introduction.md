# Introduction

This is a guide to creating an IBM Cloud Private (ICP) cluster on RHEL v7.x.  It is intended to enhance the installation instructions available in the [ICP Knowledge Center (KC)](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/kc_welcome_containers.html).

The phrase "ICP instance" is used in this document to refer to an installation of ICP.

The term "cluster" is used to mean the VMs that are under the control of a given ICP instance.  At times in this guide the word "cloud" is used to mean the same thing as cluster.

This instruction guide assumes the VMs to be used for the ICP instance are provided to you by some providing entity.

Root access, either directly or through sudo, must be available to the person doing the ICP installation for all of the ICP machines (VMs) that will be members of the ICP cluster.  If sudo is used, it is recommended that passwordless sudo is configured.  Otherwise, the cluster configuration file (config.yml) will need the sudoer's password specified.  An ICP installation as non-root is beyond the scope of this document.

IBM Cloud Private is built on Docker and Kubernetes.  

IBM Cloud Private Cloud Foundry (ICP-CF) is packaged as part of the IBM Cloud Private product.  However, ICP-CF has a completely separate installation process. In addition ICP-CF is a completely separate run-time environment that has no direct integration points or any dependencies on ICP itself. The installation and deployment of IBM Cloud Private Cloud Foundry is outside the scope of this guide.  

IBM Cloud Private has certain components (the `master` and `proxy` nodes, for example) that may be deployed as singletons in a simple, "sandbox" installation.  A production installation should include three (3) or five (5) `master` nodes and 2 or more `proxy` nodes.  A simple installation of ICP will combine the `boot`, `master` and `management` components into a single node.  A production installation will separate the `management` nodes from the `master` nodes to provide sufficient resources to each and avoid resource contention.  A simple ICP installation may use a singleton NFS server to provide a shared, persistent storage service to all of the `worker` nodes.  A production ICP installation will use something more sophisticated such as GlusterFS or IBM Spectrum Storage for persistent storage.

| Deployment | Sandbox Instance      | Production Instance                                    |
|------------|-----------------------|--------------------------------------------------------|
|  Boot      | Combined w/ Master    | Dedicated boot node recommended;<br/>Can be combined with Master01  |
|  Master    | 1                     | 3 or 5 (odd number required to support etcd quorum voting ) |
|  Proxy     | 1                     |  2 or 3                                                      |
|  Worker    | 1 to 3                | Typically, 5 or more                                   |
|  Management| 1 or combined w/Master| 2 or 3                                                 |
|  Vulnerability Advisor (VA)   | Usually deemed not needed  | 3 (odd number needed to support zookeeper quorum voting )  |
|  File Store| Singleton NFS server | GlusterFS (independent server cluster of 3 nodes)      |

*NOTE:* It is required for IBM Support of Docker on RHEL, that the Docker version provided with the ICP downloads at Passport Advantage be used for ICP.  The Docker provided along with ICP has been fully tested with all of the ICP components.

*NOTE:* In this document the standard root prompt `#` for sample shell commands is replaced with `>` to avoid having random sample commands show up in the Atom editor's markdown section navigation pane.  There are some file snippets where comment lines start with `#` that do continue to show up in the section navigation pane.
