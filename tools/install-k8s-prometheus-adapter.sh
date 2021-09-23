#!/bin/bash

curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")

source ${curr_dir}/common.sh

install_key() {
  cd ${top_dir}/.cache
  export PURPOSE=serving
  openssl req -x509 -sha256 -new -nodes -days 365 -newkey rsa:2048 -keyout ${PURPOSE}-ca.key -out ${PURPOSE}-ca.crt -subj "/CN=ca"
  echo '{"signing":{"default":{"expiry":"43800h","usages":["signing","key encipherment","'${PURPOSE}'"]}}}' > "${PURPOSE}-ca-config.json"
  kubectl -n custom-metrics create secret tls cm-adapter-serving-certs --cert=./serving-ca.crt --key=./serving-ca.key
}

download_prometheus_adapter() {
    cd ${top_dir}/.cache
    download_file ${top_dir}/.cache/k8s-prometheus-adapter-0.5.0.zip \
        https://github.com/DirectXMan12/k8s-prometheus-adapter/archive/v0.5.0.zip \
        e83263106f80404693ab1d5afd0cca62

    if [ ! -d ${top_dir}/.cache/k8s-prometheus-adapter-0.5.0 ]; then
        unzip k8s-prometheus-adapter-0.5.0.zip
    fi
}

apply_patch() {
    if [ ! -f ${top_dir}/.cache/k8s-prometheus-adapter.patch ]; then
        cat > ${top_dir}/.cache/k8s-prometheus-adapter.patch << '_EOF'
diff --git a/deploy/manifests/custom-metrics-apiserver-deployment.yaml b/deploy/manifests/custom-metrics-apiserver-deployment.yaml
index b36d517..7a94ea7 100644
--- a/deploy/manifests/custom-metrics-apiserver-deployment.yaml
+++ b/deploy/manifests/custom-metrics-apiserver-deployment.yaml
@@ -22,10 +22,10 @@ spec:
         image: directxman12/k8s-prometheus-adapter-amd64
         args:
         - --secure-port=6443
-        - --tls-cert-file=/var/run/serving-cert/serving.crt
-        - --tls-private-key-file=/var/run/serving-cert/serving.key
+        - --tls-cert-file=/var/run/serving-cert/tls.crt
+        - --tls-private-key-file=/var/run/serving-cert/tls.key
         - --logtostderr=true
-        - --prometheus-url=http://prometheus.prom.svc:9090/
+        - --prometheus-url=http://prometheus-operated.monitoring.svc:9090/
         - --metrics-relist-interval=1m
         - --v=10
         - --config=/etc/adapter/config.yaml

_EOF
        cd ${top_dir}/.cache/k8s-prometheus-adapter-0.5.0
        patch -p1 < ${top_dir}/.cache/k8s-prometheus-adapter.patch
    fi
}

install_yaml() {
    cd ${top_dir}/.cache/k8s-prometheus-adapter-0.5.0
    kubectl apply -f deploy/manifests/
}

mkdir -p ${top_dir}/.cache
kubectl create namespace custom-metrics
install_key
download_prometheus_adapter
apply_patch
install_yaml