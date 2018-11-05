Update Prometheus Resource Limits after ICP Installation
=============================================

## Overview
The installation of IBM Cloud Private installs Prometheus running with a default set of resource limits. These limits are fine for smaller 
development/test installations of ICP. For larger installations (i.e. HA, Cloud Native or Enterprise installations) with many nodes the 
default resource limits may not be sufficient for Prometheus to run. The basic symptom is the monitoring-prometheus pod will keep crashing 
and restarting (CrashLoopBackOff). If we run a "kubectl describe pod" against the monitoring-prometheus pod you will see a 137 exit code
with OOMKill.

In this document we will outline how to update the resources for Prometheus to enable it to monitor larger environments.


Configuration
------------

1.  Login to a system with access to kubectl
2.  Navigate to Hamburger -> Workloads -> Deployments
3.  Find the monitoring-prometheus deployment
4.  From the action menu choose Edit to edit the deployment
5.  Find the **monitoring.prometheus.resources.limits** section. It should look like this
    ```  
    "resources": {
      "limits": {
        "cpu": "500m",
        "memory": "512Mi"
      },
      "requests": {
        "cpu": "100m",
        "memory": "128Mi"
      }
    ```
6.  Increase the limits
    ```
    "resources": {
      "limits": {
        "cpu": "5000m",
        "memory": "4096Mi"
      },
      "requests": {
        "cpu": "100m",
        "memory": "128Mi"
      }
    ```
> **Note:** Depending on the timing you may receive an error that the deployment cannot be updated. Just renter the edit action and try again.
	
7. Updating the deployment should trigger a restart of the pod to pick up the changes. 
8. Verify the new resource limits. Click new pod link, Containers Tab, prometheus link. 
Or running the cli below substituting the actual pod name for **monitoring-prometheus-xxxxx-xxxxx**
   ```
   kubectl describe pod -n kube-system monitoring-prometheus-xxxxx-xxxxx
   ``` 

**From the CLI**
1.  Set new resource limits
    ```
    kubectl set resources deployment monitoring-prometheus -c=prometheus -n kube-system --limits=cpu=5000m,memory=4096Mi
    ```
2.  Verify the updated resources
	```
	kubectl get deployment monitoring-prometheus -n kube-system  -o json | jq '.spec.template.spec.containers' | jq '.[] | select(.name=="prometheus")' | jq '.resources'
	```
3.  Restart pod if needed substituting the actual pod name for **monitoring-prometheus-xxxxx-xxxxx**. 
The resource change should trigger a restart of the pod.
    ```
    kubectl delete pod -n kube-system monitoring-prometheus-xxxxx-xxxxx	
	```
  