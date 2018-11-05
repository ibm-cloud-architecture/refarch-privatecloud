Update Kibana to support a custom cluster name
=============================================

## Overview
The installation of IBM Cloud Private v2.1.0.3 installs Kibana as part of the ibm-icplogging-kibana Helm chart if the Kibana option is selected in the config.yaml. This new method of installation does not properly update the Helm deployment to use a custom cluster domain. This presents itself as a problem after installation where the Kibana gui fails to load and in the log output for the Kibana pod we see that the authentication request to xxx.cluster.local results with a hostname not found. The cluster.local part of the hostname is the default setting typically found in the config.yaml and in most cases customers will want to change that value.

In this document we will outline how to update the deployment resources for Kibana to enable it to suport the custom cluster domain name.

Procedure
------------

**Update the logging-elk-kibana deployment**
1. Navigate to the **Hamburger Menu -> Workloads -> Deployments**
2. Find the **logging-elk-kibana** deployment 
3. From the action menu on the right click **Edit**
4. Search for the **CLUSTER_DOMAIN** setting in the deployment JSON
5. Update the value to match the **cluster_domain** setting found in config.yaml

**Once the deployment is updated we need to restart the management ingress pod.**
1. Navigate to **Hamburger Menu -> DaemonSets**
2. Find **icp-management-ingress** and click the link
3. From the Pods section click remove from the action menu
4. Wait for the new Pod to be running (the pod name should change)
5. Then try to use the **Hamburger Menu -> Platform -> Logging** item.
