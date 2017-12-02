# IBM Cloud Private - High Availability Considerations

*CAVEATS:*
* The information contained in this document are personal preferences based on years of experience and are not official IBM recommendations.
* This document covers High Availability only and does not meaningfully cover Disaster Recovery (DR).  This will be addressed cursorily only.

High availability (HA) for applications in any environment depend upon the availability of the infrastructure on which they run.

In a containerized application, this includes the physical infrastructure (including compute, networking, and storage), the virtual infrastructure (hypervisors), the container infrastructure (docker), and the application itself.  In this document we will discuss each of these layers in turn.

## Power and Cooling Infrastructure
High availability in the datacenter depends upon highly available power and Computer Room Air Conditioning (CRAC).

The datacenter should have at least two CRAC units which are capable of cooling the room in the event one of the units fails.

Similarly, the datacenter should have two Power Distribution Units (PDUs), each capable of handling the load of the entire room.

Each rack in the datacenter will then have two local PDUs (on on each side), each attached to separate room PDUs.

Each physical infrastructure component (servers, switches, SAN arrays, etc.) should have at least two power supplies, evenly distributed to each rack PDU.

With this architecture, the failure of a room PDU, rack PDU, or component power supply will not be enough to cause an outage.

## Compute Infrastructure
Highly available compute infrastructure has a number of components and with bare metal compute infrastructure, high availability requires redundancy.

In most systems, basic components of a compute node include the system board, storage (local and SAN), and networking. System administrators have no control over the architecture of the system board, however storage and networking components can easily be made redundant.

### Local Disk Storage
Local storage (hard disk) is made redundant via RAID configuration. A best practice for cloud storage is to put all workloads on SAN storage with only the operating system running on local storage.  This is accomplished with RAID-1 (mirroring) for a system with 2 disks or, RAID-5, RAID-6, or RAID-10, etc. for a system with three or more drives.

Performance in such an environment is not critical since most disk I/O is to the SAN storage and not to the local disk. For this reason, I use two hard drives, mirrored for high availability.

### SAN Storage
High availability in a virtual environment normally requires a common data store. This means that all virtual disks associated with virtual machines should be stored on SAN volumes which can be mounted by multiple compute nodes simultaneously.

Such environments must employ technology for managing simultaneous reading and writing of data to a common filesystem to avoid race conditions.

VMware ESXi provides this capability with no additional configuration required. KVM and other hypervisors require special consideration.

### High Performance Computing
High Performance Computing (HPC) normally involves multiple compute nodes running within a single chassis.

In such an environment, high availability of the chassis is also a requirement.  If the chassis fails, so do all of the compute nodes in the chassis.

For this reason, compute chassis' are normally architected with redundancy built into the chassis.  This will include two separate back planes, two network switches, two SAN switches, two chassis management modules, and multiple power supplies.

The result is an environment where the failure of any single component cannot cause an outage of the entire chassis. A chassis without full redundancy of each component will result in a single point of failure and a loss of high availability.

## SAN Network Infrastructure
High availability of SAN infrastructure is achieved by maintaining separate and duplicate fabrics.  Having dual SAN interfaces in each compute node allows it to communicate on both SAN fabrics. SAN volume controllers are then connected to each fabric providing two or more physically separate and redundant paths to each compute node.

Most SAN chassis' will have two redundant controllers with two fiber channel interfaces each.  This makes for redundant links to each SAN fabric resulting in four total paths from each compute node to each SAN array.

Multipathing technology running on the operating system of the compute node consolidates communication across all available paths for full HA in the SAN environment.

[[ Insert dual SAN fabric architecture here]]

## Data Network Infrastructure
Data networking in a cloud environment is different than that of a traditional datacenter network.

Traditional datacenter networks are optimized for north-south traffic, this means networks are designed for clients sitting on the edge communicating with servers running in the core.

In cloud datacenters, however, data traffic is normally east-west, meaning applications running on one node will communicate with services running on other nodes within the same datacenter.

In a highly virtualized environment the application, the service, and the router could be running in separate virtual machines (VMs) on the same physical compute node.

If the application and service are on separate subnets, network traffic could have to traverse multiple layers of network switches (chassis, top of rack, core) to get to the router and then take the opposite path to get back to the other VM even though the application, service, and router are all located on the same physical compute node and share the same physical NIC.

To reduce this kind of overhead and significant additional congestion, Software Defined Networking (SDN) technologies are highly favorable.

