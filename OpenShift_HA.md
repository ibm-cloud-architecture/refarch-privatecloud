# Install Redhat Openshift
  Features:
  * HA architecture
  * GlusterFS for workload storage
  * haproxy load balancer
  * htpasswd or LDAP authentication

**Caveat:** These notes are based on steps the author took to get an instance of Red Hat OpenShift installed and running such that workloads could be provisioned.  This document should not be considered a replacement for product documentation or any kind of best practice other than as is the experience of the author.

## Important Notes

1) Nodes here are provisioned such as to enable a significant implementation.  The nature of the cloud is that physical machines are typically over-provisioned by a factor of anywhere from 4:1 to 10:1.  A VM which has been allocated 16 vCPUs where the underlying physical CPU is 3GHz will be allowed a maximum of 48GHz of CPU cycles, but will only occupy as many cycles as needed to satisfy the demand.It will not use all of that unless the VM is running at 100% utilization (which is rare).<br><br>The same is the case for memory.  The author would rather provision too much resource and have it under-utilized (allowing other VMs to use cycles this one is not using), than to provision too few resources and have stability issues with the cluster.

2) Storage (other than etcd nodes) should be thin provisioned for the same reasons.  Thin provisioned disks only occupy as much space as has been allocated in the operating system allowing the system adminitrator to over-provision physical storage by as much as 4:1.  It is not recommended to over-provision storage by more than 4:1.<br><br>Nodes which will host etcd (either the master nodes or etcd nodes, depending on the architectural decisions) should be thick provisioned and be run only on disks with high IOPS.  etcd is extremely bandwidth intensive and using slow disks to back these nodes is certain to result in performance issues.

3)  In this scenario, the haproxy node (lb) is installed for convenience and is a single point of failure for the platform. If using an external load balancer (e.g. F5, IBM Datapower) is being used, this node is not necessary. For production deployments, using a highly available external load balancer is highly recommended.

4) In HA environments, each cluster node type should have 3 instances, each running on a separate physical host.  This way the loss of a single physical host cannot disable the cluster.  On hosts running VMware, anti-affinity rules should be used to ensure hosts of a like kind are always running on separate nodes.

5) Application nodes (node[1-3] below) should be run with a utilization low enough such that the cluster can absorb the loss of a physical node.  In this case, we are running three nodes.  Once the aggregate utilization on these nodes crossed the 65% threshold we would consider adding an additional application node or increasing the size of the existing node so that in the event of a failure of one node, the workload running on that node can be re-disbursed to the remaining nodes.

6) All nodes noted below should be treated as "appliances". Meaning, users should be locked down to only `root` and a login user (e.g. `sysadmin`) and should not run any other applications such as virus scanners, backup agents, performance agents, etc.<br><br>Any such additional applications could occupy significant CPU, Memory, and Storage resources and can have a significant negative impact on the platform.  Sizing for OpenShift clusters typically does *not* account for the overhead of running such applications on the node.

7) Installing OpenShift Enterprise (OSE) requires a valid subscription from Red Hat.  There is a free opensource version called `origin`, however, it is not recommended for production use and so this document will discuss installation of OSE.

## Infrastructure Footprint

For this exercise, the following nodes will be deployed (non-HA instances will only need one of each node type):

