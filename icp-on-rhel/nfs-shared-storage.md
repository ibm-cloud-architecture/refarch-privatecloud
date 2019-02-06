# Using NFS for file sharing in ICP

NFS is an option for file sharing that is reasonable for ICP sandbox deployments where the expense of setting up a more robust distributed file system such as GlusterFS, Ceph or IBM Spectrum is not justified.  

If NFS is to be used for a production ICP deployment, then it would need to be deployed in a highly available (HA) topology.

The NFS provisioner plugin for dynamic storage allocation is not as mature as other storage providers.  This may be a show-stopper for using NFS as a dynamic storage provider in a production deployment.  The NFS storage provisioner is part of the Kubernetes [External Storage](https://github.com/kubernetes-incubator/external-storage) incubator project.  

[RHEL Configuring the NFS Server](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/nfs-serverconfig)

[RHEL Starting and Stopping the NFS server](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/s1-nfs-start)

An NFS server can share any existing file system.  In a production scenario you would want the NFS server to be using a dedicated file system and very likely dedicated disks.  For sandbox scenarios the NFS server can export a directory on any existing file system.

## Install and configure NFS Server

- The NFS server is installed with `nfs-utils`.

```
yum install -y nfs-utils
```

*NOTE:* The following assumes a a directory created in `/` named `storage`.

- Edit the `/etc/exports` file to export the `/storage` directory.  For simple scenarios `/storage` may not be a dedicated file system.  

Add a line such as the following:
- Ising a wildcard domain name
```
/storage *.my.subnet.local(rw,sync,no_root_squash)
```
- Using a network CIDR:
```
/storage 172.16.52.0/24(rw,sync,no_root_squash)
```

The man page on `exports` provides all the options and ways that a file system can be exported to some collection of clients.  Wild card characters `*` and `?` may be used to define a collection of hosts.  In practice, the host name pattern would be such that only hosts in the ICP cluster could access the share.

- Start and enable `nfs-server`
```
systemctl enable nfs-server --now
```

## NFS client configuration

- Install `nfs-utils` on all other machines in the cluster.  This will provide all machines what they need to mount the shared volume.

TBD - need a description of `/etc/fstab` entries; mount command.

If the `ansible` `mount` module is used to configure the NFS clients, everything gets configured including the immediate mount and the proper entry in `/etc/fstab`.  See the `mount-nfs-share.yaml` playbook in `playbooks/nfs`.

# Using a dedicated disk and file system

The remaining sections of this document describe how to configure a raw disk to be a file system for NFS export.  A production NFS server would used dedicated disks for the file systems that it exports.

## Adding and formatting a disk

Many articles can be found with an Internet search on the topic of logical volume management.  A particularly good one is [How to Manage and Create LVM Using vgcreate, lvcreate and lvextend Commands – Part 11](https://www.tecmint.com/manage-and-create-lvm-parition-using-vgcreate-lvcreate-and-lvextend/)

For creating an xfs file system see the RHEL v7 documentation [The XFS File System](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-xfs)

For a sandbox ICP deployment, you can put the file share most any place as long as it is a machine that is intended to be running more-or-less all the time.  In this example we added a disk to the proxy machine.  That would not be a good choice for a production deployment using NFS.  

As mentioned above, a production deployment of NFS would use dedicated VMs for the NFS server primary and secondary.

- Power off the VM.
- Added a 100 GB thin-provisioned disk through vCenter console.
- Power on the VM.
- Device is /dev/sdb (in this example)
- Use Linux commands to turn the disk into usable file system.
```
> fdisk /dev/sdb   # interactive fdisk
> n - to add a new partition
> p - primary partition (default)
> 1 - partition number (defaut)
> 2048 - first sector (default)
> 209715199 - last sector (default) (The whole disk.)
> w - write table to disk and exit

Replay of the above:
Command (m for help): n
Partition type:
   p   primary (0 primary, 0 extended, 4 free)
   e   extended
Select (default p):  
Using default response p
Partition number (1-4, default 1):
First sector (2048-209715199, default 2048):
Using default value 2048
Last sector, +sectors or +size{K,M,G} (2048-209715199, default 209715199):
Using default value 209715199
Partition 1 of type Linux and of size 100 GiB is set
Command (m for help): w
The partition table has been altered!

Calling ioctl() to re-read partition table.
Syncing disks.
```
- At this point the disk has a partition defined.  Use `lsblk` to see the partitions.  In this case the partition shows up as `sdb1`.  You may have to use `lsblk | less` if the original disk is in use for docker containers that are running on the VM.

- Now create a physical volume.
```
> pvcreate /dev/sdb1
  Physical volume "/dev/sdb1" successfully created.
```
The physical volume can be viewed with `pvdisplay`.
```
"/dev/sdb1" is a new physical volume of "<100.00 GiB"
--- NEW Physical volume ---
PV Name               /dev/sdb1
VG Name               
PV Size               <100.00 GiB
Allocatable           NO
PE Size               0   
Total PE              0
Free PE               0
Allocated PE          0
PV UUID               rsN2fY-pJzz-PoUd-0NwS-yiPz-F0Oa-x5Sj00
```
- Create a volume group with the `vgcreate` command.
```
vgcreate vg_share /dev/sdb1
  Volume group "vg_share" successfully created
```
- Now create a new logical volume with `lvcreate`.  In this example all the space available to the `vg_share` volume group is to be allocated to the logical volume named `lv_share`.
```
lvcreate -n lv_share -l 100%FREE vg_share
  Logical volume "lv_share" created.
```
- View the logical volume with `lvdisplay | less`
```
--- Logical volume ---
 LV Path                /dev/vg_share/lv_share
 LV Name                lv_share
 VG Name                vg_share
 LV UUID                aG2Eke-ypaH-cwro-bSIp-R73i-9jh4-9Y1JLK
 LV Write Access        read/write
 LV Creation host, time r75-master01.csplab.local, 2018-04-20 17:15:11 -0400
 LV Status              available
 # open                 0
 LV Size                <100.00 GiB
 Current LE             25599
 Segments               1
 Allocation             inherit
 Read ahead sectors     auto
 - currently set to     8192
 Block device           253:71
```

- At this point an XFS file system may be created on top of the new logical volume.
```
> mkfs.xfs /dev/vg_share/lv_share
meta-data=/dev/vg_share/lv_share isize=512    agcount=4, agsize=6553344 blks
         =                       sectsz=512   attr=2, projid32bit=1
         =                       crc=1        finobt=0, sparse=0
data     =                       bsize=4096   blocks=26213376, imaxpct=25
         =                       sunit=0      swidth=0 blks
naming   =version 2              bsize=4096   ascii-ci=0 ftype=1
log      =internal log           bsize=4096   blocks=12799, version=2
         =                       sectsz=512   sunit=0 blks, lazy-count=1
realtime =none                   extsz=4096   blocks=0, rtextents=0
```
- Mount the XFS file system.  In this example the file system is mounted at `/storage`.
```
mkdir /storage
mount /dev/vg_share/lv_share /storage
```
- To view the new file system you can use `df -Th`.  That will show the file system type as well as the size statistics for the new file system.

- Add a line to `/etc/fstab` to mount the file system at boot time.
```
/dev/mapper/vg_share-lv_share             /storage            xfs     defaults        0 0
```

## Install and configure NFS Server

- The NFS server is installed with `nfs-utils`.

```
yum install -y nfs-utils
```

- Edit the `/etc/exports` file to export the `/storage` file system.  Add a line such as the following:
```
/storage *.my.subnet.local(rw,sync,no_root_squash)
```
The man page on `exports` provides all the options and ways that a file system can be exported to some collection of clients.  Wild card characters `*` and `?` may be used to define a collection of hosts.  In practice, the host name pattern would be such that only hosts in the ICP cluster could access the share.

- Start and enable `nfs-server`
```
systemctl enable nfs-server --now
```

- Install `nfs-utils` on all other machines in the cluster.  This will provide all machines what is needed to mount the shared volume.

# Configure a storage class for the NFS shared file system

- TBD: Need to pull together the details for this. See [https://github.com/kubernetes-incubator/external-storage/tree/master/nfs](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs)
