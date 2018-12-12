# Installing Docker using the Passport Advantage executable

*WARNING:* For ICP 2.1.0.3 on RHEL, you must install the Docker provided in Passport Advantage for ICP.

*NOTE:* For RHEL 7.4 or later and Docker 17.06 or later, the `overlay2` storage driver is recommended.  On RHEL, when using the `overlay2` storage driver, the file system used for `/var/lib/docker` must be `xfs`. The `devicemapper` storage driver with `direct-lvm` mode is another option, but not recommended.  See the Docker documentation listed below.

*NOTE:* When reading the Docker documentation, be careful to note the Linux distribution and versions.  Sometimes the Docker documentation does not differentiate Linux distributions and it usually only refers to CentOS.  A more definitive source is the Red Hat documentation for Docker.

See ICP 2.1.0.3 Knowledge Center documentation - [Setting up Docker for IBM Cloud Private](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/installing/install_docker.html)

See the Docker documentation:
- [Docker storage drivers](https://docs.docker.com/storage/storagedriver/select-storage-driver/)
- [Architecture and storage drivers](https://docs.docker.com/install/linux/docker-ee/rhel/#architectures-and-storage-drivers)
- [Use the OverlayFS storage driver](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)

Documentation from Red Hat:
- [OverlayFS support](https://access.redhat.com/solutions/2908851)
- [File Systems](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/7.4_release_notes/technology_previews_file_systems)

## Configuration of Docker disk using devicemapper storage driver

These instructions are based on the Docker documentation, [Configure Direct-LVM Mode Manually](https://docs.docker.com/storage/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)

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

- Create two logical volumes in the volume group: `lv_thinpool` and `lv_thinpoolmeta`.  (Again, you can use a different naming scheme.)

- Create the "thin pool" logical volume consuming 95% of `vg_docker`.
```
> lvcreate --wipesignatures y -n lv_thinpool vg_docker -l 95%VG
  Logical volume "lv_thinpool" created.
```
- Create the "thin pool metadata" logical volume that is only 1% of `vg_docker`.
```
> lvcreate --wipesignatures y -n lv_thinpoolmeta vg_docker -l 1%VG
  Logical volume "lv_thinpoolmeta" created.
```

The logical volumes can be viewed using `lvdisplay -S "vgname=vg_docker"`. (Use your volume group name in the selector if it is not `vg_docker`.)  (The `-S` option is convenient to limit the output of `lvdisplay` to only the logical volumes you are interested in.)

- Now the logical volumes need to be converted to a thin pool and a storage location for the thin pool metadata.

```
> lvconvert -y --zero n -c 512K --thinpool vg_docker/lv_thinpool --poolmetadata vg_docker/lv_thinpoolmeta
  Thin pool volume with chunk size 512.00 KiB can address at most 126.50 TiB of data.
  WARNING: Converting vg_docker/lv_thinpool and vg_docker/lv_thinpoolmeta to thin pool's data and metadata volumes with metadata wiping.
  THIS WILL DESTROY CONTENT OF LOGICAL VOLUME (filesystem etc.)
  Converted vg_docker/lv_thinpool and vg_docker/lv_thinpoolmeta to thin pool.
```

- Configure autoextension of thin pools via an lvm profile.
```
> vi /etc/lvm/profile/docker-thinpool.profile
```

The content of `docker-thinpool.profile`:  (comments optional)
```
# lvm will attempt to autoextend vg_docker/lv_thinpool
# When docker disk usage reaches 80%, lvm will attempt to add 20% more capacity.
activation {
  thin_pool_autoextend_threshold=80
  thin_pool_autoextend_percent=20
}

```

- Associate the `docker-thinpool.profile` with the `vg_docker/lv_thinpool` logical volume:
```
> lvchange --metadataprofile docker-thinpool vg_docker/lv_thinpool
  Logical volume vg_docker/lv_thinpool changed.
```

- Enable monitoring for logical volumes on the VM. Without this step, automatic extension does not occur, even in the presence of the LVM profile.
```
> lvs -o+seg_monitor
  LV          VG                Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert Monitor  
  ... (other logical volumes listed here)                                                              
  lv_thinpool vg_docker         twi-a-t--- <95.00g             0.00   0.01                             monitored
```

- If `docker` has been running on the VM, then make a backup of `/var/lib/docker`.  The backup will provide a clean recovery should something go wrong in the following steps.
- If `kubelet` is running, it is a good idea to stop it. When `docker` is not running `kubelet` tends to fill up the `systemd` journal with errors that will mask problems with `docker`, should there be any.

```
> systemctl stop kubelet
> systemctl stop docker
> mkdir /var/lib/docker.bak
> mv /var/lib/docker/* /var/lib/docker.bak
```

- Edit `/etc/docker/daemon.json` and the content needs to include the options for the `devicemapper` storage driver:
```
{
    "storage-driver": "devicemapper",
    "storage-opts": [
      "dm.thinpooldev=/dev/mapper/vg_docker-lv_thinpool",
      "dm.use_deferred_removal=true",
      "dm.use_deferred_deletion=true"
    ]
}
```
*NOTE:* The value of the `dm.thinpooldev` attribute needs to match what is in the `/dev/mapper` directory for your docker volume group and thin pool logical volume.  In this example, that is `vg_docker-lv_thinpool`.

- Start docker:
```
> systemctl start docker
```

- Use `systemctl status docker` and `docker info` to make sure docker is running correctly with the `devicemapper` storage driver and using the "thin pool" you defined.  The two attributes to check in the `docker info` output are: `Storage Driver` and `Pool Name` under the storage driver details.
```
Storage Driver: devicemapper
 Pool Name: vg_docker-lv_thinpool
```

- If all is well, then delete the docker directory backup: `/var/lib/docker.bak`.

## Things that can go wrong disk configuration

- For debugging information if docker doesn't start, use `journalctl` and redirect to a file.  Long lines may get cut off from the output when viewing directly in a shell window.
```
journalctl -xe > journalctl.log
```

- Docker options defined in both the `docker.service` file and in the `daemon.json` file.
`--storagedriver` flag in `/etc/systemd/system/multi-user.target.wants/docker.service` duplicates the `storagedriver` attribute in `/etc/docker/daemon.json`.  Drop it in the `docker.service` file.

## Install docker

- Install a pre-req: `yum -y install policycoreutils-python`
- Make `icp-docker-17.12.1_x86_64.bin` executable: `chmod +x icp-docker-17.12.1_x86_64.bin`
- Run the install: `./icp-docker-17.12.1_x86_64.bin --install`

- If you docker is already installed then use the `--update` option to install a newer version of `docker`: `./icp-docker-17.12.1_x86_64.bin --update`
