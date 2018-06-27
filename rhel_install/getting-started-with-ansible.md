# Getting started with Ansible
Ansible is very useful for administration of a collection of machines such as an ICP cluster.  We recommend installing it to ease general administration of the ICP cluster.  

See the Ansible documentation for [installation instructions](http://docs.ansible.com/ansible/latest/intro_installation.html#id26). The installation instructions are very detailed and complete for virtually every platform.

Your RHEL yum repository is likely to have the Ansible RPM in the "extras" directory. If so, then you don't need to get it from the public repository.

## Configuring the public Ansible yum repository

If your RHEL yum repository doesn't have the Ansible RPM, or you want a newer version than what is available in your RHEL repo, then you can get Ansible from the public yum repository, here: https://releases.ansible.com/ansible/rpm/release/epel-7-x86_64/.

NOTE: Install `yum-utils` to get `yum-config-manager`.

To add the public Ansible yum repo do:
```
> yum-config-manager --add-repo https://releases.ansible.com/ansible/rpm/release/epel-7-x86_64/
```
The above command should add a repo to `/etc/yum.repos.d/` that will be named something like: `releases.ansible.com_ansible_rpm_release_epel-7-x86_64_.repo`
```
> ls /etc/yum.repos.d/
docker-ce.repo  redhat.repo  releases.ansible.com_ansible_rpm_release_epel-7-x86_64_.repo  rhel.repo
```
Yum will not access the public Ansible repository unless you install its public key.  The public key did not appear to be available anywhere obvious at the Ansible releases site.  The simple thing to do is edit the repo file and set `gpgcheck=0`.
```
[releases.ansible.com_ansible_rpm_release_epel-7-x86_64_]
name=added from: https://releases.ansible.com/ansible/rpm/release/epel-7-x86_64/
baseurl=https://releases.ansible.com/ansible/rpm/release/epel-7-x86_64/
gpgcheck=0
enabled=1
```
## Installing Ansible
Install yum from your RHEL "extras" repo, or the public Ansible repo, you configured in the previous section.

```
> yum -y install ansible
```

## Configuring Ansible
This section describes some very basic steps required to get Ansible configured to the point where you can start to do things with it.

The Ansible documentation is very good.  Use it to find answers to your questions.  The [Getting Started](http://docs.ansible.com/ansible/latest/intro_getting_started.html) describes what you need to do to get started. The [Introduction to Ad-Hoc Commands](http://docs.ansible.com/ansible/latest/intro_adhoc.html) provides a quick overview on running ad hoc commands through Ansible.

Some things to decide when using Ansible:
- The machine (or machines) to be an Ansible "control machine", e.g., administrator desktop, a "staging" or "jump" server, the ICP "boot" server.  See the Ansible documentation for [Control Machine Requirements](http://docs.ansible.com/ansible/latest/intro_installation.html#control-machine-requirements). If you use your ICP boot server (boot/master0) as an Ansible control server, it already has things set up for root to be able to run Ansible commands to all other nodes in the ICP cluster.
- What user to set up on the control machine(s) and all of the managed nodes that will be used by Ansible to access the managed nodes via SSH using SSH keys. It is recommended (but not required) that the SSH authentication use keys. (We refer to this user as the "*Ansible user*".) The Ansible user needs to be able to use sudo without providing a password to run commands that require root privileges.

The primary configuration tasks:
- Make sure each managed node has the Ansible user ID defined. The Ansible user will need to be able to use passwordless sudo to get root privileges.
- Create an `ssh` key for the Ansible user on the control machine.
- Use `ssh-copy-id` (or something that does the equivalent) to get the public key (`id_rsa.pub`) of the Ansible user on each Ansible control machine in the SSH `authorized_users` file for the Ansible user on each managed node.
- Set up the Ansible `hosts` (in `/etc/ansible` by default) file to defined the managed nodes.

*NOTE:* Use fully qualified domain names (FQDN) or the IP address for the hosts when using the `ssh-copy-id` command or whatever you use to get the Ansible user's SSH key spread around to the managed nodes. If you use the short host name, you will likely get *The authenticity of host 'myhost.mysite.com (xxx.xxx.x.xx)' can't be established.* errors when you try something even as simple as an Ansible ping. Check the SSH `known_hosts` file for the Ansible user on the Ansible control machine to confirm that that the FQDN, and the IP address is listed with the host key if you are not sure about what will be recognized.

*NOTE:* A simple way to provide the Ansible user with passwordless sudo privileges to run any command is to add the Ansible user to the wheel group.  For RHEL the command, `usermod -a -G wheel <ansible_user>` will add the `<ansible_user>` to the wheel group.  You will likely need to edit the `/etc/sudoers` file (using `visudo`) to comment out the default `wheel` entry and uncomment the `NOPASSWD` `wheel` entry.  See sample below:
```
## Allows people in group wheel to run all commands
# %wheel        ALL=(ALL)       ALL

## Same thing without a password
%wheel  ALL=(ALL)       NOPASSWD: ALL
```

- Edit the hosts file in `/etc/ansible/hosts` (convenient) or create your own hosts file that you provide as an argument on the command line (less convenient).

- The ansible `ping` module is the simplest thing to use to smoke test that things are working as desired.
