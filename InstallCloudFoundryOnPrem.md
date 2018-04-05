# Installing ICP CloudFoundry

## vCenter Preparations
1. (optional) Create a new Cluster for CloudFoundry<br>
  ```
  Cluster Name: CloudFoundry
  ```

2. (optional) Create a new Datastore for CloudFoundry<br>
  ```
  Datstore Name: CF_DS
  ```

3. Browse the CloudFoundry datastore and create a /Disks folder off the root<br>

4. Create a network to be used by Cloud Foundry<br>
  ```
  Network Name: CF_Net
  ```

5. Create a vCenter user with sufficient privileges

  * Create and manage VMs in 'CloudFoundry' Cluster

  * Create and manage files and VMs on 'CF_DS' Datastore

  * Use the 'CF_Net' network

6. Create a new ResourcePool for CloudFoundry<br>
  ```
  ICP_CF_210
  ```

7. Create the required user and roles in vCenter for the installer
  1. Create two roles.
    Grant the first role the following permissions:
      * Datastore: Low level file operations
      * Datastore: Update virtual machine files
      * vApp: Import
    Grant the second role the following permission:
      * Global: Manage custom attributes
      * If you use Virtual Distributed Switch Network, grant the role the following permission:
        * dvPort group: Modify

  2. Create a vCenter user
    * Assign the user the following roles for list vSphere components:
      <pre>
      <strong>VMware user permissions</strong>
        <strong>vSphere Client view</strong>                <strong>vSphere component</strong>       <strong>Role</strong>                      <strong>Other</strong>
        Hosts and Clusters                 VCenter                 Second user-defined role  Not propagated
        Hosts and Clusters                 Data Center             First user-defined role   Not propagated
        Hosts and Clusters                 Cluster                 Administrator             Propagated
        VMs and Templates                  Virtual machine folder  Administrator             Propagated
        Datastores and Datastore Clusters  Each datastore          Administrator             Propagated
      </pre>
  3. If you use a vSwitch network:
    * Assign the appropriate port group the administrator role. Ensure that Propagate to Child Objects is not selected.
  4. If you use a Virtual Distributed Switch (vDS) Network:
    * Place the vDS switch in a folder
    * Assign the vDS parent folder the Read-only role for the new user, and select Propagate to Child Objects.
    * Assign the appropriate port group the administrator role. Ensure that Propagate to Child Objects is not selected.

## Prepare Installation Virtual Machine
1. Create an installation VM in your 'CloudFoundry' cluster

  * 2 vCPU, 8GB Memory, 200GB Disk (thin provisioned)

  * Ubuntu 16.04, basic server with ssh

2. Install docker (or docker-cd)

3. Copy tarball to /opt on the newly provisioned Virtual machine
  From the /opt directory on the installation VM
  ```
  cd /opt
  scp myuser@filestore.local:/storage/icp/ibm-cloud-private-cloud-foundry-x86_64-2.1.0.tar.gz .
  ```

4. Copy CF tarball to /opt and untar to /opt/cf<br>
  ```
  mkdir -P /opt/cf
  cd /opt/cf
  gunzip -c /opt/<tarball.tar.gz> |tar -xvf -
  ```

5. Import images into docker
  ```
  cd /opt/icp/cf
  ./import_images.sh
  ```

