IBM Cloud Private on Red Hat Enterprise Linux v7
=============================================

This is the top level document that serves as a guide to other documents that capture the installation of IBM Cloud Private v3.1.0/v3.1.1 on Red Hat Enterprise Linux v7. (RHEL v7.3, 7.4 or 7.5)

# ICP installation documents

[General Introduction](general-introduction.md)

[Getting Started Overview](getting-started-overview.md) - A high level view of deploying an ICP cluster.

[General System Requirements](icp-system-requirements.md) - The detailed CPU, memory and file system requirements for the machines that make up the ICP cluster are described in this document.

[Basic RHEL Configuration](basic-rhel-configuration.md) - A guide that describes the basic RHEL configuration needed by IBM Cloud Private.

[Additional Packages](additional-packages.md) - Itemized list of certain packages that are very useful to install on ICP cluster nodes. Some packages are only needed on the `boot` node, whether that is a dedicated node, or a `master` node is used as the `boot` node.

[Configure passwordless SSH](configure-passwordless-ssh.md) Configure passwordless `ssh` for root from the boot node to all cluster member nodes including the boot node.  This allows Ansible to be used for various pre-installation steps.  This is also a pre-requisite to running the ICP inception install process.

[Special RHEL Configuration](special-rhel-configuration.md) - Things that need to be configured for IBM Cloud Private that are not usually part of a stock RHEL configuration.

[Install Docker](rhel-install-docker-using-overlay2.md) Instructions for installing Docker using the installation executable provided with ICP at Passport Advantage (external) or eXtreme Leverage (IBM internal)

[Outline for Sample HA Installation](sample-icp-ha-installation-step-by-step.md) - An outline of the steps involved in standing up an ICP environment.  Details for each step are not provided in this document.  See other documents for details.

[Install ICP 3.1.0](icp310-installation.md) - ICP 3.1.0 installation guide given all the pre-installation steps have been completed, i.e., *basic* and *special* RHEL configuration, Docker installation, etc.  A document that describes the specific steps for an ICP 2.1.0.3 installation is still part of the collection, but no longer linked in this top level guide.

[ICP `config.yaml` details](icp-config-yaml-details.md) Typical `config.yaml` settings used for non-HA and HA deployments of ICP.

[GlusterFS for shared storage running on RHEL](glusterfs-shared-storage-running-on-rhel.md) - This document describes the installation of a GlusterFS cluster and the supporting Heketi server as well as the allocation of shared volumes for use by the ICP master nodes when an HA topology is deployed.

[Configure Kubernetes Storage Class for GlussterFS](glusterfs-kubernetes-storageclass.md) Details on configuring a Kubernetes Storage Class that uses the GlusterFS provisioner that uses the Heketi server.

[Update Prometheus Resources from Default Settings](update-prometheus-resources.md) - This document describes the resource updates made to the Prometheus deployment to resolve the out of memory issue that occurs with larger ICP implementations.

[Prometheus Alerts](https://github.com/ibm-cloud-architecture/CSMO-ICP/tree/master/prometheus/alerts_prometheus2.x) - This document provides a base set of alerts for ICP environments.

[Kibana Updates](update-kibana-clustername.md) - This document provides a procedure to update Kibana to support custom cluster names. This is required if you change the **cluster_domain** setting in the `config.yaml`.

# Additional documentation

[RHEL 7 Installation - A sample](rhel7-installation-a-sample.md) - Step-by-step guide to installing RHEL 7 on VM deployed on VMware ESX hosts.  This is intended merely as a sample for people who are not familiar with a RHEL installation.

[RHEL 7 Network Interface Overview](rhel7-network-interface-overview.md) - Background on RHEL 7 network interface administration for people not experienced with Linux and RHEL.

[RHEL 7 System Parameters Overview](rhel7-system-parameters-overview.md) - Background on Linux system parameters for people not experienced with Linux and RHEL.

[Yum Repository Configuration](yum-repository-configuration.md) - Guidance on configuring `yum` repositories for those not experienced with RHEL.

[Install NTP](install-ntp.md) - Steps to install the `ntpd`, should it be needed.  See also the Ansible playbook,  [`install-ntp.yaml`](playbooks/icp-preinstall/install-ntp.yaml).

[Kubernetes Basics](kubernetes-basics.md) - Rudimentary Kubernetes information sufficient to get started in the context of using ICP.

[Docker Basics](docker-basics.md) - Rudimentary Docker information sufficient to get started in the context of using ICP.

[Getting Started with Ansible](getting-started-with-ansible.md) - Rudimentary Ansible information sufficient to get started in the context of deploying ICP.

[Getting Started with Heketi Client](heketi-client-getting-started.md) - Rudimentary information sufficient to get started using the Heketi client in the context of ICP.

[ICP Networks, DNS, PKI certificates and LDAP](icp-networks-dns-certs-ldap.md) - A collection of notes regarding the topics of networks, DNS, PKI certificates and LDAP in the context of an ICP deployment.

[Install Python Docker Support](install-python-docker-support.md) - Steps to install Python Docker support libraries for those who want to interact with Docker in the context of a Python script. Completely optional, and not needed for ICP deployment or administration.
