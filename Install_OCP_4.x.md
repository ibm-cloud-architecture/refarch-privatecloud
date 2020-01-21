# User Provisioned Installation of Red Hat OpenShift 4.x on VMware Virtual Infrastructure

## Introduction
Installing OpenShift (OCP) 4.x requires a significant amount of pre-planning and infrastructure preparation.

In this guide we will install a small OpenShift 4.2 instance.  We will use an installation server with an embedded web server.  Our cluster will consist of a bootstrap node, 3 master nodes, 3 worker nodes, 2 load balancers.  The installation server and bootstrap server can be deleted when the installation is complete, however you may want to keep the installation server around for future installs.

This document will contain information for installing in a VMware vSphere environment as well as in a "bare metal" environment.  The reason "bare metal" is in quote is that this installation method will work with any hypervisor/cloud provider.

OCP has specific installers for a number of cloud providers (AWS, Google, IBM Cloud, Azure) known as Installer Provisioned Infrastructure (or IPI) and a separate mechanism for using User Provisioned Infrastructure (UPI).

For UPI, Red Had provides an installer for VMware environments which use vCenter Server and also for bare metal.  If you have any other hypervisor in your on-prem environment than VMware (e.g. KVM or Nutanix) you can use the bare metal installer even though the platform is not technically bare metal.  You will do the installation as though it were bare metal.  You can also use this installer if you want to do an actual bare metal install. :-)

This document will *not* describe doing an IPI installation, but you can still use the bare metal installation method in those environments if you so desire.

Many of the steps to install OCP 4x in a UPI environment are common regardless of your hypervisor or bare metal infrastructure. To make the document more readable, there are collapsible sections for details of the specific environment you are trying to use, VMware or Bare Metal.  Open the expand the appropriate sections for the type of environment you are deploying.

## Terminology
* __Host__ - A physical machine with a hypervisor installed which can be used to host one or more virtual machines.
* __Server__ - A physical or virtual machine that is used to provide services to other machines.
* __Workstation__ - A physical or virtual machine that is typically used by a single person as a desktop on which work can be done.  This is typically a laptop, desktop, or virtual machine provided by some technology such as Citrix.
* __VM__ - A Virtual Machine which can be provisioned as a server or workstation and runs as a "guest" on a "host" machine.
* __Guest__ - Another name for a Virtual Machine.
* __Node__ - A specialized physical or virtual machine dedicated to a specific function.  For example, a "node" could be a Storage Node, Compute Node, Master Node, Worker node, Infrastructure Node, etc.

Installation in a UPI environment includes the following basic steps:

In this guide we will use the following topology:

* Installation server (with webserver installed)
* 1 load balancer for the control control plane (master nodes)
* 1 load balancer for the compute nodes (worker nodes)
* 1 Bootstrap node
* 3 control plane nodes (master nodes)
* 3 compute nodes (worker nodes)

<details>
<summary>Basic Install Steps for VMware</summary>

  1. Create an installation node (running RHEL 7 or 8) an with embedded web server (or reuse an existing server that you have used for a previous install - you can install multiple clusters with a single install server).
  1. Download and deploy the rhcos template onto your vcenter server.
  1. Download and explode the openshift installer onto your installation server.
  1. Create the needed install-config.yaml file on your installation server.
  1. Create the needed ignition files for your deployment
  1. Deploy, but don't boot the bootstrap, control plane, and compute nodes.
  1. Configure the DHCP server.
  1. Configure DNS to support your cluster
  1. Create or configure a load balancer for the control plane
  1. Create or configure a load balancer for the compute nodes.
  1. Complete the bootstrap process
  1. Configure persistent storage for your image registry
  1. Complete installation
  1. Login to your new cluster and configure authentication
</details>

<details>
<summary>Basic Install Steps for Bare Metal</summary>

  1. Create an installation node (running RHEL 7 or 8) an with embedded web server (or reuse an existing server that you have used for a previous install - you can install multiple clusters with a single install server).
  1. Download and deploy the .img and metal config files from Red Hat.
  1. Download and explode the openshift installer onto your installation server.
  1. Create the needed install-config.yaml file on your installation server.
  1. Create the needed ignition files for your deployment
  1. Configure the DHCP server
  1. Configure the PXE server.
  1. Configure DNS to support your cluster
  1. Create or configure a load balancer for the control plane
  1. Create or configure a load balancer for the compute nodes.
  1. Complete the bootstrap process
  1. Configure persistent storage for your image registry
  1. Complete installation
  1. Login to your new cluster and configure authentication
</details>
<br>
We will discuss each of these in turn in the rest of this document.

## Preparation

### Create the Installation Server

1. Create a new virtual machine which is network accessible from the location where your OCP cluster will run.  Only the basic server packages are needed, no UI is needed.  This guide will assume this server is running RHEL 8.0.

1. Either register with subscription manager or create a local yum repository so needed packages can be installed.

1. Disable the firewall and selinux (or open a hole for port 80)

  ```
  # Stop the firewall and set selinux to passive
  systemctl stop firewalld
  setenforce 0

  # make changes persist over a reboot
  systemctl disable firewalld
  sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
  ```

1. Create a directory for your new cluster.  In this document I will use a cluster named after my userid `vhavard`.

  ```
  mkdir /opt/vhavard
  ```

1. Install the httpd web server

  ```
  yum install -y httpd
  ```

  This will create a document root of /var/www/html.  Create a softlink from the document root to your project directory.

  ```
  ln -s /opt/vhavard /var/www/html/vhavard
  ```

1.  Download the openshift client and installer and explode it into your /opt directory.

  ```
  cd /opt
  wget -c https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux-4.2.0.tar.gz
  wget -c https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-install-linux-4.2.0.tar.gz
  ```

  Or, if you are in the IBM Cloud Adoption Lab you can get it from:

  ```
  cd /opt
  wget -c http://storage4.csplab.local/storage/ocp/4.2/openshift-client-linux-4.2.0.tar.gz
  wget -c http://storage4.csplab.local/storage/ocp/4.2/openshift-install-linux-4.2.0.tar.gz
  ```

  Explode the files into /opt
  ```
  cd /opt
  gunzip -c openshift-client-linux-4.2.0.tar.gz |tar -xvf -
  gunzip -c openshift-install-linux-4.2.0.tar.gz |tar -xvf -
  ```

  Now copy the `oc` and `kubectl` binaries into your path
  ```
  sudo cp oc /usr/local/bin/
  sudo cp kubectl /usr/local/bin/
  ```

1. Create an ssh key for your primary user

  ```
  ssh-keygen -t rsa -b 4096 -N ''
  ```

  Accept the default location for the file.

1. Start the ssh agent

  ```
  eval "$(ssh-agent -s )"
  ```

1. Add your private key to the ssh-agent

  ```
  ssh-add ~/.ssh/id_rsa
  ```

1. You will need a pull secret so your cluster can download the needed containers.  Get your pull secret from https://cloud.redhat.com/openshift/install/vsphere/user-provisioned and put it into a file in your /opt directory (e.g. pull-secret.txt).  You will need this in the next step.