## Generate Certificate keys for your CloudFoundry domains (optional)
1. Generate certificate keys for your new domain[s]

  __note:__ In ICP CF 2.1.0.2 and later, cert keys can be automatically created for you during install.  Only use this section if you want to specify your own self-signed certificates with specific information.

  Just like IBM Bluemix Public, ICP uses two domains for its CloudFoundry implementation, one for the infrastructure components (e.g. bluemix.net), and one for the applications (e.g. mybluemix.net).  In our example we will use bluemix.csplab.local and mybluemix.csplab.local.

  Perform the following on your installation virtual machine as the root user:

  * Generate the root certificate (remember the password you choose, you will need it in the next step):

    ```
    openssl genrsa -des3 -out rootCA.key 2048
    ```

  * Self-sign the Certificate (use the password from the previous step when asked):

    ```
    openssl req -x509 -new -nodes -key rootCA.key -days 1024 -out rootCA.pem
    ```

  * Store the rootCA.key file and its password in a secure location

  * Generate a domain key for the self-signed certificates each domain (use the same values as specified in the previous step):

    ```
    openssl req -new -newkey rsa:2048 -nodes -out star_<your_domain>.csr -keyout star_<your_domain>.key -subj "/C=<country_code>/ST=<state>/L=<locality>/O=<organization_name>/CN=*.<your_domain>"
    ```

    Example:

    ```
    openssl req -new -newkey rsa:2048 -nodes -out star_bluemix.csplab.local.csr -keyout star_bluemix.csplab.local.key -subj "/C=US/ST=Texas/L=Dallas/O=CASE/CN=*.bluemix.csplab.local"

    openssl req -new -newkey rsa:2048 -nodes -out star_mybluemix.csplab.local.csr -keyout star_mybluemix.csplab.local.key -subj "/C=US/ST=Texas/L=Dallas/O=CASE/CN=*.mybluemix.csplab.local"
    ```
  * Generate the domain certificates

    1. Create domain certificate extension files:

      * File name: v3_ext.bluemix
        ```
        [ v3_req ]
        subjectAltName=DNS:*.bluemix.csplab.local, DNS:csplab.local
        ```

      * File name: v3_ext.mybluemix
        ```
        [ v3_req ]
        subjectAltName=DNS:*.mybluemix.csplab.local,DNS:csplab.local
        ```

    2. Generate the domain certificate for each domain (use the password for your rootCA.key file again here):

      ```
      openssl x509 -req -in star_bluemix.csplab.local.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out star_bluemix.csplab.local.crt -days 500 -extensions v3_req -extfile v3_ext.bluemix

      openssl x509 -req -in star_mybluemix.csplab.local.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out star_mybluemix.csplab.local.crt -days 500 -extensions v3_req -extfile v3_ext.mybluemix
      ```

## Prepare CloudFoundry for Installation
1. Launch the inception image

  This will launch the inception container and copy configuration files to the local filesytem.  The container will continue to run and await further instructions.

  ```
  cd /opt/cf
  ./launch.sh -n myEnv -e LICENSE=accept -b ./BOM.yml -c /data |tee launch.log
  ```

  * **-n:** Name.  This is the name of the environment you will deploy. It is expected that an enterprise could have more than one environment.  This option keeps configuration information for separate environments separate.

  * **-b:** Location of the BOM.yml file.

  * **-c:** Local directory to hold persistent configuration data

  * **|tee launch.log 2>&1:** Copy everything from stdout and stderr to a file named launch.log in the current directory for later troubleshooting as needed.

