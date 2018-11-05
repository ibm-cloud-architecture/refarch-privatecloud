# Sample Environment Sizing

This document is intended to provide a starting point for sizing an ICP cluster.  It is merely a sample.  Do not make any significant decisions about resource requirements based on this sample.  

*NOTE:* The resource sizing recommendations change from one ICP release to the next. Consult the ICP Knowledge Center for sizing recommendations.  The sizing sample provided in this document is based on ICP 2.1.0.3.

*NOTE:* You **must** test with your expected workloads under expected load conditions and cluster sizes in order to have a good sense for the sizing and number of systems used for your deployments.

*NOTE:* A worker node with 8 CPUs and 32 GB RAM can host ~64 Liberty Containers with memory requests of 512MB each.

*NOTE:* It is a good idea to create a spreadsheet that allows for modifying the number of the various kinds of nodes and the values will ripple through to totals.

# ICP sample sizings

#### Cluster 1: Development/Unit (UNIT) and System Test (SYS)
A shared cluster with isolated resources for DEV and SYS

| Node Type       | Node Count | CPU     | Memory (GB) | Disk (GB)  |
| :--------------:| ----------:| -------:|------------:|-----------:|
|	Boot	          |    1       |   2     |   8         |  280       |
|	Master	        |    3	     |   8     |  32         |  360       |
|	Proxy	          |    2       |   4     |  16         |  240       |
|	Management      |    2       |   8     |  32         |  340       |
|	VA	            |    1       |   8     |  32         |  500       |
|	Worker (x86)    |    8       |   8     |  32         |  250       |
|	Total           |	  17       |  94     | 488         | 5020       |

#### Cluster 2: Production (QUAL/PROD) with DEVOPS TOOLS
The Production cluster will be a shared cluster with isolated resources for QUAL and PROD and also hosts the DEVOPS tools (Jenkins etc)

| Node Type       | Node Count | CPU     | Memory (GB) | Disk (GB)  |
| :--------------:| ----------:| -------:|------------:|-----------:|
|	Boot	          |    1       |   2     |   8         |  280       |
|	Master	        |    3	     |   8     |  32         |  360       |
|	Proxy	          |    3       |   4     |  16         |  240       |
|	Management      |    2       |   8     |  32         |  340       |
|	VA	            |    3       |   8     |  32         |  500       |
|	Worker (x86)    |    2       |   8     |  32         |  250       |
|	Worker (zLinux) |    6       |   8     |  32         |  250       |
|	Total           |	  20       | 142     | 568         | 6260       |


#### Cluster 3: Infrastructure Test (Sandbox)
The infrastructure test cluster provides a sandbox environment to vet out ICP and DevOps tool updates.

| Node Type       | Node Count | CPU     | Memory (GB) | Disk (GB)  |
| :--------------:| ----------:| -------:|------------:|-----------:|
|	Boot	          |    1       |   2     |   8         |  280       |
|	Master	        |    3	     |   8     |  32         |  360       |
|	Proxy	          |    2       |   4     |  16         |  240       |
|	Management      |    1       |   8     |  32         |  340       |
|	VA	            |    1       |   8     |  32         |  500       |
|	Worker (x86)    |    2       |   8     |  32         |  250       |
|	Worker (zLinux) |    2       |   8     |  32         |  250       |
|	Total           |	 12        |  82     | 328         | 3680       |


#### Cluster 4: Disaster Recover (DR)
DR cluster would be a restored version of the production cluster, it does not actually exist until a DR event occurs.

| Node Type       | Node Count | CPU     | Memory (GB) | Disk (GB)  |
| :--------------:| ----------:| -------:|------------:|-----------:|
|	Boot	          |    1       |   2     |   8         |  280       |
|	Master	        |    3	     |   8     |  32         |  360       |
|	Proxy	          |    3       |   4     |  16         |  240       |
|	Management      |    2       |   8     |  32         |  340       |
|	VA	            |    3       |   8     |  32         |  500       |
|	Worker (x86)    |    2       |   8     |  32         |  250       |
|	Worker (zLinux) |    6       |   8     |  32         |  250       |
|	Total           |	  20       | 142     | 568         | 6260       |


-------------------
### Alternate Option - Dedicated DevOps
The DevOps tools will be located in a dedicated fifth cluster.  The other clusters remain defined as-is in the first option.

Breaking out a cluster dedicated to DevOps provides separation of concerns and avoids resource contention issues between the DevOps tools and the other workloads that may be running in the DEV/TEST/QUAL/PROD clusters in the first option.

#### DevOps Cluster
The DevOps cluster will host the DEVOPS tools (Jenkins etc)

The DevOps cluster does not need `Vulnerability Advisor` nodes.  It only needs 2 `Proxy` nodes and 1 `Management` node.

The DevOps cluster has 2 `zLinux` worker nodes and 2 `x86` worker nodes.


| Node Type       | Node Count | CPU     | Memory (GB) | Disk (GB)  |
| :--------------:| ----------:| -------:|------------:|-----------:|
|	Boot	          |    1       |   2     |   8         |  280       |
|	Master	        |    3	     |   8     |  32         |  360       |
|	Proxy	          |    2       |   4     |  16         |  240       |
|	Management      |    1       |   8     |  32         |  340       |
|	Worker (x86)    |    2       |   8     |  32         |  250       |
|	Worker (zLinux) |    2       |   8     |  32         |  250       |
|	Total           |	  11       |  74     | 296         | 3180       |