1. In your project directory, create a file named `install-config.yaml` with the following contents (_expand the section for your target environment_):

  <b>IMPORTANT:</b> _Replace values in square brackets in the text below (including the square brackets) with values from your environment._

  <details>
  <summary>VMware Environment</summary>

  ```
  apiVersion: v1
  baseDomain: [ocp.csplab.local]
  compute:
  - hyperthreading: Enabled   
    name: worker
    replicas: 0
  controlPlane:
    hyperthreading: Enabled   
    name: master
    replicas: 3
  metadata:
    name: [vhavard]
  platform:
    vsphere:
      vcenter: [demo-vcenter.csplab.local]
      username: username
      password: password
      datacenter: [CSPLAB]
      defaultDatastore: [SANDBOX_TIER4]
  pullSecret: '[contents of pull-secret.txt]'
  sshKey: '[contents of ~/.ssh/id_rsa.pub]'
  ```

  * **baseDomain** - You will access applications in your cluster through a subdomain of this domain which is named after your cluster.  For example, I use my userid (vhavard) as my cluster name, and my base domain is ocp.csplab.local, therefore, my cluster's domain will be vhavard.ocp.csplab.local.

  * **metadata.name** - This is the name of your cluster.

  * **platform.vsphere.vcenter** - This is the hostname or IP address of your vsphere server.

  * **platform.vsphere.userna**me - This is a valid user in vsphere with permissions to deploy vApps and add items to the datastore.

  * **platform.vsphere.password** - The password for the username specified above (this file will be deleted when the installer creates the ignition files).

  * **platform.vsphere.datacenter** - The datacenter under which files should be created.

  * **platform.vsphere.defaultDatastore** - The datastore on which files should be stored.  A storage class will be created on your openshift cluster for dynamic storage provisioning to this datastore.

  * **pullSecret** - The contents of the pull secret you got from the Red Hat URL noted above.

  * **sshKey** - The contents of ~/.ssh/id_rsa.pub
  </details>

  <details>
  <summary>Bare Metal Environment</summary>

  ```
  apiVersion: v1
  baseDomain: [ocp.csplab.local]
  compute:
  - hyperthreading: Enabled
    name: worker
    replicas: 0
  controlPlane:
    hyperthreading: Enabled
    name: master
    replicas: 3
  metadata:
    name: [baremetal]
  networking:
    clusterNetworks:
    - cidr: [10.254.0.0/16]
      hostPrefix: [23]
    networkType: OpenShiftSDN
    serviceNetwork:
    - [172.30.0.0/16]
  platform:
    none: {}
  pullSecret: '[pull-secret]'
  sshKey: '[ssh-key]'
  ```

  * **baseDomain** - You will access applications in your cluster through a subdomain of this domain which is named after your cluster.  For example, I use my userid (vhavard) as my cluster name, and my base domain is ocp.csplab.local, therefore, my cluster's domain will be vhavard.ocp.csplab.local.

  * **metadata.name** - This is the name of your cluster.

  * **networking.clusterNetworks.cidr** - Use a valid network for your environment.  This should not conflict with any existing subnet in your environment.

  * **networking.clusterNetworks.networkPrefix** - This value specifies the size of the network to assign to each node for pod IP addresses.  For example, a /23 prefix represents 512 IP addresses, so a hostPrefix of /23 means that control-plane-1 (master1) will have 512 IP addresses available, as will control-plane-2, compute1, compute2, etc.<br><br>
  If you are using a class B network for the clusterNetwork (a /16 prefix) you have a total of 255^255 usable IP addresses. Since the lowest and highest IP addresses are assigned to the subnet name and broadcast address, respectively they are not assignable leaving 65534 addressable IP addresses in a Class B subnet.<br><br>
  If we are using a class B subnet we have 65535 total IP addresses to use over 6 nodes.  That's 19,922 IP addresses, but subnets must divided along powers of two, so you could set this value to *19* which would allow for 8190 usable IP addresses per node.  If we use 19, however, we would not be able to add any additional nodes because we would not have any addresses available for the new node.<br><br>
  On the other hand, if we are planning to expand the cluster to as many as 100 nodes in the future, we can set this value to 23 which will allow 512 IP addresses per node for up to 100 total nodes (the highest power of 2 which is lower than 65535/100).

  * **networking.serviceNetwork** - The network CIDR to assign for services.  This is not assigned per node as is the clusterNetwork, so there it no separate prefix number.

  * **pullSecret** - The contents of the pull secret you got from the Red Hat URL noted above.

  * **sshKey** - The contents of ~/.ssh/id_rsa.pub
  </details>
  <br>

1. Create your manifest files

  **NOTE:** The file you created in the previous step (install-config.yaml) will be automatically deleted in the next steps.  If you want to keep it for future use, make a backup of it now or you will have to re-create it for each additional cluster you install.

  ```
  cd /opt
  ./openshift-install create manifests --dir=./vhavard
  ```

  Where dir is the name of your cluster - the directory you created in step 3 above.

  This will create a number of .yaml files in a couple of directories which you can use to change the default installation of your cluster.

  Of particular note is the manifests/cluster-config.yaml file where you can change the default networking subnets.  See the `bare metal` section of the install-config.yaml section above (step 11) for information on how to set these values if you need/want to change them.  Note that the subnets in this section must be valid for your environment meaning these subnets must not already exist in your environment, but will not (unless explicitly reconfigured) be routed outside of the cluster.

  You will need to edit manifests/cluster-scheduler-02-config.yml file and change the value of spec.mastersSchedulable to false.

  This will make sure the cluster doesn't try to put your applications on master nodes.  Red Hat assumes that at some point in the future kubernetes will allow this and you may want to leave it true so you can use your control plane nodes as compute nodes as well.

1.  Create your ignition files

  <strong>Note:</strong> The installer will create ignition files from these manifest files and then delete the manifest files.  If you would like to keep a copy of these files, make a backup of them before taking the next step.

  ```
  cd /opt
  ./openshift-install create ignition-configs --dir=./vhavard
  ```

  Where vhavard is the name of your cluster just as in the previous step.

