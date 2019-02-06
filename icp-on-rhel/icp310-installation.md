Install IBM Cloud Private
=========================================================================

This document is focused on the steps for installing IBM Cloud Private v3.1.0.  The prerequisites section describes the assumptions for all that needs to have been done to prepare for the actual installation.

# Prerequisites

*NOTE:* Installing Ansible on the boot node for administrative use is highly recommended but not a requirement of the ICP installation.  Ansible is very useful for doing administration to the cluster nodes.  You can configure any number of groups in the `/etc/ansible/hosts` file or whatever hosts file you choose to use.  Although do not attempt to customize the cluster installer's `hosts` file. Keep that file dedicated to the use of the ICP `inception` installer.

1. A collection of virtual machines (VMs) has been provided for the ICP deployment.  One of the machines is referred to as the `boot` machine, meaning it is the machine that is used to orchestrate the installation.  For complex deployments, e.g., production or near-production deployments, or "air gapped" deployments, we highly recommend the `boot` machine be a dedicated VM and not a member of the cluster.  When it is critical to minimize deployment resources the `boot` node may also to be a `master` node of the cluster.  This node may also be referred to as the `boot-master` node.  The other machines will be assigned the roles of `management`, `vulnerability advisor` (VA), `proxy` and `worker`.

1. DNS or the `/etc/hosts` file on each VM should be configured with the proper entries so that each VM can resolve the address of the other members of the cluster.

1. SSH needs to be set up such that the `boot` VM can `ssh` as root to each of the other VMs in the cluster (including itself) without using a password.

1. Ansible is installed on the `boot` machine.  The `/etc/ansible/hosts` file has been configured to include the machines in your cluster.  A machine group named `icp` is defined in the Ansible hosts file that includes all the members of the cluster.  (If the boot node is a dedicated VM, then do not include it in the `icp` group.)  To check that Ansible is configured properly use: `ansible icp -m ping`.  You should see a response from each member of the cluster.

1. The ICP install archive (tar ball) and the Docker install executable (bin) should be available on the boot-master machine. Typically these artifacts copied to folders in a `/tmp` directory, e.g., `/tmp/icp` and `/tmp/docker` respectively. Typically, you would have downloaded the product archives from Passport Advantage (IBM external) or eXtreme Leverage (IBM internal).  You can find the GA releases by searching on, *IBM Cloud Private*.

