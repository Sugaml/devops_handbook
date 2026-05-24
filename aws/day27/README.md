# Day 27 — EKS: Managed Kubernetes

**Goal:** Create a small EKS cluster, configure `kubectl`, deploy workloads, and tear down safely.

**Time:** 6–8 hours (cluster creation ~15–20 min)

**Services:** EKS, IAM, EC2 (node groups), CloudFormation (eksctl optional)

---

## 1. Cluster creation (eksctl recommended for labs)

```bash
# Install eksctl: https://eksctl.io/
eksctl create cluster \
  --name handbook-eks \
  --region us-east-1 \
  --version 1.29 \
  --nodes 2 \
  --node-type t3.medium \
  --tags Project=devops-handbook
```

Pure CLI path uses `aws eks create-cluster` + `create-nodegroup`—more verbose; eksctl wraps IAM and VPC.

---

## 2. kubeconfig

```bash
aws eks update-kubeconfig --name handbook-eks --region us-east-1
kubectl get nodes
kubectl get pods -A
```

---

## 3. Deploy sample app

```bash
kubectl create deployment handbook-nginx --image=nginx:1.27-alpine
kubectl expose deployment handbook-nginx --port=80 --type=LoadBalancer
kubectl get svc handbook-nginx -w
```

---

## 4. EKS operations via CLI

```bash
aws eks describe-cluster --name handbook-eks \
  --query 'cluster.{Endpoint:endpoint,Status:status,Version:version}'
aws eks list-nodegroups --cluster-name handbook-eks
aws eks describe-nodegroup --cluster-name handbook-eks --nodegroup-name ...
```

---

## 5. IRSA (IAM Roles for Service Accounts)

```bash
eksctl create iamserviceaccount \
  --cluster handbook-eks \
  --name handbook-sa \
  --namespace default \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve
```

Pods use OIDC to assume IAM roles—no node-wide credentials.

---

## 6. Lab — Day 27

1. Create cluster with 2 nodes (watch cost).
2. Deploy nginx; curl LoadBalancer hostname.
3. `kubectl logs` and `aws eks describe-cluster`.
4. **Teardown:** `eksctl delete cluster --name handbook-eks` (critical).

**Previous:** [Day 26](../day26/) · **Next:** [Day 28 — WAF & security](../day28/)
