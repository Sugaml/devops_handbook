# Day 24 — CloudFormation: Infrastructure as Code

**Goal:** Deploy, update, and delete stacks from YAML templates using the CLI.

**Time:** 5–6 hours

**Services:** CloudFormation

---

## 1. Minimal template

`vpc-handbook.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Handbook VPC snippet
Parameters:
  VpcCidr:
    Type: String
    Default: 10.1.0.0/16
Resources:
  HandbookVpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: handbook-cfn-vpc
        - Key: Project
          Value: devops-handbook
Outputs:
  VpcId:
    Value: !Ref HandbookVpc
    Export:
      Name: HandbookVpcId
```

---

## 2. Stack operations

```bash
aws cloudformation validate-template --template-body file://vpc-handbook.yaml

aws cloudformation create-stack \
  --stack-name handbook-vpc \
  --template-body file://vpc-handbook.yaml \
  --capabilities CAPABILITY_IAM \
  --tags Key=Project,Value=devops-handbook

aws cloudformation wait stack-create-complete --stack-name handbook-vpc
aws cloudformation describe-stacks --stack-name handbook-vpc \
  --query 'Stacks[0].StackStatus'

aws cloudformation describe-stack-events --stack-name handbook-vpc --max-items 10
```

---

## 3. Update and drift

```bash
aws cloudformation update-stack \
  --stack-name handbook-vpc \
  --template-body file://vpc-handbook.yaml \
  --parameters ParameterKey=VpcCidr,ParameterValue=10.1.0.0/16

aws cloudformation detect-stack-drift --stack-name handbook-vpc
aws cloudformation describe-stack-resource-drifts --stack-name handbook-vpc
```

---

## 4. Delete and exports

```bash
aws cloudformation delete-stack --stack-name handbook-vpc
aws cloudformation wait stack-delete-complete --stack-name handbook-vpc

aws cloudformation list-exports --query 'Exports[?Name==`HandbookVpcId`]'
```

**DevOps note:** Teams often use **Terraform** or **CDK**—CloudFormation remains the AWS-native contract and underpins many tools.

---

## 5. Lab — Day 24

1. Deploy VPC stack; capture `VpcId` output.
2. Add subnet resources in template; `update-stack`.
3. Intentionally change resource in console; run drift detection.
4. Delete stack cleanly.

**Previous:** [Day 23](../day23/) · **Next:** [Day 25 — Systems Manager](../day25/)
