## Install NTP

Some mechanism is needed on each VM to keep the time synchronized with the rest of the world.  All of the VMs in the ICP cluster will need to share a common notion of time, and the usual approach to keeping time is to use NTP.  

*NOTE:* If you are using virtual machines provided to you, it is very likely NTP is already installed and enabled for startup at machine boot.

*NOTE:* If you are using virtual machines provided to you, and NTP is not installed and in use, the VMs may be using some other time provider, such as the hypervisor.  Check with your provider to determine if it is necessary to install NTP.

- Install NTP

    ```
    yum -y install ntp
    ```

-	Check the NTP configuration in `/etc/ntp.conf`

See the Red Hat documentation, [Configure NTP](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/s1-configure_ntp), for more detailed guidance.

*NOTE:* The default `/etc/ntp.conf` content is likely sufficient.  You may want to add one or more local time providers to the list of servers provided by Red Hat:
```
server 0.rhel.pool.ntp.org iburst
server 1.rhel.pool.ntp.org iburst
server 2.rhel.pool.ntp.org iburst
server 3.rhel.pool.ntp.org iburst
```
- Enable the NTP daemon.  (This will make sure ntpd starts up when the machine is booted.)

  *NOTE:* The name of the service is **ntpd**, not ntp.  (Go figure.)
  ```
  systemctl enable ntpd
  ```

- Start the NTP service.
  ```
  systemctl start ntpd
  ```

- Check the NTP service status.
  ```
  systemctl status ntpd
  ```

- If you need to stop the NTP service:
  ```
	systemctl stop ntpd
  ```

- To get a list of peer servers in use:
  ```
	ntpq -p
  ```

*NOTE:* Leave NTPD started and enabled (so that it starts at boot time).
