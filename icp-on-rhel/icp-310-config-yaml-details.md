# ICP `config.yaml` content

This document provides guidance for the attributes in the `config.yaml` file that may be modified for a given deployment.  A lot of the `config.yaml` content may be left at its default value depending on the particular deployment scenario.

If a particular parameter setting is not listed in the table, the default value was used.

For a detailed explanation of the `config.yaml` parameters see the IBM Cloud Private KC section, [Customizing the cluster with the config.yaml file](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_3.1.0/installing/config_yaml.html)

For more explanation of the purpose for the more commonly used parameters also see the ICP Networking section of [IBM Cloud Private Network, DNS, PKI Certificates, LDAP](icp-networks-dns-certs-ldap.md)


- **cluster_name** The default value is `mycluster`
- **cluster_domain**    leave this at the default for ICP 3.1.0. There is a defect in the installation of MongoDB that requires the `cluster_domain` to be `cluster.local`.
- **cluster_CA_domain**  "{{ cluster_name }}.icp"   This value must match the CN used for the PKI certificate created for access to the ICP admin console.
docker_version   ICP version specific  Always use the default
- **install_docker**   The default is true. Use false. We recommend pre-installing docker on all cluster nodes before running the inception installation. Preinstalling Docker allows you to ensure the `overlay2` storage driver and `xfs` file system are properly configured. If there are Internet proxies that need to be configured, we recommend that be done before the ICP installation. (See the [IBM Cloud Private Installation behind an HTTP Proxy](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_3.1.0/installing/install_proxy.html)) In general, it is expedient to have docker running at the time of the inception install is launched.
- **docker_extra_args** Default: ["--storage-driver=devicemapper"]  Since we are installing docker before installation and setting install_docer to false, the value of this parameter does not matter.  If you are letting the ICP installer install docker then set this to: ["--storage-driver=overlay2"]
- **vip_iface** Default: `eth0` The name of the NIC on the master VMs. The NIC to be assigned the `cluster_vip`.
- **cluster_vip** An "extra" IP address. The VIP used to access the currently active master node. Only needed for multi-master deployments with no master node load balancer.  *NOTE: If you are using a load balancer for the master nodes, then a `cluster_vip` is not necessary, at least on paper.  However, we have seen that during the ICP installation, it may be necessary to have a `cluster_vip` defined.  More investigation is needed to confirm.*
- **proxy_vip_iface**  Default: `eth0`  The name of the NIC on the proxy VMs. The NIC to be assigned the `proxy_vip`  
- **proxy_vip**: 127.0.1.1  An "extra" IP address. The VIP used to access the currently active proxy node. Only needed if more than one Proxy is deployed with no proxy load balancer.
