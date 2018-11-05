# ICP Console Login Problems Resolved

It is not unusual to be unable to login to the ICP console after doing an ICP installation.  

The root cause of login problems is not well understood.  These notes provide steps to correct them.

The login problem symptoms can be:
- failure to connect from the browser
  - If you check on the master node with `netstat -an | grep 8443`, you won't see anything listening.
- 504 Gateway error
  - This is an authentication or authorization error.  It may have to do with how the cluster certificates are defined (CN, SAN attribute value) and the host name you are using.  The host name you use in the URL to get to the management console needs to match the host name that was used in the CN value of the certificates that were created.  This is the value used for `cluster_CA_domain` in the `config.yaml`.
  - You do see behavior that looks like a redirect, which looks promising, but then you get the 504 error.
- 502 Gateway error
  - This is some sort of timeout issue

To do problem determination further, you will very likely need to be able to use `kubectl`.  With `kubectl` you can get pod status, delete pods and examine what is going on with the ICP and authentication pods.

*NOTE:* Deleting a pod is a common problem resolution tactic.  It is the moral equivalent of a reboot.  Kubernetes will redeploy the pod and it will spin up.

You need at least 2 things to use `kubectl` in a `bash` shell:
1. the `kubectl` executable
2. a bunch of environment variables set to values that are used by `kubectl` to connect to a Kubernetes API server as an authenticated user.  This is referred to as a `client config` or `login context` or a `kube config`.  In this write-up it will be referred to as a `client config`.

## Restarting kubelet and docker

One quick and dirty thing to try to clear up the login problem in a scenario where it is acceptable to stop and restart the master node is to go through these steps (as root on the master node):

```
systemctl stop kubelet
systemctl stop docker
systemctl start docker
systemctl start kubelet
```

Running the above steps is the equivalent of rebooting the master node.

In an HA deployment with multiple masters, you would do the above steps on the current active master, i.e., the one that has the master VIP.

## Installing the kubectl executable

**The steps described in this section need to be executed on the master node.**

From the `icpboot` node, open and `ssh` session to the master node:
```
ssh root@10.0.0.2
```

Because we have passwordless ssh configured for root from the icpboot node to all of the other cluster nodes you can use: `ssh 10.0.0.2` or you can use the host name defined in `/etc/hosts` for the master node: `ssh master01.icp.local`

The `kubectl` executable is available in the `icp-inception` image that is part of the ICP images. (It is also available in the `kubernetes` image.)  To get it out of the container and onto the machine where you need it you can use a `docker run` command that looks like:
```
docker run --net=host -v /usr/local/bin:/data ibmcom/icp-inception:2.1.0.3-ee cp /kubectl /data
```
We say "looks like" because the `icp-inception` image tag may be different from `2.1.0.3-ee` in your particular circumstance.  (In the current ICP bootcamp, `2.1.0.3-ee` is the tag for the `icp-inception` image.)

If a private registry was used to do the ICP installation, then the source of the `icp-inception` image will include a host and port for the private registry.

The above command is running an `icp-inception` image that is in the local docker registry. But you may not have the `icp-inception` image in your local registry.  

To see what is in your local registry you can use:
```
docker images
```

If there are a lot of images in your local registry you can filter for what you are looking for, in this case `icp-inception`:
```
docker images | grep inception
```
If you are getting `kubectl` from the `kubernetes` image:
```
docker images | grep kubernetes
```

If `icp-inception` is in your local registry you can see what tag it has and modify the above `docker run` command to copy the `kubectl` executable to `/usr/local/bin` on the VM you are using.

If ICP was installed from a private docker registry running on a dedicated boot VM, you may need need to `pull` the `icp-inception` image from there into your local registry and then you can run the above command to copy `kubectl` to `/usr/local/bin`.  

To do the pull from the private registry, you first need to authenticate to it:
```
docker login icpboot.icp.local:8500
```
You need to know the user and password to authenticate to the registry.  In the above example the registry is running on a machine named `icpboot.icp.local`. At the prompts provide the user and password.

Now, you can do the `pull`:
```
docker pull icpboot.icp.local:8500/ibmcom/icp-inception:2.1.0.3-ee
```

Copy the `kubectl` to the VM `/usr/local/bin`
```
docker run -e LICENSE=accept --net=host -v /usr/local/bin:/data ibmcom/icp-inception:2.1.0.3-ee cp /usr/local/bin/kubectl /data
```
At this point you should be able to run `kubetl` and get all of its usage info:
```
kubectl
```

In the next section we describe what you need to do to get a `client config`.

## Getting a client configuration

In order to use `kubectl` you need what is referred to as a `client config` or a `login context`.  Under normal circumstances you can get a client configuration from the console.  You can also use the `kubectl-client-config.sh` script provided by the IBM Cloud Private CoC.  The script uses `curl` to the master node and port `8443`.  In the scenario where you can't get to the console, the script may not work either.

When you can't get a client config, you can still use `kubectl` as long as you can `ssh` to the master node of the cluster.

In ICP 2.1.0.2 deployments you are able to use the `-s localhost:8888` option to `kubectl` on the master node and that would connect without needing to authenticate or get a full client config. That option does not work in ICP v2.1.0.3.

Another "trick" to using `kubectl` without creating your own client config is to use the `--kubeconfig` option as shown in the sample `get pods` command:
```
kubectl --kubeconfig=/var/lib/kubelet/kubelet-config get pods -n kube-system -o wide
```

The `/var/lib/kubelet/kubelet-config` file exists on all the nodes.

The `master` node also has `/var/lib/kubelet/kubectrl-config` which is needed for certain commands that require super-user permissions.

The above `get pods` command should dump out a list of all the `kube-system` pods and information about that particularly the `state`.

In the next section we describe the steps to resolve the ICP console connection and login page access issue.

## Bouncing the auth pods to resolve ICP console access issues

The pods that deal with authentication to the ICP console are referred to as the `auth` pods.  There are 4 active `auth` pods.  A fifth `auth` pod is a batch job that may show up in the list of pods.  It will have a status of `completed`.  You don't need to delete that `auth` pod.

Use `get pods` and filter for just the `auth` pods
```
kubectl --kubeconfig=/var/lib/kubelet/kubelet-config get pods -n kube-system -o wide | grep auth
```

Delete each active pod (run the command for each pod using the actual name for AUTH_POD_NAME)
```
kubectl --kubeconfig=/var/lib/kubelet/kubelet-config -n kube-system delete pod AUTH_POD_NAME
```

Once the pods have been deleted, you can run the `get pods` command filtering for the `auth` pods to see that they come back up to a `running` state.

You will likely see the `auth-pdp*` pod take the longest to get to a `running` state.  You may see it go to an `error` state and then back to `init` and the to `running`.

Once all of the `auth` pods are running again, attempt an ICP console login from your browser using the value that was provided for `cluster_CA_domain` in `config.yaml`.  (The default value of `cluster_CA_domain` is `mycluster.icp`.  You can also check the `/etc/hosts` file on any of the cluster nodes as the value of `cluster_CA_domain` gets injected into `/etc/hosts` during the ICP installation.)

If you still cannot log in to the ICP console do the following on the master node:
```
systemctl stop kubelet
systemctl stop docker
systemctl start docker
systemctl start kubelet
```

The last "bouncing" of `kubelet` and `docker` should clean out any flakes with the `auth` pods.

*NOTE:* You do need to wait for the `auth` pods to come back up before attempting a login.  Use the above `get pods` command with the `grep auth` to monitor the pod status.
