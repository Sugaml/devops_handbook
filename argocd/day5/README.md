# Day 5 — AppProjects, RBAC, Repositories & Credentials

**Goal:** Enforce multi-tenancy with AppProjects, configure Argo CD RBAC, connect private Git repos securely, and understand SSO integration patterns.

**Time:** 5–6 hours

---

## 1. Why AppProjects?

Without projects, any Application in `default` can:

- Deploy to any namespace
- Pull from any Git URL
- Install cluster-scoped resources

**AppProject** defines boundaries:

| Constraint | Example |
|------------|---------|
| `sourceRepos` | Only `https://github.com/myorg/*` |
| `destinations` | Only `handbook-lab` on in-cluster |
| `clusterResourceWhitelist` | Deny ClusterRole unless platform team |
| `namespaceResourceBlacklist` | Block Secret creation in prod project |
| `roles` | Project-scoped RBAC for teams |

```
┌─────────────────────────────────────────┐
│  AppProject: platform                   │
│  repos: gitops-platform/*               │
│  dest:  */platform-*                    │
│  apps:  cluster-addons, monitoring      │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  AppProject: team-alpha                 │
│  repos: gitops-team-alpha/*             │
│  dest:  team-alpha-dev, team-alpha-prod │
│  apps:  microservices only              │
└─────────────────────────────────────────┘
```

---

## 2. Create an AppProject

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: handbook
  namespace: argocd