|    Node   |  Host   | Storage      | vCPU  | Memory |
|:--------- |:-------:|:------------ |:----: |:------:|
| ansible   | host1   | 100,100      |   4   |    8   |
| lb-master | host1   | 100          |   4   |    8   |
| lb-infra  | host2   | 100          |   4   |    8   |
| master1   | host1   | 100,100      |  16   |   64   |
| master2   | host2   | 100,100      |  16   |   64   |
| master3   | host3   | 100,100      |  16   |   64   |
| node1     | host1   | 100,100      |   8   |   32   |
| node2     | host2   | 100,100      |   8   |   32   |
| node3     | host3   | 100,100      |   8   |   32   |
| storage1  | host1   | 100,100,500  |   4   |    8   |
| storage2  | host2   | 100,100,500  |   4   |    8   |
| storage3  | host3   | 100,100,500  |   4   |    8   |
| infra1    | host1   | 100,100      |   8   |   32   |
| infra2    | host2   | 100,100      |   8   |   32   |
| infra3    | host3   | 100,100      |   8   |   32   |
| **Total** |         | **4.3TB**    |**116**|**424** |

  * _Node_ - Name of the host
    * **ansible** - This is the installer node. Analogous to the ICP boot node.
    * **lb** - This is the haproxy node, used as a load balancer in HA environments.  One to be used for the master nodes and one for infra nodes.
    * **master[1-3]** - Manages the cluster.  In this instance, we will configure etcd to run on the master node.  The user may elect to have separate etcd nodes.  If using separate etcd nodes, add three additional nodes provisioned like the master nodes and name them etcd[1-3].
    * **node[1-3]** - Where workloads run.  This is analogous to the ICP worker node.
    * **storage[1-3]** - Nodes to host GluserFS which is installed along with the cluster.
    * **infra[1-3]** - These nodes run OpenShift infrastructure pods
  * _Host_ - For HA enviroments, each node type should have 3 instances, each running on a separate physical host.  This way the loss of a single physical host cannot disable the cluster.  On hosts running VMware, anti-affinity rules should be used to ensure hosts of a like kind are always running on separate nodes.
  * _Storage_ - comma separated list of the size of the raw disks needed (in GB).
    * **Disk 1** is for the operating system (all nodes)
    * **Disk 2** is for docker storage (all nodes).  Docker storage will be provisioned as LVM so it can be expanded as needed by adding additional PVs.
    * **Disk 3** is for GlusterFS storage (only on storage nodes). GlusterFS storage is provisioned as LVM so it can be expanded as needed by adding additional PVs.
  * _vCPU_ - Number of vCPUs to assign to this VM
  * _Memory_ - Amount of RAM to assign to this VM (in GB)

## Prepare Nodes for Installation

**Note:** The following steps should be carried out on **all** nodes and be run as the `root` user.

1. Install all nodes with Red Hat Enterprise Linux version 7.5 or later with only the Minimal installation packages. Only install the operating system on the first allocated disk (e.g. /dev/sda, /dev/vda, etc.), the other disk[s] will be allocated later.  Do not put a partition on any disk other than the disk where the operating system will be installed (the boot disk).

1. Configure passwordless SSH between the ansible (installer) node and all other nodes.
  ```
  cd ~
  ssh-keygen -t rsa -P ''  # That is two single quotes
  ```
  Accept all of the default values

1. Copy the root id_rsa.pub key to all other nodes
  ```
  ssh-copy-id -i ~/.ssh/id_rsa.pub master1.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub master2.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub master3.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub node1.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub node2.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub node3.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub infra1.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub infra2.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub infra3.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub storage1.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub storage2.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub storage3.mydomain.local
  ssh-copy-id -i ~/.ssh/id_rsa.pub lb.mydomain.local
  ```

1. Install Red Hat Subscriptions
  ```
  subscription-manager repos --disable="*"  # Remove existing Subscriptions
  subscription-manager register --username=<RedHat-UserID> --password=<RedHat-Password> # Register the node with Red Hat
  subscription-manager refresh
  subscription-manager attach --pool=<poolID>  # Pool with entitlement to RHOS
  ```

1. Enable the needed yum repositories
  ```
  subscription-manager repos --enable="rhel-7-server-rpms" --enable="rhel-7-server-extras-rpms" --enable="rhel-7-server-ose-3.11-rpms" --enable="rhel-7-server-ansible-2.6-rpms" --enable="rh-gluster-3-client-for-rhel-7-server-rpms"
  yum update -y
  ```

1. Install needed prerequisite packages
  ```
  yum install -y wget git net-tools bind-utils yum-utils iptables-services bridge-utils bash-completion kexec-tools sos psacct glusterfs-fuse
  ```

1. Install openshift-ansible package
  ```
  yum install -y openshift-ansible
  ```

1. Once prerequisites are installed, reboot the node
  ```
  systemctl reboot
  ```

  _**Note:** Load balancer nodes do not need docker so the rest of this section need not be done on lb nodes._
1. Install docker
  ```
  yum install -y docker-1.13.1
  ```

