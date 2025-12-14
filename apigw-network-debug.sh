#!/usr/bin/env bash
set -e

echo "===== AWS IDENTITY ====="
aws sts get-caller-identity
echo

echo "===== REGION ====="
aws configure get region
echo

echo "===== API GATEWAY REST APIS ====="
aws apigateway get-rest-apis
echo

echo "===== API GATEWAY RESOURCES (yas-ml-api) ====="
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='yas-ml-api'].id | [0]" --output text)
echo "API_ID=$API_ID"
aws apigateway get-resources --rest-api-id $API_ID
echo

echo "===== API GATEWAY METHODS ====="
for RID in $(aws apigateway get-resources --rest-api-id $API_ID --query "items[].id" --output text); do
  echo "--- Resource $RID ---"
  aws apigateway get-method \
    --rest-api-id $API_ID \
    --resource-id $RID \
    --http-method ANY 2>/dev/null || true
done
echo

echo "===== API GATEWAY STAGES ====="
aws apigateway get-stages --rest-api-id $API_ID
echo

echo "===== API GATEWAY VPC LINKS ====="
aws apigateway get-vpc-links
echo

echo "===== ELBv2 LOAD BALANCERS ====="
aws elbv2 describe-load-balancers
echo

echo "===== ELBv2 LISTENERS ====="
for LB_ARN in $(aws elbv2 describe-load-balancers --query "LoadBalancers[].LoadBalancerArn" --output text); do
  echo "--- $LB_ARN ---"
  aws elbv2 describe-listeners --load-balancer-arn $LB_ARN
done
echo

echo "===== ELBv2 TARGET GROUPS ====="
aws elbv2 describe-target-groups
echo

echo "===== ELBv2 TARGET HEALTH ====="
for TG_ARN in $(aws elbv2 describe-target-groups --query "TargetGroups[].TargetGroupArn" --output text); do
  echo "--- $TG_ARN ---"
  aws elbv2 describe-target-health --target-group-arn $TG_ARN
done
echo

echo "===== VPCS ====="
aws ec2 describe-vpcs
echo

echo "===== SUBNETS ====="
aws ec2 describe-subnets
echo

echo "===== SECURITY GROUPS ====="
aws ec2 describe-security-groups
echo

echo "===== ROUTE TABLES ====="
aws ec2 describe-route-tables
echo

echo "===== EKS CLUSTERS ====="
aws eks list-clusters
echo

CLUSTER_NAME=$(aws eks list-clusters --query "clusters[0]" --output text)
echo "===== EKS CLUSTER DETAILS ($CLUSTER_NAME) ====="
aws eks describe-cluster --name $CLUSTER_NAME
echo

echo "===== KUBERNETES SERVICES ====="
kubectl get svc -A
echo

echo "===== KUBERNETES INGRESS ====="
kubectl get ingress -A
echo

echo "===== KUBERNETES ENDPOINTS ====="
kubectl get endpoints -A
echo

echo "===== DONE ====="
