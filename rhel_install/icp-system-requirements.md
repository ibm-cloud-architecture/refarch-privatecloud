IBM Cloud Private System Requirements Notes
=================================================
# Introduction

This document provides a realistic summary of system requirements for the various nodes in an ICP cluster.  

As an expedient you can create one machine that meets the maximum requirements of the management nodes and clone it.

*NOTE:* This document reflects the hardware requirements for ICP v2.1.0.3.  The disk requirements for ICP v2.1.0.3 have changed from ICP v2.1.0.2. With ICP v2.1.0.3 the `/var` file system is used much more heavily because all of the content that was in `/opt` has moved to `/var`.  More details are provided in the body of this document.

Specifying the worker node resource requirements is obviously much more of an "it depends" endeavor.  The worker node requirements shown in this document are merely a suggestion.  More precise worker node requirements can only be determined based on the workloads to be run.

# Summary of ICP development environment system requirements (low performance)

Suggested ICP development environment deployment resource allocations are described in the table below.

*NOTE:* Consideration may be given to deploying the development environment with a separate disk for Docker to meet higher performance requirements.  If so, see the next section.

| Machine Role       | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB)|
|--------------------|:------:|-------------:|-------------:|-----------------------------:|
|   Boot/Master      | 1      |  4           |  16          |  1 x 360                     |
|   Proxy            | 1      |  2           |  8           |  1 x 240                     |
|   Management       | 1      |  4           |  16          |  1 x 340                     |
|   VA               | 1      |  4           |  16          |  1 x 430                     |
|   Worker           | 2 or 3 |  2           |  8           |  1 x 240                     |
|   NFS Server       | 1      |  2           |  8           |  1 x 200 (size appropriately)|

- Management = Node that is used to run ELK stack, Prometheus, Grafana and other monitoring tools
- VA = Vulnerability Advisor - security scans of images; optional if not of interest; not usually part of a development cluster
- NFS server is used for application shared storage.  Disk needs to be sized appropriately.
- All disks can be thin-provisioned.

*NOTE:* The disk sizes in the above table are based on the ICP 2.1.0.3 Knowledge Center, [Hardware requirements and recommendations - Disk space requirements](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/supported_system_config/hardware_reqs.html#disk).

*NOTE:* Additional disk space is added to the totals recommended for the ICP nodes in the ICP 2.1.0.3 KC to allow for separate file systems for `/home` (10 GB) and `/opt` (10 GB).

# Summary of ICP development system requirements (high performance)

Suggested ICP high performance development environment deployment resource allocations are described below.

*NOTE:* What is usually treated as a typical development environment would not need to deploy Docker using a separate disk.  However, for maximum performance and stable operation, Docker needs a separate disk.  For ICP a 100 GB disk is typically used to start.

| Machine Role       | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB)|
|--------------------|:------:|-------------:|-------------:|-----------------------------:|
|   Boot/Master      | 1      |  8           |  32          |  1 x 260, 1 x 100            |
|   Proxy            | 1      |  4           |  16          |  1 x 140, 1 x 100            |
|   Management       | 1      |  8           |  32          |  1 x 240, 1 x 100            |
|   VA               | 1      |  8           |  32          |  1 x 330, 1 x 100            |
|   Worker           | 2 or 3 |  4           |  16          |  1 x 140, 1 x 100            |
|   NFS Server       | 1      |  2           |  8           |  1 x 200 (size appropriately)|

- Management = Node that is used to run ELK stack, Prometheus, Grafana and other monitoring tools
- VA = Vulnerability Advisor - security scans of images; optional if not of interest; not usually part of a development cluster
- Worker nodes need to be sized based on expected load.  The suggested 4 vCPU and 16 GB memory is a starting point.
- NFS server is used for application shared storage.  Disk needs to be sized appropriately.
- All disks can be thin-provisioned.

