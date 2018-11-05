# Kubernetes basics

The following collection of sub-sections is intended to provide enough information about kubernetes to get you started.  Obviously, to become proficient with kubernetes, you will need to gain experience through use and you will need to consult more complete sources of information, including the kubernetes documentation.

## Installing kubectl on the ICP boot-master node

Copying kubectl from a container to the host /usr/local/bin
It is very useful to be able to have kubectl available at the shell on the ICP boot-master or boot machine.  

You can get kubectl from the kubernetes container already installed as part of ICP.  (*NOTE:* In the command sample below you may need to modify the version tag on kubernetes.  Use `docker images | grep kubernetes` to see your actual version tag for kubernetes.)
```
> docker run --net=host -v /usr/local/bin:/data ibmcom/kubernetes:v1.8.3 cp /kubectl /data
```

If the `kubernetes` image is not available in the local registry on the boot node, then another place that `kubectl` is available is the `inception` image.

NOTE: For ICP 2.1.0.3 the following command can be used to get a `kubectl` excutuable copied to the VM host:
```
docker run --net=host -e LICENSE=accept -v /usr/local/bin:/data ibmcom/icp-inception:2.1.0.3-ee cp /kubectl /data
```

Again, the exact name of the image may not be as shown in the command above.  Check your docker images to determine the image name.

You may also have to open a shell on the image to figure out where the `kubectl` executable is in the image.
```
docker run -it -e LICENSE=accept ibmcom/icp-inception-amd64:3.1.0-ee /bin/bash
```

NOTE: For ICP 3.1.0 the following can be used to get a `kubectl` executable copied to the VM host:
```
docker run -it -e LICENSE=accept -v /usr/local/bin:/data ibmcom/icp-inception-amd64:3.1.0-ee cp /usr/local/bin/kubectl /data
```


## Kubernetes command basics

The command line tool for working with Kubernetes is `kubectl`.

Kubernetes [Getting Started](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands)

A quick source of kubectl help: [Kubernetes kubectl "cheat sheet"](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

When working with kubectl you need to be authenticated in your shell.  Authentication involves a number of steps.

To set up authentication in your shell:
1. Log into the ICP console. The client setup command stream is available under the user name in the upper right margin of the ICP console.  
2. Click on the user name, then click on "Configure client" and in the pop-up window, click on the copy icon next to the "kubectl config" commands in the pop-up window.  
3. Do a paste in the shell window you are using.  At that point, the shell is configured to properly use `kubectl` commands.

The authentication token is good for 12 hours.  You have to log out of the ICP console and log back in to get a new token using the same procedure described in the steps above.

You can see your kubectl context using the `kubectl config view` command.

### Get a list of namespaces
```
kubectl get namespaces
```

### Get a list of pods
```
kubectl get pods --all-namespaces
```
*NOTE:* A newly deployed ICP cluster typically has pods defined only in the kube-system namespace.

You can limit the pod listing to a specific namespace with the `--namespace=NAMESPACE_NAME`, e.g.,
```
kubectl get pods --namesapce=kube-system
```

*NOTE:* If you want to see the terminated pods, i.e., those that have completed or errored out, then use the `-a (--show-all)` option with the `get` command.

### Get info about a pod
```
kubectl describe pod <pod_name>
```
The describe command is particularly useful on any of the different kinds of Kubernetes objects.

### Get a list of deployments
```
kubectl get deployments
```

### Get a log associated with a pod or container
```
kubectl logs pod/<pod_name> | tee -a mypod.log
```
or
```
kubectl logs pod/<pod_name> --container=<container_name> | tee -a mycontainer.log
```
If a pod has more than one container in it, then you need the `--container (-c)` option.

Check out the usage information for the logs command (`kubectl logs --help`) for details on all the options.

### Combining kubectl commands
You can use all the usual Linux idioms for combining commands with `kubectl`.

Here is an example of deleting a bunch of pods with `bluecompute-ce` in the pod name:
```
kubectl delete pods $(kubectl get pods -a | grep bluecompute-ce | awk '{print $1}')
```

### Change the current namespace preference

Typically the namespace associated with a given kubeconfig will be the default namespace.  However you can change it to some other namespace.

The following command changes the currently preferred namespace to `kube-system`.  By doing so the `--namespace` option for `kubectl` commands is not needed if the namespace if interest is `kube-system`.
```
kubectl config set-context $(kubectl config current-context) --namespace kube-system
```

For more detailed information on Kubernetes namespaces, see the Kubernetes [Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) documentation.

### `kubectl` without logging in
There may be times when you can get the "client config" command line content from the ICP console, but you still want to be able to use `kubectl`.  In those cases get on the one of the master nodes (with kubectl installed) and use `-s localhost:8888` as one of the command line options to `kubectl` followed by the command you want to run.

For example:
```
> kubectl -s localhost:8888 --namespace=kube-system get pods
```
NOTE: The use of the `-s localhost:8888` option has been disabled.  It can be enabled by manually configuring the service to listen on that port.

The preferred approach for using `kubectl` when a console login is not available is the following command (run on a master node)
```
kubectl --kubeconfig=/var/lib/kubelet/kubectl-config get pods -n kube-system -o wide
```
On a non-master node the config file is named `kubelet-config`:
```
kubectl --kubeconfig=/var/lib/kubelet/kubelet-config get pods -n kube-system -o wide
```
