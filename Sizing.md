# Sizing IBM Cloud Private

Although each ICP deployment will have its own characteristics, this is a simple T-shirt size for ICP deployment on the VMware environment.

Use it simply as a guide for your deployment, especially regarding the number of Worker nodes.

## Small ICP Environment								

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
| Boot	| 1	| 2	| 8	| 250 |
|	Master/Management	| 3	| 8	| 32	| 250 |
|	Proxy	| 3	| 4	| 16	| 250 |
|	Worker | 3+ (Max:20)	| 8	| 32	| 250 |
|	Total  | 10+	| 62	| 248	| 2500 |				


## Medium ICP Environment								

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
|	Boot	| 1	| 2	| 8	| 250 |
|	Master	| 3	| 8	| 32 | 250 |
|	Management | 2	| 8	| 32 | 300 |
|	Proxy	| 3	| 4	| 16 | 250 |
|	VA	| 3	| 6	| 24	| 500 |
|	Worker | 5+ (Max:70)| 8 | 32	| 250 |
|	Total |	17+	| 112	| 448	| 5100 |				


## Large ICP Environment								

| Node type | Number of nodes | CPU | Memory (GB) | Disk (GB) |
| :---: | :---: | :---: | :---: | :---: |
|	Boot	| 1	| 2	| 8	| 250 |
|	Master | 5 | 8 | 32	| 250 |
|	Management	| 3	| 8	| 32 |	300 |
|	Proxy |	3	| 4	| 16	| 250 |
|	VA |	5	 | 6	| 24	| 500 |
|	Worker | 7+	(Max:150)| 8	| 32	|250 |
|	Total |	24+ |164	| 656 |	7400 |

**Note:** Disk space can be Thin Provisioned.
