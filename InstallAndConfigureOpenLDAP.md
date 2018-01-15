# Installing OpenLDAP to support ICP authentication

## Considerations

  * For a safer environment, consider running in a container on a separate server than your ICP Cluster.  This will prevent a situation where a node going down causes the inability to login to ICP other than admin

  * As of version 2.1.0.1, configuring ICP for LDAP authentication will result in *any* LDAP user being able to successfully authenticate to ICP regardless of if the user has been imported or has any permissions.  A user with no permissions cannot see or do much, but, as of 2.1.0.1, they can create and delete repositories.

  * In ICP 2.1.0, attaching to an LDAP server which has an admin user defined will cause the hard coded internal admin superuser account to be superceded and will effectively eliminate the superuser account until the admin account is removed.  In addition, if the LDAP server configuration is defined but no users have been imported and the user doing the configuration logs out of the admin ICP account, admin will no longer be able to login and accomplish anything other than the aforementioned create and delete repositories.  If this happens, shut down the ldap server container, login to ICP as the admin user, unconfigure the LDAP connection, restart the ldap server container.  Then you can login as admin to the ICP server again.</br></br>**Note:** This issue seems to be resolved in 2.1.0.1 which seems to completely ignore any "admin" user from the LDAP server.<br><br>**Attempting to rename the default admin user will break the ldif.**

  * Once an LDAP connection has been made in ICP it cannot be removed.  It can be changed, but if you want to remove it you must re-install.

  * Use a minimum of OpenLDAP version 1.1.10 because of an important bug fix.

  * While not strictly required, we will also install phpldapadmin to make it easier to manage your OpenLDAP service.

# Install OpenLDAP and phpLdapAdmin

**Important:** This procedure requires internet access or you must bring a .tgz of the osixia/openldap and osixia/phpldapadmin containers with you and manually load them into the local docker repository.

1. For persistent storage, you will need to map a couple of volumes.  If running in a separate docker instance as recommended above, you will need to create two directories where the LDAP server can store its data for persistence across restarts.<br><br>In this example, we will create two directories on the local disk for the mount points in the /opt/ldap directory on the host server:

 * `mkdir -p /opt/ldap/var/lib/ldap`
 * `mkdir -p /opt/ldap/etc/ldap/slapd.d`

1.  You will need to know values for a few initial variables.  Set the following environment variables for use when starting the OpenLDAP server:
 * `export ORG=IBM`
 * `export DOMAIN=ibm.com`
 * `export ADMIN_PWD=Passw0rd!`
 * `export LDAP_NAME=ldap-service`
 * `export LDAPADMIN_NAME=ldapadmin-service`
 * `export LDAP_PORT=6389`
 * `export LDAPADMIN_PORT=6443`

1. (optional) Pull the OpenLDAP and phpLDAPadmin containers:
```
docker pull osixia/openldap:1.1.11
docker pull osixia/phpldapadmin:0.7.1
```
Or, if you are loading up from a local instance use the appropriate docker load command to load these images into the local docker registry.<br><br>If you have direct internet access or access via a proxy server, the step below will not find it locally and automatically pull it from dockerhub.

1. Start the OpenLDAP service:
```
docker run -v /opt/ldap/var/lib/ldap:/var/lib/ldap -v /opt/ldap/etc/ldap/slapd.d:/etc/ldap/slapd.d -p $LDAP_PORT:389 --name "$LDAP_NAME" --hostname "$LDAP_NAME" --env LDAP_ORGANIZATION="$ORG" --env LDAP_DOMAIN="$DOMAIN" --env LDAP_ADMIN_PASSWORD="$ADMIN_PWD" --hostname "$LDAP_NAME" --detach osixia/openldap:1.1.11
```
This should start up the OpenLDAP container, mapping the local volumes to the container for persistence.<br><br>Note that the ldap service here is exported on port 6389 rather than the standard 389 which is below 1024 and would require root access to open.  This will be important when configuring the LDAP service for phpLDAPadmin and ICP.