1. Environment-specific configurations

  <strong>STORAGE NOTE:</strong> If you are going to be installing rook/Ceph or Gluster storage you may also want to consider adding additional compute nodes to use as storage nodes.  If using separate storage nodes for Ceph, provision three additional nodes (minimum, but can be more) and name them appropriately (e.g. storage-0, storage-1, storage-2).  These should be provisioned exactly like compute nodes with the exception of the extra disk as noted below.

  Alternatively, you can also just use all compute nodes as storage nodes without designating them separately.  When doing this for Ceph storage you must have a minimum of three.  In this document we will assume there are three separate storage nodes.

  All nodes which will also be used as storage nodes will need a second hard disk provisioned (the installer will only use /dev/sda).  This second hard disk will be /dev/sdb and will be used by Ceph when installing the Ceph storage cluster.  You can also add more than one additional disk to be used by the Ceph storage cluster, but only one is required.

  <details>
  <summary>Configure VMware Environment</summary>

  ###  VMware Installation Specifics

  #### Create the 'append-bootstrap.ign' File

  The bootstrap.ign file is too large to be used when deploying the VMs as documented below so you will need to create a smaller file which will cause the VMware server to grab this file from the webserver you configured on the installation server.  Because we created a softlink for our project folder, the file is already accessible for download.  We just need to create the `append-bootstrap.ign` file for use when we deploy our bootstrap node.

  In your project folder (e.g. /opt/vhavard), create a new file named append-bootstrap.ign with the following contents:

  <strong>IMPORTANT:</strong> _Replace the URL in the square brackets (including the square brackets) with the URL to the bootstarp.ign file on your web server/installation server._

  ```
  {
  "ignition": {
    "config": {
      "append": [
        {
          "source": "[http://172.18.1.30/vhavard/bootstrap.ign]",
          "verification": {}
        }
      ]
    },
    "timeouts": {},
    "version": "2.1.0"
  },
  "networkd": {},
  "passwd": {},
  "storage": {},
  "systemd": {}
  }
  ```

  Where `source` is the URL where the vCenter server can download the bootstrap.ign file (from your locally running web server).

  The ignition files will need to be encoded into base64 strings so they can be placed in a form blank.  In the /opt/<project> directory (e.g. /opt/vhavard), encode master.ign, worker.ign, and append-bootstrap.ign into base64 strings.

  ```
  cd /opt/vhavard
  base64 -w0 append-bootstrap.ign > append-bootstrap.base64
  base64 -w0 master.ign > master.base64
  base64 -w0 worker.ign > worker.base64
  ```

  #### Create the RHCOS Template in vSphere

  From any computer, download the openshift 4.x vmware template and store it locally.

  <strong>NOTE:</strong> If you are in the IBM Cloud Adoption Lab, this template will have already been created in the demo-vcenter server in the SANDBOX cluster with the filename `rhcos-4.x.x-x86_64-vmware-template`, where 4.x.x is the full version number (e.g. `rhcos-4.2.0-x86_64-vmware-template`).  You can skip the rest of this step.

  Otherwise, download the needed .ova file.  For example:

  ```
  wget -c https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/latest/rhcos-4.2.0-x86_64-vmware.ova
  ```

  From the vSphere Web Client, click on the location (cluster/folder) where you would like to put your template, right-click, on the cluster/folder and click `Deploy OVF Template...`.

  Continue to use the wizard to upload your template.  Remember where you put it because you will use it in the next step.

  #### Configure vCenter and Create your Cluster Nodes

  <strong>NOTE:</strong> You will need at the very least, 1 bootstrap node, and 3 control plane (master) nodes, and 2 compute (worker) nodes.  It is recommended that you use exactly 3 control plane nodes and a minimum of 2 compute nodes.  

  With a browser, login to your vCenter server.  You will need to create a folder directly under your datacenter with the same name as your cluster.  For example, my cluster name is `vhavard`, so under my datacenter (named CSPLAB, I created a folder named `vhavard`).

 ![vCenter folder](/images/vcenter-folder.png "vCenter Folder")

  Find your previously uploaded rhcos template and create your bootstrap node.  Right-click on the template and click "New VM from this Template".

  ![Create VM from Template](/images/vm-from-template.png "Create VM from Template")

  On the `Select a name and folder` screen, name your VM so you know it's the bootstrap node (e.g. ocp-42-bootstrap), put it into the folder you created in the previous step and click 'Next'.

  On the next screen (`Select a compute resource`), select a compute resource location for your VM and click 'Next'.

  On the next screen (`Select storage`), choose the datastore you put in the `install-config.yaml` file in step 10 under the 'Create the Installation Server' section and click 'Next'.

  On the next screen (`Select clone options`), check the box to customize the virtual machine's hardware, make sure `Power on virtual machine after creation` box is *unchecked* and click 'Next'.

  On the next screen (`Customize hardware`), set the CPU and Memory values appropriately based on the table below and make sure your network adapter is set to the correct network for your OCP cluster.  For the IBM Cloud Adoption Lab, this is the `OCP` network.

  | Node Type | CPU | Memory |
  |:---------:|:---:|:-------|
  | Bootstrap |  4  | 16Gi   |
  | Control   |  4  | 16Gi   |
  | Compute   |  2  | 8Gi    |

  Click the `VM Options` tab and expand the `Advanced` twistie.

  Under `Configuration Parameters`, click the `Edit Configuration...` button.

  At the bottom of the page next to `Name:` type `disk.EnableUUID` and next to `Value:` type `TRUE`. Then click the `Add` button and then the `Next` button.

  ![disk.EnableUUID](images/disk-enable-uuid.png "disk.EnableUUID = TRUE")

  Click 'Next' and then 'Finish' to finish VM creation, but <strong>do not yet boot the new node.</strong>

  Find your newly created VM in the vSphere Web Console and click on it.  On the top-right, click `Configure`, then under `Settings`, click on `vApp Options`.

  If vApp Options are not Enabled, enable them.

  Scroll to the bottom of the vApp Options and find the `Properties` section.

  You will have two properties one labeled `Ignition config data encoding` and one labeled `Ignition config data`.

  Select the property labeled `Ignition config data encoding` and click `Set Value` at the top of the table.

  In the blank, put `base64` and click `OK`.

  On your installation machine cat the text of append-bootstrap.b64 file to the screen:

  ```
  cat append-bootstrap.base64
  ```

  Copy the output from this file into your clipboard/paste buffer.

  Back in the vSphere web client, select the property labeled `Ignition config data` and click `Set Value` at the top of the table. Paste the base64 string in your clipboard into this blank and click `OK`.

  You have now created your bootstrap node.

  Repeat these steps for each node in your cluster.  For the master/control plan nodes use the master.base64 ignition file and for the compute/worker nodes use the worker.base64 text.

  ### Note the MAC addresses for all of your VMs.

  You will need to know the MAC address for each of the nodes you just created.

  In the vCenter client, locate each node you just created, select it, and on the right, click the `Configure` tab.

  Expand the `VM Hardware` tistie and under that, the `Network adapter 1` twistie.

  Make a note of the MAC address for each cluster node.

  ![mac-address](/images/mac-address.png "MAC address")
  </details>

  <details>
  <summary>Configure the Bare Metal Environment</summary>

  ### Bare Metal Installation Specifics
  Installation of OCP in a bare metal environment requires either mounting an .iso to the local machine to install the operating system or installing via PXE (Pre-eXecution Environment).  In this tutorial, we will use a legacy PXE server.

  Installation of a PXE server is beyond the scope of this document.  If no PXE server exists in the environment one should be created.

  #### Create (but don't boot) your cluster nodes
  Before you can configure the PXE and DHCP servers, you will need to know the MAC addresses of all the nodes in your cluster.  Since we will be using virtual machines rather than bare metal servers, we will need to first create the VMs on the hypervisor.

  Assuming the environment is KVM, use `virt-manager` or `virsh` to create a VM for each node that will be a part of your cluster.  Make note of the MAC address of each node and what type of node it should be (bootstrap, control plane (master), compute (worker)).

  See the table below for recommended sizing of the various nodes:

  | Node Type | CPU | Memory |  Disk |
  |:---------:|:---:|:-------|:-----:|
  | Bootstrap |  4  | 16Gi   | 120GB |
  | Control   |  4  | 16Gi   | 120GB |
  | Compute   |  2  | 8Gi    | 120GB |

  #### Configure the PXE server
  There are three files you will need for a PXE install:
    * rhcos-4.2.0-x86_64-installer-initramfs.img
    * rhcos-4.2.0-x86_64-installer-kernel
    * rhcos-4.2.0-x86_64-metal-bios.raw.gz

  <br>On your <strong>installation/web server machine</strong>, change to your project folder and download the metal-bios file from the Red Hat download site:

  ```
  cd /opt/vhavard
  wget -c https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/latest/rhcos-4.2.0-x86_64-metal-bios.raw.gz
  ```

  On the <strong>PXE server</strong>, you will need the other two files.

  In this document we will assume that the tftpboot path is /tftpboot.

  Create a new subdirectory named "rhcos" under /tftpboot.  Download the other two files to this directory:

  ```
  mkdir -p /tftpboot/rhcos
  cd /tftpboot/rhcos
  wget -c https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/latest/rhcos-4.2.0-x86_64-installer-initramfs.img
  wget -c https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.2/latest/rhcos-4.2.0-x86_64-installer-kernel
  ```

  Under the /tftpboot directory should be a subdirectory named pxelinux.cfg.  For a streamlined installation, we will not use a menu-based installation.  Instead, we will use the MAC address of the VM to specify the exact configuration which should be applied to the VM and it will be automatically applied at boot time.

  To create a custom installation configuration for a VM, you must create a file named for the MAC address of the VM in the /tftpboot/pxelinux.cfg/ directory.

  The format of the filename is <address-type>-<xx-xx-xx-xx-xx-xx> where <address-type> is "01" for ARP and "xx-xx-xx-xx-xx-xx" represents the mac address of the VM with each "xx" being an octet of the mac address.  For example, "01-00-50-56-a5-bc-2d".

  The file should have the following contents:

  <strong>IMPORTANT:</strong> Replace the URL in square brackets (removing the square brackets) with the URL of the metal-bios file you downloaded to your installation/web server and the URL of the bootstrap.ign ignition file, respectively.

  ```
  DEFAULT pxeboot
  TIMEOUT 20
  PROMPT 0
  LABEL pxeboot
      KERNEL rhcos/rhcos-4.2.0-x86_64-installer-kernel
      APPEND ip=dhcp rd.neednet=1 initrd=rhcos/rhcos-4.2.0-x86_64-installer-initramfs.img console=tty0 console=ttyS0 coreos.inst=yes coreos.inst.install_dev=sda coreos.inst.image_url=[http://172.18.1.30/pxetest/rhcos-4.2.0-x86_64-metal-bios.raw.gz] coreos.inst.ignition_url=[http://172.18.1.30/pxetest/bootstrap.ign]
  ```

  Create a file for each of the nodes in your cluster, with each file pointing to the correct ignition file for the the type of node to which it should apply.

  For example, if your bootstrap node's mac address is 00:50:56:a5:2a:63, you will create a file named `01-00-50-56-a5-2a-63` with the contents noted above.

  If the node were a master node the file contents would be identical, but the ignition_url location would be the URL for the master.ign file, and the path for a worker node would be the same, but point to worker.ign on that same server.

  When all of the files have been created, double check to make sure there are no typos.  There is no need to restart the service, changes are picked up immediately.
  </details>

### Provision two new VMs to use as external load balancers

1. In the csplab, use the template named rhel80-cli-template in the sandbox datastore to instantiate two new VMs.  Otherwise, install any linux VM you choose, in your example, we will use RHEL 8.0.

