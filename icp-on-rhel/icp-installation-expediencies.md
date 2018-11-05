# IBM Cloud Private installation expediencies

This is a summary of the practical steps typically taken when doing an ICP installation.  Other documents in this collection describe these steps in more detail, usually as "pre-installation" steps.

- Install and configure Docker on all cluster nodes.  The primary motivation for doing this step explicitly is to make sure Docker is installed using the recommended `overlay2` storage driver.  At least with ICP 2.1.0.3 the default storage driver is `devicemapper`.

- Explicitly copy (`scp`) the ICP image archive to all nodes.  It is typically much faster to use `scp` to copy the ICP image archive (~10 GB) to all the nodes than to let the ICP installation process do it.  At least with an explicit `scp` you get progress information for the copy commands.

- Once the ICP image archive has been copied to all nodes, extract it to a pipe into a `docker load`.
```
tar -xf ibm-cloud-private-x86_64-2.1.0.3.tar.gz -O | docker load
```
Preloading the ICP images to the local docker registry of each node is faster than doing so during the ICP installation process.  The `docker load` emits progress information that can be viewed on a shell terminal session.

- When GlusterFS is the shared file storage solution, create an independent GlusterFS cluster (minimum of 3 nodes) dedicated to file storage.  Do not use a GlusterFS installation integrated with the ICP installation.  The dedicated GlusterFS cluster provides separation of concerns from ICP itself and can be used by multiple ICP clusters.
