IBM Cloud Private System Requirements Notes
=================================================
# Introduction

This document provides a realistic summary of system requirements for the various nodes in an ICP cluster.  

As an expedient you can create one machine that meets the maximum requirements of the management nodes and clone it.

Specifying the worker node resource requirements is obviously much more of an "it depends" endeavor.  The worker node requirements shown in this document are merely a suggestion.  More precise worker node requirements can only be determined based on the workloads to be run.

# Summary of ICP development environment system requirements (low performance)

Suggested ICP development environment deployment resource allocations are described in the table below.

*NOTE:* Consideration may be given to deploying the development environment with a separate disk for Docker to meet higher performance requirements.  If so see the next section.

| Machine Role       | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB)|
|--------------------|:------:|-------------:|-------------:|-----------------------------:|
|   Boot/Master      | 1      |  4           |  16          |  1 x 280                   |
|   Proxy            | 1      |  2           |  8           |  1 x 230                   |
|   Management       | 1      |  4           |  16          |  1 x 280                   |
|   VA               | 1      |  4           |  16          |  1 x 500                   |
|   Worker           | 2 or 3 |  2           |  8           |  1 x 200                   |
|   NFS Server       | 1      |  2           |  8           |  1 x 200                   |

- Management = Node that is used to run ELK stack, Prometheus, Grafana and other monitoring tools
- VA = Vulnerability Advisor - security scans of images; optional if not of interest; not usually part of a development cluster
- NFS server is used for application shared storage.  Disk needs to be sized appropriately.
- All disks can be thin-provisioned.

# Summary of ICP development system requirements (high performance)

Suggested ICP high performance development environment deployment resource allocations are described below.

*NOTE:* What is usually treated as a typical development environment would not need to deploy Docker using a separate disk.  However, for maximum performance and stable operation, Docker needs a separate disk.  For ICP a 100 GB disk is typically used to start.

| Machine Role       | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB)|
|--------------------|:------:|-------------:|-------------:|-----------------------------:|
|   Boot/Master      | 1      |  4           |  16          |  1 x 180, 1x100              |
|   Proxy            | 1      |  2           |  8           |  1 x 130, 1x100              |
|   Management       | 1      |  4           |  16          |  1 x 180, 1x100              |
|   VA               | 1      |  4           |  16          |  1 x 400, 1x100              |
|   Worker           | 2 or 3 |  2           |  8           |  1 x 100, 1x100              |
|   NFS Server       | 1      |  2           |  8           |  1 x 200                     |

- Management = Node that is used to run ELK stack, Prometheus, Grafana and other monitoring tools
- VA = Vulnerability Advisor - security scans of images; optional if not of interest; not usually part of a development cluster
- NFS server is used for application shared storage.  Disk needs to be sized appropriately.
- All disks can be thin-provisioned.


# Summary of production system requirements

Suggested ICP production deployment resource allocations are described in the table below.

| Machine Role     | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB) |
|------------------|:------:|-------------:|-------------:|------------------------------:|
|   Master         | 3 or 5 |  8           |  32          |  1 x 280  (1 x 290 if VA enabled) |
|   Proxy          |   3    |  2           |   4          |  1 x 230  (1 x 240 if VA enabled) |
|   Management     | 2 or 3 |  8           |  32          |  1 x 280  (1 x 290 if VA enabled) |
|   Vulnerability Advisor   |  3  |  8     |  32          |  1 x 500                          |
|   Worker         |  5+    |  4           |  32          |  1 x 200  (1 x 210 if VA enabled) |
|   GlusterFS      |  3+    |  4           |  16          |  1 x 40 (/dev/sda)<br/>1 x 256 (/dev/sdb)<br/>1 x 256 (/dev/sdc) |

# File system sizings

See the ICP 2.1.0.3 Knowledge Center [Hardware requirements and recommendations](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.2/supported_system_config/hardware_reqs.html) (TBD - Update link for 2.1.0.3)

*NOTE:* For a production deployment, Docker must be provided with a separate disk (raw block storage) which it manages. It is typical to start with a 100 GB disk.  It can be thin provisioned.

*NOTE:* For a production VM, be sure to use Logical Volume Manager (LVM) for all file systems other than those that require a physical partition, e.g., `/boot`, swap.

**ICP Master** and **ICP Management** nodes suggested disk partitioning (280 GB disk).  For master and management nodes we recommend that `/var` be at least 60 GB which is larger than what is specified in the ICP Knowledge Center documentation.

*NOTE:* ICP 2.1.0.3 moves to using `/var` instead of `/var` and `/opt`.  The tables below reflect disk sizings as of ICP 2.1.0.2.

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    20         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     8         |
|   var                     |   /var            |    70         |
|   tmp                     |   /tmp            |    50         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |   120         |

**ICP Vulnerbility Advisor** nodes disk partitioning (500 GB disk) For the VA nodes we recommend that `/var` be 300 GB.

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |     20        |
|   boot                    |   /boot           |       256 MB  |
|   swap                    |                   |      8        |
|   var                     |   /var            |    300        |
|   tmp                     |   /tmp            |     50        |
|   home                    |   /home           |     10        |
|   opt                     |   /opt            |    110        |

**ICP Proxy** node suggested disk partitioning (230 GB disk).

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    20         |
|   boot                    |   /boot           |      256 MB   |
|   swap                    |                   |     4         |
|   var                     |   /var            |    70         |
|   tmp                     |   /tmp            |    10         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |   120         |

**ICP Worker** node suggested disk partitioning (200 GB disk)

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    20         |
|   boot                    |   /boot           |   256 MB      |
|   swap                    |                   |     4         |
|   var                     |   /var            |    50         |
|   tmp                     |   /tmp            |    20         |
|   home                    |   /home           |    10         |
|   opt                     |   /opt            |   100         |

*NOTE:* Lack of file system space particularly in `/var` is a common problem during the installation and upgrade/update of ICP.  Particularly on master and management nodes, the `/var/lib/docker` directory can consume 40 GB to 50 GB.  The `/var/lib/kubelet` directory typically consumes ~10 GB.