1. Name your VMs for their purpose, e.g. `ocp-42-control-lb`, `ocp-42-compute-lb`.

1. Install the haproxy packages on the VMs

```
yum install -y haproxy
```

1. You will configure your load balancers when you get your IP addresses assigned.


### IBM Cloud Adoption Lab Users: Request a new subnet for your cluster

IBM employees who are deploying a cluster into the IBM Cloud Adoption Lab's OCP environment you will need to be assigned a subnet.  Send an email to the csplab-admin mailing list to request the subnet.

When you request your subnet, provide the MAC address for each of your cluster nodes including the 2 load balancers.

The lab admins will configure the DHCP and DNS servers and router for your assigned subnet.

If you are deploying into the IBM Cloud Adoption Lab you can ignore the steps `Configure DHCP Server` and `Configure DNS Server` sections, these will be done for you.

### Configure the DHCP server

Each node will need to be added to the DHCP server so that it can get a static mapped IP address and hostname at boot time.

It is also possible to add this information to the ignition files, but doing so is out of the scope of this document.  Note, however, that if you plan to modify the ignition files to add static IP addresses, you must create a separate ignition file for each node rather than just one for each type of node.

See Appendix B for an example dhcpd.conf file if using the standard isc-dhcp-server dhcp package.

If the nodes are on the correct network and the DHCP server is configured correctly, each node should boot with the IP address and hostname you configured for each node.

**IMPORTANT:** Make sure the hostname you specify for the node in the DHCP server is the same as the hostname you use for your DNS server.

### Configure the DNS Server

Make the following DNS updates make sure the hostnames and IP addresses match the information specified in the DHCP server:

1. api.\<cluster_name\>.\<base_domain\>

  Points to the load balancer for control plane nodes (master nodes)

  e.g. **api.vhavard.ocp.csplab.local**

1. api-int.\<cluster_name\>.\<base_domain\>

  Points to the load balancer for the control plane nodes (master nodes). The IP address for `api` and `api-int` should be the same.

  e.g. **api-int.vhavard.ocp.csplab.local**

1. \*.apps.\<cluster_name\>.\<base_domain\>

  Points to the load balancer for the compute nodes (worker nodes).

  e.g. **\*.apps.vhavard.ocp.csplab.local**

1. etcd-\<index\>.vhavard.ocp.csplab.local

  Points to each of the etcd nodes, respectively (master nodes, normally).

  e.g. </br>
      **etcd-0.vhavard.oc.csplab.local** <- same IP address as control-plane-0 (aka master1)</br>
      **etcd-1.vhavard.ocp.csplab.local** <- same IP address as control-plane-1 (aka master2)</br>
      **etcd-2.vhavard.ocplcsplab.local** <- same IP address as control-plane-2 (aka master3)

1. SRV Records

  For each control plane machine, OpenShift Container Platform also requires a SRV DNS record for etcd server on that machine with priority **0**, weight **10** and port **2380**. A cluster that uses three control plane machines requires the following records:

  ```
  # _service._proto.name.                            TTL    class SRV priority weight port target.
_etcd-server-ssl._tcp.<cluster_name>.<base_domain>  86400 IN    SRV 0        10     2380 etcd-0.<cluster_name>.<base_domain>.
_etcd-server-ssl._tcp.<cluster_name>.<base_domain>  86400 IN    SRV 0        10     2380 etcd-1.<cluster_name>.<base_domain>.
_etcd-server-ssl._tcp.<cluster_name>.<base_domain>  86400 IN    SRV 0        10     2380 etcd-2.<cluster_name>.<base_domain>.
  ```
  e.g.

  ```
# _service._proto.name.                            TTL    class SRV priority weight port target.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-0.vhavard.ocp.csplab.local.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-1.vhavard.ocp.csplab.local.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-2.vhavard.ocp.csplab.local.
  ```

### Configure your haproxy nodes (load balancers)

Once you have IP addresses assigned for your load balancers, bootstrap node, control plane nodes, and compute nodes, you need to configure your load balancers.

If not already provided via the DHCP server, create static IP addresses for the load balancers.

1. Configure the control plane load balancer

  1. The control plane server should proxy ports 6443 and 22623 with the bootstrap server and all master nodes as backend targets.  The mode should be `tcp`.

  1. For an example configuration see Appendix C.

1. Configure the compute load balancer

  1. The compute server should proxy ports 443 and 80 with the compute/worker nodes as the backend servers.

  1. For an example configuration see Appendix C.

#### Boot your nodes

Once you have the load balancers, dhcp server, and dns server configured, you can boot your cluster nodes and they will come up and configure themselves based on the ignition files you provided.

1. Power on all nodes

  If you have everything configured properly, you should see the correct IP address for each node on the VMware console for each node, respectively.

1. Issue the following command and wait for a completed result:

  ```
  [sysadmin@localhost opt]$ ./openshift-install --dir=./vhavard wait-for bootstrap-complete --log-level info
  ```

  Anticipated result:

  ```
  INFO Waiting up to 30m0s for the Kubernetes API at https://api.vhavard.ocp.csplab.local:6443...
  INFO API v1.13.4+c2a5caf up                       
  INFO Waiting up to 30m0s for bootstrapping to complete...
  INFO It is now safe to remove the bootstrap resources
  ```

You can watch the installation progress by logging into the bootstrap server and use journalctl.

Because of the ssh key you provided in the install-config.yaml you can ssh directly to the bootstrap node without credentials:

  ```
  ssh core@bootstrap.vhavard.ocp.csplab.local
  ```

Where bootstrap.vhavard.ocp.csplab.local is the hostname or IP address of your bootstrap server.

Once logged in, you can monitor progress with the following command:

  ```
  journalctl -b -f -u bootkube.service
  ```

Installation normally take about 30 minutes.

If you do not get a completed result then you need to troubleshoot what is failing.  Watching the logs on the bootstrap server as noted above can give you information about what is failing.

You can also ssh to one of the master nodes and execute `journalctl -f` to watch the logfile for potential errors.

You may also find it helpful to watch the traffic going through the control plane load balancer (e.g. via the haproxy log files).  You should see traffic from all nodes as they pull configuration information from the bootstrap node.  You may be able to see errors here if there are configuration issues with any of the specific nodes or the bootstrap node.

## Remove bootstrap server from control plane load balancer

Once the installation has successfully completed, you must login to the control plane load balancer and remove the bootstrap server from the list of backend servers and restart the haproxy service.

```
systemctl restart haproxy
```

When this is done you should be able to login to your new cluster.

## Login to the ocp cluster

From your installation machine where you installed the oc binary:

```
export KUBECONFIG=/opt/vhavard/auth/kubeconfig
oc whoami
system:admin
```

## Make sure all nodes are in Ready status

List all Nodes

  ```
  sysadmin@ocp42install:~$ oc get nodes
  NAME              STATUS   ROLES    AGE   VERSION
  compute-0         Ready    worker   20m   v1.14.6+8e46c0036
  compute-1         Ready    worker   20m   v1.14.6+8e46c0036
  compute-2         Ready    worker   20m   v1.14.6+8e46c0036
  control-plane-0   Ready    master   20m   v1.14.6+8e46c0036
  control-plane-1   Ready    master   20m   v1.14.6+8e46c0036
  control-plane-2   Ready    master   20m   v1.14.6+8e46c0036
  storage-0         Ready    worker   20m   v1.14.6+8e46c0036
  storage-1         Ready    worker   20m   v1.14.6+8e46c0036
  storage-2         Ready    worker   20m   v1.14.6+8e46c0036
  ```

Note: If you don't see all nodes listed you may need to approve some certificate signing requests (CSRs).

To check issue the command:

```
oc get csr
```

If you see any CSR in a pending state you must approve each one. If all CSRs were automatically approved you may not see anything in this list.

The command to approve a csr is:

```
oc adm certificate approve <csr-name>
```

The CSR name is the first column in the list of CSRs.

There are two CSRs you must approve for each node, the first will be the client-side and the second will be the server side.  You will not see the server-side CSR until the client-side CSR has been approved.  So, when you go in and approve all the client-side CSRs, wait a minute or two and check for any new CSRs and approve the server-side requests.

Once both have been approved, you should be able to execute `oc get nodes` and see all nodes listed.  It will take another few minutes for all those nodes to get to the `ready` state, but if you give it a few minutes they should all complete.

