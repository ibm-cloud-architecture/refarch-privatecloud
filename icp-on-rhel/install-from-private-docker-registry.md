Configure a Private Docker Repository for IBM Cloud private Native or Enterprise Installation
=============================================

## Overview
The installation of IBM Cloud private requires access to a repository of Docker images. For the CE installation the images are served from the public Docker Hub.
This is not possible for installation of the Native or Enterprise editions. For those versions a very large tar file is copied to each node in the environment and
loaded into each local Docker image repository.

In this document we will outline how to configure a private Docker registry on the boot node that can be used for installation in air-gap environments.
This will help reduce the constraints on disk space and time required to copy the large image file. These instructions will work for any type of installation, single
node, multi-node, HA, etc.

*NOTE:* This approach applies only when the ICP cluster to be deployed is a homogeneous collection of VMs, i.e., all x86 or all PPC.  Likewise, this approach cannot be used if some worker nodes are s390x.

Configuration
------------

1.  Configure the boot node as recommended in the IBM Cloud Private Knowledge Center up to the step where the images are extracted and loaded into Docker
2.  Ensure Docker is installed and the image file downloaded from Passport advantage is loaded.
    ```  
    docker images
    ```
3.  Create a directory called registry with auth and certs subdirectories
    ```
    mkdir -p /opt/registry/auth
    mkdir -p /opt/registry/certs
    ```
4. Change to the certs directory and generate certificates
   ```
   cd /opt/registry/certs
   openssl req -x509 -nodes -sha256 -subj "/CN=$(hostname -f)" -days 36500 -newkey rsa:2048 -keyout $(hostname -f).key -out $(hostname -f).crt
   ```
5. Create a certs directory for the Docker client to connect to the repository and copy the certs from step 4 to that directory. *TBD* This doesn't feel correct. The private key of the registry server should not be copied to the client side. Only the public key should be needed.
   ```
   mkdir -p /etc/docker/certs.d/$(hostname -f):8500
   cp /opt/registry/certs/* /etc/docker/certs.d/$(hostname -f)\:8500
   ```
 > The :8500 in this example is the port used by the registry.

6. Generate the client certificates for Docker, using the key file generated in step 4 as input.
   ```
   cd /opt/registry/certs
   openssl req -new -x509 -text -key $(hostname -f).key \
       -out /etc/docker/certs.d/$(hostname -f)\:8500/$(hostname -f).cert
   ```
   - NOTE: The files in the directory are usually named `client.key` and `client.crt`.  *TBD* Need to investigate to confirm the instructions here describe a proper approach.

*NOTE:* *TBD* The more correct approach: The registry server creates a key and a public cert and the public cert would get copied to all clients.  Then the client would generate a key and public cert and the client public cert would get copied back to the registry server "certs" directory.  Need to investigate.  Would there still be an objection to all certs being self-signed?  As best I can tell from reading the various docs and posting, Docker does a 2-way handshake, hence the need for the client to stash its public cert with the registry server.

7. Configure a password hash file for the Docker registry. Be sure to specify the latest registry image. For 2.1.0.3 it is `ibmcom/registry:2.6.2`.
   ```
   cd /opt/registry
   docker run --entrypoint htpasswd ibmcom/registry:2.6.2 -Bbn admin Passw0rd > auth/htpasswd
   ```
8. Run the Docker registry with the configurations. The 8500 port can be changed here, but must match the ports specified in the configurations above.
   ```
   cd /opt/registry
   docker run -d -p 8500:8500 --restart=always \
      --name registry \
      -v $(pwd)/auth:/auth \
      -e "REGISTRY_AUTH=htpasswd" \
      -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
      -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
      -v $(pwd)/certs:/certs \
      -e REGISTRY_HTTP_ADDR=0.0.0.0:8500 \
      -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/$(hostname -f).crt \
      -e REGISTRY_HTTP_TLS_KEY=/certs/$(hostname -f).key \
      ibmcom/registry:2.6.2
   ```

9. Login to the docker registry using id and password specified in step 7.
   ```
   docker login $(hostname -f):8500
   ```
   - If you don't have the certificates in order you will get errors:
   - Key file missing
   - Unknown certificate authority
   - *TBD*: The key and the cert of the server are needed as well as the client cert.

