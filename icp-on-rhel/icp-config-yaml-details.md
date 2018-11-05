# ICP `config.yaml` content

This document provides guidance for the attributes in the `config.yaml` file that may be modified for a given deployment.  A lot of the `config.yaml` content may be left at its default value depending on the particular deployment scenario.

If a particular parameter setting is not listed in the table, the default value was used.

For a detailed explanation of the `config.yaml` parameters see the IBM Cloud Private KC section, [Customizing the cluster with the config.yaml file](https://www.ibm.com/support/knowledgecenter/en/SSBS6K_2.1.0.3/installing/config_yaml.html)

For more explanation of the purpose for the more commonly used parameters also see the ICP Networking section of [IBM Cloud Private Network, DNS, PKI Certificates, LDAP](icp-networks-dns-certs-ldap.md)


| Parameter Name   |  Default Value           | Custom Value      | Comments     |
|------------------|--------------------------|-------------------|--------------|
|cluster_name      | mycluster                |                   |              |
|cluster_domain    |                          | leave this at the default for ICP 3.1.0. |              |
|cluster_CA_domain | "{{ cluster_name }}.icp" |                   | This value must match the CN used for the PKI certificate created for access to the ICP admin console. |
|disabled_management_services | ["istio", "vulnerability-advisor", "custom-metrics-adapter"] |  | include whatever is not of interest  |
|docker_version   | ICP version specific   |  | Always use the default  |
|install_docker   |true   |false   | We recommend pre-installing docker on all cluster nodes before running the inception installation to ensure the `overlay2` storage driver and `xfs` file system are properly configured. It is expedient to have docker running at the time of the inception install is launched.|
|docker_extra_args | ["--storage-driver=devicemapper"] |["--storage-driver=overlay2"] |   |
|docker_log_max_size   | 50m  | 50m  |   |
|docker_log_max_file   |  10 | 10  |   |
|vip_iface         | eth0  | The name of the NIC on the master VMs  | The NIC to be assigned the `cluster_vip`  |
|cluster_vip   | 172.16.12.123  | An "extra" IP address  | The VIP used to access the currently active master node. Only needed for multi-master deployments with no master node load balancer.  |
|proxy_vip_iface   | eth0   | The name of the NIC on the proxy VMs | The NIC to be assigned the `proxy_vip`   |
|proxy_vip   | 172.16.12.123  | An "extra" IP address  | The VIP used to access the currently active proxy node. Only needed if more than one Proxy is deployed with no proxy load balancer.  |
|metrics_max_age   | 1  | Typically the default is used.  | Number of days to store system and application metrics. Metric loads may consume a lot of disk space.  |
|logs_maxage   |   | 1  | Clean application log indices in Elasticsearch older than this number of days  |
|kibana_install   | false  | true  | Include Kibana in the ICP installation and integrate Kibana access through ICP console  |
