# Create a logical volume and XFS file system

These instructions are based on the Docker documentation, [Configure Direct-LVM Mode Manually](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)

A better explanation of creating a thin provisioned logical volume is here:
[Setup Thin Provisioning Volumes in Logical Volume Management (LVM) Part IV](https://www.tecmint.com/setup-thin-provisioning-volumes-in-lvm/)

Also see Red Hat documentation [The XFS File System](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/ch-xfs)

## Create an LVM volume

- Partition the disk using `fdisk`

- Create a physical volume

- Create a volume group named `vg_nfs`

- Create a logical volume that uses all of the free space in the volume group.
```
lvcreate -l 100%FREE -n lv_nfs vg_nfs
```

## Create an LVM thin provisioned volume

*NOTE:* It is assumed a block device has been defined, i.e., a disk partition is available to create a physical volume. In this example the block device was a 100 GB disk with one partition: `/dev/sdb1`.

- Create a physical volume.
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

- Create a `vg_docker` volume group.  (The name of the volume group is up to you.)
```
> vgcreate vg_docker /dev/sdb1
  Volume group "vg_docker" successfully created
```

The volume group can be viewed with `vgdisplay`.

- Create two logical volumes in the volume group: `lv_thindocker` and `lv_thindockermeta`.  (Again, you can use a different naming scheme.)

- Create the "thin pool" logical volume consuming 95% of `vg_docker`.
```
> lvcreate --wipesignatures y -n lv_thindocker vg_docker -l 95%VG
  Logical volume "lv_thindocker" created.
```
- Create the "thin pool metadata" logical volume that is only 1% of `vg_docker`.
```
> lvcreate --wipesignatures y -n lv_thindockermeta vg_docker -l 1%VG
  Logical volume "lv_thindockermeta" created.
```

The logical volumes can be viewed using `lvdisplay -S "vgname=vg_docker"`. (Use your volume group name in the selector if it is not `vg_docker`.)  (The `-S` option is convenient to limit the output of `lvdisplay` to only the logical volumes you are interested in.)

- Now the logical volumes need to be converted to a thin pool and a storage location for the thin pool metadata.

```
> lvconvert -y --zero n -c 512K --thinpool vg_docker/lv_thindocker --poolmetadata vg_docker/lv_thindockermeta
  Thin pool volume with chunk size 512.00 KiB can address at most 126.50 TiB of data.
  WARNING: Converting vg_docker/lv_thindocker and vg_docker/lv_thindockermeta to thin pool's data and metadata volumes with metadata wiping.
  THIS WILL DESTROY CONTENT OF LOGICAL VOLUME (filesystem etc.)
  Converted vg_docker/lv_thindocker and vg_docker/lv_thindockermeta to thin pool.
```

- Configure autoextension of thin pools via an lvm profile.
```
> vi /etc/lvm/profile/docker-thinpool.profile
```

The content of `docker-thinpool.profile`:  (comments optional)
```
# lvm will attempt to autoextend vg_docker/lv_thindocker
# When docker disk usage reaches 80%, lvm will attempt to add 20% more capacity.
activation {
  thin_pool_autoextend_threshold=80
  thin_pool_autoextend_percent=20
}

```

- Associate the `docker-thinpool.profile` with the `vg_docker/lv_thindocker` logical volume:
```
> lvchange --metadataprofile docker-thinpool vg_docker/lv_thindocker
  Logical volume vg_docker/lv_thindocker changed.
```

- Enable monitoring for logical volumes on the VM. Without this step, automatic extension does not occur, even in the presence of the LVM profile.
```
> lvs -o+seg_monitor
  LV          VG                Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert Monitor  
  ... (other logical volumes listed here)                                                              
  lv_thindocker vg_docker         twi-a-t--- <95.00g             0.00   0.01                             monitored
```

- Create the XFS file system.  *TBD* Need more specific details here.  This is just a sample to make sure `d_type` is enabled.  By default on RHEL/CentOS the d_type is not enabled for XFS file systems.

```
mkfs.xfs -n ftype=1 /dev/vg_docker/lv_thindocker
```

## Docker has not been installed

If Docker has not been running on the machine where you are have created the dedicated drive then you can go ahead and create the `/var/lib/docker` mount point and mount the volume.

- (Docker not yet installed) Create a mount point for `/var/lib/docker`:
```
mkdir -p /var/lib/docker
mount /dev/vg_docker/lv_thindocker /var/lib/docker
```

- Use `xfs_info /var/lib/docker` to confirm that the file system for `/var/lib/docker` is `xfs` with `ftype=1` (which implies `d_type=true`).

When docker is installed it should be configured to use the `overlay2` storage driver.

- Add a line to `/etc/fstab` to mount the file system at boot time.
```
/dev/mapper/vg_docker-lv_thindocker /var/lib/docker   xfs defaults 0 0
```

## Docker has been installed and running

If Docker has been, or is running currently, then take the following steps:

- If Kubernetes is involved, then stop kubelet to avoid complaints from it  about docker not running that fill up the `systemd` journal.
```
systemctl stop kubelet
```

- Stop docker: `systemctl stop docker`

- Make an archive of `/var/lib/docker`:
```
tar -zcvf /tmp/dockerbackup.tgz /var/lib/docker
```
The above command assumes there is enough room in `/tmp` for the backup archive.

- Delete `/var/lib/docker` content:
```
rm -rf /var/lib/docker/*
```

- Mount the file system:
```
mount /dev/vg_docker/lv_thindocker /var/lib/docker
```

- Add a line to `/etc/fstab` to mount the file system at boot time.
```
/dev/mapper/vg_docker-lv_thindocker /var/lib/docker   xfs defaults 0 0
```

- Restore the docker backup archive
```
mv /tmp/dockerbackup.tgz /var/lib
tar -zxvf dockerbackup.tgz
```

- Assuming you are using RHEL 7.4 or newer you want to configure Docker to use the `overlay2` storage driver.  You can set that in the command line arguments in the `docker.service` file.  Or you can set it in the `daemon.json` file in `/etc/docker`.

- Edit `/usr/lib/systemd/system/docker.service`.  The `ExecStart` line should look like:
```
 ExecStart=/usr/bin/dockerd --log-opt max-size=50m --log-opt max-file=10 --storage-driver=overlay2
```

- Start `docker` and `kubelet`
```
systemctl start docker
systemctl start kubelet
```
