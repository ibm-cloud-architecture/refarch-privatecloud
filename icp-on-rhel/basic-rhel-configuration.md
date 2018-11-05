# Basic RHEL configuration

The sub-sections in this section describe some basic RHEL configuration required to support ICP cluster members.  We are calling this "basic" configuration because it is typical that a RHEL VM will be configured as described in these sub-sections.

If you are creating your own virtual machine, you can do all these steps on your initial VM before cloning it.

If you are using VMs that were deployed for you, then it is likely the VMs are already configured as described in these sub-sections.  You should confirm with your VM provider or by doing the basic checks described below, that all the VMs that are going to be part of the ICP cluster have been configured as described in these sub-sections.

## Configure network interface

*NOTE:* This section describes steps you won't need to do for a virtual machine deployed for you in a typical virtualization platform.  If you are building your own VM, you will likely need to complete these steps.

*NOTE:* People familiar with configuring the network interface on Ubuntu will see that the concepts are the same, but the details are different.  In particular, some of the files that contain the configuration are different and the syntax, names and values of the configuration parameters are different.

Ideally, ICP VMs should use a static IP address, particularly the master and proxy nodes.  A static IP address ensures that a VM does not get a new IP address when it is restarted using a power down and power up.  With DHCP assigned IP addresses there may be a possibility that a VM will get a new address when it is powered down.  DHCP lease times are intended to avoid unintended changes in an IP address assigned to a given VM, but you can't count on it.

When configuring static IP addresses you need to collect the following information:
- IP address to use for the VM.
- Prefix or Netmask (Prefix is preferred.)
- The gateway server address
- DNS server addresses (usually at least 2)
- DNS search domain

*NOTE:* The BROADCAST and NETWORK attributes are unnecessary for RHEL 7.

