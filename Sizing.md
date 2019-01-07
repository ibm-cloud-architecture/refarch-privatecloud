# Sizing IBM Cloud Private

The guidelines below have been updated for IBM Cloud Private 3.1.0.  Each ICP cluster will have its own characteristics, but we are attempting to show some sample deployment sizes below.  They have been classified by size and purpose.  The considerations below are focused on clusters deployed to VMware or OpenStack environments.

> Use the included guidelines as just that, guidelines. These are not the "miniums" rather a starting point.  Please provide your feedback from the field.

## Small ICP Environment (Resilience Medium)							

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
| Boot	| 1	| 2	| 8	| 250 |
|	Master	| 3	| 16	| 32	| 500 |
|	Management	| 2	| 8	| 16	| 500 |
|	Proxy	| 2	| 4	| 16	| 400 |
|	Worker - Java Workloads | 3+ (Max:20)	| 8	| 32	| 400 |

This cluster is listed as Medium Resilience with 3 Master nodes.  To make a Sandbox out of this you could deploy a single master and less proxy (Resilience Low).  Consider not combining node types (ie. sharing masters / proxies / management) in order to provide your environment the most flexibility.  The Workers included are shaped for Java workloads.  See the below section on **Consider Your Workload**.

## Medium ICP Environment	(Resilience Medium)							

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
| Boot	| 1	| 2	| 8	| 250 |
|	Master	| 3	| 16	| 32	| 500 |
|	Management	| 2	| 16	| 32	| 500 |
|	Proxy	| 3	| 4	| 16	| 400 |
|	Worker - Java Workloads | 3+ (Max:20)	| 8	| 32	| 400 |
|	Worker | 5+ (Max:70)| 8 | 32	| 400 |
|	VA	| 3	| 6	| 24	| 500 |

This cluster is listed as Medium Resilience with 3 master nodes.  Consider not combining node types (ie. sharing masters / proxies / management) in order to provide your environment the most flexibility.  The Workers included are shaped for Java workloads.  See the below section on **Consider Your Workload**.  To move this to **Resilience High** add two additional master nodes.


## Large ICP Environment (Resilience High)							

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
|	Boot	| 1	| 2	| 8	| 250 |
|	Master | 5 | 16 | 32	| 500 |
|	Management	| 3	| 8	| 32 |	500 |
|	Proxy |	3	| 4	| 16	| 250 |
|	VA |	5	 | 6	| 24	| 500 |
|	Worker | 7+	(Max:150)| 8	| 32	|400 |

This cluster is listed as Highly Resilience with 5 master nodes.  The Workers included are shaped for Java workloads.  See the below section on **Consider Your Workload**.  To move this to a higher level of resilience (or zero RPO) you will be required to deploy and manage workload across multiple ICP clusters.  For very large clusters see the **Large Cluster Considerations** below.

> For all of the above, disk can be Thin Provisioned.

## Consider Your Workload (Worker Nodes)
When determining the number of and resource configuration of your worker nodes, consider the workload that you will be running.
- If your cluster has a small amount of workload consider increasing the number of worker nodes while decreasing the size of the nodes (for adequate headspace, efficiency, mobility, resiliency).
- If you have large pods your worker nodes should be larger to accommodate workload mobility.  In other words consider what happens within your cluster if you lose a worker node (or two).
- Consider the type of workload.  For instance Java workloads typically use 4 x CPU = Memory
- Other application frameworks may be closer to 2 x CPU = Memory

## Storage Consideration for Your Nodes
Coming very soon!

## Proxy Nodes
Considerations for proxy node sizing.  Proxy nodes can be added at any time.
- For resource sizing, consider total resource sizing versus the # of nodes
- You can (and should) tune your ingress controller to match YOUR workload (via config maps)
- Your proxy VIP will point only to a single node at a time
- Consider optionally load balancer to spread workload to your proxy nodes via there external IP
- Istio will also use the proxy node for running ingress and egress gateways

## Management Nodes
Larger clusters with more workload will require larger management nodes.  Management nodes can be added at any time as long as they were originally externalized.  As with proxy nodes, fewer large nodes will have the same impact as many small nodes, but consider the headspace requirements to carry workload due to a node failure.

## Large Cluster Considerations
A few items to consider when planning for very large clusters.  ICP carries additional enterprise capabilities workload above Kubernetes vanilla with the addition of services such as Calico (node to node mesh) and potentially microservice mesh with Istio.  Also considering monitoring, logging, vulnerability assessment.

> This guide currently does not conisder the additional load of running the microservice mesh, please check back, but in the interim have the discussion with your customers that they should consider running Istio in the future and there **will** be a considerable requirement to add resources to worker, proxy and potentially mangement nodes.

Additional items:
- The node-to-node mesh starts to completely break down with 700 nodes in the cluster.  At this point you will require routereflectors for BGP daemons.
- Consider breaking out etcd outside of the master nodes if you plan on having a cluster with several hundred worker nodes.
- Multiple master nodes does not automatically imply load balancing, you are responsible for load balancing your master node requests.
- The number of services in your cluster greatly affects the load on each node.  In large clusters with greater than 5000 services, you will require nodes to run in IPVS mode rather than the default of IPTables.  (IPVS takes additional considerations for deployment).
