# Install and configure a GlusterFS server cluster running in Docker

If you are not going to use GlusterFS, then this section can be skipped.

This section describes the steps for installation and configuration of a 3 node GlusterFS server cluster.  The GlusterFS server cluster is not included in the ICP cluster itself in order to keep the GlusterFS servers dedicated to the role of providing a file sharing service.

Heketi is the administrative client for Gluster.  The section, [Install Heketi administration client for Gluster](#Install Heketi administration client for Gluster) desribes the installation and configuration of Heketi.

The instructions in this section describe how to run Gluster from a docker container. Other approaches run Gluster "natively".  

*NOTE:* It is recommended that the GlusterFS server cluster be created prior to the actual installation of ICP.  You may choose to incorporate a GlusterFS cluster after ICP is installed.

A sample resource configuration for the GlusterFS VMs is summarized in the table below.

| Machine Role     | Number |  vCPU/Core   | Memory (GB)  | Storage<br/>Disks x Size (GB) |
|------------------|:------:|-------------:|-------------:|------------------------------:|
|   GlusterFS      |  3+    |  4           |  16          |  1 x 40 (/dev/sda)<br/>1 x 128 (/dev/sdb)<br/>1 x 128 (/dev/sdc) |

- During the VM creation using vCenter, you can add disks when you get to the "machine settings" screen.  At the bottom of the screen there is a "New devices" pull-down menu.  Select "Hard disk" and click the add button. (See figure below.)

![Adding Hard Disk at VM creation](images/09_GlusterServerRHELInstall.png)

![Gluster Server Disks (Sample)](images/10_GlusterDisksAtInstall.png)

- The GlusterFS disks can be thin provisioned.

- You can add disks to an already deployed VM from the vCenter console by opening the "Machine Settings" dialog and adding the disks as described above.

- Only the system disk needs to be partitioned.  Heketi will do all the configuration of the storage drives.

The following table is a summary of the system disk partitioning on a GlusterFS server.

| File System Name          |  Mount Point      |  Size (GB)    |
|:--------------------------|:------------------|--------------:|
|   system (aka root)       |   /               |    32         |
|   boot                    |   /boot           |   256 MB      |
|   swap                    |                   |     8         |

*NOTE:* The remainder of these instructions assume that Ansible is set up on an administrator machine or some machine that can be used for running Ansible command lines.  The Ansible hosts file is assumed to have a group defined named "gluster" with the GlusterFS servers in it.  In the example Ansible command lines, the default Ansible hosts file in `/etc/ansible/hosts` is used.  You may prefer to create a hosts file and pass its path in on the command line with the -i option.

*NOTE:* It is assumed the user running Ansible has passwordless sudo root privileges on the GlusterFS servers.

*NOTE:* In the Ansible commands the -b and --become options are synonyms.  Usually the module or shell command to be executed requires that the user privileges become elevated to root.

*NOTE:* The simplest instructions assume the GlusterFS server VMs have public Internet access to get to the site where Docker can pull the latest GlusterFS image. If that is not the case, we provide alternate steps that assume only that the Ansible control machine has access to the public Internet.

On each GlusterFS server in the GlusterFS cluster:
- Set up yum repository for RHEL
- Update RHEL
- Install NTP, start and enable NTPD
- Install yum-utils (if you want to use yum-config-manager)
- Install bind-utils
- Install Docker, start and enable Docker
- Stop, disable firewalld
- Create an "Ansible user", e.g., icpmaestro and include that user in the wheel group.
- Modify the /etc/sudoers file (`visudo`) to allow the wheel group sudo any command without password.

- Install the latest version of GlusterFS
```
ansible gluster -b -m shell -a "docker pull gluster/gluster-centos:latest"
```

If the GlusterFS VMs cannot get directly to the public Internet, then the following steps can be used to install GlusterFS.  We're assuming your Ansible control machine has Docker installed on it.

- Pull the latest Gluster image on the Ansible control machine; save it; and push it to the GlusterFS server nodes using Ansible. (This step is a substitute for the previous step when the GlusterFS server VMs do not have access to the public Internet.)
```
docker pull gluster/gluster-centos:latest
docker save gluster/gluster-centos:latest | gzip -c > gluster-centos.tar.gz
ansible gluster -b -m copy -a 'src=gluster-centos.tar.gz dest=/tmp/gluster-centos.tar.gz'
ansible gluster -b -m shell -a 'tar -xf /tmp/gluster-centos.tar.gz' -O | docker load'
```
- To check that the gluster image got loaded:
```
$ ansible gluster -b -m shell -a 'docker images'
```

- Create a `/var/lib/heketi` directory on the GlusterFS machines. Gluster mounts are to be persisted in `/var/lib/heketi/fstab` on each host.
```
$ ansible gluster -b -m file -a 'path=/var/lib/heketi state=directory'
```

- Start docker in privileged mode running gluster. (Most of the command below is bind mounting container "volumes" to host directories.) (For details on options used in the docker run command below, see Docker documentation: [docker container run](https://docs.docker.com/edge/engine/reference/commandline/container_run/))
```
$ ansible gluster -b -m shell -a 'docker run --restart always -v /etc/glusterfs:/etc/glusterfs:z -v /var/lib/glusterd:/var/lib/glusterd:z -v /var/log/glusterfs:/var/log/glusterfs:z -v /sys/fs/cgroup:/sys/fs/cgroup:ro -v /root/.ssh:/root/.ssh:z -v /var/lib/heketi:/var/lib/heketi:z -d --privileged=true --net=host -v /dev/:/dev gluster/gluster-centos:latest'
```

- To check that gluster is running on each GlusterFS machine, you can use the following command:
```
$ ansible gluster -b -m shell -a 'docker ps -a'
```

*NOTE:* For information about working with RHEL 7 kernel modules see the Red Hat documentation section [Working with Kernel Modules](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/Kernel_Administration_Guide/chap-Documentation-Kernel_Administration_Guide-Working_with_kernel_modules.html)

- Configure kernel to use the `dm_thin_pool` module.  (The `dm_thin_pool` module supports LVM thin provisioning. Kernel modules to be loaded at startup are listed in `*.conf` files in `/etc/modules-load.d`.)
```
ansible gluster -m shell -a 'modprobe dm_thin_pool' --become
ansible gluster -m shell -a 'echo dm_thin_pool | tee -a /etc/modules-load.d/modules.conf' --become
```
If you want to check that dm_thin_pool got loaded in the docker image repository:
```
$ ansible gluster -b -m shell -a 'lsmod | grep dm_thin_pool'
gluster03.yyy.zzz | SUCCESS | rc=0 >>
dm_thin_pool           65565  0
dm_persistent_data     67216  1 dm_thin_pool
dm_bio_prison          15907  1 dm_thin_pool
dm_mod                114430  11 dm_log,dm_persistent_data,dm_mirror,dm_bufio,dm_thin_pool

gluster01.yyy.zzz | SUCCESS | rc=0 >>
dm_thin_pool           65565  0
dm_persistent_data     67216  1 dm_thin_pool
dm_bio_prison          15907  1 dm_thin_pool
dm_mod                114430  11 dm_log,dm_persistent_data,dm_mirror,dm_bufio,dm_thin_pool

gluster02.yyy.zzz | SUCCESS | rc=0 >>
dm_thin_pool           65565  0
dm_persistent_data     67216  1 dm_thin_pool
dm_bio_prison          15907  1 dm_thin_pool
dm_mod                114430  11 dm_log,dm_persistent_data,dm_mirror,dm_bufio,dm_thin_pool

```

At this point, the GlusterFS server cluster is up and running and you can proceed with the ICP installation. (*TBD:* There are more steps needed to allocate storage for the ICP master node shared file systems before doing the actual ICP installation.)

# Install Heketi administration client for GlusterFS in Kubernetes

*NOTE:* The installation of Heketi in Kubernetes is very confusing.  This section is currently under review and should be taken as a collection of notes rather than verified guidance.

If you are not using GlusterFS for the shared file service, this section can be skipped.

If you installed Heketi directly on RHEL, then (obviously) this section can be skipped.

This section describes the steps to install the Heketi administration client for GlusterFS in a Docker container managed by Kubernetes. Another option is to do a "native" Heketi installation.  See [Install Heketi on RHEL (aka "native" install)](#Install Heketi on RHEL (aka "native" install)).

Public Heketi install guide: [Heketi Install for Kubernetes](https://github.com/heketi/heketi/blob/master/doc/admin/install-kubernetes.md)

The Heketi client is installed on the boot-master machine.  (A Heketi client can be installed where you prefer, including on an administrator's desktop machine. The Heketi client obviously must have network access to the Gluster servers to be managed.)

- Follow the instructions for the [Heketi install](https://github.com/heketi/heketi/blob/master/doc/admin/install-kubernetes.md).  (Ignore the GlusterFS installation instructions.  The GlusterFS install was done into docker containers on each of the GlusterFS servers. (See above section of this guide.) Important to note that the glusterfs install uses Docker only, not Kubernetes.  *TBD:* Should we create a separate Kubernetes cluster for GlusterFS?  That seems like overkill.  I would do a "native" GlusterFS install instead.)

- Get the [Heketi CLI](https://github.com/heketi/heketi/releases) for the current release.  (*TBD:* The instructions mention that this has heketi-cli in it.  However, it is vague as to what it means to "install" the heketi-cli.  I'm not sure what it is used for.)

- Extract the archive on the machine where you are doing the installation.  (Create a heketi directory in /root on master01 and extracted the archive there. `tar -xvf heketi-client-v5.0.1.linux.amd64.tar.gz`.  The root of everything in the archive is `heketi-client`, so no need to create a separate directory where the archive is extracted.)

- *TBD:* Also cloned the heketi git hub.  There appears to be more useful content in the git repo than what comes with the release tar ball.  (The following clone command was executed from the /root/heketi staging directory.) Is this a reasonable step or unnecessary? Or should this be done instead of downloading and extracting the heketi tar ball? The heketi release tar ball has the heketi-cli executable in it.  But I'm not sure what that is used for.
```
git clone https://github.com/heketi/heketi heketi-git-hub
```

- Create a kubernetes service account.
```
kubectl create -f heketi-client/share/heketi/kubernetes/heketi-service-account.json
```

- Create a cluster role binding for the service account so it can administer the gluster servers.
```
kubectl create clusterrolebinding heketi-gluster-admin --clusterrole=edit --serviceaccount=default:heketi-service-account
```

- Create kubernetes secret:
```
kubectl create secret generic master01-root-ssh-key --from-file=/root/.ssh/id_rsa
```
*TDB:* What/where does this secret get used?  Looks like it should be referenced in the heketi.json config file, but I'm not sure how yet.  That's where the heketi executor is set and in this case `ssh` should be used for the executor.

- Make a copy of the `heketi.json` to edit for the install.  (*TBD:* There are a number of `heketi.json` files in the git repo.  I started with the one in `<repo-clone>/etc/heketi.json` )

- Things that may need to be changed in `heketi.json`:
  - Server port: 8081  (8080 is used by the ICP console.)
  - use_auth: True
  - admin key, user key (*TBD:* Are these two secrets a password? Or the name of a kubernetes secret?  Looks like they are supposed to be a password.)
  - glusterfs executor: ssh
    - user: root  (*TBD:* Likely need to create a separate heketi user rather than use root.)
    - key file: /root/.ssh/id_rsa
    - fstab: (*TBD* Not sure what to use here. On the gluster server nodes we created a `/var/lib/heketi/` where `fstab` is intended to go. So for now, use `/var/lib/heketi/fstab`.)
  - kubernetes exec (kubeexec)
    - host: https:<master-vip>:8443
    - cert: don't care (*TBD:* What would this be in a more realistic configuration.)
    - insecure: true (*TBD:* Should be false in a realistic deployment.)
    - user: admin
    - password: admin
    - namespace: default (*TBD:* Not sure what this should be.  Maybe `service`)
    - fstab: `/var/lib/heketi/fstab` (*TBD:* Need to confirm this is the correct path.)
  - auto_create_block_hosting_volume: false  (*TBD:* Confirm this is correct.  I'm pretty sure we don't want this.)
  - block_hosting_volume_size: 100 (in GB)

  - The next step in the heketi install guide is to create a secret based on the heketi.json.  (*TBD:* Not really sure what it means to use that whole config file to create a "secret". How is that secret used?)
```
kubectl create secret generic heketi-config-secret --from-file=./heketi.json
```

- Make a copy of `heketi-bootstrap.json` that comes in the `<repo-clone>/extras/kubernetes/`
- Edit the `heketi-bootstrap.json` file to make sure it is what you want.
  - Originally I had replicas set at 2.  But then realized that for the heketi bootrap service, likely I only need 1 replica.
  - I changed all the port 8080 to 8081.  (*TBD:* Need to confirm.)
  - There is an env var HEKETI_EXECUTOR that I changed to `ssh` from `kubernetes`.
  - The names of some other things are in this file.  They match the names used in earlier commands.  If different names are used, then corresponding changes would need to be made in this file.
- Then do the following:
```
kubectl create -f heketi-bootstrap.json
```

- The first run of the heketi-bootstrap create failed.  Below is the event list from `kubectl describe pods`:
```
Events:
  Type     Reason                  Age              From                    Message
  ----     ------                  ----             ----                    -------
  Normal   Scheduled               4m               default-scheduler       Successfully assigned deploy-heketi-6f6dfb498-g52pb to 172.16.249.84
  Normal   SuccessfulMountVolume   4m               kubelet, 172.16.249.84  MountVolume.SetUp succeeded for volume "db"
  Normal   SuccessfulMountVolume   4m               kubelet, 172.16.249.84  MountVolume.SetUp succeeded for volume "config"
  Normal   SuccessfulMountVolume   4m               kubelet, 172.16.249.84  MountVolume.SetUp succeeded for volume "heketi-service-account-token-jg4m2"
  Warning  FailedCreatePodSandBox  4m (x7 over 4m)  kubelet, 172.16.249.84  Failed create pod sandbox.
  Normal   SandboxChanged          4m (x7 over 4m)  kubelet, 172.16.249.84  Pod sandbox changed, it will be killed and re-created.
  Warning  FailedSync              4m (x8 over 4m)  kubelet, 172.16.249.84  Error syncing pod

```

- To delete things you need to do the following:
  - Delete the heketi deployment: `kubectl delete deployment deploy-heketi`
  - Deleting the service as well: `kubectl delete service deploy-heketi`
  - NOTE: Deleting the deployment, deletes the pod(s), but it doesn't delete the service.  (*TBD:* Not sure why deleting a deployment does not delete the service.)

- Second try with only 1 replica.
```
kubectl create -f heketi-bootstrap.json
```