2. Configure your deployment
  * Copy the text below into a file called uiconfig-csplab.yml

  * Update the file to match your environment

  * __note:__ In the section below, if you did not create your own certificate keys then you should leave that section blank.  In the example template, remove the -----BEGIN CERTIFICATE----- and -----END CERTIFICATE----- lines in each of the cert sections and also remove the "|+" on the key line.  With an empty value here the installer will create the keys for you.

  ```
  uiconfig:
   bluemix_apps_domain: mybluemix.csplab.local
   bluemix_apps_domain_cert: |+
     -----BEGIN CERTIFICATE-----
     MIIDmTCCAoGgAwIBAgIJAILSR4FPR9bvMA0GCSqGSIb3DQEBCwUAMIGAMQswCQYD
     VQQGEwJVUzEOMAwGA1UECAwFVGV4YXMxDzANBgNVBAcMBkRhbGxhczEMMAoGA1UE
     CgwDSUJNMQ0wCwYDVQQLDARDQVNFMRAwDgYDVQQDDAdibHVlbWl4MSEwHwYJKoZI
     hvcNAQkBFhJ2aGF2YXJkQHVzLmlibS5jb20wHhcNMTcxMDI1MjM0MDAzWhcNMTkw
     MzA5MjM0MDAzWjBgMQswCQYDVQQGEwJVUzEOMAwGA1UECAwFVGV4YXMxDzANBgNV
     BAcMBkRhbGxhczENMAsGA1UECgwEQ0FTRTEhMB8GA1UEAwwYKi5teWJsdWVtaXgu
     Y3NwbGFiLmxvY2FsMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAptt7
     r56D3wEvo9hwke2t039650a0M8hdOq44IZzIRxM2zAPyM122PJvFhtJTjtBGyOYS
     jl6ajkPBxyQINd0Cna1+EyBcMGFmExoyyJErOqLJJbC9XPLGy733ZB4xApcA2LpO
     8btxQy5Pa656PKcgQtL/ejMqvXopKtZmohsmcgHLsX4RR9V4F09yiNYdcBAPGBIN
     cv1DriuKWWdLsh6lLXxhh42OVhTzzru2M6zdUxzRvHxuyoL/8ZCHX20EiefW80PY
     dLyOItLSHwm9ZtBBDTCvGbuRB91Rhs9IyTMN9eRUl5iFOa/vvC+I/7KXs72DiP1q
     ySVkU/L4fNPZJolHZwIDAQABozUwMzAxBgNVHREEKjAoghgqLm15Ymx1ZW1peC5j
     c3BsYWIubG9jYWyCDGNzcGxhYi5sb2NhbDANBgkqhkiG9w0BAQsFAAOCAQEAqgvn
     dYws5sJzaf7PUOB1hGKKk6gmttt1LTaap7mwZqIRI3wF72O5sqw69HeV4SFrhnd3
     EPDL8RMFKwnxWUzs5ZudcRLIxXMFvmggj7tMIwNkZsgf4W4l6QzN7/XoTw4KAdif
     iP29w5mHk52EEIUrzpenVZFyMXK2KzsSa9+Ybh7wZUYleGATHuo4gJv9ObK9PAUN
     +DpDXbye+MyKt5s3znkYQ8QqLhp1K2c3zFNGiUI1v4hFgDdWt1W/NHhgh16AlKOa
     QgSjE06w2G6DUYY3y7nV3j+ZxZd0DS1B7s6iEPafFcw9SiNzDsXZBhkMKr2kG/pQ
     aWrnD11AKjIuqV0T/w==
     -----END CERTIFICATE-----
   bluemix_apps_domain_cert_rsa_key: |+
     -----BEGIN PRIVATE KEY-----
     MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCm23uvnoPfAS+j
     2HCR7a3Tf3rnRrQzyF06rjghnMhHEzbMA/IzXbY8m8WG0lOO0EbI5hKOXpqOQ8HH
     JAg13QKdrX4TIFwwYWYTGjLIkSs6osklsL1c8sbLvfdkHjEClwDYuk7xu3FDLk9r
     rno8pyBC0v96Myq9eikq1maiGyZyAcuxfhFH1XgXT3KI1h1wEA8YEg1y/UOuK4pZ
     Z0uyHqUtfGGHjY5WFPPOu7YzrN1THNG8fG7Kgv/xkIdfbQSJ59bzQ9h0vI4i0tIf
     Cb1m0EENMK8Zu5EH3VGGz0jJMw315FSXmIU5r++8L4j/spezvYOI/WrJJWRT8vh8
     09kmiUdnAgMBAAECggEAQ0XkpVbcxjGdOosOP9e7KLWSIOMBzorvA7SwTuT+XqGh
     izngEdOroN4REp2EMOVKVL9mJd6Ao/EvlJGzebwEzPvhA+cdJChw1izO4sycyERP
     oxGSF4KOoiCSONxvWCL3pWngYFf5f2ORg9HR2NhtCmQ1utgcWE6DgJD2yk71/iqS
     PREZTXR2HcvFa0Z/wms3q2PXgZI/9arA0ZXTqPUNOcQBD5Rm9rXvrIOf7Av9rv03
     jvWbue62TWAL52hVKnwhW+D3DqMsN9DRfoBq0GsDIhmD/cqiBD9043DKKj72WvZ1
     4eNVeIVhLih7jkPVULTwvUQNKiEvr8BjVfhLl2Wj4QKBgQDa+BRyZV1PBiGeb3VG
     +uTK1bq2WqQTHCA/J0CHPxp3yqZFcbTCaxBjPAzGOEaPdN/wq9uhHM8hMAmVEG5d
     D4y7YRIvfz6sYSM3iBJueJ4xnQD1pDlO5w8WBs34UdyoI7g5vag3dh8Rljg/qnNM
     5DFMZmoHKTNUZeZlu3iuaR0+sQKBgQDDE08l45EEAYh7Y/iWvK4l6yE4me9Ralfi
     9Chw7TN+ifnNzlnIzBfP5wxUo6u8GrlpAz8lZyWBLu03Rt0gWBgpVqAycWpcYmia
     c3Lh6DM1OO+nQFUGQRLQ8lK9k/m9khqUcGFML6STvrCDt/DFUSOVqf6MwDbzDwS5
     hnuFbXNdlwKBgQCSz2nGGTgqV44Kz+ftoyHq7Mm2oacIOP9V2FdnVmPElVZNkSME
     hwwBvK1D6U9Ft7K9hjxHFS26rp5+Fvon4tkUeMzck4/Nu4MFJHJXJv/Je96801Kp
     GDoBJqbKKviqsug9rm8uYEAMZo9oADw1/XkgJDpKetEzcO68nqkXJtq4wQKBgCzs
     IWnkQdzeTYO8vd5YjPIGd5wFNutUxfBpsXZv6U/WjkQqpNpsxX8HAfvrxPyIWvIn
     4T7Hxgc9uzrjgsCUCNxcKn/zRj8IGnaW53nGcyRqfCXT1sCd86tSYmNt1DEnmB9e
     0cktn4S2gQeUMEoAKWWpxAi9qunGJ5xhr8hGMC75AoGBALp5SffLh+LVnv4euV5h
     xxgjRoV32n0IoPIOt+ajVasu5lb2ON4WzKYA5Ru83frXM5Cy/w/XE9pxjg54HSmC
     lFAC49k3i/AMRe8ASHFF/h4aA79YvzZEoHaVhYikcecjTN2Q0L+eY8asREvYxYkN
     rLb983i+d6dor+qR8VBp7FR2
     -----END PRIVATE KEY-----
   bluemix_env_domain: bluemix.csplab.local
   bluemix_env_domain_cert: |+
     -----BEGIN CERTIFICATE-----
     MIIDlTCCAn2gAwIBAgIJAILSR4FPR9buMA0GCSqGSIb3DQEBCwUAMIGAMQswCQYD
     VQQGEwJVUzEOMAwGA1UECAwFVGV4YXMxDzANBgNVBAcMBkRhbGxhczEMMAoGA1UE
     CgwDSUJNMQ0wCwYDVQQLDARDQVNFMRAwDgYDVQQDDAdibHVlbWl4MSEwHwYJKoZI
     hvcNAQkBFhJ2aGF2YXJkQHVzLmlibS5jb20wHhcNMTcxMDI1MjMzODIzWhcNMTkw
     MzA5MjMzODIzWjBeMQswCQYDVQQGEwJVUzEOMAwGA1UECAwFVGV4YXMxDzANBgNV
     BAcMBkRhbGxhczENMAsGA1UECgwEQ0FTRTEfMB0GA1UEAwwWKi5ibHVlbWl4LmNz
     cGxhYi5sb2NhbDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALpR45vl
     8dvKi9YIzT5NiAtcnEm0M7D2uii0y5OAsEAt/bGCbbkYAPGz01CjA3bdFlULtctq
     500LIv2GjqnHkDmvvtmrSwEk8GFxs06HKizHkHvGPtI27OrGVZ78m5uKwQDj/17O
     MA8jp10Sj9dIOyQviyQi9xkHmnsd3Y99NcRFnw/cFN2NyEfDUWAv0woh8q97R3yH
     BVRzUXLbnmwUvAhBYn05KN2gRq806ILDbn6YwYeV0SFJUc7SgLQ+/Eri9DLXZsdn
     MpMLf6axVBh0dKGEHRvTMaU9qzdcj9IOOUyz1rst5N/104RgQvqXZAzKJsFS3Z11
     kf/ujGpQwJmkOb8CAwEAAaMzMDEwLwYDVR0RBCgwJoIWKi5ibHVlbWl4LmNzcGxh
     Yi5sb2NhbIIMY3NwbGFiLmxvY2FsMA0GCSqGSIb3DQEBCwUAA4IBAQAxM26IX2Iy
     pZySi1fc+m5LcYbZvFXYjdO9oQGphTl5JyuqWuA4SUl96dXni9ttaIlVoMF51EbV
     go/1CUQM8fWizvcbzO0NvfnJuv8k1gEYLIl8BiqoVGk9ITAB29z10if+IePWcBUd
     Ig2MZDsaOkoyOaL2V2fcKe4h0dIq5H3BaYVxOIYcOAwAownDk37AvvfYgrp0S8mT
     ddXfitec4x/g2K68SP0H71Ban5iadf54biZGfA9n3p90J+tebpahtRuxyEXy4OVU
     4Vt+DReEUa2+zgJkomqtCoSxSaVdVv0AcNZSIkPPVAwYhic4pXvv+dQU/XzSCpev
     60w6Qf+M3rSx
     -----END CERTIFICATE-----
   bluemix_env_domain_cert_ca: |+
     -----BEGIN CERTIFICATE-----
     MIID1TCCAr2gAwIBAgIJAMHggyW+s9u7MA0GCSqGSIb3DQEBCwUAMIGAMQswCQYD
     VQQGEwJVUzEOMAwGA1UECAwFVGV4YXMxDzANBgNVBAcMBkRhbGxhczEMMAoGA1UE
     CgwDSUJNMQ0wCwYDVQQLDARDQVNFMRAwDgYDVQQDDAdibHVlbWl4MSEwHwYJKoZI
     hvcNAQkBFhJ2aGF2YXJkQHVzLmlibS5jb20wHhcNMTcxMDI1MjMyNjM4WhcNMjAw
     ODE0MjMyNjM4WjCBgDELMAkGA1UEBhMCVVMxDjAMBgNVBAgMBVRleGFzMQ8wDQYD
     VQQHDAZEYWxsYXMxDDAKBgNVBAoMA0lCTTENMAsGA1UECwwEQ0FTRTEQMA4GA1UE
     AwwHYmx1ZW1peDEhMB8GCSqGSIb3DQEJARYSdmhhdmFyZEB1cy5pYm0uY29tMIIB
     IjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxHmodXtTQz/jq5hPSO1Ng5TD
     HGFEN5KJWu4q3H6wNS0sonRWE3XrJ/Z+cgU1MjsaF25WU3n0jTx/a5ixNyI+0OJP
     N38r7BZds7PUxbbvj+8FOi08MOWAL0LHLBjK9ujY10oCO40tus5joOIe0kdeu2gv
     npIWt3fxuRfmm49VIw2DudcS7cxD2bCBdDYy715H1Cu59MtcNo/EBQ/xrmDIx2gC
     D4nO+heOIwog/Ch2BREczLjG5qEXkrZ6BtK1xtAX5zlzaxLYflMPiigC59n4PvHZ
     ILAOQLJm56ejEcZaTOuCYq6Ik26lubtWNrmCe44jf51fyBzCekUT1SPX317mrQID
     AQABo1AwTjAdBgNVHQ4EFgQU0nCb2ORRmj3XSpwPzC9XzO8jo88wHwYDVR0jBBgw
     FoAU0nCb2ORRmj3XSpwPzC9XzO8jo88wDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0B
     AQsFAAOCAQEAHiQVcVUtN8UPouoFjXfwNIIW4CqJ+RRxag4o6Y9aILGk5JYKY70w
     F3T0UL596WwyVYUyXGdKJiPZ4IsHCSqrPgk8SDZ5Bv9rjbvnD+c92Ewz/AjMwd6z
     lrxC2KA47dJOfJ88DJVeQ1e56fkj2QM6aZHxcQMkjaDUizeNygP9gDcqSPwD6gmj
     +JAPOBo2RP8t8zYxp/Yp3Z3qZY2/fkePmaAFI3xa0cObqIZCGQrScWJQhWE6Gmha
     ns8ciwsLkldkBqHMjjqu8TktRqgaDPDqr3ryv4LKjHSj0E5MCjmK6qU13hEPeq6c
     l1Ng9KDpe0LSlMu2YrAZpQzp0MqifdRC+A==
     -----END CERTIFICATE-----
   bluemix_env_domain_cert_rsa_key: |+
   -----BEGIN PRIVATE KEY-----
   MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC6UeOb5fHbyovW
   CM0+TYgLXJxJtDOw9rootMuTgLBALf2xgm25GADxs9NQowN23RZVC7XLaudNCyL9
   ho6px5A5r77Zq0sBJPBhcbNOhyosx5B7xj7SNuzqxlWe/JubisEA4/9ezjAPI6dd
   Eo/XSDskL4skIvcZB5p7Hd2PfTXERZ8P3BTdjchHw1FgL9MKIfKve0d8hwVUc1Fy
   255sFLwIQWJ9OSjdoEavNOiCw25+mMGHldEhSVHO0oC0PvxK4vQy12bHZzKTC3+m
   sVQYdHShhB0b0zGlPas3XI/SDjlMs9a7LeTf9dOEYEL6l2QMyibBUt2ddZH/7oxq
   UMCZpDm/AgMBAAECggEACRVS7lfAecGfHZkiQGZROpSSPfmeB4OPwcpGnnNIpGhZ
   lNzR8pMcAKyOocDAu3u9yfmfLEKS8iuX0hpMPDSxcE6EFGKIbo7ZdTaw0iQ+xx4X
   iiE5ENCCrlNq+yw/fc6+6Ac1fO66YxKO5zevcYRg9bunoeRefYbkXhovof4tr9rL
   wJckacOtxhFNm7cDtqf9Ah5kbhotak/oi0cVDz9fpqH+shQBiNix/HO8XOhAfhBw
   xcVBD5tCe3igQRBh0XqbIikbcBSWsRVZxzIKQr4/+Muy5LQvxo0Kmz/lqWM03ObZ
   Majqu5BviKm+jeoBmK9qQxBFBBYGVIBnHNZNUN25KQKBgQDfUK0YV/Uug90LK8/s
   0UAw7rZHWieIe2MflPBbj71v7YuGzEfPetRfFdTmqI8YZefrNGySGPtcINa87Hv8
   xUlCTxEjvYfHaMUlEvm0m4+pTYuWsmc5BR7mFE1urXak9LpqPowKVstolQuhOaQg
   Gdj32Mk5out3X2GxUCsZtWXf7QKBgQDVlwycx5yk18OvpdyzNXXa51uXiADRgEI0
   Vfn6KSV3sSI9wjGPe3Tm8kGTEVyG8o56APNV4Rj9ZKkEd1hcZeq7hgI6SjYNXWQr
   5oBM0Od2EjbjKh3PitJRabBtuEX98KLM/zo4Z2tkMkr/2Rpn3qtl/wKfixUB/I4r
   NUa7OtsS2wKBgQCdveoXOQJashBwtKjx2jlilywwqJEmSioRg+5obtdcecpGFIRh
   HZ1n8Q7rQ4OYs1sn/Gb4qCbdw+CLoOxP97ew3BL6UQXZKLuhXY7/Mac/6yO/9hMN
   5v0Vfp/XnzYgfTI0nCvlnbufCzEk2IeDmV52bC5vxRJYxwpF6qAXT9g/XQKBgQCx
   dpMwIFnyTKN2aWT6MUz+2IOtX37ukpZvTZApXc6XqEE+9v6erIDw8g+x1hb+uMHQ
   dMG5dRGCWARmhZKREsz5idqH++j1Kcd1AktPh7MI0xFvpSqnqjwdEKdaQmVFHI7n
   rJf/DU6ZLYBLG2NpMgVO9ZaEYNbPk7u8AsQGBFzJSQKBgCgRpgWmqd4kq60FDkKT
   FrjN+P19I1vekiousJTGd7waeLmQU52NMpJQhE/dVItmxPPlk8P8QxZqNbKrVo+R
   40Zjy5MTZQQkk+e9rmML5xD0F7xGjD4ED7uwjPaA7Z9og/bK5auiHi3DVCKOSdJa
   S8r3oTDRn9rM7qPztU+iZHuB
   -----END PRIVATE KEY-----
   cluster_name: cf
   datacenter_name: CSPLAB
   datastore_pattern: CloudFoundry
   diego_cell_instances: 1
   director_ip: 172.16.60.0
   disk_path: /Disks
   external_dns: 172.16.0.11,172.16.0.17
   gateway: 172.16.255.250
   haproxy_ip: 172.16.60.1
   main_user_name: cfadmin
   main_user_password: Passw0rd!
   ntp_servers: 172.16.0.9
   persistent_datastore_pattern: CloudFoundry
   portgroup: csplab
   resource_pool: ICP-CF-210
   subnet: 172.16.0.0/16
   address_range: 172.16.60.0-172.16.60.255
   template_folder: /icp-cf-210/templates
   vm_folder: /icp-cf-210/vms
   vmware_address: 10.1.212.26
   vmware_password: Passw0rd!
   vmware_username: cfadmin
  ```

  * Under *bluemix_apps_domain_cert* paste the contents of star_mybluemix.csplab.local.crt

  * Under *bluemix_apps_domain_cert_rsa_key* paste the contents of star_mybluemix.csplab.local.key

  * Under *bluemix_env_domain_cert* paste the contents of star_bluemix.csplab.local.crt

  * Under *bluemix_env_domain_cert_ca* paste the contents of rootCA.pem

  * Under *bluemix_env_domain_cert_rsa_key* paste the contents of star_bluemix.csplab.local.key

  **Important:** Any folders, resource pools, datacenters, etc. specified in the uiconfig.yml file must exist on the target vCenter server prior to installation and the user specified as the vmware username must have authority to create virtual machines and deploy vApps to these objects.  That user must also have the authority to write to the specified datastores.

  * **main_user_name:** The username that should be used to login to the CF UI as the administrator (will be created in the environment). e.g. "cfadmin"

  * **main_user_password:** Password for the administrator user. e.g. "SuperS3cretPassw0rd"

  * **bluemix_env_domain:** API and Management domain for the CF environment.  Config for this domain in the DNS server will occur later. e.g. "cf.mydomain.local"

  * **bluemix_app_domain:** The default shared domain to which applications are deployed. e.g. "cfapps.mydomain.local"

  * **diego_cell_instances:** Number of Diego cells to deploy. Each Diego cell uses 4 vCPU, 32GB of RAM, and 300GB of disk space. e.g. "1"

  * **external_dns:** Comma separated list of enterprise or lab domain name servers. e.g. "172.16.0.11,172.16.0.17"

  * **ntp_servers:** Comma separated list of local ntp servers. e.g. "172.16.0.9"

  * **vmware_address:** IP address of the VMware vCenter Server e.g. "10.1.212.26"

  * **vmware_username:** Value username on the vCenter Server with permissions to create VMs on the <CloudFoundry> Cluster, on the <CF_DS> datastore, and using the <CF_Net> network. e.g. "cfadmin"

  * **vmware_password:** Password for vmware_username.  e.g. "SuperS3cretPassw0rd"

  * **datacenter_name:** The name of the datacenter on the vCenter server where the <CloudFoundry> cluster was created e.g. "ICPLAB"

  * **cluster_name:** Name of the cluster where CF VMs should be created. Cluster should have DRS enabled. e.g. "CloudFoundry".

  * **resource_pool:** Name of resource pool to hold CF VMs. e.g. "ICP_CF_21"

  * **vm_folder:** (optional) Name of folder on VMware Datastore where VMs should be created. e.g. "VMs"

  * **template_folder:** (optional) Name of vSphere folder where stemcell VMs (templates) should be stored. e.g. "Templates"

  * **disk_path:** The subdirectory on the datastore where VM persistent disks should be stored. e.g. "/icp-cf-210/Disks".  This directory must exist.  If it does not, you must create it.  e.g. In the vCenter web client browse the specified datastore in *persistent_datastore_pattern* and create the *icp-cf-210* folder and then under that create the *Disks* folder.

  * **datastore_pattern:** A pattern describing which datastore hosts the virtual machines. e.g. "CF_DS"

  * **persistent_datastore_pattern:** A pattern describing which datastore hosts persistend disks (can be the same as datastore_pattern) e.g. "CF_DS"

  * **subnet:** Subnet for VMs. e.g. "172.16.0.0/16"

  * **address_range:** Range of IP addresses that are available for use in 'subnet'. e.g. "172.16.60.0-172.16.60.255"

  * **portgroup:** The vmware network portgroup on which the VMs should communicate. e.g. "CF_net"

  * **director_ip:** The IP address within the address_range which should be used for the director VM. e.g. "172.16.60.0"


