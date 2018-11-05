# Configure passwordless ssh among cluster members

Passwordless `ssh` is needed in the following scenarios when working with ICP:

- The "boot master" VM needs to have root access via ssh to the other members of the ICP cluster.
- If you are using a GlusterFS cluster, all the members of the GlusterFS server cluster must have passwordless `ssh` configured to each of the other servers, i.e., multi-way passwordless `ssh`.
- If the Heketi server is using `ssh` to administer the GlusterFS servers, the Heketi server identity (e.g., heketi), needs passwordless `ssh` to all of the GlusterFS servers.

*NOTE:* In this description the word "cluster" is used to refer to a group of machines (VMs) that need to have passwordless `ssh` access configured.  The actual cluster may be an ICP cluster or a GlusterFS cluster, for example.

*NOTE:* In this description the phrase "source node" or "source" is intended to mean the node from which passwordless `ssh` is intended to originate.  The source node would be the `boot` node for an ICP cluster.  The source node would be each GlusterFS server node in turn for a GlusterFS cluster.  The Heketi server would be the source node when it is configured to use `ssh` to administer a GlusterFS cluster. 

*NOTE:* In the description below, it is assumed that DNS is in use and the host names for the cluster VMs are registered in the DNS.  If DNS is not in use, then the `/etc/hosts` files on each of the ICP cluster VMs must have been set up to map host names to IP addresses.  Hence, host names are used in the samples.

*NOTE:* Substitute your actual host names or IP addresses in the sample commands in this section.
For the ICP Knowledge Center instructions to do this work, see [Sharing SSH keys among cluster nodes](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/installing/ssh_keys.html)

- Login to the "source" node as root

- As root execute:
```
> ssh-keygen -b 4096 -f ~/.ssh/id_rsa -N ""
```
The above command requires no responses to prompts.
You should see something like:
```
Generating public/private rsa key pair.
Your identification has been saved in /root/.ssh/id_rsa.
Your public key has been saved in /root/.ssh/id_rsa.pub.
The key fingerprint is:
REDACTED root@REDACTED
The key's randomart image is:
REDACTED
```

- Now, executing a directory listing on `~/.ssh` should show two files: `id_rsa`, `id_rsa.pub`. (A `known_hosts` file may also be present.)
```
> ls -l ~/.ssh
  total 8
  -rw-------. 1 root root 1675 Jun 30 12:11 id_rsa
  -rw-r--r--. 1 root root  402 Jun 30 12:11 id_rsa.pub
```

- Using the `ssh-copy-id` command from root's home directory, copy the resulting `id_rsa.pub` key file to each node in the cluster, including the source node on which you are currently operating.

In the command below `<target01>` is used as a placeholder for the actual fully qualified host name (FQDN) or IP address of the first target node for passwordless `ssh`.
```
> ssh-copy-id -i ~/.ssh/id_rsa.pub root@<target01>
```

You will be prompted to confirm that you want to connect to the `<target01>`. Then you will be prompted for root's password on `<target01>`, which is the target for this passwordless `ssh` configuration.

*NOTE:* If you are not prompted to confirm that you want to connect to the target machine, and for the root password of the target machine, then make sure the target machine has a `.ssh` directory in `/root`.  The permissions on the `.ssh` directory should be 700. Also make sure you have network connectivity to the target host. (If `ping` is not blocked it can be used as a simple network connectivity test.)  (If you are using host names, DNS or `/etc/hosts` on the needs to be configured to allow the target host name to be resolved.)

- Now try logging into the machine, with: `ssh root@<target01>` and check to make sure that only the key(s) you wanted were added.

At this point you should see two additional files in the .ssh directory:
```
> ls -l ~/.ssh
  total 16
  -rw-------. 1 root root  402 Jun 30 12:17 authorized_keys
  -rw-------. 1 root root 1675 Jun 30 12:11 id_rsa
  -rw-r--r--. 1 root root  402 Jun 30 12:11 id_rsa.pub
  -rw-r--r--. 1 root root  191 Jun 30 12:17 known_hosts
```
-	Repeat for each additional server in the cluster/cloud.  (As above, you will need to answer yes to add the ECDSA key for each host to the `known_hosts` file and provide the root password of the target host.)

Repeat the above steps for each of the passwordless `ssh` target nodes, i.e., all the nodes in an ICP cluster, all the nodes in a GlusterFS cluster.
```
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<target02>
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<target03>
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<target04>
  etc
```

- When this is complete, you should be able to ssh from the source node to each of the other nodes as root without having to provide a password. You can test this by executing and ssh from the boot-master host to any of the other members of the ICP cluster:
```
[root@<source> ~]# ssh root@<target01>
Last login: Thu Jun 29 14:44:34 2017
[root@<target01> ~]# exit
logout
Connection to <target01> closed.
[root@<source> ~]# ssh root@<target02>
Last login: Fri Jun 30 09:39:31 2017
[root@<target02> ~]# exit
logout
Connection to <target02> closed.
[root@<source> ~]#
etc
```
If you cannot gain access via SSH without a password, check the `known_hosts` and `authorized_keys` files on the hosts other than the source node.
