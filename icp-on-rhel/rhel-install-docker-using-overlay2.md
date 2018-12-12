# Installing Docker using overlay2 storage driver

This document describes the steps for installing Docker using the `overlay2` storage driver.

It is confusing to determine which storage driver to use for Docker when installing it on RHEL. Depending on what documentation you read you may conclude that you must use the `devicemapper` storage driver.  Or you may conclude it is OK to use the `overlay2` storage driver.

If you stick to what the Red Hat documentation recommends you can proceed with using the `overlay2` storage driver as long as you are running RHEL 7.3 or later and you are using Docker 17.10 or later.

For ICP 3.1.0 this is the recommended installation process.  RHEL 7.4 or later is assumed.

- Use `xfs_info` to confirm that the file system for `/var/lib/docker` is `xfs` with `d_type=true`.

- Install docker
```
./icp-docker-17.12.1_x86_64.bin --install
```

- Edit `/usr/lib/systemd/system/docker.service`.  The `ExecStart` line should look like:
```
 ExecStart=/usr/bin/dockerd --log-opt max-size=50m --log-opt max-file=10 --storage-driver=overlay2
```

Reload daemons and restart Docker.
```
reload systemd - systemctl daemon-reload
restart docker - systemctl restart docker
```

- After Docker is running use `docker info` to confirm that the `overlay2` storage driver is in use with an `xfs` file system and `d_type` is supported.  See output below for a sample:
```
# docker info
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