## Change configuration to install POC instance (or opposite to install production instance)

  `cm state -s cfpoc set --status READY  # Install POC instance`

  `cm state -s cf set --status SKIP      # Do not install production instance`

  `cm state -s diegopoc set --status READY # Install Diego POC instance`

  `cm state -s diego set --status SKIP  # Skip the Diego Production instance`

  *NOTE:* To install a production instance, reverse the flags setting cf and diego to READY and cfpoc and diegopoc to SKIP. The default environment will do a production install.

## Deploy the environment
  **NOTE:** You may have to execute this command many times to get to completion.  See troubleshooting section below.

  ```
  cd /opt/cf
  ./launch_deployment.sh -c uiconfig.json |tee deploy.log
  ```

  * **-c:** Config file to use for this deployment

  * **|tee deploy.log** Copy all output to deploy.log for later troubleshooting and redirect stderr to stdout to capture it as well.

## Configure the DNS

  Create an `A` Record in the DNS pointing to hte IP address of your ha_proxy (which was defined in your uiconfig-csplab.yml file) with a hostname of \*.bluemix.csplab.local and another for \*.bluemix.csplab.local

  In Microsoft Active Directory:
  * Highlight the domain (csplab.local in our example)

  * Right click on the domain name and choose to add an "A" record

  * In the hostname blank put `*.bluemix` and in the address blank use the IP address of the ha_proxy returned from the bosh command.

  * Repeat and create an "A" record for `*.mybluemix` using the same IP address.

