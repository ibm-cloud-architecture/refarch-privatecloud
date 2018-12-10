Configure GlusterFS for use as Shared Storage
===========================================================
# Introduction

When working with GlusterFS as a shared storage provider for a Kubernetes cluster, the following components need to be installed and configured.
- The GlusterFS server on a cluster of at least 3 nodes (VMs).
- The GlusterFS client on the nodes that will be using the shared storage.
  - In the case of ICP, this is the `master` nodes and the `worker` nodes.
- A Heketi server used to administer the GlusterFS storage using the `heketi-cli` and a Kubernetes StorageClass.
- A Kubernetes StorageClass object that points to the Heketi server

The following approaches can be taken when installing these components.
- So called, "native" installation
- Containerized installation

This document only covers using a Red Hat Enterprise Linux (RHEL) native installation.

References to vendor/product documentation are provided for more detail.

# Install "native" GlusterFS server

This section describes the steps to installing the GlusterFS server directly on RHEL (not in a container).

*NOTE:* The GlusterFS server topology and storage volumes do not need to be configured manually.  In a later section the `hekeit-cli` is used to configure the server topology based on a YAML configuration file.  The `heketi-cli` can then be used to define mountable storage volumes.  Many sources you find on the Internet describe extensive manual steps to configure storage devices and volumes.  You can ignore/skip all those configuration instructions.  The GlusterFS server machines need only to have raw disk devices defined on them.

Installing GlusterFS server on RHEL rather than in a container may be a matter of preference and your level of comfort with containers vs native processes.  This section is for those who are more comfortable with working native RHEL processes.

*NOTE:* Some sources may indicate that SELinux needs to be disabled on the GlusterFS servers.  SELinux does not need to be disabled.

*NOTE:* The ICP installation process supports an option to install GlusterFS on some of the ICP cluster nodes.  Choosing to do so is not recommended.  Keep the GlusterFS server cluster and Heketi server completely separated as dedicated, independent installations.  The GlusterFS cluster and Heketi server typically are used by multiple ICP clusters and other systems needing shared storage. The GlusterFS cluster and Heketi server will typically have a different life cycle than the ICP clusters.   

- A yum repository needs to be configured to get the GlusterFS, and Heketi RPMs.
Here is a sample yum `gluster.repo` file that needs to be created in `/etc/yum.repos.d/`.
```
[Gluster_4.0]
name=Gluster 4.0
baseurl=http://mirror.centos.org/centos/7/storage/$basearch/gluster-4.0/
gpgcheck=0
enabled=1
```
*NOTE:* Go out to http://mirror.centos.org/ and walk down the `centos` and `storage` directory tree to find out the latest `gluster` release and update the `gluster.repo` `baseurl` accordingly.

- Configure `dm_thin_pool` kernel module
```
> modprobe dm_thin_pool
```

- Configure a `dm_thin_pool` in a conf file in `/etc/modules-load.d/` to support setting it at machine reboot. (The files in `/etc/modules-load.d/` are used to configure the kernel when the machine boots.)
```
> echo dm_thin_pool >> /etc/modules-load.d/dm_thin_pool.conf
```

- Install `glusterfs-server`
```
> yum -y install glusterfs-server
```

- Enable and start the `glusterd` daemon.
```
> systemctl enable --now glusterd
```

- Configure passwordless `ssh` for root among the GlusterFS servers in the cluster.  This is a multi-way configuration.  Each server needs to be able to `ssh` to the other servers in the cluster. If you are unfamiliar with the steps to configure passwordless `ssh` see [Configure passwordless ssh among cluster members](configure-passwordless-ssh.md).