10. Run the following script to tag all the images and push to the registry. (The `grep -v REPOSITORY` eliminates the column title line in the `docker images` output.)
    ```
    docker images | grep -v REPOSITORY | while read line
    do
      package=$(echo $line | cut -f1 -d " ")
      version=$(echo $line | cut -f2 -d " ")
      docker tag $package:$version $(hostname -f):8500/$package:$version
      docker push $(hostname -f):8500/$package:$version
    done
    ```

11. Clean the images from the local image repository. All except the registry and inception images:
    ```
    docker images | grep -v registry | grep -v inception | grep -v REPOSITORY | while read line
    do
      imagename=$(echo $line | cut -f1 -d " ")
      imagever=$(echo $line | cut -f2 -d " ")
      echo "docker rmi $imagename:$imagever"
      docker rmi $imagename:$imagever
    done
    ```

12. Configure the firewall on the private registry VM to allow access to the port it is listening on, i.e., 8500
    ```
    firewall-cmd --permanent --zone=public --add-port=8500/tcp
    ```
- The above allows IPv4 and IPv6 traffic to port 8500.  
- Some things to note:
  - The registry does not support an HTTP interface.  If you access it with a browser you will get an empty screen.  (You also get complaints about the certificate since it is self-signed.)
  - You can see the registry container running using `docker ps` or `docker ps --all` if the registry container happens to be stopped.
  - You an access the registry container to see the registry content in its file system with:
  ```
  docker exec -it CONTAINER_ID sh
  ```
  - The registry container does not include `/bin/bash`.
  - The registry content is down the `/var/lib/registry` path.  
  - To see the tags for the images you need to go into the directory associated with each image.  Eventually you get to a tags directory.
  - Do not do an `attach` to the container.  You will cause it to exit if you `Ctrl-C` out of the `attach`.
  - You can run the registry with a `-v` argument that maps a directory on the host with the `/var/lib/registy` directory in the container.  Just be sure you use a file system on the host that has plenty of space.  The registry is ~10GB to start.

12. Pull the inception image from the new registry
- *TBD* Not necessary if you don't remove the inception image in the above loop.
    ```
    docker pull $(hostname -f):8500/ibmcom/icp-inception:2.1.0.3-ee
    ```

- At this point you can run some simple tests to convince yourself the private registry has been set up properly and is accessible from the cluster nodes.
- Doing a `docker login` from a remote node is a good test to ensure you can access the registry on the port it is listening on.

13. Extract the configuration files from the installer image
    ```
    docker run -v $(pwd):/data -e LICENSE=accept \
        $(hostname -f):8500/ibmcom/icp-inception:2.1.0.3-ee \
        cp -r cluster /data
    ```
    or (if you left the inception image in the local registry)
    ```
    docker run -v $(pwd):/data -e LICENSE=accept \
        ibmcom/icp-inception:2.1.0.3-ee \
        cp -r cluster /data
    ```
14. Copy the content of `/etc/docker/certs.d/$(hostname -f)` directory to all nodes.
15. Add these lines to config.yaml to configure use of the private registry.
    ```
    image_repo: <b><myhost.mydomain.local></b>:8500/ibmcom
    private_registry_enabled: true
    private_registry_server: <b><myhost.mydomain.local></b>:8500
    docker_username: admin
    docker_password: Passw0rd
    ```

> Replace **<myhost.mydomain.local>** with the FQDN of the boot node.

ENDNOTES

[1] It should be possible to leverage other registries such as artifactory.

[2] Keep in mind that references to Docker images will require specification of the registry. For example, to get the cluster configurations the
instructions state the following command:
   ```
   docker run -v $(pwd):/data -e LICENSE=accept \
     ibmcom/icp-inception:2.1.0.3-ee \
     cp -r cluster /data
   ```
and we used this command:
   ```
   docker run -v $(pwd):/data -e LICENSE=accept \
     $(hostname -f):8500/ibmcom/icp-inception:2.1.0.3-ee \
     cp -r cluster /data
   ```
