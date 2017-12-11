Federating ICP v2.1 Clusters
=======================================================
# Introduction

This is a guide for federating two or more ICP v2.1 clusters.

The guide here also references the approach documented by at [Kubernetes Federation for on-premises clusters](https://github.com/ufcg-lsd/k8s-onpremise-federation)

Here is the federation topology:
![icp_federation.png](images/icp_federation.png)

The information in this guide is based on federating on-premises ICP clusters.  ICP is running Kubernetes.  The federation of ICP clusters is essentially the federation of Kubernetes clusters.

This guide is based on using two ICP v2.1 clusters.  For purposes of this document, one cluster is referred to as FC01 and the other cluster is referred to as FC02.

The federation work is done on the bootmaster VM of each ICP cluster:
```
fc01-bootmaster01
fc02-bootmaster01
```

The ICP home directory on the bootmaster VM is referred to as `ICP_HOME` in this document.  (The actual directory may appear in some code samples, and it is: `/opt/icp`.)

# Prepare the federation environments
This section describes some preliminary steps required to get prepared to do the federation.

## Install kubectl and kubefed

You need kubectl and kubefed cli for much of the configuration work.  On a machine where ICP has been installed (recommend the ICP bootmaster node), run following command:

```
# Linux
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/kubernetes-client-linux-amd64.tar.gz
tar -xzvf kubernetes-client-linux-amd64.tar.gz
```

Copy the extracted binaries to one of the directories in your $PATH and set the executable permission on those binaries.

```
sudo cp kubernetes/client/bin/kubefed /usr/local/bin
sudo chmod +x /usr/local/bin/kubefed
sudo cp kubernetes/client/bin/kubectl /usr/local/bin
sudo chmod +x /usr/local/bin/kubectl
```

You can run something simple from the command line like `kubectl version`, to confirm that kubectl is available in your shell.
```
# kubectl version
Client Version: version.Info{Major:"1", Minor:"7+", GitVersion:"v1.7.3-11+f747daa02c9ffb", GitCommit:"f747daa02c9ffba3fabc9f679b5003b3f7fcb2c0", GitTreeState:"clean", BuildDate:"2017-08-28T07:04:45Z", GoVersion:"go1.8.3", Compiler:"gc", Platform:"linux/amd64"}
Error from server (NotFound): the server could not find the requested resource
```
The error message at the end of the version information is because no _context_ has been established.  The section below describes the steps for configuring a Kubernetes context for using kubectl.

## Create a kubernetes context for interacting with the current cluster

(TBD - I need to confirm this definition of a context.) Kubernetes uses the term "context" to mean the collection of configuration information that establishes which Kubernetes cluster is to be referenced by kubectl commands. The context information may be defined in what is referred to as a _kubeconfig_ file. The context information includes a connection URL and an authentication token among numerous other things.

To set up a Kubernetes context for use with the cluster in ICP do the following:
- Login to the ICP console.
- Click on your user name in the upper right corner of the console window.  (See figure below.)
![Configure Kubectl Client from ICP Console](images/01_ConfigureKubectlClientFromICPConsole.png)
- A pop-up window should appear with the kubectl commands listed that are needed to configure a kubectl context for your ICP cluster.  (See figure below.)
![Getting Kubeconfig from ICP Console](images/02_GettingKubeconfigFromICPConsole.png)   
You can copy the command block into the clipboard by clicking in the icon in the upper right corner of the kubeconfig pop-up window that looks like two overlapping sheets of paper.  (See figure above.)

- Paste the the kubectl commands into a shell and they will execute.  At that point you will have a context established for the Kubernetes cluster for the ICP instance where you were logged in.

You can view the defined contexts using the `kubectl config get-contexts` command.
```
# kubectl config get-contexts
[root@fc02-bootmaster01 federation]# kubectl config get-contexts
CURRENT   NAME                    CLUSTER         AUTHINFO             NAMESPACE
*         mycluster.icp-context   mycluster.icp   mycluster.icp-user   default
```
Once a context has been established for the kubectl client, you an run the `kubectl version` command and you should not see an error message.

You can view the details of the current configuration with the command: `kubectl config view`

## Create a work area directory in the file system

In order to keep all of the federation related artifacts organized, create a work area directory named `federation` in `ICP_HOME`.
```
# cd /opt/icp
# mkdir federation
# cd federation
```
The steps in the process that create a file system artifact are executed in `ICP_HOME/federation`.

## Save kubeconfig for the context of each ICP cluster to a file

On the boot-master host for each cluster (where you have a shell with the cluster context defined) run the `kubectl config view` command with output directed to a file.

```
kubectl config view > fc01-kubeconfig.yml
```
Then on the other boot-master host:
```
kubectl config view > fc02-kubeconfig.yml
```

## Merge the kubeconfig files from all clusters

- Copy all of the kubeconfig files to the federation host into its `ICP_HOME/federation` directory.

- Edit each kubeconfig file and do a global replace of mycluster with something that uniquely identifies the cluster.  In this example we replaced mycluster with fc01 for the kubeconfig YAML file from cluster 01, and mycluster with fc02 for the kubeconfig YAML file from cluster 02.

- Merge the kubeconfig files from each cluster by appending them into a single file.  In this example the merged kubeonfig file is named `fc-kubeconfig.yml`.

- In the merged kubeconfig file (`fc-kubeconfig.yml`) combine the `clusters`, `contexts` and `users` sections.  Remove redundancies for attributes such as `apiVersion`, `kind`, `preferences`.

The resulting fc-kubeconfig.yml file looks like:
```
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://10.11.12.1:8001
  name: fc01.icp
- cluster:
    insecure-skip-tls-verify: true
    server: https://10.11.12.2:8001
  name: fc02.icp
contexts:
- context:
    cluster: fc01.icp
    namespace: kube-system
    user: fc01.icp-user
  name: fc01.icp-context
- context:
    cluster: fc02.icp
    namespace: default
    user: fc02.icp-user
  name: fc02.icp-context
current-context: fc01.icp-context
users:
- name: fc01.icp-user
  user:
    token: REDACTED
- name: fc02.icp-user
  user:
    token: REDACTED
kind: Config
preferences: {}
```

- Set the KUBECONFIG environment variable to the combined kubeconfig file, e.g., `fc-kubeconfig.yml`.
```
[root@fc01-bootmaster01 federation]# export KUBECONFIG=./fc-kubeconfig.yml
[root@fc01-bootmaster01 federation]# kubectl config get-contexts
CURRENT   NAME               CLUSTER    AUTHINFO        NAMESPACE
*         fc01-context        fc01      fc01.icp-user   default
          fc02-context        fc02      fc02.icp-user   default

```

## Setup the CoreDNS

ICP runs in a non-cloud datacenter where the typical cloud services such as DNS and loadBalance services are not available. To provide the DNS provider required by kubernetes federation, we will use CoreDNS.

### Label the nodes

Kubernetes federated clusters uses region and zone based service discovery. Thus we need to add the region and zone labels for all the nodes in each cluster.

```
# Adding region "us" and zone "east" labels in all nodes of fc01
kubectl label --all nodes failure-domain.beta.kubernetes.io/region=us --context fc01-context
kubectl label --all nodes failure-domain.beta.kubernetes.io/zone=east --context fc01-context

# Adding region "us" and zone "west" labels in all nodes of fc01.icp
kubectl label --all nodes failure-domain.beta.kubernetes.io/region=us --context fc02-context
kubectl label --all nodes failure-domain.beta.kubernetes.io/zone=west --context fc02-context
```

### Deploy the etcd-operator

CoreDNS runs as a kubernetes component, itself needs persistent tier. We followed the approach documented by at [Kubernetes Federation for on-premises clusters](https://github.com/ufcg-lsd/k8s-onpremise-federation), which creates a separate etcd deployment for CoreDNS.

Under the `federation` folder, clone the following github project:
```
git clone https://github.com/ufcg-lsd/k8s-onpremise-federation
```

Navigate into the k8s-onpremise-federation folder, then install the etcd-operator service:

```
# RBAC
kubectl apply -f etcd-operator/rbac.yaml
serviceaccount "etcd-operator" created
clusterrole "etcd-operator" created
clusterrolebinding "etcd-operator" created

# Deployment
kubectl apply -f etcd-operator/deployment.yaml
deployment "etcd-operator" created

# Wait the Pod status of etcd-operator to be running before creating the etcd-cluster
kubectl apply -f etcd-operator/cluster.yaml
etcdcluster "etcd-cluster" created

```

Make sure you have the `etcd-cluster-client` running at port 2379
```
kubectl get svc etcd-cluster-client
```
 Run the following commands below to test your etcd-cluster-client endpoint

 ```
 kubectl run --rm -i --tty fun --image quay.io/coreos/etcd --restart=Never -- /bin/sh

 / # ETCDCTL_API=3 etcdctl --endpoints http://etcd-cluster-client.default:2379 put foo bar
OK
/ # ETCDCTL_API=3 etcdctl --endpoints http://etcd-cluster-client.default:2379 get foo
foo
bar
/ # ETCDCTL_API=3 etcdctl --endpoints http://etcd-cluster-client.default:2379 del foo
1
exit
 ```


### Deploy CoreDNS

This guide uses the [CoreDNS helm charts](https://github.com/kubernetes/charts/tree/master/stable/coredns) to deploy the CoreDNS as DNS provider of federation.

Navigate back to the `federation` folder and create a file for CoreDNS chart:

```
cat <<EOF >  coredns-chart-values.yaml
isClusterService: false
serviceType: "NodePort"
middleware:
  kubernetes:
    enabled: false
  etcd:
    enabled: true
    zones:
    - "fc-federated.com."
    endpoint: "http://etcd-cluster-client.default:2379"
EOF
```

Then deploy the CoreDNS chart:
```
helm install --name coredns -f  coredns-chart-values.yaml  stable/coredns
```
You should see the installation message:
```
NOTES:

CoreDNS is now running in the cluster.
It can be accessed using the below endpoint
  export NODE_PORT=$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services coredns-coredns)
  export NODE_IP=$(kubectl get nodes --namespace default -o jsonpath="{.items[0].status.addresses[0].address}")
  echo "$NODE_IP:$NODE_PORT"

It can be tested with the following:

1. Launch a Pod with DNS tools:

kubectl run -it --rm --restart=Never --image=infoblox/dnstools:latest dnstools

2. Query the DNS server:

/ # host kubernetes
```

## Initialize the Federation Control Plane

We'll be using `kubefed` for most of the operation here. Make sure you have installed kubefed as documented earlier.

Create coredns-provider.conf file under the current (federation) directory
```
cat <<EOF > coredns-provider.conf
[Global]
etcd-endpoints = http://etcd-cluster-client.default:2379
zones = fc-federated.com.
coredns-endpoints = 172.16.254.59:30669
EOF

```

Notes:

* The zones field must have the same value of CoreDNS chart config
* coredns-endpoints is the endpoint to access coredns server. CoreDNS was deployed with NodePort type, so the endpoints is composed by <ip-of-icp-proxy-nodes>:<port-of-service>.

Now, initialize the Federation Control Plane

```
kubefed init fc-federated-cluster \
    --host-cluster-context="fc01-context" \
    --dns-provider="coredns" \
    --dns-zone-name="fc-federated.com." \
    --api-server-advertise-address=172.16.254.64 \
    --api-server-service-type='NodePort' \
    --dns-provider-config="coredns-provider.conf" \
    --etcd-persistent-storage=true
```

NOTE:

* I used the ICP master node IP address for the api-server-advertise-address field
* Make sure your hosting cluster has Dynamic Persistent Volume enabled and available storage

You should see the execution result similar as following:
```
Creating a namespace federation-system for federation system components... done
Creating federation control plane service... done
Creating federation control plane objects (credentials, persistent volume claim)... done
Creating federation component deployments... done
Updating kubeconfig... done
Waiting for federation control plane to come up......................... done
Federation API server is running at: 172.16.254.64:30130
```

Note that this creates a namespace `federation-system` in the host-cluster, and drops a federated api-server , a persistent volume claim (for etcd), and controller manager which programs DNS.

Now you should have a new context as following:

```
[root@fc01-bootmaster01 federation]# kubectl config get-contexts
CURRENT   NAME                   CLUSTER                AUTHINFO               NAMESPACE
          fc-federated-cluster   fc-federated-cluster   fc-federated-cluster   
*         fc01.icp-context       fc01.icp               fc01.icp-user          default
          fc02.icp-context       fc02.icp               fc02.icp-user          default

```


## Join ICP Clusters

switch to use the new context:

```
kubectl config use-context fc-federated-cluster
```

Join the clusters to the federation
```
# join fc01 cluster to the federated cluster
kubefed join fc01-context --host-cluster-context=fc01-context

# join fc02 cluster to the federated cluster
kubefed join fc02-context --host-cluster-context=fc01-context

```
Now, you can check the federated cluster:

```
[root@fc01-bootmaster01 federation]# kubectl get clusters
NAME           STATUS    AGE
fc01-context   Ready     6m
fc02-context   Ready     2m
```

## Setting up Load Balancer

ICP deployment doesn't currectly have a loadBalancer type for federated api server. We'll need some ways to create services with `LoadBalancer` type for the federated service discovery. Here we uses [keepalived-cloud-provider](https://github.com/munnerz/keepalived-cloud-provider).

we need create the service account called `keepalived` and grant superuser access to it.

### Aquire CIDR subnet
Work with your admin to assign you a CIDR subnet.  should also set up a gateway IP on the subnet (typically network address +1)

### Create a service account and cluster role binding

keepalived will use the following service account and role binding before deployment.
Note: The following procedure have to be executed on all the clusters under each context.

```
# create service account
```

Create a cluster role that has access to most of the kubernetes components
```
echo 'apiVersion: rbac.authorization.k8s.io/v1alpha1
kind: ClusterRole
metadata:
  name: kube-keepalived-vip
rules:
- apiGroups: [""]
  resources:
  - pods
  - nodes
  - endpoints
  - services
  - configmaps
  verbs: ["get", "list", "watch"]' | kubectl create -f -
```

Bind the service account to the ClusterRole you created above:

```
echo "apiVersion: rbac.authorization.k8s.io/v1alpha1
kind: ClusterRoleBinding
metadata:
  name: kube-keepalived-vip
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kube-keepalived-vip
subjects:
- kind: ServiceAccount
  name: kube-keepalived-vip
  namespace: kube-system" | kubectl create -f -
```
also, for ICP, make sure the kube-keepalived-vip ServiceAccount can launch privileged containers by running following command:
```
kubectl create clusterrolebinding kube-keepalived-vip-privileged --serviceaccount=kube-system:kube-keepalived-vip --clusterrole=privileged
```

### Install the keepalived-vip Daemonset

Ideally, this should be limited to the ICP proxy node only.

```
echo "apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
  name: kube-keepalived-vip
  namespace: kube-system
spec:
  template:
    metadata:
      labels:
        name: kube-keepalived-vip
    spec:
      hostNetwork: true
      serviceAccount: kube-keepalived-vip
      containers:
        - image: gcr.io/google_containers/kube-keepalived-vip:0.11
          name: kube-keepalived-vip
          imagePullPolicy: Always
          securityContext:
            privileged: true
          volumeMounts:
            - mountPath: /lib/modules
              name: modules
              readOnly: true
            - mountPath: /dev
              name: dev
          # use downward API
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          # to use unicast
          args:
          - --services-configmap=kube-system/vip-configmap
          - --watch-all-namespaces=true
          - --vrid=51
          # unicast uses the ip of the nodes instead of multicast
          # this is useful if running in cloud providers (like AWS)
          #- --use-unicast=true
          # vrrp version can be set to 2.  Default 3.
          #- --vrrp-version=2
      volumes:
        - name: modules
          hostPath:
            path: /lib/modules
        - name: dev
          hostPath:
            path: /dev
      nodeSelector:
        beta.kubernetes.io/arch: amd64" | kubectl create -f -
```

Now, let's create the ConfigMap to store the VIP information later:
```
echo "apiVersion: v1
kind: ConfigMap
metadata:
  name: vip-configmap
  namespace: kube-system
data: " | kubectl create -f -
```
You can see what's in the ConfigMap:
```
kubectl get cm vip-configmap -o yaml --namespace kube-system
```

### Deploy the keepalived-cloud-provider

make sure you set the CIDR correctly.  i.e. in the lab we used 10.250.0.0/24 for fc01 cluster and 10.250.1.0/24 for fc02 cluster.

```
echo 'apiVersion: apps/v1beta1
kind: Deployment
metadata:
  labels:
    app: keepalived-cloud-provider
  name: keepalived-cloud-provider
  namespace: kube-system
spec:
  replicas: 1
  revisionHistoryLimit: 2
  selector:
    matchLabels:
      app: keepalived-cloud-provider
  strategy:
    type: RollingUpdate
  template:
    metadata:
      annotations:
        scheduler.alpha.kubernetes.io/critical-pod: ""
        scheduler.alpha.kubernetes.io/tolerations: "[{\"key\":\"CriticalAddonsOnly\", \"operator\":\"Exists\"}]"
      labels:
        app: keepalived-cloud-provider
    spec:
      containers:
      - name: keepalived-cloud-provider
        image: jkwong/keepalived-cloud-provider:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: KEEPALIVED_NAMESPACE
          value: kube-system
        - name: KEEPALIVED_CONFIG_MAP
          value: vip-configmap
        - name: KEEPALIVED_SERVICE_CIDR
          value: 10.250.1.0/24 # pick a CIDR that is explicitly reserved for keepalived
        - name: KEEPALIVED_SERVICE_RESERVED
          value: 10.250.1.1 # router address for my CIDR
        volumeMounts:
        - name: certs
          mountPath: /etc/ssl/certs
        resources:
          requests:
            cpu: 200m
        livenessProbe:
          httpGet:
            path: /healthz
            port: 10252
            host: 127.0.0.1
          initialDelaySeconds: 15
          timeoutSeconds: 15
          failureThreshold: 8
      volumes:
      - name: certs
        hostPath:
          path: /etc/ssl/certs' | kubectl create -f -
```



## Validate the Federation Setup

We'll use simple NGINX to validate our setup, both the kubernetes federation and the load Balancer

Switch to federated kubernetes context:
```
kubectl config use-context fc-federated-cluster
```
Create default namespace for the federeated control plane:
```
kubectl create ns default
```

Create a nginx deployment and scale to 4 pods:
```
kubectl --context=fc-federated-cluster create deployment nginx --image=nginx && \
  kubectl --context=fc-federated-cluster scale deployment nginx --replicas=4
```

Expose the deployment as a federeated service with type as `LoadBalancer`
```
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

You should see the external VIP associated with the service now:
```
kubectl describe services nginx
```

You can test the NGINX deployment by lanuch browser and point to the VIP assigned to the service above:
http://{{vip}}/

Let's test the DNS lookup for the service:
```
kubectl config use-context fc01-context
kubectl run -it --rm --restart=Never --image=infoblox/dnstools:latest dnstools
dig @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.fc-federated.com
```

You should see the DNS answer with the correct DNS qualified name as we specified:
```
dnstools# dig @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.fc-federated.com

; <<>> DiG 9.11.1-P1 <<>> @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.fc-federated.com
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 36245
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
; COOKIE: b1f9988e7a6c5a96 (echoed)
;; QUESTION SECTION:
;nginx.default.fc-federated-cluster.svc.fc-federated.com. IN A

;; ANSWER SECTION:
nginx.default.fc-federated-cluster.svc.fc-federated.com. 30 IN A 10.250.0.2
nginx.default.fc-federated-cluster.svc.fc-federated.com. 30 IN A 10.210.1.65

;; Query time: 3 msec
;; SERVER: 172.16.254.59#30743(172.16.254.59)
;; WHEN: Fri Nov 17 01:15:38 UTC 2017
;; MSG SIZE  rcvd: 128

```


```
dig @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.east.us.fc-federated.com

dnstools# dig @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.eas
t.us.fc-federated.com

; <<>> DiG 9.11.1-P1 <<>> @172.16.254.59 -p 30743 nginx.default.fc-federated-cluster.svc.east.us.fc-federated.com
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 3341
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
; COOKIE: f1aa7935cf9ebd07 (echoed)
;; QUESTION SECTION:
;nginx.default.fc-federated-cluster.svc.east.us.fc-federated.com. IN A

;; ANSWER SECTION:
nginx.default.fc-federated-cluster.svc.east.us.fc-federated.com. 30 IN A 10.250.0.3

;; Query time: 2 msec
;; SERVER: 172.16.254.59#30743(172.16.254.59)
;; WHEN: Fri Nov 17 14:25:15 UTC 2017
;; MSG SIZE  rcvd: 120
```

## Setup the DNS server



## Delete the Federation Control Plane

Proper cleanup of federation control plane is not fully implemented in this beta release of kubefed. However, for the time being, deleting the federation system namespace should remove all the resources except the persistent storage volume dynamically provisioned for the federation control plane’s etcd. You can delete the federation namespace by running the following command:

```
kubectl delete ns federation-system
```

Note: Make sure you run this command under the host cluster context.

# References
- [Kubernetes Federation for on-premises clusters](https://github.com/ufcg-lsd/k8s-onpremise-federation) This document may prove to be useful. Jeff Kwong referenced it and I found it helpful as background.
- Kubernetes documentation: [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/)