1. Configure Docker Storage
  ```
  cat > /etc/sysconfig/docker-storage-config <<EOF
  STORAGE_DRIVER=overlay2
  DEVS=/dev/vdb
  CONTAINER_ROOT_LV_NAME=dockerlv
  CONTAINER_ROOT_LV_SIZE=100%FREE
  CONTAINER_ROOT_LV_MOUNT_PATH=/var/lib/docker
  VG=dockervg
  EOF
  ```
  This will create a new file named `docker-storage-config` in /etc/sysconfig.  DEVS should contain the raw device which should be used for the docker partition.  The raw disk will be configured for Logical Volume Mapping (LVM) and mounted at the location specified by `CONTAINER_ROOT_LV_MOUNT_PATH`, this specified location is the default location for the docker local registry.<br><br>The value in `DEVS` should be the second raw disk in the system (e.g. /dev/sdb or /dev/vdb).  This value should be the raw disk device and should not have a partition.

1. Enable docker to be auto-started with the system
  ```
  systemctl enable docker
  ```

1. Start docker
  ```
  systemctl start docker
  ```

1. Check to make sure docker is running properly
  ```
  rpm -V docker-1.13.1
  docker version
  ```

  The results of the above command should look something like this:

  ```
  [root@ansible ~]# rpm -V docker-1.13.1
  S.5....T.  c /etc/sysconfig/docker-storage
  .M.......    /var/lib/docker

  [root@rhos-ansible ~]# docker version
  Client:
   Version:         1.13.1
   API version:     1.26
   Package version: docker-1.13.1-91.git07f3374.el7.x86_64
   Go version:      go1.10.3
   Git commit:      07f3374/1.13.1
   Built:           Fri Feb  8 20:24:43 2019
   OS/Arch:         linux/amd64

  Server:
   Version:         1.13.1
   API version:     1.26 (minimum version 1.12)
   Package version: docker-1.13.1-91.git07f3374.el7.x86_64
   Go version:      go1.10.3
   Git commit:      07f3374/1.13.1
   Built:           Fri Feb  8 20:24:43 2019
   OS/Arch:         linux/amd64
   Experimental:    false
  ```
  If you don't get similar results, make sure docker is running using the `systemctl restart docker` command.

1. Ensure the newly created docker volume is properly mounted
  ```
  [root@ansible ~]# df -h
  Filesystem                     Size  Used Avail Use% Mounted on
  /dev/mapper/rhel-root          100G  2.1G   98G   2% /
  devtmpfs                       3.9G     0  3.9G   0% /dev
  tmpfs                          3.9G     0  3.9G   0% /dev/shm
  tmpfs                          3.9G  8.7M  3.9G   1% /run
  tmpfs                          3.9G     0  3.9G   0% /sys/fs/cgroup
  /dev/vda1                     1014M  132M  883M  14% /boot
  tmpfs                          799M     0  799M   0% /run/user/0
  tmpfs                          799M     0  799M   0% /run/user/1000
  /dev/mapper/dockervg-dockerlv  100G   33M  100G   1% /var/lib/docker
  ```

  If you do not see a volume mounted to /var/lib/docker repeat the above process.

## Install Red Hat OpenShift Enterprise (OSE)
**Note:** The following should only be done on the ansible (installer) node.