If you have waited a long time before checking the CSRs, the process will end and get restarted and you could have dozens or even more pending CSRs.  You must approve all of them.  That can be a fairly tedious task and you can run the following command to approve them all at once:

```
oc get csr -ojson | jq -r '.items[] | select(.status == {} ) | .metadata.name' | xargs oc adm certificate approve
```

Note that `jq` in the above string of commands is an application you will likely need to install via your package manager (`yum -y install jq`).

## Make sure all controllers are up

Once the initial boot is complete it will still take a short while for the cluster operators to complete their configuration.

Watch the following command until all operators except for image-registry are available.

  ```
  watch -n5 oc get clusteroperators
  ```

When complete the output should look something like this:

  ```
  $ watch -n5 oc get clusteroperators

  NAME                                 VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE
  authentication                       4.2.0     True        False         False      69s
  cloud-credential                     4.2.0     True        False         False      12m
  cluster-autoscaler                   4.2.0     True        False         False      11m
  console                              4.2.0     True        False         False      46s
  dns                                  4.2.0     True        False         False      11m
  image-registry                                 False       True          False      5m26s
  ingress                              4.2.0     True        False         False      5m36s
  kube-apiserver                       4.2.0     True        False         False      8m53s
  kube-controller-manager              4.2.0     True        False         False      7m24s
  kube-scheduler                       4.2.0     True        False         False      12m
  machine-api                          4.2.0     True        False         False      12m
  machine-config                       4.2.0     True        False         False      7m36s
  marketplace                          4.2.0     True        False         False      7m54m
  monitoring                           4.2.0     True        False         False      7h54s
  network                              4.2.0     True        False         False      5m9s
  node-tuning                          4.2.0     True        False         False      11m
  openshift-apiserver                  4.2.0     True        False         False      11m
  openshift-controller-manager         4.2.0     True        False         False      5m943s
  openshift-samples                    4.2.0     True        False         False      3m55s
  operator-lifecycle-manager           4.2.0     True        False         False      11m
  operator-lifecycle-manager-catalog   4.2.0     True        False         False      11m
  service-ca                           4.2.0     True        False         False      11m
  service-catalog-apiserver            4.2.0     True        False         False      5m26s
  service-catalog-controller-manager   4.2.0     True        False         False      5m25s
  storage                              4.2.0     True        False         False      5m30s
  ```

## Configure Storage for the image-registry Operator

The image registry requires persistent storage with access mode of ReadWriteMany (RWX), however, the vSphere storage class does not support RWX.  There are two options, 1) do not use persistent storage, in which case an images placed in the registry are lost with each start, or 2) configure persistent storage which does support RWX (e.g. NFS).


_Option 1_ - Do not use persistent storage

  If you just want to get the cluster up and running quickly, you can tell the image registry operator to not use persistent storage.  To do this, execute the following command:

  ```
  oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch '{"spec":{"storage":{"emptyDir":{}}}}'
  ```

  Your image-registry cluster operator should complete its installation in a couple of minutes and your cluster will be usable.

_Option 2_ - Configure persistent storage

  <details>
  <summary>Configure Ceph storage (recommended)</summary>
  <br><strong>NOTE:</strong>  These instructions should be carried out on the installation node.

  <br>If you have not already done so, add at least one additional hard disk to all compute nodes which should be used as storage nodes and note the node names of all storage nodes (this will be needed later).

  ```
  sysadmin@ocp42install:/opt$ oc get nodes
  NAME              STATUS   ROLES    AGE   VERSION
  compute-0         Ready    worker   41h   v1.14.6+8e46c0036
  compute-1         Ready    worker   41h   v1.14.6+8e46c0036
  compute-2         Ready    worker   41h   v1.14.6+8e46c0036
  control-plane-0   Ready    master   42h   v1.14.6+8e46c0036
  control-plane-1   Ready    master   42h   v1.14.6+8e46c0036
  control-plane-2   Ready    master   42h   v1.14.6+8e46c0036
  storage-0         Ready    worker   41h   v1.14.6+8e46c0036
  storage-1         Ready    worker   41h   v1.14.6+8e46c0036
  storage-2         Ready    worker   42h   v1.14.6+8e46c0036
  ```

Label storage nodes

  ```
  oc label node storage-0 role=storage-node
  oc label node storage-1 role=storage-node
  oc label node storage-2 role=storage-node
  ```

Clone the rook project from github

  ```
  cd /opt
  git clone https://github.com/rook/rook.git
  ```

  You should now have a subdirectory under /opt named `rook`.

Change to the `ceph` directory:

  ```
  cd /opt/rook/cluster/examples/kubernetes/ceph
  ```

Create the common and operator objects

  ```
  oc create -f common.yaml
  oc create -f operator-openshift.yaml
  ```

Wait for all pods to enter the 'Running' state

    ```
    watch -n5 "oc get pods -n rook-ceph"
    ```

Modify the cluster.yaml file for your environment.

  ```
  apiVersion: ceph.rook.io/v1
  kind: CephCluster
  metadata:
    name: rook-ceph
    namespace: rook-ceph
  spec:
    cephVersion:
      image: ceph/ceph:v14.2.5
      allowUnsupported: false
    dataDirHostPath: /var/lib/rook
    skipUpgradeChecks: false
    continueUpgradeAfterChecksEvenIfNotHealthy: false
    mon:
      count: 3
      allowMultiplePerNode: false
    dashboard:
      enabled: true
      ssl: true
    monitoring:
      enabled: true
      rulesNamespace: rook-ceph
    network:
      hostNetwork: false
    rbdMirroring:
      workers: 0
    placement:
      all:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: role
                operator: In
                values:
                - storage-node
        podAffinity:
        podAntiAffinity:
        tolerations:
        - key: storage-node
          operator: Exists
    annotations:
    resources:
      mgr:
        limits:
          cpu: "500m"
          memory: "1024Mi"
        requests:
          cpu: "500m"
          memory: "1024Mi"
    removeOSDsIfOutAndSafeToRemove: false
    storage: # cluster level storage configuration and selection
      useAllNodes: false
      useAllDevices: false
      config:
      nodes:
      - name: "storage-0"
        devices: # specific devices to use for storage can be specified for each node
        - name: "sdb"
          config:
            osdsPerDevice: "1"
      - name: "storage-1"
        devices: # specific devices to use for storage can be specified for each node
        - name: "sdb"
          config:
            osdsPerDevice: "1"
      - name: "storage-2"
        devices: # specific devices to use for storage can be specified for each node
        - name: "sdb"
          config:
            osdsPerDevice: "1"
    disruptionManagement:
      managePodBudgets: false
      osdMaintenanceTimeout: 30
      manageMachineDisruptionBudgets: false
      machineDisruptionBudgetNamespace: openshift-machine-api
  ```

Create the Ceph cluster

  ```
  oc create -f cluster.yaml
  ```

Wait for all pods to enter 'Running' state

  ```
  watch -n5 "oc get pods -n rook-ceph"
  ```

Create the Ceph toolbox pod to check cluster health

  ```
  oc create -f toolbox.yaml
  ```

  It should take less than a minute to provision.  Check with `oc get pods -n rook-ceph`.

Check the health of the Ceph cluster

  ```
  oc -n rook-ceph exec -it <rook_pod> -- /usr/bin/ceph -s
  ```

Should return something like this:

  ```
  [sysadmin@vhavard-installer ceph]$ oc -n rook-ceph exec -it rook-ceph-tools-7f9b9bfdb4-p6g5r -- /usr/bin/ceph -s
  cluster:
    id:     8eaa6336-6ff1-4721-9978-867f5fdfdafd
    health: HEALTH_OK

  services:
    mon: 3 daemons, quorum a,b,c (age 13m)
    mgr: a(active, since 12m)
    osd: 3 osds: 3 up (since 11m), 3 in (since 11m)

  data:
    pools:   0 pools, 0 pgs
    objects: 0 objects, 0 B
    usage:   3.0 GiB used, 1.5 TiB / 1.5 TiB avail
    pgs:
  ```

  You now have a running Ceph cluster, provisioned by rook.  You now need to configure OCP to consume it.

