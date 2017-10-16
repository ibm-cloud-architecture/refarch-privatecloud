# IBM Private cloud

This project provides guidance on how to deploy IBM Private Cloud

## Architecture

![Architecture](architecture_1.2.jpeg)

## Sizing ICP

See the following page for recommended sizing of ICP environments: [Sizing](Sizing.md)

## Installing ICP

* VMware: [Installing ICP](Installing_ICp_on_prem.md)
* AWS: [Installing ICP on AWS](Installing_ICp_on_aws.md)
* VirtualBow: [Installing ICP on VirtualBox](https://github.com/ibm-cloud-architecture/refarch-privatecloud-virtualbox)

### Deployment using TerraForm
* Terraform Module for provisioning ICP cluster: [terraform-module-icp-deploy](https://github.com/ibm-cloud-architecture/terraform-module-icp-deploy)
* Bluemix Infrastructure (formerly SoftLayer): [Deploy ICP Cluster to SoftLayer](https://github.com/ibm-cloud-architecture/terraform-icp-softlayer)

## Accessing IBM Cloud Private (ICP) through the CLI

[Accessing ICp](Accessing_ICp_through_CLI.md)


## Best practices 

### Storage 

[Storage Best Practices](ICp-Storage_best_practice.md)

See also the following article on working on storage in ICp: [Working with Storage](https://www.ibm.com/developerworks/community/blogs/fe25b4ef-ea6a-4d86-a629-6f87ccf4649e/entry/Working_with_storage?lang=en)

### LDAP

[LDAP Best Practices](ICP%20LDAP%20Best%20Practices.md)

### DevOps

[DevOps Best Practices](Implementing%20DevOps%20for%20IBM%20Cloud.private.md)
