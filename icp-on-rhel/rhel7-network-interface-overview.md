# RHEL 7 network interface overview

This document describes some basic information about networking for RHEL 7.

RHEL 7 networking is controlled by the Network Manager (network service). Normally the network service will be running and it will be started at boot time.

The usual `systemctl` commands are used for dealing with the network service.
```
systemctl status|start|stop|restart network
```
For example:
```
systemctl status network
network.service - LSB: Bring up/down networking
Loaded: loaded (/etc/rc.d/init.d/network; bad; vendor preset: disabled)
Active: active (exited) since Thu 2017-06-29 16:51:39 EDT; 2 days ago
Docs: man:systemd-sysv-generator(8)
...
```
Even though the network service may be running, that does not mean a particular network interface is running.

To view the status of the network interfaces on a machine (and to get the names of the interfaces) use the `ip addr` command.  (The `ip addr` command is the replacement for `ifconfig -a` and on occasion provides more accurate information about the network interfaces than `ifconfig -a`.)
```
ip addr
```

The commands for starting and stopping a network interface are `ifup` (start), `ifdown` (stop).  You need to provide the interface name.

For example, suppose the name of the interface is `ens33`.

To stop the ens33 interface:
```
ifdown ens33
Device 'ens33' successfully disconnected.
```
To start the ens33 interface:
```
ifup ens33
Connection successfully activated (D-Bus active path: /org/freedesktop/NetworkManager/ActiveConnection/5)
```
The `ifup` and `ifdown` commands work through the Network Manager (i.e., the network service).

For a lot more details on RHEL 7 networking see the various sections in the [Introduction to Red Hat Enterprise Linux Networking](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/networking_guide/ch-introduction_to_rhel_networking) chapter of the RHEL documentation.
