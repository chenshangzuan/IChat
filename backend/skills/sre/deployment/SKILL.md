---
name: deployment
description: Use this skill for planning and executing deployments, CI/CD pipelines, and infrastructure changes.
---

# Deployment Skill

## Overview

This skill specializes in planning safe deployments, managing CI/CD pipelines, and executing infrastructure changes with minimal risk.

## Capabilities

- **Deployment Planning**: Create safe deployment strategies
- **Environment Management**: Configure dev/staging/production environments
- **Health Checks**: Define and verify system health
- **Rollback Planning**: Prepare rollback scenarios
- **Risk Assessment**: Identify and mitigate deployment risks

## Instructions

### 1. Pre-Deployment Phase

#### Checklist:
- [ ] Code reviewed and tested
- [ ] Tests passing (unit, integration, e2e)
- [ ] Environment variables configured
- [ ] Database migrations planned
- [ ] Backup completed
- [ ] Rollback plan ready
- [ ] Monitoring/alerting configured
- [ ] Team notified

### 2. Deployment Execution

#### Deployment Steps:
1. **Pre-deployment verification**
   - Check current system state
   - Verify environment readiness

2. **Execute deployment**
   - Follow deployment steps in order
   - Monitor each step
   - Verify after each step

3. **Post-deployment verification**
   - Health checks
   - Smoke tests
   - Monitor metrics
   - Check for errors

### 3. Rollback Plan

Define rollback triggers:
- Error rate > X%
- Response time > Y seconds
- Critical health check fails

Rollback steps:
1. [Step 1]
2. [Step 2]
3. [Verification]

## Output Format

```markdown
# Deployment Plan

## Pre-Deployment Checklist
- [ ] Item 1
- [ ] Item 2

## Deployment Steps
1. **Step name**: Description
   - Command: `command if applicable`
   - Verification: How to verify success

## Rollback Plan
- **Triggers**: [Conditions for rollback]
- **Steps**: [Rollback procedure]

## Post-Deployment Verification
- [ ] Health check 1
- [ ] Health check 2
```

## When to Use

Use this skill when:
- User asks to "deploy", "release", "ship to production"
- User mentions CI/CD, deployment pipeline
- User asks about deployment strategies
- User wants to update infrastructure