Deploy the `rbd` storage class for non-ReadWriteMany PVs

  ```
  cd /opt/rook/cluster/examples/kubernetes/ceph/csi/rbd
  oc create -f storageclass.yaml
  ```

  <strong>NOTE:</strong> Ceph rbd volumes are raw storage volumes.  The storage class defines how the volume should be formatted after it is created.  The default is ext4.  If you would like something other than ext4 (e.g. xfs), modify the storage class to specify `csi.storage.k8s.io/fstype: xfs`.

  Check that your new storage class was created:

  ```
  oc get sc
  ```

Deploy the `CephFS` storage class for ReadWriteMany PVs.

  <strong>IMPORTANT:</strong> Although Ceph supports unlimited filesystems, rook (the k8s implementation of Ceph), only supports one.  This means that you can only deploy one single RWX PV using rook/CephFS.  If you need more than one RWX volume, you much use an external Ceph implementation and integrate it with OCP.  Doing so is outside of the scope of this document.

  As of this writing, allowing multiple filesystems in rook/ceph is *experimental* and is thus possible, but doing so would not be production ready and so is outside the scope of this document.

  For our OCP 4.2 deployment, we need one RWX volume to use for the image registry.  We will deploy the only available filesystem PV for use by the image registry later in this document.

  ```
  cd /opt/rook/cluster/examples/kubernetes/ceph/csi/cephfs
  oc create -f storageclass.yaml
  oc get sc
  ```

Create a filesystem to be used by our image registry

  ```
  /opt/rook/cluster/examples/kubernetes/ceph
  oc create -f filesystem.yaml
  ```

Wait for all pod to reach 'Running' state

  ```
  watch -n5 "oc get pods -n rook-ceph"
  ```

Check Ceph cluster health:

  ```
  [sysadmin@vhavard-installer ceph]$ oc -n rook-ceph exec -it rook-ceph-tools-7f9b9bfdb4-p6g5r -- /usr/bin/ceph -s
  cluster:
    id:     8eaa6336-6ff1-4721-9978-867f5fdfdafd
    health: HEALTH_OK

  services:
    mon: 3 daemons, quorum a,b,c (age 34m)
    mgr: a(active, since 4m)
    mds: myfs:1 {0=myfs-a=up:active} 1 up:standby-replay
    osd: 3 osds: 3 up (since 32m), 3 in (since 32m)

  data:
    pools:   10 pools, 80 pgs
    objects: 37 objects, 4.4 KiB
    usage:   3.0 GiB used, 1.5 TiB / 1.5 TiB avail
    pgs:     80 active+clean

  io:
    client:   1.2 KiB/s rd, 0 B/s wr, 1 op/s rd, 0 op/s wr
  ```

Create a PVC to be consumed by the image registry (pvc.yaml)

  ```
  # pvc.yaml
  ---
  apiVersion: v1
  kind: PersistentVolumeClaim
  metadata:
    finalizers:
    - kubernetes.io/pvc-protection
    name: image-registry-storage
    namespace: openshift-image-registry
  spec:
    accessModes:
    - ReadWriteMany
    resources:
      requests:
        storage: 100Gi
    persistentVolumeReclaimPolicy: Retain
    storageClassName: csi-cephfs
  ```

Deploy the PVC:

  ```
  oc create -f pvc.yaml
  ```

  </details>


  <details>
  <summary>Configure NFS Storage (not recommended for production)</summary>
  <br><strong>Note:</strong> Using NFS in a production environment is <strong>not</strong> recommended.  It is described here because it is the easiest to get configured and up and running.  The recommendation is to use rook/Ceph for all persistent storage needs.

  1. In order to configure persistent storage for the image repository you will need a storage server configured to serve up ReadWriteMany (RWX) volumes.  Creation of an NFS server is beyond the scope of this document, however, to prevent problems, the exports for the mounted NFS volume should be specified with the following options:

  ```
  /storage	*(rw,no_subtree_check,sync,no_wdelay,insecure,no_root_squash)
  ```

  For security purposes, you could also create a separate entry for each control plane and compute node to ensure no other node can mount the directory.

  With an NFS mount available, next you will configure a storage class, a PV, and a PVC in your openshift cluster to consume it.

  1. To create the storage class create a file on your installation server named `sc.yml` with the following contents:

  ```
  kind: StorageClass
  apiVersion: storage.k8s.io/v1
  metadata:
    name: nfs
  provisioner: no-provisioning
  parameters:
  ```

  Create the storage class by executing `oc create -f sc.yml`.  Your new storage class name is `nfs`.

  1. Make your new storage class the default.

  By default, with a vSphere installation, vsphere storage is the default storage class.  If this isn't changed the image-registry operator will try to create a RWX volume on the vsphere datastore and it will fail.

  To remove the default flag for the `thin` (vsphere) storage class, execute the following command:

  ```
  oc patch storageclass thin -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "false"}}}'
  ```

  Next, you will need to set your newly created storage class as the default.  Do that by executing the following command:

  ```
  oc patch storageclass nfs -p '{"metadata": {"annotations": {"storageclass.kubernetes.io/is-default-class": "true"}}}'
  ```

  Your new `nfs` storage class is now the default.

  1. Create a file on the installation server named `pv.yml` with the following contents:

  ```
  apiVersion: v1
  kind: PersistentVolume
  metadata:
    name: [pv0001]
  spec:
    capacity:
      storage: 100Gi
    accessModes:
    - ReadWriteMany
    nfs:
      path: [/server]
      server: [10.x.x.138]
    persistentVolumeReclaimPolicy: Retain
    storageClassName: nfs
  ```

  Replace `pv0001` with something more descriptive like `image-registry-pv`.

  Replace `spec.nfs.path` with the path on the NFS server to the volume to mount (e.g. `/storage`).

  Replace `spec.nfs.server` with the ip address of your nfs server.

  Deploy your PV to the clsuter with the following command:

  ```
  oc create -f pv.yml
  ```

  1. Create a file on the installation server named `pvc.yml` with the following contents.

  ```
  apiVersion: v1
  kind: PersistentVolumeClaim
  metadata:
    finalizers:
    - kubernetes.io/pvc-protection
    name: image-registry-storage
    namespace: openshift-image-registry
  spec:
    accessModes:
    - ReadWriteMany
    resources:
      requests:
        storage: 100Gi
  ```

  Deploy the PVC to the cluster with the following command:

  ```
  oc create -f pvc.yml
  ```

  1. Check to make sure your PVC is bound to your PV

  ```
  oc get pv --all-namespaces
  ```

  The result should show the PV bound to a PVC.

  ```
  [sysadmin@localhost vhavard]$ oc get pv --all-namespaces
  NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                             STORAGECLASS   REASON   AGE
  image-repo   100Gi      RWX            Retain           Bound    openshift-image-registry/image-registry-storage   nfs             7h22m
  ```
</details>

<br>Configure the image-registry operator to use persistent storage

  ```
  oc edit configs.imageregistry.operator.openshift.io

    storage:
      pvc:
        claim:
  ```
  Leave the value of `claim` blank.

  The result should look something like this:

  ```
  spec:
    defaultRoute: false
    httpSecret: 76c5cf9d7cd2684b7805495d1d31578009e035f0750dd2c5b79e57e2c6db1ce4e05d101b58e25feb00382a66044b76513d792f8628609b5d417ed2101b52a62c
    logging: 2
    managementState: Managed
    proxy:
      http: ""
      https: ""
      noProxy: ""
    readOnly: false
    replicas: 1
    requests:
      read:
        maxInQueue: 0
        maxRunning: 0
        maxWaitInQueue: 0s
      write:
        maxInQueue: 0
        maxRunning: 0
        maxWaitInQueue: 0s
    storage:
      pvc:
        claim:
  ```

  When this is complete, recheck your clusteroperator status to make sure the status becomes available.

  ```
  watch -n5 oc get clusteroperators
  ```

  After a minute or two all operators should show available.

  ```
  NAME                                       VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE
  authentication                             4.2.0     True        False         False	  7h49m
  cloud-credential                           4.2.0     True        False         False	  8h
  cluster-autoscaler                         4.2.0     True        False         False	  7h55m
  console                                    4.2.0     True        False         False	  7h51m
  dns                                        4.2.0     True        False         False	  8h
  image-registry                             4.2.0     True        False         False	  7h24m
  ingress                                    4.2.0     True        False         False	  7h54m
  insights                                   4.2.0     True        False         False	  8h
  kube-apiserver                             4.2.0     True        False         False	  7h59m
  kube-controller-manager                    4.2.0     True        False         False	  7h57m
  kube-scheduler                             4.2.0     True        False         False	  7h58m
  machine-api                                4.2.0     True        False         False	  8h
  machine-config                             4.2.0     True        False         False	  8h
  marketplace                                4.2.0     True        False         False	  7h55m
  monitoring                                 4.2.0     True        False         False	  7h52m
  network                                    4.2.0     True        False         False	  7h57m
  node-tuning                                4.2.0     True        False         False	  7h55m
  openshift-apiserver                        4.2.0     True        False         False	  7h56m
  openshift-controller-manager               4.2.0     True        False         False	  7h58m
  openshift-samples                          4.2.0     True        False         False	  7h53m
  operator-lifecycle-manager                 4.2.0     True        False         False	  7h58m
  operator-lifecycle-manager-catalog         4.2.0     True        False         False	  7h58m
  operator-lifecycle-manager-packageserver   4.2.0     True        False         False	  7h57m
  service-ca                                 4.2.0     True        False         False	  8h
  service-catalog-apiserver                  4.2.0     True        False         False	  7h56m
  service-catalog-controller-manager         4.2.0     True        False         False	  7h56m
  storage                                    4.2.0     True        False         False	  7h56m
  ```

