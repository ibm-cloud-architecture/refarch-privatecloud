# How To Move OCP to a New vCenter Server

There is occasionally the need to move OCP from one vCenter server to another.  Doing this will break vSphere storage as the credentials and hostnames defined in the OCP configs are no longer valid.

To resolve this (as of OCP 4.3) you need to update two cluster resources:
  * The `cloud-provider-config` configmap in the `openshift-config` namespace
  * The `vsphere-creds` secret in the `kube-system` namespace

## Updating the cloud-provider-config configMap

Use the following command to edit the `cloud-provider-config` configMap:

```
oc edit cm cloud-provider-config -n openshift-config
```

Modify the data under the [Workspace] stansa to reflect the new vSphere configurattion:

```apiVersion: v1
data:
  config: |+
    [Global]
    secret-name      = vsphere-creds
    secret-namespace = kube-system
    insecure-flag    = 1

    [Workspace]
    server            = newhost.newdomain.com
    datacenter        = CSPLAB
    default-datastore = INFRA_TIER0_OCS
    folder            = labdev

    [VirtualCenter "vcsa.csplab.local"]
    datacenters = CSPLAB

kind: ConfigMap```

## Modify the vsphere-creds secret

Use the following command to modify the `vmware-creds` secret:

```
oc edit secret vsphere-creds -n kube-system
```

Change the data.<hostname>.password and data.<hostname>.username values such that the hostname reflects the new hostname used in the configmap in the first step. Then save it (:wq).


```apiVersion: v1
data:
  newhost.newdomain.com.password: Sm9ob3E6MS0xNA==
  newhost.newdomain.com.username: dmhhd7FyZA==
kind: Secret
metadata:
  creationTimestamp: "2020-02-06T04:17:42Z"
  name: vsphere-creds
  namespace: kube-system
  resourceVersion: "43979774"
  selfLink: /api/v1/namespaces/kube-system/secrets/vsphere-creds
  uid: 8ae036ba-9c76-43ce-9855-4330aad391ff
type: Opaque```
