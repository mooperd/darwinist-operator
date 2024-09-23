#!/bin/bash

export GITSHA=$(git rev-parse HEAD)

cat manifests/api_server_deployment.yaml | envsubst | kubectl apply -n darwinist -f -
cat manifests/api_server_rbac.yaml | envsubst | kubectl apply -n darwinist -f -
cat manifests/imageprocessingjob_crd.yaml | envsubst | kubectl apply -n darwinist -f -
cat manifests/operator_deployment.yaml | envsubst | kubectl apply -n darwinist -f -
cat manifests/operator_rbac.yaml | envsubst | kubectl apply -n darwinist -f -

