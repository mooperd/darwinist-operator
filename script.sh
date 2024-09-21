
kubectl apply -f imageprocessingjob_crd.yaml
kubectl apply -f operator_rbac.yaml
kubectl apply -f operator_deployment.yaml
kubectl apply -f api_server_rbac.yaml
kubectl apply -f api_server_deployment.yaml

kubectl port-forward svc/api-server-service 8080:8080