1. The ICP Knowledge Center (KC) installation instructions for ICP Cloud Private "Cloud Native" are rooted in the section: [Installing ICP Cloud Private either Cloud Native or Enterprise](https://www.ibm.com/support/knowledgecenter/SSBS6K_3.1.0/installing/install_containers.html). (Cloud Native and Enterprise editions differ only in that Enterprise comes with more IBM middleware software entitlements.)

1. On all VMs in the ICP cluster, if `firewalld` is running, stop it and disable it until after the ICP install completes.  (Assuming you have ansible installed on the boot node, use the ansible playbook to stop and disable the firewall on each VM.)

*NOTE:* The firewall only needs to be disabled during install.  It gets enabled again on all members of the cluster after the install has completed.  

*NOTE:* The installation may be configured to install with firewalls enabled, but that is not recommended.

*NOTE* In a scenario where an ICP cluster VMs (members) on more than one network segment/VLAN, then there may be physical firewalls that need to be configured to allow the ICP installation to proceed. See the ICP Knowledge Center section, [Default ports](https://www.ibm.com/support/knowledgecenter/SSBS6K_3.1.0/supported_system_config/required_ports.html).

## Some additional boot node pre-installation steps

This section has some steps that need to be taken on the `boot-master` before the actual installation command can be run.

*NOTE:* In these instructions, the root directory of the installation is referred to as `<ICP_HOME>`.  A common convention is to install ICP in a directory path that includes the ICP version, e.g., `/opt/icp/3.1.0/`. Or alternatively the version is included in one of the directory names, e.g., `/opt/icp310/`.

- It is assumed that Docker is installed and running on the `boot` machine.
- It is assumed that the ICP images archive has been loaded into the Docker registry on the `boot` machine.

**NOTE: The actual archive file name may be different depending on the version of ICP and the platform architecture.**
```
tar -xf ibm-cloud-private-x86_64-3.1.0.tar.gz -O | docker load
```
- (On the `boot` node) Extract the ICP boot meta-data to the `<ICP_HOME>/cluster` directory:
```
> cd <ICP_HOME>
> docker run -v $(pwd):/data -e LICENSE=accept ibmcom/icp-inception-amd64:3.1.0-ee cp -r cluster /data  
```
*NOTE:* You may need to using a different version tag for the `icp-inception` image. Use `docker images | grep icp-inception` to see the version tag in your image repository.

The above command creates a directory named `cluster` in `<ICP_HOME>`.  The `cluster` directory has the following contents:
```
> ls -l cluster
  -rw-r--r--. 1 root root 3998 Oct 30 06:37 config.yaml
  -rw-r--r--. 1 root root   88 Oct 30 06:37 hosts
  drwxr-xr-x. 4 root root   39 Oct 30 06:37 misc
  -r--------. 1 root root    1 Oct 30 06:37 ssh_key
```
- Add the IP address of all the cluster members to the `hosts` file in `<ICP_HOME>/cluster`.

    *NOTE:* The ICP hosts file must use IP addresses.  Host names are not used.  

- Copy the ssh key file to the <ICP_HOME>/cluster. (This overwrites the empty ssh_key file already there.)
```
> cp ~/.ssh/id_rsa ssh_key
cp: overwrite ‘ssh_key’? y
```

- Check the permissions on the ssh_key file and make sure they are read-only for the owner (root). If necessary, change the permissions on the ssh_key file in `<ICP_HOME>/cluster` to "read-only" by owner, i.e., root.

- Check the access:
```
> ls -l ssh_key
  -r--------. 1 root root 1675 Jun 30 13:46 ssh_key
```

- If the access is not read-only by owner, then change it:
```
> chmod 400 ssh_key
```

- Check again to make sure you changed it correctly.

- Copy/move the "image" archive (`ibm-cloud-private-x86_64-3.1.0.tar.gz`) to the `images` directory in `<ICP_HOME>/cluster`. (You first need to create the images directory.) In the command below it is assumed the image archive is located initially in `<ICP_HOME>`.

From `<ICP_HOME>/cluster`:
```
> mkdir images
> mv `<ICP_HOME>/ibm-cloud-private-x86_64-3.1.0.tar.gz` images
```

Working with the `config.yaml` file is described in the next section.

## Configuring `config.yaml` on the boot-master

For information on the content of `config.yaml`, see the ICP KC section, [Customizing the cluster with the config.yaml file](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_3.1.0/installing/config_yaml.html).

For a simple sandbox deployment, the content of `config.yaml` can remain as is.

*NOTE:* The network_cidr and service_cluster_ip_range are set to "10." IP networks.  If your infrastructure provider is using that same address range, then change the values to something else, e.g., some other "10." subnet or the "172.16." networks.

For help with figuring out network address ranges search the Internet for a `subnet calculator`.  [Subnet Calculator](http://www.subnet-calculator.com/subnet.php?net_class=B)

Things that can be left as-is for a small sandbox environment:

- network_type calico
- network_cidr: 10.1.0.0/16
- service_cluster_ip_range: 10.0.0.1/24
- For a simple cluster, everything else in `config.yaml` remains commented out.  

There are many parameters that may be set in `config.yaml`.  It is a good idea to read through the file to become familiar with the options.

For a more in-depth description of the important `config.yaml` attributes see [ICP config.yaml content](icp-310-config-yaml-details.md).

A quick list of `config.yaml` attributes that need more serious consideration for a near-production or production deployment:

- cluster_name
- network_cidr
- service_cluster_ip_range
- vip_iface, cluster_vip - when deploying multiple master nodes for HA
- proxy_vip_iface, proxy_vip - when deploying multiple proxy nodes for HA
- cluster_lb_address - if you have a master node load balancer
- proxy_lb_address - if you have a proxy node load balancer
- cluser_CA_domain
- default_admin_user - Be sure this is not going to conflict with a user name in the LDAP that will be configured.
- default_admin_password

*NOTE:* Do not change the value of the `cluster_domain` attribute. A defect in the ICP 3.1.0 deployment of MongoDB requires that the `cluster_domain` be `cluster.local`.

You may want to include a `version` attribute in `config.yaml`.  If you do, be sure it matches the version of the images in the docker registry that you want to use.  You can do a `docker images` list to check the version tags of the available images.  The version that will be deployed is set to an appropriate default in a YAML file in the `icp-inception` container. Setting the `version` value in `config.yaml` is intended for cases where the docker registry being used contains images from more than one version.  This is not likely in the case of a fresh install, but is likely when doing an upgrade on an existing deployment.

Likewise, you may want to include a `backup_version` attribute value in the `config.yaml`.  Again, make sure the value of `backup_version` makes sense for the docker registry in use in that it matches the tag on the images that are intended to be the backup version.  Setting the `backup_version` is relevant when doing an upgrade to an existing deployment.

*NOTE:* For "separation of concerns" reasons, we do not recommend including support for shared storage file systems as part of the ICP deployment.  ICP and a shared storage provider very likely have different life cycles and different resource and administrative concerns that are best kept separated. Hence, any shared storage provider configuration in the `config.yaml` can be ignored. For example all of the GlusterFS configuration in `config.yml` can be ignored when the GlusterFS servers are set up outside the ICP cluster.

## Other things that you may need to check

This section has a collection of items that have led to a failure in the installation process. This is a work in progress and is a place to keep track of this sort of stuff that seems a bit random.

- Make sure all the VMs in the cluster/cloud are running.  

You may want to double check the following on each VM that is a member of the cluster:
- The network interface on each VM is started.
- The firewall on each VM is disabled.
- If you pre-installed Docker on each VM, then check that Docker is running on each VM.
- Docker must be installed and running on the `boot` VM.
- The ICP docker images must be loaded into the Docker registry on the `boot` VM.  

## Run the ICP install command

Docker is used to run the install for all members of the cluster.  Run the install from `<ICP_HOME>/cluster` directory.

*NOTE:* It is assumed Docker is installed on the boot VM.

*NOTE:* It is assumed the ICP (tar ball) images have been loaded into the local docker registry on the `boot-master` VM.

*NOTE:* In the docker commands below, `$(pwd)` is the current working directory of the shell where the command is run, i.e. `<ICP_HOME>/cluster`.  It is assumed there are no space characters in the current working directory path.  (It is a really bad idea to use space characters in directory and file names.)  If you happen to have space characters in the current working directory path, then surround the `$(pwd)` with double quotes.

*NOTE:* It is OK to run this command multiple times to get things installed on all members of the cluster should problems show up with a particular cluster member.  At least for basic problems, the error messages are very clear about where the problems are, e.g., network connectivity, firewall issues, docker not running.

*NOTE:* As of ICP 3.1.0, an uninstall usually is not required after a failed installation.  If you end up interrupting an installation with Ctrl-C or some other "kill" mechanism, then an uninstall may be needed.

*NOTE:* As of ICP 3.1.0, all information messages are captured in a log file in the `<ICP_HOME>/cluster/logs` directory.  A log file is created for each install and uninstall (if you execute an uninstall).  Each log file gets a time stamp in its name.  During the installation the log messages appear on stdout in your terminal session.  You can also use `tail -f` on the current log file to monitor progress.

```
> cd <ICP_HOME>/cluster
> docker run --net=host -t -e LICENSE=accept -v $(pwd):/installer/cluster ibmcom/icp-inception-amd64:3.1.0-ee install -v
```

NOTE: A single `-v` option is recommended to include a useful amount of trace information in the log.  If you need to get more detail for installation problem determination purposes add a `-vv` or `-vvv` to the command line after the install verb for progressively more information, e.g.,
```
> docker run -e LICENSE=accept --net=host --rm -t -v $(pwd):/installer/cluster ibmcom/icp-inception-amd64:3.1.0-ee install -vvv
```

- When the install completes, you want to see all "ok" and no "failed" in the recap. (The play recap sample below is from a sandbox deployment.  A production cluster will obviously have a lot more machines listed.)
```
PLAY RECAP *********************************************************************
xxx.xx.xxx.50              : ok=109  changed=36   unreachable=0    failed=0   
xxx.xx.xxx.52              : ok=109  changed=36   unreachable=0    failed=0   
xxx.xx.xxx.57              : ok=137  changed=36   unreachable=0    failed=0   
xxx.xx.xxx.60              : ok=163  changed=55   unreachable=0    failed=0   
localhost                  : ok=216  changed=114  unreachable=0    failed=0   
```

- Problem determination is based on the installation log.  The error messages are relatively clear. If the recap contains a non-zero failed count for any of the cluster members or something is unreachable, then grep/search the install log for `FAIL` or `fatal` to begin the problem determination process.

-	Assuming the install went correctly move on to some basic "smoke tests" described in the section below.

- If the installation failed, check the log for the cause of the failure, take corrective action and run the install command again.

## Start and enable the firewalld on all cluster members

You may want to hold off on this step until some basic smoke tests have been executed.  See the [Simple ICP smoke tests](#Simple ICP "smoke" tests) section below.

# Simple ICP "smoke" tests

This section documents some basic measures to confirm correct ICP operation.

1.	The simplest "smoke test" is to fire up the ICP admin console:
```
https://<boot_master>:8443/
```
Default user ID and password: admin/admin

2.	Check that all processes are "available".  In the ICP admin console you can see the workloads via the "hamburger" menu in the upper left corner margin.

# Uninstalling ICP

As of ICP 3.1.0, it is rarely necessary to run and uninstall after a failed installation attempt.  However, if you have some evidence that something from a previous install attempt may be a factor in successive installation failures, then doing an uninstall gets you back to a "clean" state.

*NOTE:* An uninstall does not undo the pre-installation steps, e.g., you do not have to reload the ICP image tar ball on the boot node.

```
> docker run -e LICENSE=accept --net=host --rm -t -v $(pwd):/installer/cluster ibmcom/icp-inception-amd64:3.1.0-ee uninstall -v
```
- A separate log is kept for the uninstall.
