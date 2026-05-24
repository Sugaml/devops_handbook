# Day 1 — Kubernetes Architecture & Your First Cluster

**Goal:** Understand what Kubernetes is, how the control plane and nodes interact, and stand up a local lab cluster you will use for the next 29 days.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Why Kubernetes?

| Problem without orchestration | What Kubernetes provides |
|------------------------------|---------------------------|
| Manual placement of containers on VMs | Scheduler assigns Pods to nodes |
| No built-in restart on crash | Controllers reconcile desired state |
| Ad-hoc service discovery | Services + DNS |
| Rolling deploys are custom scripts | Deployments with declarative updates |
| Config scattered on hosts | ConfigMaps, Secrets as API objects |

Kubernetes is **not** a PaaS — it is a **container orchestration platform**. You still own images, app config, observability, and security policies.

---

## 2. Core architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ API      │  │ etcd     │  │ Scheduler│  │ Controller  │  │
│  │ Server   │  │ (state)  │  │          │  │ Manager     │  │
│  └────┬─────┘  └──────────┘  └──────────┘  └─────────────┘  │
└───────┼─────────────────────────────────────────────────────┘
        │ kubectl / controllers / kubelet watch API
┌───────┴─────────────────────────────────────────────────────┐
│  WORKER NODE(s)                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │ kubelet  │  │ kube-    │  │ Container runtime        │   │
│  │          │  │ proxy    │  │ (containerd / CRI-O)     │   │
│  └──────────┘  └──────────┘  └──────────────────────────┘   │
│         Pods (1+ containers sharing network/IP)             │
└─────────────────────────────────────────────────────────────┘
```

### Key components

| Component | Role |
|-----------|------|
| **API Server** | Front door; all operations go through REST; validates and persists objects |
| **etcd** | Distributed key-value store; cluster source of truth |
| **Scheduler** | Assigns unscheduled Pods to Nodes |
| **Controller Manager** | Runs loops (Deployment, ReplicaSet, Node, etc.) |
| **kubelet** | Agent on each node; ensures containers in Pod spec are running |
| **kube-proxy** | Maintains Service network rules (iptables/IPVS/eBPF) |
| **Container runtime** | Runs containers (containerd is default on most distros) |

**DevOps mental model:** Everything is an **API object** with `spec` (desired) and `status` (observed). Controllers continuously reconcile the gap.

---

## 3. Objects, not containers directly

You rarely create bare containers. You declare **Pods** (and higher abstractions like Deployments). The smallest schedulable unit is a **Pod** — one or more containers sharing:

- Network namespace (one IP per Pod)
- Optional shared volumes
- IPC namespace (optional)

---

## 4. Install tools

### kubectl

```bash
# macOS
brew install kubectl

# Linux (generic)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

kubectl version --client
```

### kind (Kubernetes IN Docker)

```bash
brew install kind   # or: go install sigs.k8s.io/kind@latest

cat <<'EOF' > /tmp/kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
        protocol: TCP
  - role: worker
  - role: worker
EOF

kind create cluster --name devops-handbook --config /tmp/kind-config.yaml
kubectl cluster-info --context kind-devops-handbook
kubectl get nodes -o wide
```

### minikube (alternative)

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
minikube kubectl -- get nodes
# alias: alias kubectl="minikube kubectl --"
```

---

## 5. First interactions

```bash
# Cluster health
kubectl get componentstatuses 2>/dev/null || kubectl get --raw='/readyz?verbose'
kubectl get nodes

# Run a throwaway Pod
kubectl run nginx --image=nginx:1.27-alpine --port=80
kubectl get pods -o wide
kubectl describe pod nginx
kubectl logs nginx
kubectl delete pod nginx

# Imperative vs declarative — prefer declarative YAML from Day 2 onward
kubectl create deployment web --image=nginx:1.27-alpine --replicas=2
kubectl get deployments,pods,rs
kubectl delete deployment web
```

---

## 6. Managed vs self-managed

| Environment | Control plane | You manage |
|-------------|---------------|------------|
| **kind / minikube** | Local, disposable | Learning only |
| **EKS / GKE / AKS** | Cloud provider | Node pools, IAM, add-ons |
| **kubeadm / RKE / k3s** | You or vendor | OS, etcd backups, upgrades |

Production teams often use managed control planes and GitOps for workloads (Days 23–24).

---

## 7. Lab — Day 1

1. Install `kubectl` and create a **kind** cluster named `devops-handbook` with at least one worker node.
2. Run `kubectl get nodes` and record Kubernetes version and container runtime (`kubectl describe node | grep -i container`).
3. Deploy nginx imperatively with 2 replicas: `kubectl create deployment lab-nginx --image=nginx:1.27-alpine --replicas=2`.
4. Draw (on paper or Excalidraw) control plane vs worker for your cluster.
5. Delete the deployment: `kubectl delete deployment lab-nginx`.
6. **Stretch:** Install [k9s](https://k9scli.io/) and explore nodes and namespaces interactively.

---

## 8. DevOps connections

- **CI/CD:** Pipelines build images; Kubernetes pulls them at deploy time — Day 5+ covers Deployments.
- **Infra as code:** Cluster creation (Terraform, Cluster API) is separate from workload manifests (Helm, Kustomize).
- **On-call:** Most incidents start with `kubectl get nodes,pods -A` and API/etcd health — build that habit today.

---

## Quick reference

| Task | Command |
|------|---------|
| Cluster info | `kubectl cluster-info` |
| Node list | `kubectl get nodes -o wide` |
| Run test pod | `kubectl run tmp --image=nginx --rm -it --restart=Never -- curl localhost` |
| Delete kind cluster | `kind delete cluster --name devops-handbook` |

**Next:** [Day 2 — kubectl, contexts & namespaces](../day2/)