spec:
  description: DevOps handbook lab project
  sourceRepos:
    - https://github.com/argoproj/argocd-example-apps.git
    - https://github.com/YOUR_ORG/gitops-handbook.git
    - https://charts.bitnami.com/bitnami
  destinations:
    - namespace: handbook-lab
      server: https://kubernetes.default.svc
    - namespace: handbook-staging
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ""
      kind: Namespace
  namespaceResourceBlacklist:
    - group: ""
      kind: ResourceQuota
  orphanedResources:
    warn: true
  roles:
    - name: developer
      description: Sync and read apps
      policies:
        - p, proj:handbook:developer, applications, get, handbook/*, allow
        - p, proj:handbook:developer, applications, sync, handbook/*, allow
      groups:
        - handbook-developers
```

Apply and assign Application to project:

```yaml
spec:
  project: handbook   # not default
```

```bash
kubectl apply -f manifests/appproject-handbook.yaml
argocd proj create handbook --description "Handbook lab"   # or declarative only
argocd app set guestbook --project handbook
```

---

## 3. Argo CD RBAC model

RBAC uses Casbin policies in ConfigMap `argocd-rbac-cm`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    p, role:org-admin, applications, *, */*, allow
    p, role:org-admin, clusters, *, *, allow
    p, role:org-admin, repositories, *, *, allow
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    p, role:developer, applications, update, */*, deny
    g, handbook-developers, role:developer
    g, platform-admins, role:org-admin
  scopes: '[groups, email]'
```

Policy format:

```
p, <role>, <resource>, <action>, <object>, <allow|deny>
g, <user|group>, <role>
```

| Resource | Actions |
|----------|---------|
| `applications` | get, create, update, delete, sync, override, action |
| `repositories` | get, create, update, delete |
| `clusters` | get, create, update, delete |
| `projects` | get, create, update, delete |
| `logs` | get |

Test policy:

```bash
argocd account can sync guestbook --auth-token "$TOKEN"
argocd proj role list handbook
```

**Production:** Default deny; grant least privilege per team. Never leave `policy.default: role:admin`.

---

## 4. Repository credentials

### HTTPS — personal access token

```bash
argocd repo add https://github.com/YOUR_ORG/gitops-handbook.git \
  --username git \
  --password "$GITHUB_PAT"

kubectl create secret generic repo-gitops \
  -n argocd \
  --from-literal=type=git \
  --from-literal=url=https://github.com/YOUR_ORG/gitops-handbook.git \
  --from-literal=password="$GITHUB_PAT" \
  --from-literal=username=git \
  --label argocd.argoproj.io/secret-type=repository
```

### SSH — deploy key

```bash
argocd repo add git@github.com:YOUR_ORG/gitops-handbook.git \
  --ssh-private-key-path ~/.ssh/gitops_deploy_key

kubectl create secret generic repo-gitops-ssh \
  -n argocd \
  --from-file=sshPrivateKey=~/.ssh/gitops_deploy_key \
  --from-literal=url=git@github.com:YOUR_ORG/gitops-handbook.git \
  --label argocd.argoproj.io/secret-type=repository
```

Mount known hosts for SSH:

```yaml
# argocd-cm
data:
  ssh.knownhosts: |
    github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...
```

### Credential templates (many repos, one credential)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: github-org-creds
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repo-creds
stringData:
  url: https://github.com/YOUR_ORG
  password: "$GITHUB_PAT"
  username: git
```

All repos under `https://github.com/YOUR_ORG/*` inherit credentials.

Verify connection:

```bash
argocd repo list
argocd repo get https://github.com/YOUR_ORG/gitops-handbook.git
```

---

## 5. SSO with Dex (overview)

Argo CD ships with **Dex** for OIDC/LDAP/SAML:

```yaml
# argocd-cm excerpt
data:
  url: https://argocd.example.com
  oidc.config: |
    name: GitHub
    issuer: https://token.actions.githubusercontent.com
    clientID: $oidc.github.clientId
    clientSecret: $oidc.github.clientSecret
    requestedScopes: ["openid", "profile", "email"]
```

```yaml
# argocd-rbac-cm — map IdP groups
g, myorg:platform-team, role:org-admin
```

```bash
# Disable local admin in production
kubectl patch configmap argocd-cm -n argocd --type merge \
  -p '{"data":{"admin.enabled":"false"}}'
```

**Lab note:** Full SSO requires DNS, TLS, and IdP app registration — use port-forward + local admin for handbook labs; document prod steps.

---

## 6. Secrets in Git — never plain text

| Pattern | Tool |
|---------|------|
| Encrypted in Git | Mozilla SOPS, age, PGP |
| Reference only | External Secrets Operator, Sealed Secrets |
| Vault integration | Argo CD Vault Plugin (AVP) |

Argo CD reads decrypted manifests at sync time — encryption keys live in cluster or KMS, not in Git.

Example ExternalSecret flow (Day 7):

```
Vault/AWS SM → ExternalSecret → K8s Secret → Pod
Git holds ExternalSecret YAML only
```

---

## 7. Project-level sync windows and signatures

Restrict prod deploys:

```yaml
spec:
  syncWindows:
    - kind: deny
      schedule: "0 0 * * 6"
      duration: 48h
      manualSync: false
  signatureKeys:
    - keyID: ABCD1234
```

Signed commits (optional, GPG) add supply-chain assurance for regulated environments.

---

## 8. Orphaned resource monitoring

```yaml
spec:
  orphanedResources:
    warn: true
    ignore:
      - group: ""
        kind: ConfigMap
        name: kube-root-ca.crt
```

Orphaned = exists in cluster, not in Git — often manual debugging leftovers.

```bash
argocd app resources guestbook --orphaned
```

---

## 9. Lab — Day 5

1. Apply `manifests/appproject-handbook.yaml`.
2. Move `guestbook` Application to project `handbook`; verify deploy still works.
3. Attempt to deploy to a **disallowed** namespace — confirm Argo CD rejects.
4. Add a private repo credential via Secret (or PAT to your fork); `argocd repo list` shows Successful.
5. Edit `argocd-rbac-cm` — create `role:developer` that can sync but not delete; test with a non-admin account.
6. Enable orphaned resource warnings; create a stray ConfigMap manually; observe warning in UI.
7. **Stretch:** Document Dex OIDC config for your org's IdP (GitHub/Google/Okta).

---

## 10. DevOps connections

- **Blast radius:** AppProjects are how platform teams say "team A cannot touch team B namespaces."
- **Credential rotation:** Use repo-creds templates; rotate PATs without updating every Application.
- **Compliance:** RBAC audit logs + Git history = who deployed what, when, from which commit.

---

## Quick reference

| Task | Command |
|------|---------|
| Create project | `kubectl apply -f appproject.yaml` |
| List projects | `argocd proj list` |
| Add repo | `argocd repo add URL --username U --password P` |
| Project roles | `argocd proj role list PROJECT` |
| RBAC test | `argocd account can sync APP` |

**Previous:** [Day 4](../day4/) · **Next:** [Day 6 — ApplicationSets](../day6/)