1. Edit the file at /etc/ansible/hosts and add the below stanzas making updates as is needed for your implementation
  ```
  ### OSE Inventory File
  # For more information see: https://docs.openshift.com/container-platform/3.11/install/configuring_inventory_file.html#configuring-ansible
  # This section defines the types of nodes we will deploy
  [OSEv3:children]
  masters
  nodes
  etcd
  lb
  glusterfs

  [OSEv3:vars]
  # User to use to ssh to other nodes in the environment (passwordless ssh should be configured)
  ansible_ssh_user=root
  openshift_deployment_type=openshift-enterprise
  openshift_release=v3.11

  # Replace the bit in brackets (<>) with your redhat subscription credentials
  oreg_auth_user=<your_redhat_userid>
  oreg_auth_password=<your_redhat_password>

  # This section defines htpasswd authentication.
  openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider'}]
  # This file will exist on all master nodes and this file must be identical on all systems
  # It is recommended to add users to master1 and then copy to master2 and master3 in the same location
  # To add users, use the command htpasswd -c <filename> <username> and provide a password
  openshift_master_htpasswd_file=/etc/origin/master/users.htpasswd

  # This section defines authentication via LDAP
  # You can only have one identity provider provisioned at a time
  # If you decide to use LDAP authorization you must comment out the htpasswd bit above
  # LDAP auth
  # openshift_master_identity_providers=[{'name': 'OpenLDAP', 'challenge': 'true', 'login': 'true', 'kind': 'LDAPPasswordIdentityProvider', 'attributes': {'id': ['cn'], 'email': ['Email'], 'name': ['displayName'], 'preferredUsername': ['cn']}, 'bindDN': 'cn=readonly,ou=readonly,dc=stt,dc=local', 'bindPassword': 'Passw0rd!', 'ca': '', 'insecure': 'true', 'url': 'ldap://10.10.0.1:389/ou=users,dc=mydomain,dc=local?cn'}]

  openshift_master_cluster_method=native
  openshift_master_cluster_hostname=lb.mydomain.local
  openshift_master_cluster_public_hostname=openshift.mydomain.local

  openshift_master_api_port=443
  openshift_master_console_port=443
  os_firewall_use_firewalld=true
  # When your install is complete, you will reach your cluster at:
  # https://{openshift_master_cluster_public_hostname}[:${openshift_master_console_port}]

  openshift_console_install=true

  # Use this if you are getting image availability errors
  # openshift_disable_check=docker_image_availability

  # Configure GlusterFS storage
  openshift_storage_glusterfs_namespace=app-storage
  openshift_storage_glusterfs_storageclass=true
  openshift_storage_glusterfs_storageclass_default=true
  openshift_storage_glusterfs_block_deploy=true
  openshift_storage_glusterfs_block_host_vol_size=100
  openshift_storage_glusterfs_block_storageclass=true
  openshift_storage_glusterfs_block_storageclass_default=true

  # host group for masters
  [masters]
  master1.mydomain.local
  master2.mydomain.local
  master3.mydomain.local

  # If etcd should run on the master nodes, these nodes should be identical to the [masters] section above
  # If using separate etcd nodes, specify the hostnames of the etcd nodes here
  [etcd]
  master1.mydomain.local
  master2.mydomain.local
  master3.mydomain.local

  [lb]
  lb-master.mydomain.local
  lb-infra.mydomain.com

  # The value in the square brackets should indicate the raw disk to use for GlusterFS bricks.
  # These shoudld be raw disks and have no partitions defined.  If you have multiple
  #  raw disks, use a comma separated list within each square bracket.
  [glusterfs]
  storage1.mydomain.local glusterfs_devices='[ "/dev/vdc" ]'
  storage2.mydomain.local glusterfs_devices='[ "/dev/vdc" ]'
  storage3.mydomain.local glusterfs_devices='[ "/dev/vdc" ]'

  # All nodes and their respective node types
  [nodes]
  master1.mydomain.local openshift_node_group_name='node-config-master'
  master2.mydomain.local openshift_node_group_name='node-config-master'
  master3.mydomain.local openshift_node_group_name='node-config-master'
  node1.mydomain.local openshift_node_group_name='node-config-compute'
  node2.mydomain.local openshift_node_group_name='node-config-compute'
  node3.mydomain.local openshift_node_group_name='node-config-compute'
  infra1.mydomain.local openshift_node_group_name='node-config-infra'
  infra2.mydomain.local openshift_node_group_name='node-config-infra'
  infra3.mydomain.local openshift_node_group_name='node-config-infra'
  storage1.mydomain.local openshift_node_group_name='node-config-compute'
  storage2.mydomain.local openshift_node_group_name='node-config-compute'
  storage3.mydomain.local openshift_node_group_name='node-config-compute'
  ```

1. Check your installation prior to install
  ```
  [root@ansible ~]# cd /usr/share/ansible/openshift-ansible

  [root@ansible openshift-ansible]# ansible-playbook playbooks/prerequisites.yml
  ```

1. Deploy the cluster
  ```
  [root@ansible openshift-ansible]# ansible-playbook playbooks/deploy_cluster.yml
  ```

  **Note:** This author found that the installer failed for random reasons during deploy.  After each failure, however, is a log message providing an ansible playbook to launch to retry this specific recipe (rather than the full install).

  If the failure message indicates an issue that can be easily remediated (a misconfiguration), remediate your installation and retry the deploy_cluster playbook.

  If the error message indicates a 503 error, success might be achieved by running just the failed playbook as a stand-alone deployment, and after success, re-launch the deploy_cluster playbook and continue doing so as long as you get further along the process and until ultimate success.

  ```
  INSTALLER STATUS *******************************************************************************************************************************************
  Initialization              : Complete (0:01:10)
  Health Check                : Complete (0:00:14)
  Node Bootstrap Preparation  : Complete (0:06:40)
  etcd Install                : Complete (0:02:04)
  Load Balancer Install       : Complete (0:00:53)
  Master Install              : Complete (0:06:37)
  Master Additional Install   : Complete (0:04:43)
  Node Join                   : Complete (0:01:44)
  GlusterFS Install           : In Progress (0:02:02)
  	This phase can be restarted by running: playbooks/openshift-glusterfs/new_install.yml
  Thursday 21 February 2019  11:18:14 -0600 (0:00:05.127)       0:26:07.595 *****
  ===============================================================================
  ```

