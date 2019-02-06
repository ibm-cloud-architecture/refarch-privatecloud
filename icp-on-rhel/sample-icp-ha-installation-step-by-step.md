# Sample ICP HA installation step-by-step

This document is a rough description of the steps to do an HA installation of IBM Cloud Private.  The details of each step are described in other documents in this collection or the references, such as the ICP Knowledge Center or Red Hat documentation.

The intent of this document is to provide an uncluttered, "straight line" view of the installation process.

- Create the VMs
  - Allocate the disk to the file systems
  - (Optional) A separate disk for Docker is optional.
  - Admin nodes of type Master, Management and Vulnerability Advisor can be clones of the same initial VM.  
  - Worker nodes and proxy nodes have lower resource requirements and may be cloned from a VM with fewer resources than the admin nodes.
- Configure network on each VM with static IP (probably already done)
- Set the hostname (probably already done)
- Configure DNS with cluster host names or create `/etc/hosts` on `boot` and copy to all nodes.
- Configure passwordless SSH for root from `boot` to all nodes, including `boot` (assuming a root install) (See [Configure passwordless SSH](configure-passwordless-ssh.md))
  - For non-root install, the user must have "no password" sudoer privileges to all commands.)
- Make sure Python 2.7.x is installed on all machines (including the boot node).
- Make sure `socat` is installed on all machines (other than the boot node). Calico uses `socat`. (`yum list installed | grep socat`)
- Install Ansible on the `boot` (See [Getting Started with Ansible](getting-started-with-ansible.md))
- (optional) Configure a non-root Ansible user for all nodes
  - The Ansible user needs passwordless sudo on all nodes including boot-master.
  - Configure passwordless SSH for the non-root Ansible user including the `boot` node.
  - Configuring a non-root Ansible user is commonly required due to restrictions on who has root.
- Configure yum repos or RHS for all cluster nodes. (RHS is preferred as the repositories are more likely to be complete and up-to-date.)
- Update to latest RHEL RPMs (e.g., 7.5) Reboot all nodes to pick up kernel updates.
- Install NTP on all nodes (probably already done or time is managed by the hypervisor)
  - Start and enable ntpd service (probably already done or not necessary because time is managed by the hypervisor)
- Set `vm.max_map_count` on all nodes (playbook available) (See [set-vm-max-mapcount.yaml](playbooks/icp-preinstall/set-mv-max-mapcount.yaml))
- Install Docker on all nodes (playbook available) (See [install-docker-rhel.yaml](playbooks/icp-preinstall/install-docker-rhel.yaml))
  - Use the Docker install binary that comes with ICP.  It is the version of Docker that has been tested with the given release of ICP and is supported by IBM.
- Install and configured shared storage, e.g, NFS, GlusterFS, Ceph.
  - If doing an HA deployment where there are 3 or more Master nodes, the shared storage provider needs to be installed and configured.  
  - An HA ICP installation will fail if shared storage is not configured for the Master nodes.
- Install ICP
  - Load docker images from ICP install tar ball on the boot node.
  - Get the initial ICP install artifacts from the `inception` container.
  - Configure ICP `hosts` file
  - Copy root `ssh` `id_rsa` to `ssh_key`;
  - Edit `config.yaml`.  See [ICP config.yaml content](icp310-config-yaml-details.md)
  - Stop, disable `firewalld` on all nodes. (playbook available)
  - Move ICP install tar ball to images directory in <ICP_HOME>/cluster
  - Kick off the ICP install process using the `inception` container.
  - If a given install attempt fails, check logs to determine cause and correct. Install again.  (As of ICP 3.1.0, the installation is more-or-less idempotent.  We have seen cases where an uninstall is needed after a failed installation, particularly if the installation was killed.  If the installation failed "gracefully" then it is very unlikely an uninstall is necessary.)
  - Once the ICP install succeeds, perform simple ICP smoke tests to confirm installation.  (The first test is to log into the ICP console and check the status of all the deployments.)
  - Start, enable `firewalld` on all nodes. (playbook available)
- Install `kubectl` on the boot node.  (As of ICP 3.1.0 the master nodes get `kubectl` installed as part of the inception install.)
- Install ICP CLI (`cloudctl`) on the boot node and (optionally) all master nodes.
  - See [Installing the IBM Cloud Private CLI](https://www.ibm.com/support/knowledgecenter/SSBS6K_3.1.0/manage_cluster/install_cli.html)
- Install Helm CLI on the boot node and (optionally) all master nodes.
  - See [Setting up Helm CLI](https://www.ibm.com/support/knowledgecenter/SSBS6K_3.1.0/app_center/create_helm_cli.html)
