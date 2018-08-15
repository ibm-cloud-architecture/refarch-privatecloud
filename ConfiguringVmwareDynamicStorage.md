### Configuring ICP to use VMware for dynamic storage provisioning

It is important to note that using VMware storage for dynamic storage provisioning uses the VMware API and this is *not* vSAN.  vSAN is a completely separate technology which takes storage local to multiple hypervisors and makes it available as a VMware datastore.

To use VMware for dynamic storage provisioning you need an existing VMware datastore and access to the API server with the needed credentials for creating storage volumes.  That is what this tutorial will focus on.

All of the prerequisites noted here must be complete prior to installing ICP.

## Configure vSphere for use by ICP

First, to use dynamic storage provisioning on VMware you must create a user with the proper VMware permissions that can be used to interact with VMware.

The IBM knowledgebase for this topic can be found at https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/manage_cluster/add_vsphere.html.

Prerequisites for creating the vssphere storage can be found at https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0.3/installing/cloud_provider_vsphere.html#prereq

It should be noted that as of this writing, only the ReadWriteOnce storage access mode.

The following are important restrictions on using VMware for your dynamic storage.

* All IBM® Cloud Private cluster nodes must be under one vSphere VM folder.
* All IBM Cloud Private master nodes must be able to access vCenter.
* The node host name must be same as the VM name.
* Node host names must comply with the regex: \[[a-z\]](([-0-9a-z]+)?[0-9a-z])?(\\.\[[a-z0-9\]](([-0-9a-z]+)?[0-9a-z])?)\*, and must also comply with the following restrictions:

  * They must not begin with numbers.
  * They must not use capital letters.
  * They must not have any special characters except . and -.
  * They must contain at least three characters but no more than 63 characters.
  * The disk UUID on the node VMs must be enabled: the disk.EnableUUID value must be set to True.
  * The user that is specified in the vSphere cloud configuration must have privileges to interact with vCenter.

You will ned to create a vCenter user to use for the dynamic storage provisioning.  We will use "icpadmin" as our user.  We also need to create a few roles and assign them to this user so that it has the correct authority.  The following information is correct for VMware 6.5 and may not be applicable for other versions.

Role 1: manage-k8s-node-vms
  Privileges:
    * Resource: Assign virtual machine to resource pool
    * Virtual Machine -> Configuration: Add existing disk
    * Virtual Machine -> Configuration: Add new disk
    * Virtual Machine -> Configuration: Add or remove device
    * Virtual Machine -> Configuration: Remove disk
    * Virtual Machine -> Inventory: Create from existing
    * Virtual Machine -> Inventory: Create new
    * Virtual Machine -> Inventory: Create remove

Role 2: manage-k8s-volumes
  Privileges:
    * Datastore -> Allocate space
    * Datastore -> Browse datastore
    * Datastore -> Configure datastore
    * Datastore -> Low level file operations
    * Datastore -> Remove file
    * Datastore -> Update virtual machine files
    * Datastore -> Update virtual machine metadata

Role 3: k8s-system-read-and-spbm-profile-view
  Privileges:
    * Storage views: Configure service
    * Storage views: view

Role 4: ReadOnly
  Privileges: none

_Alternatively, you can just create a single role called "icpadmin" which has all of these privileges._

Next, assign the following roles for this user on all the needed vmware objects:
  * Datacenter (only): k8s-system-read-and-spbm-profile-view
  * Cluster (propogate ): manage-k8s-node-vms
  * VM Folder (propogate): manage-k8s-node-vms
  * Target Datastore (only): manage-k8s-volumes
  * Datacenter, Datastore Cluster, and Datastore storage folder: ReadOnly

If you have created one role with all needed privileges, just assign that role to that user for all of the entities noted above: All pertinent Datacenters, clusters, hosts, resource pools, datastores, and folders.

## Configure ICP for vSphere storage

On your ICP boot node, open the config.yaml file and add the following (spacing is important, use spaces and not tabs):

```
kubelet_nodename: hostname
cloud_provider: vsphere
vsphere_conf:
   user: "<vCenter username for vSphere Cloud Provider>"
   password: "<password for vCenter user>"
   server: <vCenter server IP or FQDN>
   port: [vCenter Server Port; default: 443]
   insecure_flag: [set to 1 if vCenter uses a self-signed certificate]
   datacenter: <datacenter name on which Node VMs are deployed>
   datastore: <default datastore to be used for provisioning volumes>
   working_dir: <vCenter VM folder path in which node VMs are located>
   ```

Example:
```
kubelet_nodename: hostname
cloud_provider: vsphere
vsphere_conf:
   user: icpadmin
   password: Passw0rd!
   server: 1.2.3.4
   port: 443
   insecure_flag: 1
   datacenter: CSPLAB
   datastore: ExternalDemo
   working_dir: my-icp-2103
```

Deploy your ICP instance as per normal.

Once your instance has been deployed you must create a storage class to consume the storage.

First, Create a .yaml file (vsphere.yaml) with the following contents:

```
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: vsphere
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: kubernetes.io/vsphere-volume
parameters:
  diskformat: thin
  datastore: MyDatastore
```

The diskformat can be thin,zeroedthick, or eagerzeroedthick.  The datastore should be changed to specify the name of the datastore where you want your volumes created.

Configure kubectl to point to your ICP instance.

Deploy your new storage class

```
kubectl create -f vsphere.yaml
```

Now, when installing helm charts you can specify dynamic storage using the 'vsphere' storage class and it will dynamically provision your PV to the specified datastore.
