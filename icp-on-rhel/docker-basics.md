# Docker basics

The following collection of sub-sections is intended to provide enough information about Docker to get you started. The commands described tend to be things that come up frequently in the operation of IBM Cloud Private.  Your favorite Internet search engine is your friend when it comes to learning Docker and Docker command idioms.

For step-by-step guidance on installing docker: [Installing Docker](installing-docker.md).

## Starting, stopping and enabling Docker

This section has commands for starting, stopping and enabling docker and checking its status.

After Docker is installed, you need to start it.  You need root privileges to start, stop and enable a service.

To enable docker so that it starts on machine reboot and start docker immediately:
```
> systemctl enable docker --now
```
To start docker:
```
> systemctl start docker
```
To get docker status:
```
> systemctl status docker
```
To enable docker (so that it starts on machine reboot):
```
> systemctl enable docker
Created symlink from /etc/systemd/system/multi-user.target.wants/docker.service to /usr/lib/systemd/system/docker.service.
```
To stop docker:
```
> systemctl stop docker
```

## Getting a list of docker container status
The `docker ps` command is likely one of the first commands you will want to know and you will use it often.  You can add the -a option to see all containers, i.e., those that have exited as well as those still running.
```
> docker ps
```
or
```
> docker ps -a
```
use
```
> docker help ps
```
to get more information on ps options.

## Getting a list of local docker registry content

It is useful to get a list of what is in the local docker registry.  (The term registry is misused by docker.  The docker registry is really a repository, i.e., it holds the docker images, not just a list of where the images are located.)

```
docker images
```

Once ICP is loaded into the local docker repository, there are a lot of images. You will likely want to grep for some string that is part of the image of interest to cut down the amount of output from a full docker images list.

## Exec a shell in a running Docker container.
It is assumed the container includes a bash shell.  (Every once in awhile you run into one that doesn't.)
```
docker exec -it <container_id>|<container_name> /bin/bash
```

## Run a shell in a Docker image
It is assumed the container includes a bash shell.

When you want to explore and image and it is not already running in a container, then you use the `docker run` command:
```
docker run -it <image_name> /bin/bash
```

For example:
```
docker run -it -e LICENSE=accept ibmcom/icp-inception-amd64:3.1.0-ee /bin/bash
```

## Getting a shell inside the icp-inception container

The command below will open a shell console in a container for the given docker image.  (You will need to use an appropriate image name for the local docker registry.)
```
> docker run -e LICENSE=accept --net=host --rm -it -v "$(pwd)":/installer/cluster --entrypoint=/bin/bash ibmcom/icp-inception:2.1.0.3-ee
```
## Delete docker containers using an image with a given tag
When you get a list of all containers (running and terminated) using `docker ps -a`, the first column is the container ID, which is the primary argument to `docker rm`, that removes a container.

You may find that you need to remove all containers using a particular image (with a particular tag) in order to remove the image from the local docker registry.
```
> docker rm $(docker ps -a | grep 2.1.0.2-rc2-ee | awk '{print $1}')
```

## Delete images from the local Docker registry with a given tag

In order to free up file system space you may want to delete a bunch of images with a given tag.  In the example images associated with a particular ICP release are deleted.

When you get a list of docker images using `docker images`, the third column is the image ID, which is the primary argument to `docker image rm`.
```
> docker image rm $(docker images | grep 2.1.0.2-rc1 | awk '{print $3}')
```
