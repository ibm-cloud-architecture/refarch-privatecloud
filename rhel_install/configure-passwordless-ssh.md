# Configure passwordless ssh among cluster/cloud members

The "boot master" VM needs to have root access via ssh to the other members of the ICP cluster.

*NOTE:* In the description below, it is assumed that DNS is in use and the host names for the ICP cluster VMs are registered in the DNS.  If DNS is not in use, then the `/etc/hosts` files on each of the ICP cluster VMs must have been set up to map host names to IP addresses.  Hence, host names are used in the samples. (The ssh-copy-id command requires the use of host names.)

*NOTE:* Substitute your actual host names In the sample commands in this section.
For the ICP KC instructions to do this work, see [Sharing SSH keys among cluster nodes](https://www.ibm.com/support/knowledgecenter/SSBS6K_2.1.0/installing/ssh_keys.html)

- Login to the boot-master node as root

- On the boot-master, as root, from root’s home directory (/root) execute:
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

- Now, executing a directory listing on /root/.ssh should show two files: id_rsa, id_rsa.pub. (A known_hosts file may also be present.)
```
> ls -l ~/.ssh
  total 8
  -rw-------. 1 root root 1675 Jun 30 12:11 id_rsa
  -rw-r--r--. 1 root root  402 Jun 30 12:11 id_rsa.pub
```
- Using the `ssh-copy-id` command from root's home directory, copy the resulting `id_rsa.pub` key file to each node in the cluster (including the boot-master node on which you are currently operating).

*NOTE:* The copy of the SSH ID to other hosts requires the use of the target host name in the ssh-copy-id command.  Do not use an IP address, you will not be able to get past the authentication step when you attempt to enter the password for root on the target host. (TODO - Test this. It may be that an IP address or host name can be used.)

In the command below `<master>` is used as a placeholder for the actual boot-master fully qualified host name (FQDN).
```
> ssh-copy-id -i ~/.ssh/id_rsa.pub root@<master>
```

You will be prompted to confirm that you want to connect to the `<master>`. Then you will be prompted for root's password on `<master>`, which is the target for this first passwordless ssh configuration.

*NOTE:* If you are not prompted to confirm that you want to connect to the target machine, and for the root password of the target machine, then make sure the target machine has a .ssh directory in /root.  The permissions on the .ssh directory should be 700. Also make sure you can ping the target host by host name.  (DNS or `/etc/hosts` on the boot-master needs to be configured to allow the target host name to be resolved.)

- Now try logging into the machine, with: `ssh root@<master>` and check to make sure that only the key(s) you wanted were added.

At this point you should see two additional files in the .ssh directory:
```
> ls -l ~/.ssh
  total 16
  -rw-------. 1 root root  402 Jun 30 12:17 authorized_keys
  -rw-------. 1 root root 1675 Jun 30 12:11 id_rsa
  -rw-r--r--. 1 root root  402 Jun 30 12:11 id_rsa.pub
  -rw-r--r--. 1 root root  191 Jun 30 12:17 known_hosts
```
-	Repeat for each additional server in the cluster/cloud.  (As above, you will need to answer yes to add the ECDSA key for each host to the known_hosts file and provide the root password of the target host.)

In the commands below, `<proxy>` and `<worker_##>` is used as a placeholder for the fully qualified host names (FQDN) for machines in the cluster.
```
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<proxy>
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<worker_01>
> ssh-copy-id -i ./.ssh/id_rsa.pub root@<worker_02>
  etc
```

- When this is complete, you should be able to ssh from the boot-master node to each of the other nodes as root without having to provide a password. You can test this by executing and ssh from the boot-master host to any of the other members of the ICP cluster:
```
[root@<master> ~]# ssh root@<proxy>
Last login: Thu Jun 29 14:44:34 2017
[root@<proxy> ~]# exit
logout
Connection to <proxy> closed.
[root@<master> ~]# ssh root@<worker_01>
Last login: Fri Jun 30 09:39:31 2017
[root@<worker_01> ~]# exit
logout
Connection to <worker_01> closed.
[root@<master> ~]#
etc
```
If you cannot gain access via SSH without a password, check the known_hosts and authorized_keys files on the hosts other than the boot-master.