Various sources of information on static IP address configuration for RHEL:
- See [Editing Network Configuration Files](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/networking_guide/sec-editing_network_configuration_files)
- See [Linux Network Configuration](http://www.yolinux.com/TUTORIALS/LinuxTutorialNetworking.html#ASSIGNIP)
- See [How to configure static IP address on CentOS 7/RHEL 7](https://www.cyberciti.biz/faq/howto-setting-rhel7-centos-7-static-ip-configuration/)
- See [How to configure Static IP Addresses in CentOS 7/RHEL 7/Fedora 27/26](https://www.itzgeek.com/how-tos/linux/centos-how-tos/how-to-configure-static-ip-address-in-centos-7-rhel-7-fedora-26.html)

The options for network configuration are all defined in `sysconfig.txt`.  Use `find / -name sysconfig.txt` to find where it is located on your machine.

To find out the names of the network interfaces on a machine you can use the `ip addr` command.  The name of each network interface is in the first column. (The `ifconfig -a` command may also be used, however `ip addr` is recommended.)

The network interface configuration files are in `/etc/sysconfig/network-scripts/`.  The file names include the name of the network interface as seen in the `ifconfig` command output.

- Edit the file in `/etc/sysconfig/network-scripts` associated with the network interface to be started at boot time, e.g., `/etc/sysconfig/network-scripts/ifcfg-ens192`.  (See example content below.)

- The value of `ONBOOT` should be  `yes`.
- For static IP address on RHEL:
  - `BOOTPROTO` value should be `none`.  (The value `static` is not a valid option as of RHEL 6.)
  - Be sure to include attributes for:
    - IPADDR
    - PREFIX
    - GATEWAY
    - DNS servers (DNS1, DNS2)
    - DOMAIN

```
NAME="ens192"
DEVICE="ens192"
ONBOOT=yes
NETBOOT=yes
UUID="1a89d56d-935e-49f9-81de-4287291b7708"
IPV6INIT=yes
BOOTPROTO=none
TYPE=Ethernet
# Linux on System Z also requires the following:
SUBCHANNELS=0.0.xxxx,0.0.yyyy,0.0.zzzz
NETTYPE=qeth
OPTIONS=layer2=1
# xxxx, yyyy, zzzz are the device addresses of the OSA ethernet adapter or VSWITCH NIC
# end of Linux on System Z specific parameters

# IPv4 network configuration
IPADDR=xxx.xxx.xxx.xxx
# PREFIX=16 equivalent NETMASK=255.255.0.0
PREFIX=16
GATEWAY xxx.xxx.xxx.xxx

# DNS servers
# By default the DNS servers get copied to /etc/resolv.conf
DNS1=xxx.xxx.xxx.xxx
DNS2=xxx.xxx.xxx.xxx

# Default domain search
DOMAIN=somedomain.whatever
```

- Save the changes.

- Test by restarting the network service:
```
systemctl restart network
```

*NOTE:* If you are setting the static IP address to something different from what the VM is currently using, then you will lose your ssh connection to the machine.  Reconnect using the new network address.

When the network service comes back up the network interface should be UP/RUNNING. The `ip addr` command includes the status of each interface.  You should see the static address assigned to the interface that has been configured.

Another test is to reboot the VM and see that it comes up correctly.
```
shutdown -r now
```

## Configure the host name
This section describes the configuration of the host name for RHEL 7 VMs.

If you are cloning VMs, then you will need to change the host name on the cloned VM.

*NOTE:* This step is unnecessary and is **not advisable** in scenarios where the VMs were provided to you. Check with your VM provider, system administrator and/or network administrator before changing a host name.

Host name considerations usually involve using naming conventions provided by the network and system administrators.

Be sure to use a fully qualified domain name (FQDN) for the value of the host name.

Some sample "toy" host names: `bootmaster`, `proxy`, `worker01`, etc.  

There are a couple of different places where the host name is specified.

For RHEL 7 the host name can be set using the `hostnamectl` command. For example:
```
hostnamectl set-hostname bootmaster01.site.org.com
```

See the man pages for `hostnamectl` for more information.

Additional notes on host name:
1.	The host name is stored in the `/etc/hostname` file.  (NOTE: This file should only have the text of the host name on a single line with no newline character.)

2.	There may be a HOSTNAME directive in the `/etc/sysconfig/network` file.

3.	A reboot is needed to have the host name change take effect: `shutdown -r now`


## Enable remote login for root via ssh

*NOTE:* For RHEL v7.x, by default root can login via ssh using a password.

The configuration for ssh is in `/etc/ssh/sshd_config`.  You will notice that `PermitRootLogin` is commented out.  However, `UsePAM` is set to yes.  A PAM configuration file for `sshd` is in `/etc/pam.d`. Configuration of the PAM plugin for `sshd` is beyond the scope of this document.

## Configure yum repositories

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

See [Yum repository configuration](yum-repository-configuration.md)

## Update RHEL
This section describes the steps to update RHEL.

*NOTE:* This is an optional step and may not be necessary depending on the virtual machine that has been provided to you.  You may also not be permitted to do a full update, as that may move your RHEL to a version that is not yet supported by your operations team.  For example, if the VM is running RHEL 7.3 a full update will result in RHEL 7.4.

If you are building a VM from scratch, then you should do a full RHEL update to pick up updates since the release of the RHEL image you are using for the initial install.

It is assumed you have configured your VM with yum repositories. See [Yum Repository Configuration](yum-repository-configuration.md)

1. Do a yum update (`yum -y update`) - This gets all the latest patches for everything already installed.

2. Then reboot. (`shutdown -r now`). You need to reboot to get to the latest kernel.

[Additional (optional) Packages to Install](additional-packages.md)


## Configure /etc/hosts

This section describes the steps to add entries to the `/etc/hosts` file of each cluster member for all the hosts in the cluster.

*NOTE:* This section can be skipped if DNS is being used for host name resolution.  You can use `nslookup` on the IP addresses of a sampling of cluster members to determine if there are DNS entries for the cluster member VMs.  If not, then you need to configure `/etc/hosts`.

*NOTE:* The "minimal" RHEL install does not include `bind-utils`, which is the RPM that contains the `nslookup` command.  If you are using a minimal RHEL image, then you need to install `bind-utils` if you want to use `nslookup`.  (`yum -y install bind-utils`)

- For each VM in the cluster, edit `/etc/hosts` and add an entry for each VM in the cluster.

In some circumstances you can edit `/etc/hosts` once on the boot-master and then `scp` the hosts file to the other members of the cluster. This expedient is only feasible if the all VMs in the cluster are freshly deployed VMs and they all have the same content in `/etc/hosts` when they are initially deployed, e.g., the default content.  

## Check the file system sizing

The file system size minimum requirements are described in the ICP v2.1 Knowledge Center section, [Hardware requirements and recommendations](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/supported_system_config/hardware_reqs.html)(See Table 3).

Also see the [IBM Cloud Private System Requirements Notes](icp-system-requirements.md)

*NOTE:* If you are creating your own RHEL VMs, there is a step at the point where the install is being set up where you can customize the disk partitions rather than take the automatic defaults. It is recommended that you choose to customize the disk partitions to ensure the VM meets the ICP file system sizing requirements. The RHEL 7 documentation for installation that describes the file system configuration is in the section [Installation Destination](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/installation_guide/sect-disk-partitioning-setup-x86) Scroll down to the "Manual Partitioning" section to get to the details that describe the manual partitioning steps.

The RHEL 7 documentation for [Mounting a file system](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/sect-using_the_mount_command-mounting) provides detailed information about the mount command.
