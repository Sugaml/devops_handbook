# Day 4 — Helm, Kustomize & Multi-Source Applications

**Goal:** Deploy Helm charts and Kustomize overlays through Argo CD, override values per environment, and combine multiple sources in one Application.

**Time:** 5–6 hours

---

## 1. Native tooling support

Argo CD generates manifests **without** running `helm install` or `kubectl apply -k` on your laptop:

| Tool | Argo CD behavior |
|------|------------------|
| **Plain YAML / directory** | Recurse manifests |
| **Kustomize** | Detects `kustomization.yaml`, runs `kustomize build` |
| **Helm** | `helm template` with values from Git or parameters |
| **Helm OCI** | Pull chart from `oci://` registry |
| **Jsonnet / Plugins** | Config Management Plugins (CMP) on repo-server |

Repo server does the rendering; application controller applies the output.

---

## 2. Helm application

### Basic Helm source

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-helm
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: nginx
    targetRevision: 15.4.4          # pin chart version
    helm:
      releaseName: handbook-nginx
      valueFiles:
        - values.yaml
      values: |
        replicaCount: 2
        service:
          type: ClusterIP
  destination:
    server: https://kubernetes.default.svc
    namespace: handbook-lab
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

CLI equivalent:

```bash
argocd app create nginx-helm \
  --repo https://charts.bitnami.com/bitnami \
  --helm-chart nginx \
  --revision 15.4.4 \
  --dest-namespace handbook-lab \
  --helm-set replicaCount=2 \
  --sync-option CreateNamespace=true
```

### Values from Git (recommended pattern)

Store values in your GitOps repo, not only inline:

```
apps/helm-nginx/
├── Chart.yaml          # optional wrapper chart
├── values.yaml         # defaults
├── values-dev.yaml
└── values-prod.yaml
```

```yaml
source:
  repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
  path: apps/helm-nginx
  targetRevision: main
  helm:
    valueFiles:
      - values-dev.yaml
```

For **remote chart + local values**, use a **wrapper chart** or **multi-source** (below).

---

## 3. Kustomize application

```yaml
source:
  repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
  targetRevision: main
  path: apps/guestbook/overlays/dev
```

Kustomize overlay structure in this handbook:

```
labs/kustomize-guestbook/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    └── dev/
        ├── kustomization.yaml
        └── patch-replicas.yaml
```

```yaml
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - path: patch-replicas.yaml
namePrefix: dev-
commonLabels:
  env: dev
```

Argo CD 2.6+ supports **kustomize build options**:

```yaml
source:
  path: apps/guestbook/overlays/dev
  kustomize:
    images:
      - gcr.io/heptio-images/ks-guestbook-demo:0.2
    commonLabels:
      team: platform
```

---

## 4. Multi-source applications (Argo CD 2.6+)

Combine external chart with values from your repo:

```yaml
spec:
  sources:
    - repoURL: https://charts.bitnami.com/bitnami
      chart: nginx
      targetRevision: 15.4.4
      helm:
        releaseName: handbook-nginx
        valueFiles:
          - $values/apps/helm-nginx/values-dev.yaml
    - repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
      targetRevision: main
      ref: values
      path: apps/helm-nginx    # not deployed; supplies value files
  destination:
    server: https://kubernetes.default.svc
    namespace: handbook-lab
```

The `ref: values` source is referenced as `$values/...` in valueFiles.

**Use case:** Platform team owns values; app team consumes pinned upstream charts.

---

## 5. Helm parameters and file parameters

Override without editing values files:

```yaml
helm:
  parameters:
    - name: replicaCount
      value: "3"
    - name: service.type
      value: ClusterIP
  fileParameters:
    - name: config
      path: files/config.json
```

CLI:

```bash
argocd app set nginx-helm --helm-set replicaCount=3
argocd app sync nginx-helm
```

**Production:** Prefer values files in Git over CLI `--helm-set` — reproducible and reviewable.

---

## 6. OCI Helm registries

```yaml
source:
  repoURL: oci://registry.example.com/charts
  chart: my-app
  targetRevision: 2.1.0
  helm:
    releaseName: my-app
```

Add OCI repo:

```bash
argocd repo add oci://registry.example.com/charts \
  --type helm \
  --enable-oci \
  --username "$USER" \
  --password "$TOKEN"
```

Same pattern works for **ECR**, **ACR**, **GCR** artifact registries.

---

## 7. Compare options for Helm

Helm adds labels and annotations Argo CD tracks. Common issues:

| Issue | Fix |
|-------|-----|
| Secret data drift | Use External Secrets; ignore data field |
| Random chart hooks | `ignoreDifferences` on hook Jobs |
| HPA owns replicas | Ignore `/spec/replicas` on Deployment |

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    jqPathExpressions:
      - .spec.template.metadata.annotations."checksum/config"
```

---

## 8. Config Management Plugins (overview)

When Helm/Kustomize is not enough (e.g. SOPS-encrypted YAML, custom templating):

1. Build a container with your tool.
2. Register CMP in `argocd-repo-server` sidecar.
3. Application references plugin name in `source.plugin`.

```yaml
source:
  repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
  path: apps/encrypted
  plugin:
  name: sops-kustomize
  env:
    - name: SOPS_AGE_KEY_FILE
      value: /etc/sops/age.key
```

Day 7 covers SOPS + External Secrets in production; CMP is the escape hatch.

---

## 9. Lab — Day 4

1. Deploy Bitnami NGINX via Helm Application (`manifests/application-helm-nginx.yaml`); pin chart version.
2. Upgrade by changing `replicaCount` in inline values; sync and verify.
3. Apply Kustomize overlay app from `labs/kustomize-guestbook/overlays/dev`; confirm namePrefix and patches.
4. Convert to multi-source: chart from Bitnami + values file from a Git repo you control.
5. Run `argocd app manifests nginx-helm` — inspect rendered YAML.
6. **Stretch:** Add an OCI chart from a public registry (if available) or document ECR login steps for your cloud.

---

## 10. DevOps connections

- **Chart vs values split:** Vendors publish charts; your org owns `values-*.yaml` per environment — standard enterprise pattern.
- **Kustomize overlays:** Base from upstream or internal template; overlays for dev/staging/prod — no chart fork required.
- **Version pinning:** Always pin `targetRevision` on charts; floating tags cause surprise upgrades.

---

## Quick reference

| Task | Command |
|------|---------|
| Helm app create | `argocd app create APP --repo URL --helm-chart CHART --revision VER` |
| Helm set | `argocd app set APP --helm-set key=val` |
| View rendered | `argocd app manifests APP` |
| Kustomize images | Set in Application `source.kustomize.images` |

**Previous:** [Day 3](../day3/) · **Next:** [Day 5 — AppProjects & RBAC](../day5/)
