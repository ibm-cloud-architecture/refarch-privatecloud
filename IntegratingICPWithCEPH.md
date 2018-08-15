### Integrating ICP with CEPH

Starting with version 2.1.0.3, IBM Cloud Private supports dynamic storage provisioning using Ceph, code name "rook".

Doing so requires an existing CEPH infrastructure.  This document will walk through installing Ceph and integrating it with ICP for dynamic storage provisioning.

Ceph is short for "cephalopod", a class of mollusks of which the octopus is a member.  The octopus is used as the logo for Ceph and this name was chosen because the parallel processing nature of both the octopus and the software.

CEPH requires physical block devices for its storage.  You can use separate partitions as your target devices, but in this document we will use raw block devices spanning a number of physical hosts.

Management nodes should not run on the same physical nodes as storage nodes, so to implement this solution, you should use at least two servers (or VMs), one for hosting management nodes and one for hosting storage nodes.

In a highly available environment, it is recommended to run three management nodes and at least three storage nodes so that it can handle the loss of a node.

In this document we will use ubuntu as our host operating system.

Our environment will consist of three management nodes and three storage nodes.

Each storage node has two available raw disks.  The operating system is installed on /dev/sda and /dev/sdb and /dev/sdc are available raw devices.

The hosts are named node1 - node6, respectively, and node1 will be our admin node.  node2 and node3 will be additional managment nodes for HA and node4 - node6 will be storage nodes.

We will first install Ceph and test creating and mounting a block device.  Then we will integrate with ICP.

## Prepare for Ceph installation

# Download and install ceph-deploy
1. Add the release Key

   ```
   wget -q -O- 'https://download.ceph.com/keys/release.asc' | sudo apt-key add -
   ```

2. Add the CEPH packages to your repository

  ```
  echo deb https://download.ceph.com/debian-{ceph-stable-release}/ $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/ceph.list
  ```

3. Update and install

  ```
  apt-get update
  apt-get install -y ceph-deploy
  ```

# Create a user and configure passwordless SSH and sudo
1. Create a `ceph-deploy` user on all nodes.
  ```
  sudo useradd -m -s /bin/bash -c "Ceph deploy user" ceph-deploy
  echo "ceph-deploy:Passw0rd!" | sudo -S chpasswd
  ```
2. Add ceph-deploy user to passwordless sudo
  ```
    echo 'ceph-deploy   ALL=(root) NOPASSWD:ALL' |sudo EDITOR='tee -a' visudo
  ```

3. Enable running Ceph commands easier on other nodes
  Login as you ceph-deploy user and create the following file at ~/.ssh/config

  ```
  Host node1
   Hostname node1
   User ceph-deploy
Host node2
   Hostname node2
   User ceph-deploy
Host node3
   Hostname node3
   User ceph-deploy
Host node4
    Hostname node4
    User ceph-deploy
 Host node5
    Hostname node5
    User ceph-deploy
 Host node6
    Hostname node6
    User ceph-deploy
  ```

4. Enable passwordless SSH for the ceph-deploy user from the admin node to all other nodes.  Execute these commands as the the ceph-deploy user.  Accept all defaults.

  ```
  ssh-keygen -t rsa -P ''
  ```

  This will create ssh public and private keys in ~/.ssh .  Copy the keys to all other nodes:

  ```
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node1
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node2
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node3
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node4
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node5
  ssh-copy-id -i ~/.ssh/id_rsa ceph-deploy@node6
  ```

  It will ask you for the password for the ceph-deploy user, answer with the password you created when you created the user.  When this is complete you should be able to execute `ssh ceph-deploy@node1` and get from the ceph-deploy user on the admin host to the remote host without providing a password.

  _IMPORTANT:_ Make sure you copy the ID back to the local node (node1) as well so the process can ssh back to itself.

# Install ntp on all nodes
```
apt-get install -y ntp
```
If there is a local ntp server on your network, update /etc/ntp.conf with your local pool server and restart ntp.

# Install python on all nodes
```
apt-get install -y python
```

## Deploy Ceph
Execute these commands as the ceph-deploy user on the admin node.

1. Create the cluster
From the ceph-deploy user's home directory:
```
mkdir mycluster
cd mycluster
ceph-deploy new node1
```

2. Install Ceph on all nodes
```
ceph-deploy install node1 node2 node3 node4 node5 node6
```

3. Deploy the initial monitor and gather the keys
```
ceph-deploy mon create-initial
```

4. Copy the admin config files to all nodes
```
ceph-deploy admin node1 node2 node3 node4 node5 node6
```

5. Deploy a manager node
```
ceph-deploy mgr create node1
```

6. Deploy storage nodes

The data should be the raw device name of an unused raw device installed in the host.  The final parameter is the hostname.  Execute this command once for every raw device and host in the environment.
```
ceph-deploy osd create --data /dev/sdb node4
ceph-deploy osd create --data /dev/sdc node4

ceph-deploy osd create --data /dev/sdb node5
ceph-deploy osd create --data /dev/sdc node5

ceph-deploy osd create --data /dev/sdb node6
ceph-deploy osd create --data /dev/sdc node6
```

7. Install a metadata server
```
ceph-deploy mds create node1
```

8. Deploy the object gateway (S3/Swift)
```
ceph-deploy rgw create node1
```

