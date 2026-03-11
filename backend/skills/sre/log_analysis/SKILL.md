---
name: log-analysis
description: Use this skill for analyzing logs, identifying errors, finding patterns, and troubleshooting system issues.
---

# Log Analysis Skill

## Overview

This skill specializes in analyzing system and application logs to identify issues, patterns, and root causes of problems.

## Capabilities

- **Error Identification**: Spot critical errors and failures
- **Pattern Recognition**: Find recurring issues and trends
- **Root Cause Analysis**: Trace problems to their source
- **Performance Issues**: Identify slow requests and bottlenecks
- **Security Detection**: Find potential security threats

## Instructions

### 1. Understand the Log Context
- **Service**: What application/service generated the logs?
- **Time Range**: What period are we analyzing?
- **Symptoms**: What problems are being reported?

### 2. Analysis Process

#### Step 1: Categorize Issues
- **Critical** (🔴): Service down, data loss, security breach
- **High** (🟠): Performance degradation, partial outage
- **Medium** (🟡): Intermittent issues, warnings
- **Low** (🟢): Informational, minor issues

#### Step 2: Identify Patterns
- Error codes: 4xx, 5xx
- Repeated failures
- Timing correlations
- Error rates and trends

#### Step 3: Extract Key Metrics
- Total requests/operations
- Error rate percentage
- Response times
- Throughput

### 3. Provide Findings

```markdown
# Log Analysis Report

## Summary
- **Time Range**: [start to end]
- **Total Entries**: X log entries
- **Error Rate**: Y%

## Critical Issues
### [Severity] Issue Title
- **Pattern**: [Error pattern]
- **Occurrences**: X times
- **Impact**: [What's affected]
- **Recommendation**: [Fix steps]

## Performance Issues
- [Performance bottlenecks found]

## Recommendations
1. [Immediate actions]
2. [Long-term fixes]
```

## When to Use

Use this skill when:
- User asks to "analyze logs", "check for errors"
- User mentions log files, error messages
- User reports system issues
- User asks about troubleshooting
