# How to do HPA on prometheus metrics

Assuming the [`kube-prometheus`](https://github.com/coreos/kube-prometheus) got deployed already.
Steps could refer to the [`doc`](README.md).
We could deploy [`k8s-prometheus-adapter`](https://github.com/DirectXMan12/k8s-prometheus-adapter) to implement our target.

## Deploy `k8s-prometheus-adapter`

### Create namespace custom-metrics to ensure that the namespace that we're installing the custom metrics adapter in exists.

```shell
$ kubectl create namespace custom-metrics
```

### Create a secret called `cm-adapter-serving-certs` with two values: `serving.crt` and `serving.key`.

```shell
$ export PURPOSE=serving
$ openssl req -x509 -sha256 -new -nodes -days 365 -newkey rsa:2048 -keyout ${PURPOSE}-ca.key -out ${PURPOSE}-ca.crt -subj "/CN=ca"
$ echo '{"signing":{"default":{"expiry":"43800h","usages":["signing","key encipherment","'${PURPOSE}'"]}}}' > "${PURPOSE}-ca-config.json"
$ kubectl -n custom-metrics create secret tls cm-adapter-serving-certs --cert=./serving-ca.crt --key=./serving-ca.key
```

### Download [`kube-prometheus`](https://github.com/coreos/kube-prometheus)

```shell
$ git clone https://github.com/directxman12/k8s-prometheus-adapter.git
$ cd k8s-prometheus-adapter
$ git checkout -b v0.5.0 v0.5.0
```

### Make changes to `k8s-prometheus-adapter/deploy/manifests/custom-metrics-apiserver-deployment.yaml`.

```shell
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
```

### Deploy the k8s-prometheus-adapter

```shell
$ kubectl create -f deploy/manifests/
```

## Deploy a sample HPA

[`infer-hpa.yaml`](infer-hpa.yaml) is a sample for scaling on people inference scale ratio.

```shell
spec:
  maxReplicas: 4
  metrics:
  - type: Pods
    pods:
      metric:
        name: ei_scale_ratio
      target:
        type: AverageValue
        averageValue: 1
```

Once prometheus metric `ei_scale_ratio` is not 1, the HPA will calculate the replicas to scalei up or down.
