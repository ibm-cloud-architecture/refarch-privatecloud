# Special RHEL configuration

The sub-sections in this section describe RHEL configuration that is not typical.  Even on a VM provided to you, you will very likely need to take the steps described in these sub-sections in order to prepare the machine to be a member of an ICP cluster.

## vm.max_map_count

The map_max_count determines the maximum number of memory map areas a process can have. Docker requires that the max_map_count be substantially greater than the default (65530).  This section describes the steps to setting the `vm.max_map_count` to an appropriate number.

*NOTE:* Do not confuse the `sysctl` command with the `systemctl` command. The command for getting and setting system (kernel) parameters is `sysctl` not `systemctl`.

To make an immediate change to the `vm.max_map_count` system parameter:
```
sysctl -w vm.max_map_count=262144
```

*NOTE:* The above command writes the value of max_map_count to the file `/proc/sys/vm/max_map_count`. However, the `vm.max_map_count` will revert to its default value on reboot.

*NOTE:* Consult your system administrator to determine the preferred place to persist the value of `vm.max_map_count`.

In order to have the `vm.max_map_count` carry over through a reboot, edit the `/etc/sysctl.conf` file and add a line to define the value:
```
vm.max_map_count=262144
```
or
```
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
```

If you want to see the value of a system control variable just use: `sysctl <name>`, e.g.,
```
sysctl vm.max_map_count
```

## Delete the /var/lib/mysql directory

If the `/var/lib/mysql` directory exists on any of the ICP cluster VMs, the install will fail on that VM. At least on some RHEL 7 installations, it seems mysql gets a directory in `/var/lib` even if it is not used for anything.  

- On all VMs in the cluster/cloud, make sure there is no `mysql` directory in `/var/lib`, i.e.,

  ```
  rmdir /var/lib/mysql
  ```
