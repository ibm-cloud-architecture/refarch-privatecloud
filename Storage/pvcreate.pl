#!/usr/bin/perl

############################################################################################
#This script bulk creates a range of standard storage for a new IBM Cloud Private cluster
#It assumes that it is being run on an NFS server and that the exported storage filesystem
#is in /storage.  
#
#It will create a number of volumes beginning with "vol" and ending with a 2 digit number
#e.g. vol01 and then create a new PV in the cluster which points to this path.
#
#Look for comments beginning with EDIT: for the changes you can make to tailor the results.
#
#By default the following PVs are created
#
# New cluster storage pattern
# 10x 1GB RWO - Recycle
# 5x 5GB RWO - Recycle
# 3x 5GB RWX - Retain
# 5x 10GB RWO - Recycle
# 5x 10GB RWX - Retain
# 1x 50GB RWO - Recycle
# 1x 50GB RWX - Retain
#
# IMPORTANT: prior to running this script kubectl must be installed, in your path, and 
# configured to connect to the correct cluster.  To configure kubectl you must use commands
# similar to the following:

# kubectl config set-cluster cfc --server=https://172.16.50.249:8001 --insecure-skip-tls-verify=true
# kubectl config set-context cfc --cluster=cfc
# kubectl config set-credentials user --token=eyJhbGciOiJSUzI1NiIsImtpZCI6IjY5NjI2ZDJkNjM2NjYzMmQ3MzY1NzI3NjY5NjM2NTJkNmI2NTc5NjkiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJjZmMtc2VydmljZSIsImV4cCI6MTQ5ODcwNjU3NywiaWF0IjoxNDk4NjYzMzc3LCJpc3MiOiJodHRwczovL21hc3Rlci5jZmM6ODQ0My9hY3MvYXBpL3YxL2F1dGgiLCJwcm9qZWN0cyI6WyJkZWZhdWx0Il0sInN1YiI6ImNmY2FkbWluIn0.OZGmGavUhCx2Cys33CQCkpKGu7VTE2x8fG068eS0PojGQxmDnh-VdlFTh1G1D5S6vxm_fv_O-npm21maleqow_vh-70JqMeTzAuVWYbCLQE6Zs9P5zvdTcnFOcBZVbpronOYloYsG01_02llgdes5vvetmhMx4j5f3KYmo7K6MUq6M7Zye3b3riL7IlE6x-hhE4iGZI87kTebCaYQxpZKI-Zureg3f2AswXr3o7vxoSIjMBDdnYhwjKjWff3sNnAOeOSn_fhXdW9zQ3bQeJndEDkoXjK4V4CeDxfNJBq83VjbHdoW2QNutGm2C44uR29n_GazW1cVg2aZSYAusZsOg
# kubectl config set-context cfc --user=user --namespace=default
# kubectl config use-context cfc
############################################################################################

#my $ipaddrcmd = "host `hostname`|cut -d' ' -f4";

# EDIT: By Default we use the IP address of the local machine
# You may need to change this if the above command returns an incorrect value
#my $server = `ipaddrcmd`;

#EDIT: The number at which to start volume numbering. 1 will start with "vol01" 20 will start with "vol20"
my $startVol = 0;

# EDIT: Update with the correct paths if any of these is incorrect for your system
my $HOST = "/usr/bin/host";
my $CUT = "/usr/bin/cut";
my $HOSTNAME = "/bin/hostname";
my $HOSTFILE = "/etc/hosts";
my $GREP = "/bin/grep";
my $KUBECTL = "/usr/local/bin/kubectl";

# EDIT: Grep for the IP address in the local hostfile
my $server = `grep \`$HOSTNAME\` $HOSTFILE|$CUT -f1`;

# EDIT: If the hostname is in DNS, you can use this version instead
#my $server = `$HOST \`$HOSTNAME\`|grep -f4`;

#EDIT: Or, you can simply hard code the address or hostname
#my $server = "172.16.50.250";

print "Using NFS server address of $server";
my $filename = "/tmp/pv.yaml";

my $command = "$KUBECTL create -f \"$filename\"";

my @PATTERNS = ();

#EDIT: Update each of the following patterns to represent your target environment
#number = the number of instances of this pattern
#size = the size of the PV to create
#AccessMode = the AccessMode or the volume.  Can be ReadWriteOnce, ReadWriteMany, or ReadOnlyMany
#ReclaimPolicy = What to do with the volume after the claim is released.  Can be Retain or Recycle.
#Note that a PV creation uses no space on the disk and only enforces limits on the user side.
#It is possible (and probably preferable) to overprovision this storage by a factor of 4 to 1 or more.

push @PATTERNS, {
  "number" => 10,
  "size" => "1Gi",
  "AccessMode" => "ReadWriteOnce",
  "ReclaimPolicy" => "Recycle",
};

# push @PATTERNS, {
#   "number" => 5,
#   "size" => "5Gi",
#   "AccessMode" => "ReadWriteOnce",
#   "ReclaimPolicy" => "Recycle",
# };
# 
# push @PATTERNS, {
#   "number" => 3,
#   "size" => "5Gi",
#   "AccessMode" => "ReadWriteMany",
#   "ReclaimPolicy" => "Retain",
# };
# 
# push @PATTERNS, {
#   "number" => 5,
#   "size" => "10Gi",
#   "AccessMode" => "ReadWriteOnce",
#   "ReclaimPolicy" => "Recycle",
# };
# 
# push @PATTERNS, {
#   "number" => 5,
#   "size" => "10Gi",
#   "AccessMode" => "ReadWriteMany",
#   "ReclaimPolicy" => "Retain",
# };
# 
# push @PATTERNS, {
#   "number" => 1,
#   "size" => "50Gi",
#   "AccessMode" => "ReadWriteOnce",
#   "ReclaimPolicy" => "Recycle",
# };
# 
# push @PATTERNS, {
#   "number" => 1,
#   "size" => "50Gi",
#   "AccessMode" => "ReadWriteMany",
#   "ReclaimPolicy" => "Retain",
# };

################################
# Do NOT edit below this line
################################

for(my $i=0;$i<scalar(@PATTERNS);$i++) {
  for(my $j=0;$j<$PATTERNS[$i]->{"number"};$j++) {

    my $size = $PATTERNS[$i]->{"size"};
    my $accessMode = $PATTERNS[$i]->{"AccessMode"};
    my $reclaimPolicy = $PATTERNS[$i]->{"ReclaimPolicy"};

    my $volName = sprintf("vol%02i",$startVol);
    my $volPath = "/storage/$volName";

    mkdir($volPath);
    chmod 0777,$volPath;

    my $yaml = "kind: PersistentVolume
apiVersion: v1
metadata:
  name: $volName
spec:
  capacity:
    storage: $size
  accessModes:
    - $accessMode
  persistentVolumeReclaimPolicy: $reclaimPolicy
  nfs:
    path: $volPath
    server: $server";

    open(OUTPUT,">$filename") || die "Unable to open $filename for outpute: $!\n";   
    print OUTPUT $yaml;
    close(OUTPUT);

    print `$command`;

    $startVol++;
  }
}
