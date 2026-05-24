# Day 25 — Systems Manager: Session Manager & Run Command

**Goal:** Access private EC2 without SSH keys, run remote commands, and patch with maintenance windows.

**Time:** 5–6 hours

**Services:** SSM, EC2, IAM

---

## 1. Instance prerequisites

Instance profile with:

- `AmazonSSMManagedInstanceCore`
- Network path to SSM endpoints (public subnet, NAT, or VPC interface endpoints from Day 9)

```bash
aws ssm describe-instance-information \
  --query 'InstanceInformationList[].[InstanceId,PingStatus,PlatformName]' --output table
```

---

## 2. Session Manager

```bash
# Install session-manager-plugin (macOS)
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

aws ssm start-session --target "$INSTANCE_ID"
# Non-interactive port forward
aws ssm start-session --target "$INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSession \
  --parameters portNumber=80,localPortNumber=8080
```

---

## 3. Run Command

```bash
aws ssm send-command \
  --document-name AWS-RunShellScript \
  --targets Key=instanceids,Values="$INSTANCE_ID" \
  --parameters commands=['uname -a','df -h'] \
  --comment "handbook audit"

CMD_ID=...
aws ssm list-command-invocations --command-id "$CMD_ID" --details
```

---

## 4. Parameter Store integration

```bash
aws ssm send-command \
  --document-name AWS-RunShellScript \
  --instance-ids "$INSTANCE_ID" \
  --parameters commands=["echo $(aws ssm get-parameter --name /handbook/app/log-level --query Parameter.Value --output text)"]
```

---

## 5. Patch Manager (overview)

```bash
aws ssm describe-available-patches --max-items 5
# Maintenance windows: register-targets, register-task, create-window
```

---

## 6. Lab — Day 25

1. Launch private subnet instance with SSM role.
2. `start-session` and run `sudo dnf update -y` manually.
3. `send-command` to collect disk and memory stats from 3 instances (or same instance thrice).
4. Document why Session Manager beats bastion SSH for compliance.

**Previous:** [Day 24](../day24/) · **Next:** [Day 26 — CI/CD](../day26/)