## Ensure cluster is up and ready

To complete your installation run the following command.  When the installation is complete it will output the credentials for the initial login to your new cluster.

```
cd /opt
./openshift-install --dir=./vhavard wait-for install-complete
```

The output should look something like this:

```
[sysadmin@localhost opt]$ ./openshift-install --dir=./vhavard wait-for install-complete
INFO Waiting up to 30m0s for the cluster at https://api.vhavard.ocp.csplab.local:6443 to initialize...
INFO Waiting up to 10m0s for the openshift-console route to be created...
INFO Install complete!                            
INFO To access the cluster as the system:admin user when using 'oc', run 'export KUBECONFIG=/opt/vhavard/auth/kubeconfig'
INFO Access the OpenShift web-console here: https://console-openshift-console.apps.vhavard.ocp.csplab.local
INFO Login to the console with user: kubeadmin, password: wSbzT-DCZCU-BRYF7-C7bXz
```

Login to your new cluster as kubeadmin with the credentials output to the screen.  If you lose that screen output, the same information can be found on your installation server in the `<projectdir>/auth/kubeadmin-password` file.

# Post-Install Tasks to Have a Usable Cluster
<details>
<summary>
1. Integrating with Microsoft Active Directory for authentication
</summary>

<br>Login to your cluster as kubeadmin as noted above.

Navigate to "Administration -> Cluster Settings -> Global Configuration", scroll down and click the "OAuth" link.

At the bottom of the page you will find a section entitled "Identity Providers" and it will be blank.

If you click the "Add" drop-down list you will find a number of different options for authentication integration.

Scroll down the list and choose "LDAP".  This will bring up a form with a number of fields you must fill:

* Name - This is the name of the provider and can be any value label.  You should name it something meaningful - I named mine 'csplab' since I will be authenticating against the csplab Active Directory service.

  e.g `csplab`

* URL - This is not just the URL of the LDAP server, but also the basedn and attribute to use as your login name.

  e.g `ldap://<hostname of AD server>:389/CN=users,DC=csplab,DC=local?sAMAccountName`

* Bind DN - Although the docs say this can be blank for anonymous bind, experience shows it must not be blank.  Provide the full binddn for the user to use to bind to the service and query for valid users.

  e.g. `CN=ReadOnly,CN=Users,DC=csplab,DC=local`

* Bind Password - The password for the user specified in the BindDN blank.

  e.g. `mySup3rS3cr3tPassw0rd!`

* ID - This is the LDAP attribute that should be used for authentication.  For AD, this should be `sAMAccountName`.

  e.g. `sAMAccountName`

* Preferred Username - Typically, the userid and username are the same.

  e.g. `sAMAccountName`

* Name - This is the user's display name.  The field that containes the user's full name.

  e.g. `displayName`

* Email - The field that contains the user's email address

  e.g. `mail`

If you are using TLS for authentication, use the `CA File` blank to put your CA Cert file.

Click 'Add' to create your new identity provider.

<strong>IMPORTANT:</strong> You can have multiple identity providers, but a single userid can only be used by one.  For example, if I have an htpasswd provider and a user `vhavard` is defined and claimed from that provider, I cannot also have a user named `vhavard` from the LDAP identity provider.

When this is complete you should be able to login with any value user from your LDAP identity provider as the most basic user.

_Once you have logged in for the first time_ you should be able to click on the `Role Bindings` menu item under `Administration` and find your new user.  You will then need to specify a role for your new user.

Lets add an LDAP user as a cluster administrator.  Either use the oc command line or the console UI to login as a valid LDAP user.

  ```
  oc login -u <validLdapUser>
  oc get users  # Note the user exists
  oc get identities  # Note the user is from the correct identity provider
  ```

At the top of this page, click "Create Binding" which will bring up a form.

* Binding Type - A role within the namespace or a role within the cluster?

  `Cluster-wide Role Binding (ClusterRoleBinding)`

* Role Binding - Any Valid Label

  `vhavard-cluster-admin`

* Role Name - Click the drop-down list and choose `cluster-admin`

* Subject - Who should this role belong to?

  * User

  * Subject Name - The name of the user to bind to this role

    `vhavard`

Click the `Create` button to create the role binding.  Your user should now be a cluster administrator.

<strong>Note:</strong> You an also create groups and apply the role to a group, then anyone within that group will have that role.

You can also sync local groups from LDAP groups.  For more information see: https://docs.openshift.com/container-platform/4.2/authentication/ldap-syncing.html
</details>

# Appendix A - Example DNS Configuration

## named.conf.local

```
//
// Do any local configuration here
//

// Consider adding the 1918 zones here, if they are not used in your
// organization
include "/etc/bind/zones.rfc1918";

zone "ocp.csplab.local" { type master; file "/etc/bind/db.ocp.csplab.local"; };
zone "vhavard.ocp.csplab.local" { type master; file "/etc/bind/db.vhavard.ocp.csplab.local"; };
zone "18.172.in-addr.arpa" { type master; file "/etc/bind/db.172.18"; };
```

## db.172.18

```
$TTL    86400 ; 24 hours, could have been written as 24h or 1d
; $ORIGIN 172.IN-ADDR.ARPA.
@    IN  SOA ns1.ocp.csplab.local.      root.ocp.csplab.local. (
                              11 ; serial
                              3H ; refresh
                              15 ; retry
                              1w ; expire
                              3h ; minimum
                             )
; Name servers for the zone - both out-of-zone - no A RRs required
       IN  NS ns1.ocp.csplab.local.
; Infrastructure
$ORIGIN 0.18.172.IN-ADDR.ARPA.
1        IN  PTR    gwy.ocp.csplab.local.
9        IN  PTR    dhcp.ocp.csplab.local.
10       IN  PTR    ns1.ocp.csplab.local.
$ORIGIN 1.18.172.IN-ADDR.ARPA.
1       IN  PTR    gwy.vhavard.ocp.csplab.local.
2       IN  PTR    control-plane-0.vhavard.ocp.csplab.local.
3       IN  PTR    control-plane-1.vhavard.ocp.csplab.local.
4       IN  PTR    control-plane-2.vhavard.ocp.csplab.local.
5       IN  PTR    storage-0.vhavard.ocp.csplab.local.
6       IN  PTR    storage-1.vhavard.ocp.csplab.local.
7       IN  PTR    sgtorage-2.vhavard.ocp.csplab.local.
5       IN  PTR    compute-0.vhavard.ocp.csplab.local.
6       IN  PTR    compute-1.vhavard.ocp.csplab.local.
7       IN  PTR    compute-2.vhavard.ocp.csplab.local.
11       IN  PTR    api-int.vhavard.ocp.csplab.local.
11       IN  PTR    api.vhavard.ocp.csplab.local.
12       IN  PTR    compute-lb.vhavard.ocp.csplab.local.
29       IN  PTR    bootstrap.vhavard.ocp.csplab.local.
30       IN  PTR    installer.vhavard.ocp.csplab.local.
```