1. Start the phpLDAPadmin service:
```
docker run --name "$LDAPADMIN_NAME" --hostname "$LDAPADMIN_NAME" -p $LDAPADMIN_PORT:443 --link "$LDAP_NAME:ldap-host" --env PHPLDAPADMIN_LDAP_HOSTS="ldap-host" --detach osixia/phpldapadmin:0.7.1
```
This should start up the phpLDAPadmin service and configure it to communicate with the exposed LDAP port.<br><br>Of particular interest is the --link command which links the OpenLDAP and phpLDAPadmin hosts so that they can communicate directly by name and on their standard ports (the internal port vs the exposed port).  With this --link command, there is no need to specify the exposed port to phpLDAPadmin.<br><br>Externally, you will reach phpLDAPadmin on its exposed port of $LDAPADMIN_PORT and the LDAP server on its exposed port $LDAP_PORT.

1. Login to your new phpLDAPadmin interface at https://<IP_OF_PHPLDAPADMIN_SERVER>:6443 using the login of cn=admin,dc=yourdomain,dc=com and the password specified in $ADMIN_PWD above.

1. **(ICP v2.1.0 only)** Expand the domain tree (you may have to click 'refresh' to see it), click on the admin user, and change the userid from "admin" to "icpadmin" (or some such other name, it cannot be named "admin").

  **NOTE:** This is an OpenLDAP hack.  When using phpLDAPadmin to manage openldap, logging in with this new userid will result in not being able to config the instance.  It seems the admin user is hard coded somewhere, though, and even though you renamed the user to "icpadmin", you can still login as "admin" via phpLDAPadmin.

1. Create a new group<br><br>
**NOTE:** ICP requires an OU for groups, do not skip this bit.<br><br>
**NOTE:** OpenLDAP supports posix groups and generic user accounts with functionality that mimics unix.  This means that it expects each user to be in his/her own group as well as in any other needed groups.<br><br>
When creating a user, a required field is "GID Number". The group this is expecting is the user's group.  So, as in a posix/unix environment when I create a user named vhavard I would also create a group named vhavard.

 * At the bottom of the left menu in the phpldapadmin UI, click on the "Create new entry here" button.
 * For the template select "Organizational Unit"
 * In the blank, put "groups", and then click "Create Object".
 * Now select the OU you just created and at the menu at the top on the right-hand pane, click "Create a child entry".
 * For the template choose "Generic: Posix Group"
 * In the blank provide a group name. e.g. "vhavard"
 * IN the left-hand tree, at the very bottom (*not* under the ou=groups branch) click on "Create new entry here".
 * For the template, choose "Generic: User Account".
 * Fill in the blanks for the user you want to create
   * First name="Victor"
   * Last name="Havard"
   * Common Name="Victor Havard"
   * User ID="cn=vhavard,dc=ibm,dc=com"
   * GID Number: Drop down the combo box and select the group you just created for this user.
   * Home directory="/home/vhavard"
   * Login shell="bash"
 * Repeat for as many users and groups as you would like to add.

 You should now have a user inside his/her own group.

1. Now create a new group which will contain all of the users you will want to import into ICP.
   * From the tree on the left, click the "Create new entry here" link which falls under the "ou=groups" branch.
   * Select the "Generic: Posix Group" template
   * Provide a group name (e.g. "ibm")
   * Under the "Users" section, check each user that should be a part of this group. _When you import this group into ICP, each of these users will be able to be assigned to a team and have access to team resources._
   * Click the "Create Object" button to create the group.

1. Find the group you just created on the left and click on it.  You will see the group membership under the "memberUid" section on the right. Notice that the value in each blank is only the uid value of the user e.g. vhavard.<br><br>
ICP 2.1.0.1 requires this memberUID value to be a DN and not just a parameter value.  You must update each memberUid value and replace the uid with the full DN for the user.<br><br> "vhavard" becomes "cn=Victor Havard,dc=ibm,dc=com".

1. Configure ICP to authenticate against your LDAP admin.

  * Login to ICP as "admin".
  * In v2.1.0.1, click on Menu->Manage->Authentication and use the following values in each blank:
    * First, set the "Type" value to "Custom".  If you do this later the UI will reset all your values, do it first and you can update the values.
  Name: OpenLDAP (or any other name)
    * URL: ldap://<IP_OF_YOUR_LDAP_SERVER>:<EXTERNAL_PORT><BR>For example: ldap://10.111.70.228:6389
    * BaseDN: dc=ibm,dc=com
    * BindDN: cn=admin,dc=ibm,dc=com
    * Admin password: Passw0rd!
    * Group filter: (&(cn=%v)(objectclass=posixGroup))
    * User filter: (&(cn=%v)(objectclass=inetOrgPerson))
    * Group ID map: \*.cn
    * User ID map: \*.userid
    * Group member ID map: posixGroup:memberUid
    * Click "Save".