## Deploy the buildpacks

  **Important:** Deploying the buildpacks requires the access to the api server and should not be completed prior to making the DNS changes described above.

  ```
  cd /opt/cf
  ./create_buildpacks.sh
  ```

2. You are now ready to use your CloudFoundy environment, the target for  your cf commands is `http://api.<bluemix domain>`.  e.g. `http://api.bluemix.csplab.local`.

## Test your newly provisioned environment
1. Install the cloud foundry CLI to your local workstation

  **Note:** As of the time of this writing, setting roles for an org requires cf cli version 6.13.  All other commands can use the latest version of the cf cli which is available.

  Go to https://github.com/cloudfoundry/cli/releases to find the release for your workstation's architecture.

2. Install the certificate key for the api server
  * Linux
    ```
    cat rootCA.pem >> /etc/ssl/certs/ca-certificates.crt
    ```

  * Mac
    ```
    sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain rootCA.pem
    ```

2. Configure your cf client's local
  ```
  cf config --locale en-US
  ```

2. Login to CF using the credentials you provided in uiconfig.json.  In our example we used `cfadmin/Passw0rd!`.
  ```
  cf api http://api.bluemix.mydomain.local
  cf login -u cfadmin -p Passw0rd!
  ```


## Troubleshooting
If the installer fails it will output some information which is not very useful plus something like "bosh task 97 --debug" for more information (the 97 may be any number). bosh runs inside the inception container and so executing this command requires a bash shell on the container and not on the installer VM's local filesystem.

