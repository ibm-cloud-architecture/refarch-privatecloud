# Ansible recipe for preparing nodes for ICP installation

# WORK IN PROGRESS

This recipe provides all needed pre-requisites for installing ICP.  In order for these scripts to work the ICP nodes should be installed with the basic operating system only.  Use the recipe for the operating system you have installed on the ICP nodes.

All nodes should have a user created (with the same user name for all nodes) that has sudo privileges.

If each node has been provisioned with DHCP and the user can specify the static IP address that should be used for each node and ansible will properly configure static IP addresses.