9. Deploy mgr to standby nodes for HA
On the admin node edit /home/ceph-deploy/mycluster/ceph.conf file and update the mon_initial_members, mon_host, and public_network values to reflect the additional nodes.  The resulting file should look something like this:

```
[global]
fsid = 264349d2-8eb0-4fb3-9992-bbef4c2759cc
mon_initial_members = node1,node2,node3
mon_host = 10.10.2.1,10.10.2.2,10.10.2.3
public_network = 10.10.0.0/16
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
```
Then deploy the new nodes:
```
ceph-deploy --overwrite-conf mon add node2
ceph-deploy --overwrite-conf mon add node3
```

10. Check the status of your cluster
```
sudo ceph -s
```
The result should look something like this:
```
  cluster:
    id:     2fdde238-b426-4042-8cf3-6fc9a151cb9b
    health: HEALTH_OK

  services:
    mon: 3 daemons, quorum node1,node2,node3
    mgr: node1(active), standbys: node2, node3
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active

  data:
    pools:   4 pools, 1280 pgs
    objects: 221  objects, 1.2 KiB
    usage:   54 GiB used, 11 TiB / 11 TiB avail
    pgs:     1280 active+clean
```
You should see HEALTH_OK.  If not, look for your error message in the troubleshooting section below.

The likelihood is that your health message will say something like:

```
health: HEALTH_WARN
   too few PGs per OSD (3 < min 30)
```
If you do not see this error, you can skip this section until you do see it (and you will).

A PG is a "placement group" and governs how data is stored in your environment.  A full discussion of how this works is beyond the scope of this document, but resolving the warning can be done without knowing all of the details.

For more information on this number see:
* http://docs.ceph.com/docs/giant/rados/operations/placement-groups/
* https://stackoverflow.com/questions/39589696/ceph-too-many-pgs-per-osd-all-you-need-to-know

There are two numbers that are important to modify to resolve this issue, the first is the PGs and the second is the PGPs.  The PG is the number of placement groups available and the PGP is the number that are applied to your implementation.  Any time you increase the PGs you should also increase the number of PGPs.

The documentation recommends using PG numbers with powers of 2 (2, 4, 16, 32, 64, 128,...). The simple solution to this issue is to start with a smaller number, apply it and see what the status says.  If it is still too small, continue to apply ever larger powers of 2 until the warning goes away.

To change the number of PGs and PGPs, us the following command against every pool in your environment.

To see the pools in your environment use the command:

```
sudo ceph osd lspools
```

Which should result in a list that looks something like this:

```
1 .rgw.root
2 default.rgw.control
3 default.rgw.meta
4 default.rgw.log
```

For each pool in the list execute:

```
sudo ceph osd pool set [pool name] pg_num 64
```

Example:

```
sudo ceph osd pool set .rgw.root pg_num 32
sudo ceph osd pool set .rgw.root pgp_num 32
```
Then check your status and see if you need to raise it further.  Continue increasing the number at the end of that command by powers of 2 until the warning goes away.

Once you have a healthy cluster you can start using your new storage.

The following command will show you all of your storage devices and their status.

_Note:_ OSD = Object Storage Daemon

```
sudo ceph osd tree
```
The result should look something like this:
```
-1       192.85042 root default                           
-3        87.32849     host node4                         
 0   ssd   3.63869         osd.0      up  1.00000 1.00000
 1   ssd   3.63869         osd.1      up  1.00000 1.00000
 -5        47.30293     host node5                         
 24   ssd   3.63869         osd.2     up  1.00000 1.00000
 25   ssd   3.63869         osd.3     up  1.00000 1.00000
 -7        14.55475     host node6                         
 37   ssd   3.63869         osd.4     up  1.00000 1.00000
 38   ssd   3.63869         osd.5     up  1.00000 1.00000
```
## Create and mount a block device
Block devices are the most commonly used types of storage provisioned by Ceph users.  Creating and using them is relatively easy once your environment is up and running.

Block devices are known as rbd devices (Rados Block Device).  When you create a new block device and attach it to your filesystem it will show up as /dev/rbd0, /eev/rbd1, etc.

Before you can create a block device you need to create a new pool in which they can be stored.
```
sudo ceph osd pool create rbd 128 128
```
_NOTE:_ The two numbers at the end of this command are the PG and PGP for this pool.  As a start, you should use the same values you used to get the health warning error to go away.  These values may need to be changed based on the size of your environment and number of pools as per the above discussion.

Once your pool has been created you can then create a new image in that pool.  An image is block storage on which you can create a filesystem and is analogous to a virtual disk.

```
sudo rbd map myimage --size 10240 --image-feature layering
```

This command will create a new 10GB disk named "myimage" suitable for mounting on your filesystem.  The --size parameter is in MB.

Now, ssh to the machine on which you want to mount this image.

Before the storage can be mounted you must install the Ceph client on the target machine.

```
sudo apt-get install -y ceph-common ceph-fuse
```

Create yourself a mount point:

```
sudo mkdir /mnt/myimage

sudo rbd map myimage --name client.admin
```

myimage is the name of the image you created previously everything else should be exactly as shown.

The result of this command is a new device named /dev/rbd0.

Next, put a filesystem on your new block device :

```
sudo mkfs.ext4 -m0 /dev/rbd0
```
... and mount your new filesystem at your created mount point:

```
mount /dev/rbd0 /mnt/myimage
```
### Interating ICP with CEPH
... Coming