1. Import a group of users.
  * In v2.1.0.1, click Menu->Manage->users
  * Click "Import Group"
  * In the "Common Name (CN)" blank put "cn=<your_group_name>" (eg cn=ibm)
  * In the "Organizational Unit (OU)" blank put "ou=<your_ou_name>" (e.g. ou=groups).
  * Click "Import".
  * Repeat for as many groups as you would like to import.<br><br>
  You should now have at least one user in your user list.

1. Create a new Team
  * Click Menu->Manage->Teams
  * Click "Create Team"
  * In the "Team Name" blank provide a name for your team (e.g. ibm)
  * At the bottom, chose the users who should be in this team.  If you have more than 10 users, you may have to type a part of the user name in the search blank to find a particular user. ICP will not put the entire list in the box at the bottom if the number of entries in the list is large.
  * For each user, specify the role they should have in the team (Administrator|Editor|Operator|Viewer).
  * Click "Create"

1. Give your new team access to some resources
  * Click your new team name
  * Near the top, click the "Resources" tab
  * Click "Add Resource"
  * Check the box of each namespace to which this team should have access.
  * Click "Add Resource"

  That's it, you should now be able to login as any of the imported users and access any of the resources available to the user.

# Appendix
The following script should install OpenLDAP and phpLDAP admin as per the above parameters.  Note that, if a proxy is available which allows access to the internet, this script will pull the appropriate containers and install them.

If no proxy server is available and the environment is fully air-gapped, the images for OpenLDAP and phpLdapAdmin must exist in the local docker registry.

```
#!/bin/bash

ORG="IBM"
DOMAIN="ibm.com"
ADMIN_PWD="Passw0rd!"
LDAP_NAME="ldap-service"
LDAPADMIN_NAME="ldapadmin-service"
LDAP_PORT=6389
LDAPADMIN_PORT=6443
HTTP_PROXY=http://proxy.mydomain.com:9480
HTTPS_PROXY=http://proxy.mydomain.com:9480
PV_PATH=/opt/ldap
PV_PATH_VAR=$PV_PATH/var/lib/ldap
PV_PATH_ETC=$PV_PATH/etc/ldap/slapd.d
LINK_HOST=ldap-host

# Create the PV path
# Uncomment the following two lines to automatically create the hostPath storage paths if they do not already exist.
# mkdir -p $PV_PATH_VAR
# mkdir -p $PV_PATH_ETC

# First, kill any running instance
# Uncomment the following lines if this is a re-installation and you want to remove the previous installation. Use at your own risk!
#echo "Removing any existing running instance"
#docker rm -f $(docker ps -a |grep "$LDAP_NAME" |cut -f1 -d' ') 2>&1 >/dev/null
#docker rm -f $(docker ps -a |grep "$LDAPADMIN_NAME" |cut -f1 -d' ') 2>&1 >/dev/null

echo "Starting new OpenLDAP instance"
docker run -v $PV_PATH_VAR:/var/lib/ldap -v $PV_PATH_ETC:/etc/ldap/slapd.d -p $LDAP_PORT:389 --name "$LDAP_NAME" --hostname "$LDAP_NAME" --env LDAP_ORGANIZATION="$ORG" --env LDAP_DOMAIN="$DOMAIN" --env LDAP_ADMIN_PASSWORD="$ADMIN_PWD" --hostname "$LDAP_NAME" --detach osixia/openldap:1.1.11

echo "Starting new phpLdapAdmin instance"
docker run --name "$LDAPADMIN_NAME" --hostname "$LDAPADMIN_NAME" -p $LDAPADMIN_PORT:443 --link "$LDAP_NAME:$LINK_HOST" --env PHPLDAPADMIN_LDAP_HOSTS="$LINK_HOST" --detach osixia/phpldapadmin:0.7.1

```
