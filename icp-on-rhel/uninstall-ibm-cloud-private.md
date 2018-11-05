# Uninstall IBM Cloud Private

This document describes the steps to uninstall ICP.  Starting with ICP v2.1.0.2 it is required that an uninstall be done after a failed installation attempt.
```
> docker run -e LICENSE=accept --net=host --rm -t -v $(pwd):/installer/cluster ibmcom/icp-inception:2.1.0.3-ee uninstall -v | tee logs/icp_uninstall.log
```

The following directories should not exist on any nodes in the cluster/cloud:
```
/var/lib/etcd/
/var/lib/kubelet/
/etc/cfc/
```