In an SDN environment (such as VMware's NSX), each hypervisor contains a router component which is controlled by the SDN controller.  Traffic which is destined for a VM on the same physical compute node is routed within the the hypervisor rather than having to traverse the entire network (twice) for these components to communicate.

This SDN technology helps to optimize east-west traffic and maximize efficiency in a cloud enabled datacenter.

The underlying physical infrastructure, however, must still be highly available.  It can be less intelligent since all routing capabilities are handled in the SDN, but the basic architecture of the physical data network still needs to be redundant and it should be as flat as possible.

Redundancy of the physical network begins with redundancy of the NICs in the physical compute nodes.  At the operating system level, these two NICs are bonded together such that they provide both redundancy and link aggregation.

with link aggregation, bonded 1Gb/s NICs is capable of communicating with the core at 2Gb/s (assuming both are up and avaiable), and a 10Gb/s NIC can communicate at 20GB/s.

At the core, each NIC on the compute node (or chassis switch in the HPC chassis) is connected to a separate core switch.  This will require two core switches which are also connected together via virtual link aggregation protocol (vLAG) and/or Link Aggregation Control Protocol (LACP).

When configured with dual network paths from each compute node to the core, a failure of any single network device will not cause an outage.

Redundancy of network routers can be handled via the SDN or something like Virtual Router Redundancy Protocol (VRRP) or Hot Standby Router Protocol (HSRP).  A discussion of this technology is beyond the scope of this document.

[[ Redundant network architecture diagram here]]

## Virtualization Infrastructure
High availability of the virtual infrastructure is different based on the hypervisor provider.  This document will be limited to VMware which commands as much as 70% or more of the hypervisor market.

High availability requires multiple hosts (physical machines running a hypervisor) configured within compute cluster.

For the most highly available infrastructure when running in an HPC environment, compute nodes within a virtualization cluster should be evenly distributed across available chassis'. In this way, the environment can recover from the failure of an entire chassis.

In a VMware environment, vSwitches should be configured with vMotion enabled and clusters should be configured for Dynamic Resource Scheduler (DRS) and HA.

This requires that all hosts in the cluster store their virtual disks on a common datastore.  When a VM in an HA configuration fails it is automatically restarted on another host in the cluster.

In addition, with vMotion and DRS enabled, resources can be actively moved between hosts and datastores in the cluster to balance the load and minimize outages due to overprovisioning.

[[ VMware high availability architecture ]]

## Container Architecture
The most functional, portable, scalable, and highly available cloud platform available today is a containerized platform and the most prevalent container technology is Docker.

Whereas containers alone provide some improved capabilities in the area of portability, to realize the full potential of continer technology requires an orchestration engine and the most prominent such engine today is kubernetes.

IBM Cloud Private includes an implementation of kubernetes as well as (optionally) an implementation of CloudFoundry (which also uses container technology, although a different type of container).

### kubernetes
A highly available kubernetes environment includes an odd number of master nodes (greater than one), and two or more worker nodes.

In this configuration, the master nodes communicate with each other an elect an active master.  The others are on host standby.  If the other master nodes lose communication with the active master they will negotiate a new master to continue controlling the cluster.

With two or more worker nodes, when multiple instances of a pod (one or more containers, grouped together) are instanciated, the master node will ensure that they are evenly distributed amongst the available worker nodes.

So, if the kubernetes installation contains three worker nodes and the deployment asks for three pods, kubernetes will ensure each pod is running on a separate worker node.

When deploying multiple pods in this way, a service is also created which acts as a load balancer between all of the pods. This way any process trying to communicate with a microservice running in a pod hits the service address and the service will load balance between the various pods.

In this design, if any worker node fails, there is no outage of the application because there are still additional instances running in other pods on other worker nodes.

The more pods (instances of the application) that are run the more resilient the application will be.

Because more pods can also handle higher loads, this also provides for application elasticity.

An application which is written based on 12 factor principles is perfectly suited to take advantage of these kubernetes capabilities.

This mechanism also allows for deploying application updates in a blue-green configuration where one of the pods (in a multiple pod implementation) is running a newer version for some period of time to test and make sure it is working as designed. If not, only transactions that are assigned to that pod will fail and it can rolled back to a previous version.

If the new version works as designed, the operator can simply kill the instances of the older version and they will be re-spawned by kubernetes using the newer version.

Importantly, in a micro-services based architecture, a failure of any single component does not cause an outage of the entire application, only that single component, and when deployed in a blue-green configuration (as discussed), a failure will only affect transactions being processed by a single pod, which can be detected and resolved quickly.

### CloudFoundry
Deploying IBM Cloud Private CloudFoundry (CF) in a highly available configuration involves deploying redundant instances of each CF component on a highly available virtualization infrastructure.

When deploying a "production" environment, the CF installer will create an HA deployment (doing a "poc" installation will result in a non-HA deployment).

Application developers in a CF environment, however, do not have as much control over how HA is implemented as they do in a kubernetes environment.

CloudFoundry provides an easier deployment platform for developers whereas kubernetes provides a more configurable deployment.

## Application Architecture
However highly available the virtual and physical infrastructure may be, if the application is not designed to be highly available, a single bug can cause a service outage.

To provide for a highly scalable and highly resilient application, a containerized, [12 factor](https://12factor.net/) application utilizing microservices is optimal.

In a 12 factor app, each functional aspect of the application is broken out into a separate microservice which performs only that function.

Each microservice then has its own development lifecycle and can be updated with new features or bug fixes independent of all other microservices.

Importantly, as previously noted, a single bug in a single microservice cannot take down an entire application, especially in a Continuous Integration/Continuous Development (CI/CD) environment, where blue-green deployment methodologies are employed.

## Conclusion
HA in a private cloud environment must be designed from the physical layer all the way through the application layer.

How highly available an environment can be approaches 100% barring a natural disaster or catastrophic power outage.  How HA it *should* be becomes a business decision and is based on the business' tolerance for data loss and length of outages.

## Disaster Recovery
Disaster Recovery (DR) in a private cloud environment is a much more difficult challenge with a number of different options based on the tolerance for data loss and length of outages.

Ideally, an HA environment as described above would be spread across geographically dispursed datacenters with low latency network connections.

In such an environment, DR is achieved simply by physical separation of resources such that a natural disaster could not affect all included datacenters.

In a fully cloud native environment which utilizes a decentralized datastore (such as CleverSafe) or microservices which write the same data to multiple databases with one write operation, it may be possible to achieve very close to 100% availability via a robust application architecture and HA environments in each respective datacenter.