*NOTE:* The disk sizes in the above table are based on the ICP 2.1.0.3 Knowledge Center, [Hardware requirements and recommendations - Disk space requirements](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/supported_system_config/hardware_reqs.html#disk).

*NOTE:* Additional disk space is added to the totals recommended for the ICP nodes in the ICP 2.1.0.3 KC to allow for separate file systems for `/home` (10 GB) and `/opt` (10 GB).

*NOTE:* For simplicity, swap space size of 8 GB is used for calculating total disk size. For RHEL 7 swap space size guidelines see the chapter on [Swap Space](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/5/html/deployment_guide/ch-swapspace).

# Summary of production system requirements

Suggested ICP production deployment resource allocations are described in the table below.

*NOTE:* For RHEL 7.4 or later, and Docker 17.06 or later, the `overlay2` storage driver can be used on an `xfs` file system.  Older versions of Docker require the `devicemapper` storage driver using the `direct-lvm` mode.  When using `direct-lvm` it is convenient to use a disk dedicated to Docker. The recommended starting disk size is 100 GB.  Hence, the sizes in the storage requirements below.

*NOTE:* ICP 2.1.0.3 ships with Docker 17.12. If you are using RHEL 7.4 or later, it is recommended that the `overlay2` storage-driver is used.  Make sure that option is set in the `config.yaml`.  Or if you install you install Docker independently of the ICP installation, be sure to configure `overlay2` for the storage driver.

For production deployments, particularly those where the ICP nodes will not have access to the Internet, it is recommended that the boot node be a separate VM.  The boot node typically is permitted to have access to the Internet to make it convenient to download software from places like GitHub and DockerHub and other sources of commonly used software.  The boot node can serve as an administrative server for the cluster.

| Machine Role     | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB)     |
|------------------|:------:|-------------:|-------------:|----------------------------------:|
|   Boot           |   1    |  2           |   8          |  1 x 180, 1 x 100                 |
|   Master         | 3 or 5 |  8           |  32          |  1 x 260, 1 x 100                 |
|   Proxy          |   3    |  4           |  16          |  1 x 140, 1 x 100                 |
|   Management     | 2 or 3 |  8           |  32          |  1 x 240, 1 x 100                 |
|   VA             |  3     |  8           |  32          |  1 x 330, 1 x 100                 |
|   Worker         |  5+    |  4           |  16          |  1 x 140, 1 x 100                 |
|   GlusterFS      |  3+    |  4           |  16          |  1 x 50 (/dev/sda)<br/>1 x 256 (/dev/sdb)<br/>1 x 256 (/dev/sdc) |

- Management = Node that is used to run ELK stack, Prometheus, Grafana and other monitoring tools
- VA = Vulnerability Advisor - security scans of images; optional if not of interest; not usually part of a development cluster
- Worker nodes need to be sized based on expected load.  The suggested 4 vCPU and 16 GB memory is a starting point.
- GlusterFS servers are used for application shared storage.  Disk needs to be sized appropriately. The sizes in the table above are a suggested starting point.
- All disks can be thin-provisioned.

*NOTE:* The disk sizes in the above table are based on the ICP 2.1.0.3 Knowledge Center, [Hardware requirements and recommendations - Disk space requirements](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/supported_system_config/hardware_reqs.html#disk).

*NOTE:* Additional disk space is added to the totals recommended for the ICP nodes in the ICP 2.1.0.3 KC to allow for separate file systems for `/home` (10 GB) and `/opt` (10 GB).

*NOTE:* For simplicity and round numbers, swap space size of 10 GB is used for calculating total disk size. For RHEL 7 swap space size guidelines see the chapter on [Swap Space](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/5/html/deployment_guide/ch-swapspace).

# File system sizings

See the ICP 2.1.0.3 Knowledge Center [Hardware requirements and recommendations - Disk space requirements](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/supported_system_config/hardware_reqs.html#disk)

*NOTE:* For a production VM, be sure to use Logical Volume Manager (LVM) for all file systems other than those that require a physical partition, e.g., `/boot`, swap.

*NOTE:* ICP 2.1.0.3 moves to using `/var` instead of `/var` and `/opt`.  The tables below reflect the recommendations for ICP 2.1.0.3.  The docker disk (`disk2` (100 GB) in the tables below) is dedicated to docker. (The sizing for the docker disk is recommended to start at 100 GB.)

**ICP Master** nodes suggested disk1 partitioning:  

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    50         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |   130         |
|   docker                  |   /var/lib/docker |   disk2       |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |    10         |

**ICP Management** nodes suggested disk1 partitioning:  

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    50         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |   110         |
|   docker                  |   /var/lib/docker |   disk2       |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |    10         |


**ICP Vulnerbility Advisor** nodes disk1 partitioning:

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |     50        |
|   boot                    |   /boot           |       256 MB  |
|   swap                    |                   |      8        |
|   var                     |   /var            |    200        |
|   docker                  |   /var/lib/docker |    disk2      |
|   tmp                     |   /tmp            |     50        |
|   home                    |   /home           |     10        |
|   opt                     |   /opt            |     10        |

**ICP Proxy** nodes suggested disk1 partitioning:

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    50         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |    10         |
|   docker                  |   /var/lib/docker |    disk2      |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |    10         |

**ICP Worker** nodes suggested disk1 partitioning:

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    50         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |    10         |
|   docker                  |   /var/lib/docker |    disk2      |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |    10         |

**Boot** nodes suggested disk1 partitioning:

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    50         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |    10         |
|   docker                  |   /var/lib/docker |    disk2      |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |    50*        |

The boot node `/opt` is allocated a suggested 50 GB to allow space for software installation for administrative tools. That may be excessive. It can be adjusted based or specific requirements.
