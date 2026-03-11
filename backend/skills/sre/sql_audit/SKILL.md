---
name: sql-audit
description: Use this skill for reviewing and optimizing SQL queries, analyzing database performance, and identifying security issues.
---

# SQL Audit Skill

## Overview

This skill specializes in analyzing SQL queries for performance, security, and best practices compliance.

## Capabilities

- **Performance Analysis**: Review query execution plans and performance
- **Index Recommendations**: Suggest proper indexing strategies
- **Security Review**: Check for SQL injection and other vulnerabilities
- **Optimization**: Rewrite inefficient queries
- **Best Practices**: Ensure proper SQL patterns

## Instructions

### 1. Query Analysis

#### Check for:
- SELECT * vs specific columns
- JOIN operations and efficiency
- WHERE clause optimization
- Subquery performance
- Index usage

### 2. Performance Review

#### Execution Plan Analysis:
- Table scans vs index seeks
- Sort operations
- Hash joins vs nested loops
- Missing indexes

### 3. Security Review

#### Check:
- Parameterized queries
- String concatenation risks
- Permission requirements
- Injection vulnerabilities
- Data access patterns

## Output Format

```markdown
# SQL Audit Report

## Query Assessment
- **Performance**: [Good/Fair/Poor]
- **Security**: [Secure/Needs Review]
- **Complexity**: [Low/Medium/High]

## Issues Found

### Performance Issues
- **Issue**: Description
- **Impact**: Explanation
- **Recommendation**: Fix

### Security Concerns
- **Issue**: Vulnerability
- **Severity**: [High/Medium/Low]
- **Recommendation**: Fix

## Optimizations
- **Indexes to Add**: [recommendations]
- **Query Rewrites**: [improved queries]
```

## When to Use

Use this skill when:
- User asks to "review SQL", "optimize query"
- User mentions database performance, slow queries
- User asks about SQL injection, security
- User requests query analysis