Your environment name is the value you used as the "-n" parameter to your launch.sh command (in this case "csplab").

```
connect.sh -name csplab
```

You are now running a bash shell on the inception vm.  To get more information about the failed task execute:

```
bosh task <task number> --debug
```

Don't forget to type `exit` on the command line to exit the container shell when you are done.

To output debug information for the task and save the data to a file on the disk using a single command, try something like this:

```
docker exec -it $(docker ps -a |grep inception |cut -d' ' -f1) bosh task <97> --debug |tee task<97>.log 2>&1
```

Substitute the two <97>'s with the task ID output by the installer. This will write the debugging output to the screen and save it as a file named task97.log on your local filesystem for further scrutiny.

### Checking the status of the install
View the file: <installdir>/data/<env>/CloudFoundry/pie/states-to-deploy-cf.yaml

Each task shows a status which could be READY, FAILED, or SUCCESS.

If a task is in a SUCCESS state and you want to reinstall, edit the file and replace "SUCCESS" with "READY".  Tasks in a FAILED state will automatically be reattempted on the next launch_deployment.sh execution.

### Login to a specific bosh image
From the inception container execute "bosh ssh <service>"
e.g. `bosh -d /data/CloudFoundry/cf-deploy-poc.yml ssh cc_core/0`
On the bosh container, data is in /var/vcap.  Most calls will require running as root, so use `sudo <command>` or become root with `sudo su -`.