- Configure `firewalld` to open gluster server ports (See [Getting started with Red Hat Gluster Storage Server](https://access.redhat.com/documentation/en-us/red_hat_gluster_storage/3.1/html/administration_guide/chap-getting_started) for on ports that need to be open and the steps to configure `firewalld`.)

**NOTE** Be sure to get the firewall configured properly.  If not you will see connection problems when you attempt to load the `toplogy.json` file to configure the servers.

# Install "native" GlusterFS client

*NOTE:* Ansible playbook to do this: `icp-install-glusterfs-client.yaml` with supporting file `dm_thin_pool.conf` and `fuse.conf`.  See content in `playbooks/glusterfs`.

See GlusterFS documentation for client installation: [Accessing Data: Setting up GlusterFS Clients](http://docs.gluster.org/en/latest/Administrator%20Guide/Setting%20Up%20Clients/)

# Install Heketi on RHEL (aka "native" install)

This section describes the installation of Heketi on RHEL.  Heketi and the Heketi client will be running directly on the VM rather than in Kubernetes pods.

Heketi is only used for administration of the GlusterFS storage.  At run time the clients using the storage do not use Heketi.  The clients use the GlusterFS client and work directly with the GlusterFS servers.

See [Managing Volumes using Heketi](https://access.redhat.com/documentation/en-us/red_hat_gluster_storage/3.3/html/administration_guide/ch05s02) for Red Hat documentation on the Heketi installation and configuration.  

A reasonable place to install Heketi is on one of the GlusterFS servers.

*NOTE:* Heketi is not architected to run in a highly available configuration, i.e., a cluster.  The Heketi server runs as a singleton.  The `heketi.db` should be backed up regularly in order to recover from a catastrophic loss of the file system or machine where the Heketi server is deployed.

- A yum repository needs to be configured to get the GlusterFS, and Heketi RPMs.
Here is a sample yum `glusterfs.repo` file that needs to be created in `/etc/yum.repos.d/`.
```
[Gluster_4.0]
name=Gluster 3.13
baseurl=http://mirror.centos.org/centos/7/storage/$basearch/gluster-4.0/
gpgcheck=0
enabled=1
```

- It is assumed a yum repo has been configured that points to a GlusterFS repository.
- Install Heketi server and Heketi CLI
```
> yum -y install heketi
> yum -y install heketi-client
```
- Confirm that port 8080 is not already in use. (`netstat -an | grep 8080`)  The heketi server uses port 8080 by default, but that can be changed in the `/etc/heketi/heketi.json` configuration file.  (If you run the heketi server on an ICP master node, you will need to use a port other than 8080 since the ICP admin console process uses 8080.)

- Make sure the command line options on the `ExecStart` property in `/usr/lib/systemd/system/heketi.service` use double-dash (--) rather than a single dash (-).  It is likely the only option will be `--config`.

- Set up passwordless `ssh` between the heketi server node and all of the gluster server nodes for the gluster cluster to be managed.
```
> ssh-keygen -b 4096 -t rsa -f /etc/heketi/heketi_key -N ""
> ssh-copy-id -i /etc/heketi/heketi_key.pub root@gluster##.xxx.yyy
```
where gluster##.xxx.yyy represents each of the VMs in your gluster server cluster.

- Change the owner and group of the heketi keys to heketi.  (The heketi user got created as part of the heketi install.)
```
> chown heketi:heketi /etc/heketi/heketi_key*
```

- Modify the `/etc/heketi/heketi.json` file for your installation.
  - Things to check in particular:
    - port: something not already in use
    - use_auth: true
    - admin key
    - user key
    - executor: ssh
    - sshexec:
      - keyfile: `/etc/heketi/heketi_key`
      - user: root
      - port: 22
      - fstab: `/etc/fstab`
  - The kubeexec section can be ignored since sshexec is being used.
  - The heketi database is in the default location `/var/lib/heketi/heketi.db`.
  - The remainder of the options can be left at the defaults.

- Enable and start the heketi server.
```
> systemctl enable --now heketi
```

- Smoke test for heketi server:
NOTE: If `heketi` is configured to require authentication the simple curl command does not respond.
```
> curl http://localhost:8080/hello
Hello from Heketi
```
In the above URL, you will need to use the port you configured for the Heketi server.

*NOTE:* This native install of Heketi server has a single point of failure in the `heketi.db` being located on the node where it gets installed.  

*NOTE:* Installing Heketi server in a more resilient topology is beyond the scope of this document.  An approach for consideration:
- Move the `heketi-db` to the GlusterFS storage once it is stood up.
- Create a `heketi-db` shared volume in GlusterFS after the initial installation of Heketi.  
- Stop Heketi.  
- Move the `heketi.db` file out of `/var/lib/heketi` to some temporary location.
- Mount the `heketi-db` shared volume on `/var/lib/heketi` and copy the existing `heketi.db` into the shared volume.  
- Heketi can then be installed on some additional GlusterFS server nodes with that same shared volume mounted on `/var/lib/heketi`.  
- Only one Heketi server an be running at any given time to avoid issues with multiple servers accessing the `heketi.db` file concurrently.  

## Things that can go wrong with the Heketi install

### unknown shorthand flag: 'c'
With Heketi 4.0.0, the service wouild fail to start.  The error in `/var/log/messages` was:
```
Error: unknown shorthand flag: 'c' in -config=/etc/heketi/heketi.json
pvs-master01 heketi: unknown shorthand flag: 'c' in -config=/etc/heketi/heketi.json
```
There is nothing actually wrong with the heketi.json.  (You can paste the content into a JSON validator to convince yourself.)

The problem is the -config option to the Heketi executable.  

See https://bugzilla.redhat.com/show_bug.cgi?id=1439120  

You need to edit the `/usr/lib/systemd/system/heketi.service` file and change the `-config` to `--config`.

## Creating the GlusterFS topology using the native heketi-cli.

- Create a topology.json file that represents your GlusterFS server cluster.

*NOTE:* The GlusterFS documentation and other sources indicate the "manage" attribute for each host name dictionary should be a fully qualified host name and the storage attribute for each host name should be an IP address. Whether that is a strict requirement has not been confirmed.  Some deployments have shown that using IP addresses for both attributes also appears to work.

Here is a sample topology.json for a 3 server cluster.
```
{
  "clusters": [
    {
      "nodes": [
        {
          "node": {
            "hostnames": {
              "manage": [
                "gluster01.yyy.zzz"
              ],
              "storage": [
                "172.16.20.15"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb",
            "/dev/sdc"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "gluster02.yyy.zzz"
              ],
              "storage": [
                "172.16.20.16"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb",
            "/dev/sdc"
          ]
        },
        {
          "node": {
            "hostnames": {
              "manage": [
                "gluster03.yyy.zzz"
              ],
              "storage": [
                "172.16.20.17"
              ]
            },
            "zone": 1
          },
          "devices": [
            "/dev/sdb",
            "/dev/sdc"
          ]
        }
      ]
    }
  ]
}
```
If you tend to fat-finger JSON files, it is a good idea to run the `topology.json` content through a JSON validator. (It is easy to incorrectly edit JSON syntax.)  Search the Internet for a JSON validator to your liking.

To get general usage help with the heketi-cli, use `heketi-cli --help`.

To get more specific help use `heketi-cli command --help` where `command` is one of the heketi-cli commands.  (The "commands" are not verbs but rather an object type or class, e.g., topology, cluster, volume, node and device.)

To get specific help for the "commands" associated with a given object type use `heketi-cli type command --help`, for example `heketi-cli topology load --help`.

When working with `heketi-cli` it is very convenient to export values for the following environment variables:
```
> export HEKETI_CLI_SERVER=http://localhost:8080
> export HEKETI_CLI_USER=admin
> export HEKETI_CLI_KEY=passw0rd
```

*NOTE:* When providing the Heketi server URL, be sure not to include a trailing slash on the URL.  So for example `http://localhost:8080/` will lead to problems.  The trailing slash causes an issue for a volume create operation, for example.

You may want to create a shell file named something like `configHeketiCLI.sh` and put the export statements there and then you can source the file.  Be careful to protect the file as it has user and password in it.

The above example assumes the Heketi server is listening on port 8080, which is the default.  You may have to use something different if port 8080 is already in use on the machine where the Heketi server is intended to run.  The port the Heketi server is using is defined in the `heketi.json`. In the above, the user and key are based on what is defined in the `heketi.json` that you configured before starting the Heketi server.  

- Use the heketi-cli to load the topology.json file.
```
> heketi-cli topology load --json=topology.json
```

Obviously, the above command is assumed to have been run from the directory where the topology.json file is located.

Once the topology has successfully loaded you can use `heketi-cli topology info` to see information about the topology.

At this point you are ready to create mountable volumes that can be used by the ICP master nodes for shared storage.

## Things that can go wrong with Heketi CLI

### Error: Unable to get topology information: Unknown user
This is caused by not having a --user argument or HEKETI_CLI_USER set.

### Error: Unable to get topology information: signature is invalid

This error may occur when you run:
```
heketi-cli topology load --json=topology.json
```

The above assumes the `topology.json` file is in the current directory.

The "signature" in question has nothing to do with the content of the `topology.json` file or some digital signature it might be missing.

When you run an heketi-cli command, and you have JWT authentication enabled (see your `heketi.json`), you need to provide a user and "key" (aka password or secret).  One way to provide the key is to set the environment variable, HEKETI_CLI_KEY.  You can also pass it in on the `heketi-cli` command line with the `--secret` option. (See `heketi-cli --help` usage info.)

If the password/secret you provide does not match up with the user and key in the `heketi.json` file in current use by the Heketi service, then you will get the `signature is invalid` error.

*NOTE:* If you change anything in the `heketi.json` file you need to restart the Heketi service (`systemctl restart heketi`) to pick up the changes.

### Can't connect to gluster server

If the firewalls are not configured properly for use with glusterd and heketi, then you will get errors when you try to load the `topology.json`. The error message clearly states that connection was refused.

### Multiple attempts to load the topology

This note refers to Heketi 6.0.  Newer versions of Heketi may behave better.

If multiple attempts to load the `topolgoy.json` are made and fail, then you will likely need to clean things up.  Be sure to use the `heketi-cli topology info` command to examine your topology.  If you see clusters defined with nothing in them, then delete them.  If you see clusters defined with fewer servers than you intended from the topology, then delete them.  

# Deleting GlusterFS objects

Every type of object supports a `delete` action/verb.  You may not delete a node unless that node has no devices.  In order to delete a device it must not have any volumes.  

Before you can delete a device you need to `disable` it, then `remove`, then `delete`.

It can be very tedious to delete a cluster that is populated with nodes and devices.

# Using heketi-cli to create persistent volumes for ICP master node shared file systems

This section applies to an HA ICP deployment where there are 3 or 5 master nodes.  If you are doing a simple sandbox installation with a single master node, this section can be skipped.

*NOTE:* The `heketi-cli` commands in this section assume that the following environment variables have been set appropriately:
- HEKETI_CLI_SERVER
- HEKETI_CLI_USER
- HEKETI_CLI_KEY

- Get the glusterfs cluster ID.  The topology info will have the cluster ID.
```
heketi-cli topology info
```
*NOTE:* The Heketi documentation recommends not providing a name for the created persistent volumes.  That is debatable. If you have a good naming convention that ensures uniqueness, then using a descriptive name seems like a good idea rather than using the default names that are generated strings which have no descriptive value.)

- Create a volume for the master audit log.  In this example a 10GB volume is created.
```
> heketi-cli volume create --size=10 --clusters=042e3eb4b386b086c17d9d947e8ba885
10GiB volume created for use by master nodes for shared audit log (mounted at /var/lib/icp/audit:
Name: vol_de785f066ce0e0ce86c39c5fb920682c
Size: 10
Volume Id: de785f066ce0e0ce86c39c5fb920682c
Cluster Id: 042e3eb4b386b086c17d9d947e8ba885
Mount: 172.16.20.17:vol_de785f066ce0e0ce86c39c5fb920682c
Mount Options: backup-volfile-servers=172.16.20.15,172.16.20.16
Durability Type: replicate
Distributed+Replica: 3
```

- Make note of the mountable volume host and name. That is what is used in the mount command and the entry in `/etc/fstab` on each of the master nodes. In the above example it is: `172.16.20.17:vol_de785f066ce0e0ce86c39c5fb920682c` You can replace the IP address with an actual hostname if you have an entry in DNS or `/etc/hosts` on the master nodes for the GlusterFS servers.

- Mount the volume on each master node (Note the colon used to separate the backup servers rather than a comma.)
```
> mount -t glusterfs -o backup-volfile-servers=gluster01.xxx.yyy:gluster02.yyy.zzz gluster03.yyy.zzz:vol_de785f066ce0e0ce86c39c5fb920682c /var/lib/icp/audit
```
- Add a line to `/etc/fstab`
```
gluster03.xxx.yyy:vol_de785f066ce0e0ce86c39c5fb920682c /var/lib/icp/audit glusterfs defaults,_netdev,backup-volfile-servers=gluster01.yyy.zzz:gluster02.yyy.zzz 0 0
```

- Create a volume for the master docker registry.  In this example a 50GB volume is created.
```
> heketi-cli volume create --size=50 --clusters=042e3eb4b386b086c17d9d947e8ba885
Name: vol_ccdb21cfd1e83cf9c3299207f66fb705
Size: 50
Volume Id: ccdb21cfd1e83cf9c3299207f66fb705
Cluster Id: 042e3eb4b386b086c17d9d947e8ba885
Mount: 172.16.20.17:vol_ccdb21cfd1e83cf9c3299207f66fb705
Mount Options: backup-volfile-servers=172.16.20.15,172.16.20.16
Durability Type: replicate
Distributed+Replica: 3
```

- Mount the volume on each master node (Note the colon used to separate the backup servers rather than a comma.)
```
> mount -t glusterfs -o backup-volfile-servers=gluster01.xxx.yyy:gluster02.yyy.zzz gluster03.yyy.zzz:vol_ccdb21cfd1e83cf9c3299207f66fb705 /var/lib/registry
```

- Add a line to `/etc/fstab`
```
gluster03.xxx.yyy:vol_ccdb21cfd1e83cf9c3299207f66fb705 /var/lib/registry glusterfs defaults,_netdev,backup-volfile-servers=gluster01.yyy.zzz:gluster02.yyy.zzz 0 0
```

# Monitoring and alerting

GlusterFS monitoring and alerting is beyond the scope of this document.  Obviously, it is critical to monitor the storage utilization of the disks assigned to the GlusterFS servers.

Adding additional disks to a collection of GlusterFS servers is fortunately very easy.

Some topics for consideration:

- If glusterfs does thin provisioning, how does that impact the alerting regarding free space?  

- What happens to running pods that may need space when some new deployment hits GlusterFS that exhausts its free space?
  - The request for space by the running pods fails.  How a given pod behaves when it is out of storage space is application dependent.

- What happens if a new deployment needs more space than what is available?
  - The deployment fails with an out of space error on the request for a storage volume.
