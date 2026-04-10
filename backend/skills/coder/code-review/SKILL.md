---
name: code-review
description: Use this skill for code review tasks to analyze code quality, identify potential issues, and provide improvement suggestions.
---

# Code Review Skill

## Overview

This skill specializes in comprehensive code review and quality assessment.

## Capabilities

- **Code Structure Analysis**: Examine code organization, design patterns, and architectural decisions
- **Bug Detection**: Identify potential bugs, edge cases, and error handling issues
- **Performance Optimization**: Suggest performance improvements and optimization opportunities
- **Security Review**: Highlight security vulnerabilities and best practices violations
- **Best Practices**: Ensure adherence to language-specific and industry best practices

## Instructions

### 1. Understand the Context
- Identify the programming language and framework
- Understand the purpose and requirements of the code
- Consider the project context and constraints

### 2. Analyze the Code
Review the following aspects:
- **Correctness**: Does the code do what it's supposed to do?
- **Readability**: Is the code clear and maintainable?
- **Performance**: Are there any performance bottlenecks?
- **Security**: Are there any security vulnerabilities?
- **Error Handling**: Are errors properly handled?

### 3. Provide Feedback

Structure your review as follows:

#### Overall Assessment
- Brief summary of code quality (Excellent/Good/Fair/Poor)
- Main strengths
- Primary concerns

#### Detailed Findings
For each issue found:
- **Line Number**: Reference specific lines
- **Severity**: (Critical/Major/Minor)
- **Issue**: Clear description of the problem
- **Suggestion**: Specific improvement recommendation

#### Best Practices Recommendations
List any additional best practices that should be followed.

## Output Format

```markdown
# Code Review Report

## Overall Assessment
**Rating**: [Good/Fair/Poor]
**Summary**: [Brief evaluation]

## Strengths
- [List what's done well]

## Issues Found

### [Severity] Issue Title
- **Location**: Line X-Y
- **Description**: [What's the problem]
- **Suggestion**: [How to fix it]

## Best Practices Recommendations
- [Additional recommendations]
```

## When to Use

Use this skill when:
- User asks to review code
- User requests code quality assessment
- User mentions "code review", "check my code", or similar phrases
- User shares code snippets asking for feedback
