# Uninstall IBM Cloud Private

*NOTE:* As of ICP 3.1.0 it is not required that an uninstall be done after every failed installation.  The installation process is more-or-less idempotent.

The general rule, is that if the install failed gracefully, i.e., the error is reported in the install log and a final status of all the cluster nodes is reported, then an uninstall is not needed.  

```
> docker run -e LICENSE=accept --net=host --rm -t -v $(pwd):/installer/cluster ibmcom/icp-inception-amd64:3.1.0-ee uninstall -v
```

After the uninstall, the following directories should not exist on any nodes in the cluster/cloud:
```
/var/lib/etcd/
/var/lib/kubelet/
/etc/cfc/
```
