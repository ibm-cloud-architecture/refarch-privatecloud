# Storage best practices

If you are used to the terminology used in the Kubernetes documentation,
terminology for IBM Cloud Private (ICP )is a bit
different. In Kubernetes a PersistentVolume (PV) is a definition of
available storage for the entire cluster and a PersistentVolumeClaim
(PVC) is a specific application’s claim to some of that storage.

The equivalent to a PV in ICP is “Storage” and the equivalent of a PVC
is a “Volume”. So, a Storage object is available to the entire cluster
and a volume is used by an application to store data. This document may
use these terms interchangeably depending on the context.

For a primer and user guide for handling storage in ICP refer to the
[ICP Storage Guide on IBM Knowledge Center](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0/manage_cluster/cluster_storage.html)
and the Kubernetes page about 
[Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## Storage back-ends

ICP supports a number of storage back ends, where the most commonly used 
would be `NFS`, `vsphere-volume` and `glusterfs`. In this document we will 
primeraly concentrate on NFS and vsphere-volume


## Storage provisioning types

As a cluster administrator, from ICP 2.1.0 onwards you have two options to provision storage: Static and Dynamic


### Static
With static volume provisioning the cluster administrator will need to pre-create 
a number of Persistent Volumes with specific sizes.
When a user creates a Persistent Volume Claim for a volume with a certain size 
an available Persistent Volume with the same size or nearest larger is selected for that claim.
Hence it is typically beneficial to create a number of different sizes of volumes.

Statically created volumes are useful in a variety of use cases, but cluster 
administrators need to monitor the amount of available volumes to ensure that 
there are a sufficient quantity to support persistent volume claims.

### Dynamic
With dynamic volume provisioning the cluster administrator will create one or more `StorageClass`. 
The StorageClass allow cluster administrators to define abstractions for the 
underlying storage platform.

When a user creates a Persisten Volume Claim, the user can simply refer to a 
`StorageClassName` created by the cluster administrator. This will trigger 
the dynamic creation of a volume in the underlying storage platform as 
spacified by the cluster administrator.

Dynamically created volumes using storage classes are a very useful way for 
cluster administrator to make different storage tiers available to users, 
while monitoring the underlying storage platform using their existing tooling.

However, cluster administrators should make sure to create a default storage 
class, typically on a lower tier storage, such that users that do not have 
pecific performance requirements, or are using old manifests will still be 
served even if they do not reference a specific storage class.



## Naming and labels
When users create persistent storage claims they need to be able to ensure 
that the underlying storage platform meet the requirements they have. The 
matching of offered storage types and requirements is done by declaring
`storageClassName` and/or `selector` in the persistent volume claim to match 
the relevant StorageClass and Labels created by the cluster administrator.

For statically provisioned storage you can use a `Selector` to uniquely identify 
and match a particular volume or type to bind to.

It is however worth noting that at the time of writing the vSphere dynamic 
provisioner does not support Selector, so in this case it is necessary to 
rely on naming convension of `StorageClassName` to identify the right storage 
type or tier.
