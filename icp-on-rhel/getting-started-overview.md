# Getting started overview

This section provides a big picture summary of the installation process.

* An IBM Cloud Private (ICP) installation is usually made up of multiple virtual machines that are collectively referred to as a cluster.  (This document may also refer to the collection of machines as a cloud or an ICP instance.) Individual machines are referred to as nodes.  An ICP installation includes machines with a special role as itemized here:
  * Boot - the machine used to orchestrate the ICP installation and used for post-installation administration
  * Master - The nodes that control the cluster.
  * Management - The nodes used for utilization and log monitoring of the machines and components running in the cluster.
  * Vulnerability Advisor (VA) - The nodes used for doing security scans on the Docker images and containers running in the cluster
  * Proxy - Machine used for request routing
  * Worker - The nodes that run the application workloads.


* The ICP v2.1.0.3 Knowledge Center section [Supported operating systems and platforms](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0/supported_system_config/supported_os.html), has a list of supported operating systems.  ICP is supported on RHEL 7. ICP is not supported on RHEL 6.

* System requirements: The ICP v2.1 Knowledge Center section [Hardware Requirements and Recommendations](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0/supported_system_config/hardware_reqs.html), has a table describing the system requirements for each of the types of nodes in an ICP instance. The installation described in this document is a "multi-node cluster".

* It is a really good idea that all machines used for ICP have access to the RHEL yum repositories (os, optional and extras) in order to install various RHEL packages that are pre-requisites for ICP.  Many data centers have a Red Hat Satellite server available. (A public Centos yum repository is available at http://mirror.centos.org/.)

* It is recommended that static IP addresses be allocated for all VMs that will be associated with the ICP cluster or supporting systems, e.g., GlusterFS servers, LDAP server.  If DHCP is providing the IP addresses, the address reservation policy should protect against a given VM inadvertently getting a new IP address if it has to be power booted. A sandbox ICP deployment can get away with using DHCP assigned IP addresses, but a production ICP deployment should use statically assigned IP addresses.  

* It is a really good idea for the `boot` node to have access to the public Internet.  Docker Hub is convenient for access to commonly available Docker images. It is convenient to have access to public sources in Git Hub and other repositories.

* The details of an "air-gap" install are not covered in this document.  Needless to say, doing an air-gap installation is more challenging due to the inconvenience of pulling together all of the RPMs and other artifacts needed to do an installation.  An air-gap install will take at least an extra day, more likely 2 days, to do the installation.

## The simple, "sandbox" ICP installation in a nutshell:
See the ICP Knowledge Center section, [Installing an IBM Cloud Private Cloud Native environment](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/installing/install_containers.html)

1. Customize RHEL for Docker and ICP.
2. Install Docker on the boot-master.
3. Set up RSA based ssh login from the Boot-Master to all nodes in the cluster.
4. Run the ICP inception installer on the boot-master.

Suggested ICP "sandbox" deployment resource allocations are described in [ICP System Requirements](icp-system-requirements.md)

## A production ICP installation in a nutshell:
See the ICP Knowledge Center section, [Installing an IBM Cloud Private Cloud Native environment](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/installing/install_containers.html)

Suggested ICP production deployment resource allocations are described in [ICP System Requirements](icp-system-requirements.md)

1. Customize RHEL for Docker and ICP.
2. Install Docker on the boot node and all cluster nodes.
3. Set up RSA based ssh login from the Boot-Master to all nodes in the cluster.
4. Run the ICP inception installer on the boot-master.
5. Install GlusterFS server on the GlusterFS nodes.
6. Install GlusterFS client on all ICP `master` and `worker` nodes.
7. Install Heketi for storage administration.
8. Configure the shared Docker repository and audit log for the master nodes.
9. Configure LDAP registry from authentication and role based access control.

## Additional steps depending on specific circumstances and requirements

* Configure access to RHEL yum repositories or Red Hat Satellite (RHS).
* Configure `/etc/hosts` files on all cluster members if DNS is not available to resolve host names and IP addresses.
* Update RHEL to the latest patch level.
* Install NTP.
* Install Docker on each cluster member VM in addition to the boot-master VM. (This gives you full control over what version of Docker is installed, but more importantly, Docker on each VM is needed for the next step.)
* Use Docker on each cluster member VM to pre-load the ICP Docker images rather than let the inception installation load the ICP Docker images.  (It turns out to be expedient to copy the ICP image tar-ball to each cluster member VM and then load the local Docker registry from that tar-ball rather than waiting for the inception installer to do that part of the installation.)
* Install `kubectl` on the boot-master node.  `Kubectl` is useful for interacting with the ICP cluster.
* Install the ICP CLI.  (Pre-req for running helm.)
* Install `helm` on the boot or boot-master node.  Helm is useful for installing additional software on the cluster.
* Install Ansible on the boot or boot-master node or, even better, on the administrator's desktop/laptop.  Ansible is very useful for administration when dealing with multiple machines.  See the [Getting Started with Ansible](getting-started-with-ansible.md) document for guidance on installing and configuring Ansible.
* Install Python Docker modules on the boot master node to support the convenient use of Docker APIs in Python scripts.
