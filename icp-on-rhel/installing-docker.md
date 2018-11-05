# Installing Docker using the Passport Advantage executable

*WARNING:* For ICP 2.1.0.3 on RHEL, you must install Docker provided in Passport Advantage for ICP.  Search Passport Advantage using `IBM Cloud Private 2.1.0.3 Docker`.  The part number is `CNT2AEN`

You have two options for installing Docker:
1. Install Docker only on the boot-master machine and let Docker be installed on all of the other cluster members as part of the ICP installation.

2. Install Docker on the boot-master and all of the cluster members.  This install guide uses this option because it tends to be faster to install Docker on each machine.  Once Docker is installed on each machine, the ICP Docker images can be loaded into the local Docker registry on each machine, which is another expedient to speed up the ICP installation.

For additional information see the ICP Knowledge Center section [Setting up Docker for IBM Cloud Private](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/installing/install_docker.html)  

## Some pre-reqs

You may need to install `policycoreutils-python`:
```
yum -y install policycoreutils-python
```

- Make the Docker installation binary that you downloaded along with the ICP installation image, `icp-docker-17.12.1_x86_64.bin`, executable:
```
chmod +x icp-docker-17.12.1_x86_64.bin
```

- Use `xfs_info` to confirm that the file system for `/var/lib/docker` is `xfs` with `d_type=true`.


## Installing Docker using overlay2 storage driver

For ICP 2.1.0.3 this is the recommended installation process.  RHEL 7.4 or later is assumed.

- Install docker
```
./icp-docker-17.12.1_x86_64.bin --install
```

- Edit `/usr/lib/systemd/system/docker.service`.  The `ExecStart` line should look like:
```
 ExecStart=/usr/bin/dockerd --log-opt max-size=50m --log-opt max-file=10 --storage-driver=overlay2
```

- (Optional) To the `Service` section, add the line:
```
MountFlags=shared
```

Either MountFlags needs to be set to shared, or not present in the `docker.service` file.

- Reload daemons and restart Docker.
```
reload systemd - systemctl daemon-reload
restart docker - systemctl restart docker
```

- After Docker is running use `docker info` to confirm that the `overlay2` storage driver is in use with an `xfs` file system and `d_type` is supported.  See output below for a sample:
```
> docker info
Containers: 0
 Running: 0
 Paused: 0
 Stopped: 0
Images: 0
Server Version: 17.12.1-ce
Storage Driver: overlay2
 Backing Filesystem: xfs
 Supports d_type: true
 Native Overlay Diff: true
Logging Driver: json-file
Cgroup Driver: cgroupfs
Plugins:
 Volume: local
 Network: bridge host macvlan null overlay
 Log: awslogs fluentd gcplogs gelf journald json-file logentries splunk syslog
Swarm: inactive
Runtimes: runc
Default Runtime: runc
Init Binary: docker-init
containerd version: 9b55aab90508bd389d7654c4baf173a981477d55
runc version: 9f9c96235cc97674e935002fc3d78361b696a69e
init version: 949e6fa
Security Options:
 seccomp
  Profile: default
```

-	If the node has access to the public Docker hub, use `docker run hello-world` to confirm the installation.  (The container with `hello-world` in it will be downloaded from the public Docker hub.)

- If the node does not have access to the public Docker hub, you can download the `hello-world` container, `scp` it to the ICP VM where you want to smoke test Docker; load it into the local registry and then run it.

```
docker run hello-world
```

- The main thing to check for in the output from hello-world:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

You should not see errors when running the docker hello-world smoke test.

As an installation expedient, it is recommended that you repeat the Docker installation on all the other VMs in the ICP cluster.

# MountFlags in docker.service

The Kubernetes kubelet process that runs on each VM in the ICP cluster needs `MountFlags=shared` in docker.service configuration file.

The MountFlags setting needs to be done on all machines in the cluster.  

It is assumed that docker has been installed.  (You won't see a `docker.service` file in `/lib/systemd/system` if docker has not been installed.)

- Edit the file: `/lib/systemd/system/docker.service`

- To the `Service` section, add the line:
```
MountFlags=shared
```

See [Docker Basics](docker-basics.md) for rudimentary "getting started with Docker" information.
