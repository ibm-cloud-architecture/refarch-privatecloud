# Configure a Kubernetes StorageClass for GlusterFS

In order to use the shared storage provided by the GlusterFS cluster, some additional Kubernetes artifacts need to be created.  The ICP cluster needs to be up and running in order to create these artifacts.

*NOTE:* It appears that you need to be logged in as admin to the Kubernetes/ICP cluster to work with Storage Classes.

## Create a secret for Heketi admin

[Kubernetes documentation on secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

The Heketi admin secret holds the admin user and password defined in the `/etc/heketi/heketi.json` file used to configure the Heketi server.  The secret is needed to create a Kubernetes Storage Class as described in the next sub-section.

The user and key attributes must be base64 encoded.  The `base64` utility is handy for encoding and decoding strings.

*NOTE:* Make sure you use the -n option to echo so that the string to be encoded does not include a newline character.

```
> echo -n passw0rd | base64
cGFzc3cwcmQ=
```
```
> echo -n admin | base64
YWRtaW4=
```

Here is a sample YAML for a secret named `heketi-secret` defined in the default namespace.  (Be careful about proper indenting if you cut-and-paste to a file.)

```
---
apiVersion: v1
type: kubernetes.io/glusterfs
kind: Secret
metadata:
  name: heketi-secret
  namespace: default
data:
  user: YWRtaW4=
  key: cGFzc3cwcmQ=
```

Assuming the above content is in a file named `heketi-secret.yml`, the command to create the secret:
```
kubectl create -f heketi-secret.yml
```

## Create a storage class for persistent volume claims

[Kubernetes Storage Class documentation](https://kubernetes.io/docs/concepts/storage/storage-classes/)
[Kubernetes Persistent Volume and Persistent Volume Claim documentation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

When a Persistent Volume Claim (PVC) is made in Kubernetes, a Storage Class (SC) is needed to satisfy the claim.

To create a storage class you need:
1. The GlusterFS cluster ID of the GlusterFS cluster to be used.
2. The URL that points to the Heketi server to be used to manage the storage.  (If the Heketi server is running in a Kubernetes pod, then the host name (FQDN) or IP address will be the proxy server virtual host name or VIP.)
3. The name and namespace of the Kubernetes secret that holds the Heketi server admin user and password.
4. Other optional configuration parameters. (It is best to err on the side of explicitly defining attributes rather than relying on default values.)

The following YAML can be used to create a storage class named cluster.shared.storage in the default namespace.  (Be careful about proper indenting if you cut-and-paste to a file.)
```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cluster.shared.storage
provisioner: kubernetes.io/glusterfs
parameters:
  resturl: "http://172.16.25.100:8081"
  clusterid: "042e3eb4b386b086c17d9d947e8ba885"
  restuser: "admin"
  secretNamespace: "default"
  secretName: "heketi-secret"
  volumetype: "replicate:3"
```
*WARNING:* Be very careful not to include a trailing slash on the `resturl` for the Heketi server.  For example, `http://172.16.25.100:8081/` will fail when you use the storage class to create a PVC with a cryptic error message. The storage class will fail when creating a volume.  The state of the PVC will be "pending". You can see the error in the "events" associated with the PVC.

Assuming the above content is in a file named `cluster-shared-storage.yml`, the command to create the storage class:
```
> kubectl create -f cluster-shared-storage.yml
```

At least one StorageClass object should be set as the `default`.  To make the `cluster.shared.storage` the default StorageClass use the following command:
```
> kubectl patch storageclass cluster.shared.storage -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

Once the storage class is created and made the default, confirm that it works by created a test PVC using `kubectl` or the ICP console.
