# Day 2 — kubectl, Contexts, Namespaces & the API

**Goal:** Master kubectl for daily operations, understand kubeconfig/contexts, use namespaces for isolation, and read the Kubernetes API model.

**Time:** 4–5 hours

---

## 1. kubectl command structure

```bash
kubectl [command] [TYPE] [NAME] [flags]

# Examples
kubectl get pods
kubectl get pods -n kube-system
kubectl describe pod my-pod
kubectl apply -f manifest.yaml
kubectl delete -f manifest.yaml
```

### Essential commands

| Command | Purpose |
|---------|---------|
| `get` | List resources |
| `describe` | Detailed state + events |
| `apply` | Create/update from YAML (declarative) |
| `create` | Create imperatively or from file |
| `delete` | Remove resources |
| `edit` | Live-edit in `$EDITOR` |
| `logs` | Container stdout/stderr |
| `exec` | Run command in container |
| `port-forward` | Local access to Pod/Service |
| `explain` | OpenAPI docs in terminal |

```bash
kubectl explain pod.spec.containers
kubectl explain deployment.spec.strategy
```

---

## 2. Output formats

```bash
kubectl get pods -o wide
kubectl get pods -o yaml
kubectl get pods -o json
kubectl get pods -o custom-columns=NAME:.metadata.name,IP:.status.podIP,STATUS:.status.phase

# Watch mode
kubectl get pods -w

# Label selector (preview of Day 4)
kubectl get pods -l app=web
```

---

## 3. kubeconfig and contexts

Default file: `~/.kube/config`

```bash
kubectl config view
kubectl config get-contexts
kubectl config current-context
kubectl config use-context kind-devops-handbook

# Merge another cluster config
KUBECONFIG=~/.kube/config:~/.kube/other-config kubectl config view --flatten > /tmp/merged
mv /tmp/merged ~/.kube/config

# Set default namespace for context
kubectl config set-context --current --namespace=handbook-lab
```

Structure:

```yaml
clusters:    # API server URLs + CA
contexts:    # cluster + user + default namespace
users:       # credentials (cert, token, exec plugin)
current-context: kind-devops-handbook
```

**DevOps:** CI uses dedicated ServiceAccounts with limited kubeconfig; never commit cluster-admin kubeconfig to Git.

---

## 4. Namespaces

Logical isolation — not security boundaries alone (Day 13 RBAC).

```bash
kubectl create namespace handbook-lab
kubectl get namespaces
kubectl get all -n handbook-lab

# All namespaces
kubectl get pods -A
kubectl get pods --all-namespaces
```

Built-in namespaces:

| Namespace | Purpose |
|-----------|---------|
| `default` | User workloads if unspecified |
| `kube-system` | Control plane add-ons (CoreDNS, kube-proxy, CNI) |
| `kube-public` | Public info |
| `kube-node-lease` | Node heartbeats |

---

## 5. Declarative manifests — anatomy

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello
  namespace: handbook-lab
  labels:
    app: hello
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "echo Hello Kubernetes; sleep 3600"]
```

```bash
kubectl apply -f pod.yaml
kubectl get pod hello -n handbook-lab
kubectl delete -f pod.yaml
```

### Dry-run and validation

```bash
kubectl apply -f pod.yaml --dry-run=client -o yaml   # client-side validation
kubectl diff -f pod.yaml                              # show diff before apply
```

---

## 6. Imperative helpers (know them, prefer YAML)

```bash
kubectl create deployment api --image=nginx:1.27-alpine -n handbook-lab
kubectl expose deployment api --port=80 --target-port=80 -n handbook-lab
kubectl scale deployment api --replicas=3 -n handbook-lab

# Export to YAML for learning
kubectl get deployment api -n handbook-lab -o yaml > deployment-export.yaml
```

---

## 7. Useful flags and shortcuts

```bash
# Short resource names
kubectl get po,svc,deploy,ns

# Force replace (avoid for routine ops)
kubectl replace -f pod.yaml --force

# Delete all pods in namespace (controllers recreate them)
kubectl delete pods --all -n handbook-lab

# Aliases (add to ~/.bashrc)
alias k='kubectl'
alias kn='kubectl -n handbook-lab'
```

---

## 8. Lab — Day 2

1. Create namespace `handbook-lab`: `kubectl create namespace handbook-lab`.
2. Write `manifests/hello-pod.yaml` (see section 5) and apply it.
3. Use `kubectl explain` to find where container `env` variables are defined.
4. Run `kubectl logs hello -n handbook-lab` and `kubectl exec -it hello -n handbook-lab -- sh`.
5. Set default namespace to `handbook-lab` for your current context; verify with `kubectl config view --minify`.
6. Export the live Pod to YAML; identify fields added by the system (`resourceVersion`, `uid`, `status`).
7. Clean up: `kubectl delete pod hello -n handbook-lab`.

**Stretch:** Install `kubectx` and `kubens`; switch namespaces without editing config.

---

## 9. DevOps connections

- **GitOps:** Repos store manifests; `kubectl apply` becomes pipeline/operator responsibility.
- **Multi-env:** Same manifest + different namespace or overlay (Kustomize) = dev/staging/prod.
- **Break-glass:** `kubectl edit` is fine in incidents; drift should return to Git source of truth.

---

## Quick reference

| Task | Command |
|------|---------|
| API docs | `kubectl explain <field>` |
| All resources in NS | `kubectl get all -n handbook-lab` |
| Current context | `kubectl config current-context` |
| Apply manifest | `kubectl apply -f file.yaml` |
| Shell in pod | `kubectl exec -it POD -- sh` |

**Next:** [Day 3 — Pods](../day3/)
