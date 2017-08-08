CLOUD_NATIVE_DIR=~/github/refarch-cloudnative-kubernetes/docs/charts
helm repo index --url https://raw.githubusercontent.com/ibm-cloud-architecture/refarch-cloudnative-kubernetes/kube-int/docs/charts $CLOUD_NATIVE_DIR
mv $CLOUD_NATIVE_DIR/index.yaml .