### To find the credentials for various users
See `less /data/<env>/CloudFoundry/credentials.yml`

### To execute bosh commands
```
bosh login
bosh target http://<director_ip>:25555
```

### Show all bosh VMs and their IP addresses
From the inception container execute `bosh vms`



Trace cf calls: `export CF_TRACE=true`

Default vcap credentials: vcap/c1oudc0w

### Troubleshoot director installation
connect to inception container
```
export BOSH_INIT_LOG_LEVEL=DEBUG
bosh-init deploy /data/gen-vmware_micro_boshinit.yml
```

# Using CloudFoundry
1. First, you much install the CloudFoundry client (cf) version 6.13 https://github.com/cloudfoundry/cli/releases/tag/v6.13.0

2. Configure your client
  * Set your locale
  ```
  cf config --locale en-US --color true
  ```
  For Debugging, you can also set `-trace true`

3. Login to your environment
  * Specify your api target
  ```
  cf api https://api.cf.csplab.locale
  ```

  * Login to your instance
  ```
  cf login -u cfadmin -p Password!
  ```

  **important:** to login with a self-signed certificate you should import the cert key (operation varies by operating system), or specify --skip-ssl-validation on the command line.
  ```
  cf login -u cfadmin -p Password! --skip-ssl-validation
  ```

  * Create a new org
  ```
  cf create-org vhavard@us.ibm.com
  ```

  * Create a new user
  ```
  cf create-user vhavard@us.ibm.com Passw0rd!
  ```

  * Make a user the manager of his/her org
  ```
  cf set-org-role vhavard@us.ibm.com vhavard@us.ibm.com OrgManager
  ```

  * Login as your new user to your new org
  ```
  cf login -u vhavard@us.ibm.com -p Password! -o vhavard@us.ibm.com
  ```

  * Create a new space in your new org and use it as your target
  ```
  cf create-space dev
  cf target -s dev
  ```

  * Login to an api, org, and space with a single command
  ```
  cf login -a https://api.cf.csplab.local -u vhavard@us.ibm.com -p Password! -o vhavard@us.ibm.com -s dev
  ```

  * See what buildpacks are available
  ```
  cf buildpacks
  ```

  * Get the node.js starter code from github
  ```
  git clone https://github.com/IBM-Bluemix/get-started-node
  ```

  * Get needed packages
  ```
  cd get-started-node
  npm install
  ```

  *  Start your getting started apps
  ```
  node server.js
  ```

  * Using a browser test your app at http://localhost:3000

  * Push to bluemix public
  ```
  cf login -a https://api.ng.bluemix.net -u vhavard@us.ibm.com -p myPassword -o vhavard@us.ibm.com -s dev
  cf push
  ```

  * Push to bluemix private
  ```
  cf login -a https://api.cf.csplab.local -u vhavard@us.ibm.com -p myPassword -o vhavard@us.ibm.com -s dev
  cf push
  ```

  * Set an envar in your environment
  ```
  cf set-env LOCATION csplab-beta3
  ```