## Configure your new cluster

1. Create a DNS entry for our main OpenShift UI.

  In our inventory file, we created an openshift_master_cluster_public_hostname entry and set its value to openshift.mydomain.local. Before we can login to the UI using this hostname we need a alias configured in the DNS which aliases openshift.mydomain.local to your first load balancer (master-lb.mydomain.local).

  In bind9, that entry would look something like this:

  ```
  openshift	IN	CNAME	master-lb
  ```

1. Adding users via htpasswd

  If you configured LDAP authentication in your inventory file, you should be able to login with a valid LDAP user and you can skip this step.  If you used htpasswd authentication, however, you will need to create a user so you can login.

  1. Add a new htpasswd user
  ```
  [root@ansible openshift-ansible]# ssh master1

  [root@master1 ~]# cd /etc/origin/master

  [root@master1 master]# htpasswd -c ./users.htpasswd sysadmin
  ```

  1. Copy the htpasswd file to the other master nodes
  ```
  [root@master1 master]# scp users.htpasswd master2:/etc/origin/master/

  [root@master1 master]# scp users.htpasswd master3:/etc/origin/master/
  ```

  1. With a browser access your new cluster

    https://openshift.mydomain.local

  1. Login with the credentials you just created

1. Configure a wildcard domain in bind (DNS)

  Before you can access your cluster console or apps deployed to your subdomain, you must configure your DNS to forward all requests to for in the configured subdomain (apps.mydomain.local in this case) to your infra nodes.

  You will also need to configure your second load balancer (infra-lb) to load balance traffic to your infra nodes.

  1.  Configure the second load balancer to load balance traffic to your infra nodes.

  When you configured two nodes in the [lb] stanza, it created two load balancer nodes for you and installed haproxy on those nodes.  Both nodes were configured as load balancers with an ingress IP address of the node's IP and load balancing across each of the three master nodes defined in the [master] stanza.

  We want the first load balancer (master-lb) to remain as it is because that is how we will access the OpenShift UI.

  The second load balancer (infra-lb), however, will need to be reconfigured to load balance traffic aross your infra nodes.

  ssh to your infra-lb node and edit the file /etc/haproxy/haproxy.cfg.

  You should find a section at the bottom that looks something like this:

  ```
  backend atomic-openshift-api
    balance source
    mode tcp
    server      master0 10.10.0.1:443 check
    server      master1 10.10.0.2:443 check
    server      master2 10.10.0.3:443 check
  ```

  Change the server lines to point to your infra nodes instead.  The result should look something like this:

  ```
  backend atomic-openshift-api
    balance source
    mode tcp
    server      infra0 10.10.0.4:443 check
    server      infra1 10.10.0.5:443 check
    server      infra2 10.10.0.6:443 check
  ```

  Save your file and restart your haproxy service

  ```
  systemctl restart haproxy
  ```

  1. Configure a wildcard domain record in your DNS to point to your infra load balancer

  When configured correctly all queries for any hostname in the apps.mydomain.local domain should return the IP address of your infra-lb node.

  In bind9, the entry should look something like this:

  ```
  *.apps.mydomain.local.		IN	A	10.10.0.7
  ```

  Where 10.10.0.7 is the IP address of the infra-lb node.

  Update the serial number of your db file and restart bind9 for your changes to take affect.

  Test your updates by executing something like:

  ```
  nslookup whatever.apps.mydomain.local
  ```

  Querying any host in the apps.mydomain.local domain should return the value of your A record above: 10.10.0.7 in this case.

  Login to your OpenShift UI and at the top of the page you should see "OpenShift Container Platform" and right next to it "Service Catalog" with a down arrow.  Click the arrow and change your perspective to "Cluster Console".

  If all of your configuration efforts have been successful, you should see the cluster console.  If anything went wrong, your page will fail to load with a not found error; check your load balancer configuration and DNS configuration for any mistakes.