## db.vhavard.ocp.csplab.local

```
;
; BIND data file for example.com
;
$TTL    604800
@       IN      SOA     vhavard.ocp.csplab.local. root.vhavard.ocp.csplab.local. (
                             3         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
        IN      A       172.18.0.10
;
@       IN      NS      ns1.vhavard.ocp.csplab.local.
@       IN      A       17.18.0.10
@       IN      AAAA    ::1
ns1     IN      A       172.18.0.10
gwy     IN      A       172.18.1.1
control-plane-1 IN      A       172.18.1.2
control-plane-2 IN      A       172.18.1.3
control-plane-3 IN      A       172.18.1.4
compute1 IN      A       172.18.1.5
compute2 IN      A       172.18.1.6
compute3 IN      A       172.18.1.7
control-lb      IN      CNAME   api
compute-lb        IN      A       172.18.1.12
bootstrap       IN      A       172.18.1.29
installer       IN      A       172.18.1.30
api     IN      A       172.18.1.11
api-int IN      A       172.18.1.11
*.apps  IN      A       172.18.1.12
etcd-0  IN      A       172.18.1.2
etcd-1  IN      A       172.18.1.3
etcd-2  IN      A       172.18.1.4
; _service._proto.name.                         TTL   class SRV priority weight port target.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-0.vhavard.ocp.csplab.local.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-1.vhavard.ocp.csplab.local.
_etcd-server-ssl._tcp.vhavard.ocp.csplab.local  86400 IN    SRV 0        10     2380 etcd-2.vhavard.ocp.csplab.local.
```

# Appendix B - Example DHCP configuration

## dhcpd.conf

```
shared-network ocp {
  option domain-name-servers 172.18.0.10;
  subnet 172.18.1.0 netmask 255.255.255.224 {
    option domain-name "vhavard.ocp.csplab.local";
    option subnet-mask 255.255.255.224;
    option routers 172.18.1.1;
    option broadcast-address 172.18.1.31;
    default-lease-time 86400;
  }
  subnet 172.18.0.0 netmask 255.255.255.224 {
    option domain-name "ocp.csplab.local";
    option subnet-mask 255.255.255.224;
    option routers 172.18.0.1;
    option broadcast-address 172.18.0.31;
    default-lease-time 86400;
    range 172.18.0.21 172.18.0.30;
  }
}

host vhavard-control-lb {
  hardware ethernet 00:50:56:a5:84:3f;
  fixed-address 172.18.1.11;
}

host vhavard-infra-lb {
  hardware ethernet 00:50:56:a5:bb:a9;
  fixed-address 172.18.1.12;
}

host vhavard-installer {
  hardware ethernet 00:50:56:a5:a8:95;
  fixed-address 172.18.1.30;
  option host-name "vhavard-installer";
}

host vhavard-bootstrap {
  hardware ethernet 00:50:56:a5:74:91;
  fixed-address 172.18.1.29;
  option host-name "bootstrap";
}

host vhavard-control-plane-0 {
  hardware ethernet 00:50:56:a5:22:5b;
  fixed-address 172.18.1.2;
  option host-name "control-plane-0";
}

host vhavard-control-plane-1 {
  hardware ethernet 00:50:56:a5:1e:a7;
  fixed-address 172.18.1.3;
  option host-name "control-plane-1]";
}

host vhavard-control-plane-2 {
  hardware ethernet 00:50:56:a5:1d:8d;
  fixed-address 172.18.1.4;
  option host-name "control-plane-2]";
}

host vhavard-storage-0 {
  hardware ethernet 00:50:56:a5:e9:8f;
  fixed-address 172.18.1.5;
  option host-name "storage-0";
}

host vhavard-storage-1 {
  hardware ethernet 00:50:56:a5:ef:47;
  fixed-address 172.18.1.6;
  option host-name "storage-1";
}

host vhavard-storage-2 {
  hardware ethernet 00:50:56:a5:f4:2a;
  fixed-address 172.18.1.7;
  option host-name "storage-2";
}

host vhavard-compute-0 {
  hardware ethernet 00:50:56:a5:e9:14;
  fixed-address 172.18.1.5;
  option host-name "compute-0";
}

host vhavard-compute-1 {
  hardware ethernet 00:50:56:a5:ef:d0;
  fixed-address 172.18.1.6;
  option host-name "compute-1";
}

host vhavard-compute-2 {
  hardware ethernet 00:50:56:a5:f4:53;
  fixed-address 172.18.1.7;
  option host-name "compute-2";
}
```

# Appendix C - Example haproxy comfiguration

1. Control plane haproxy.conf

  ```
  global
      log         127.0.0.1 local2

      chroot      /var/lib/haproxy
      pidfile     /var/run/haproxy.pid
      maxconn     4000
      user        haproxy
      group       haproxy
      daemon

      # turn on stats unix socket
      stats socket /var/lib/haproxy/stats

      # utilize system-wide crypto-policies
      ssl-default-bind-ciphers PROFILE=SYSTEM
      ssl-default-server-ciphers PROFILE=SYSTEM

  #---------------------------------------------------------------------
  # common defaults that all the 'listen' and 'backend' sections will
  # use if not designated in their block
  #---------------------------------------------------------------------
  defaults
      mode                    http
      log                     global
      option                  httplog
      option                  dontlognull
      option http-server-close
      option forwardfor       except 127.0.0.0/8
      option                  redispatch
      retries                 3
      timeout http-request    10s
      timeout queue           1m
      timeout connect         10s
      timeout client          1m
      timeout server          1m
      timeout http-keep-alive 10s
      timeout check           10s
      maxconn                 3000

  #---------------------------------------------------------------------
  # main frontend which proxys to the backends
  #---------------------------------------------------------------------
  frontend api
      bind *:6443
      mode tcp
      default_backend             api

  frontend machine-config
      bind *:22623
      mode tcp
      default_backend		machine-config

  #---------------------------------------------------------------------
  # round robin balancing between the various backends
  #---------------------------------------------------------------------
  backend api
      mode tcp
      balance     roundrobin
      server  bootstrap 172.18.1.29:6443 check
      server  master1 172.18.1.2:6443 check
      server  master2 172.18.1.3:6443 check
      server  master3 172.18.1.4:6443 check

  backend machine-config
      mode tcp
      balance     roundrobin
      server  bootstrap 172.18.1.29:22623 check
      server  master1 172.18.1.2:22623 check
      server  master2 172.18.1.3:22623 check
      server  master3 172.18.1.4:22623 check
  ```

1. Compute haproxy.conf

  ```
  global
      log         127.0.0.1 local2
      chroot      /var/lib/haproxy
      pidfile     /var/run/haproxy.pid
      maxconn     4000
      user        haproxy
      group       haproxy
      daemon

      # turn on stats unix socket
      stats socket /var/lib/haproxy/stats

      # utilize system-wide crypto-policies
      ssl-default-bind-ciphers PROFILE=SYSTEM
      ssl-default-server-ciphers PROFILE=SYSTEM

  #---------------------------------------------------------------------
  # common defaults that all the 'listen' and 'backend' sections will
  # use if not designated in their block
  #---------------------------------------------------------------------
  defaults
      mode                    tcp
      log                     global
      option                  httplog
      option                  dontlognull
      option http-server-close
      option forwardfor       except 127.0.0.0/8
      option                  redispatch
      retries                 3
      timeout http-request    10s
      timeout queue           1m
      timeout connect         10s
      timeout client          1m
      timeout server          1m
      timeout http-keep-alive 10s
      timeout check           10s
      maxconn                 3000

  #---------------------------------------------------------------------
  # main frontend which proxys to the backends
  #---------------------------------------------------------------------
  frontend https
      bind *:443
      mode tcp
      default_backend             https

  frontend http
      bind *:80
      mode http
      default_backend             http

  #---------------------------------------------------------------------
  # round robin balancing between the various backends
  #---------------------------------------------------------------------
  backend https
      balance     roundrobin
      server  worker1 172.18.1.5:443 check
      server  worker2 172.18.1.6:443 check
      server  worker3 172.18.1.7:443 check

  backend http
      balance     roundrobin
      mode http
      server  worker1 172.18.1.5:80 check
      server  worker2 172.18.1.6:80 check
      server  worker3 172.18.1.7:80 check
  ```
