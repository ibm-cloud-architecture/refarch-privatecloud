# Sizing IBM Cloud Private

Although each ICP deployment will have its own characteristics, this is a simple T-shirt size for ICP deployment on the VMware environment.

Use it simply as a guide for your deployment, especially regarding the number of Worker nodes.

## Small ICP environment

| Node type | Number of nodes | CPU | Memory | Disk |
| --- | --- | --- | --- | --- | 
| Master | 3 | 4 | 16 GB | 200 GB |
| Worker | 3 | 4 | 8 GB | 100 GB |
| Proxy | 3 | 2 | 4 GB | 25 GB |

## Medium ICP environment

| Node type | Number of nodes | CPU | Memory | Disk |
| --- | --- | --- | --- | --- | 
| Master | 3 | 4 | 32 GB | 300 GB |
| Worker | 5 | 4 | 8 GB | 100 GB |
| Proxy | 3 | 4 | 8 GB | 25 GB |

## Large ICP environment

| Node type | Number of nodes | CPU | Memory | Disk |
| --- | --- | --- | --- | --- | 
| Master | 5 | 4 | 64 GB | 500 GB |
| Worker | 7 | 8 | 16 GB | 100 GB |
| Proxy | 5 | 4 | 8 GB | 25 GB |
