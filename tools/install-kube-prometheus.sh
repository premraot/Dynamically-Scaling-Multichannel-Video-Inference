#!/bin/bash

curr_dir=$(readlink -f $(dirname "${BASH_SOURCE[0]}"))
top_dir=$(dirname "${curr_dir}")

source ${curr_dir}/common.sh

download_prometheus() {
    cd ${top_dir}/.cache
    download_file ${top_dir}/.cache/kube-prometheus-0.3.0.zip \
        https://github.com/coreos/kube-prometheus/archive/v0.3.0.zip \
        5428ba512ebac46ebc44d45c3e16fd18

    if [ ! -d ${top_dir}/.cache/kube-prometheus-0.3.0 ]; then
        unzip kube-prometheus-0.3.0.zip
    fi
}

apply_patch() {
    if [ ! -f ${top_dir}/.cache/kube-prometheus.patch ]; then
        cat > ${top_dir}/.cache/kube-prometheus.patch << '_EOF'
diff --git a/manifests/grafana-service.yaml b/manifests/grafana-service.yaml
index 3acdf1e..6587f02 100644
--- a/manifests/grafana-service.yaml
+++ b/manifests/grafana-service.yaml
@@ -6,9 +6,11 @@ metadata:
   name: grafana
   namespace: monitoring
 spec:
+  type: NodePort
   ports:
   - name: http
     port: 3000
     targetPort: http
+    nodePort: 31008
   selector:
     app: grafana
diff --git a/manifests/prometheus-service.yaml b/manifests/prometheus-service.yaml
index 4f61e88..56af5ce 100644
--- a/manifests/prometheus-service.yaml
+++ b/manifests/prometheus-service.yaml
@@ -6,10 +6,12 @@ metadata:
   name: prometheus-k8s
   namespace: monitoring
 spec:
+  type: NodePort
   ports:
   - name: web
     port: 9090
     targetPort: web
+    nodePort: 31009
   selector:
     app: prometheus
     prometheus: k8s
_EOF
        cd ${top_dir}/.cache/kube-prometheus-0.3.0
        patch -p1 < ${top_dir}/.cache/kube-prometheus.patch
    fi
}

install_yaml() {
    cd ${top_dir}/.cache/kube-prometheus-0.3.0
    kubectl apply -f manifests/setup
    sleep 5
    kubectl apply -f manifests
}

mkdir -p ${top_dir}/.cache
download_prometheus
apply_patch
install_yaml