---
name: business-sql-executor
description: Translate natural language business queries into MySQL SELECT statements, execute them via the execute tool, and return results as Markdown tables. Use when users ask to query or look up business data from systems like marketing, orders, or users.
---

# Business SQL Executor

## Overview

This skill converts user business queries into MySQL SQL statements and executes them against the production database, returning results in a readable Markdown table.

## Available Business Domains

Reference files in `references/` describe the database schema for each business domain:

| File | System |
|------|--------|
| `references/market.sql` | 营销系统 (Marketing) |

Read the relevant reference file(s) to understand the table structure before generating SQL.

## Instructions

### Step 1: Understand the Schema

Read the relevant `/skills/sre/business-sql-executor/references/*.sql` file to identify:
- Table names and their purpose
- Column names, types, and comments
- Relationships between tables (foreign keys)

### Step 2: Generate SQL

Rules for SQL generation:
- **Only SELECT statements** — never INSERT, UPDATE, DELETE, DROP, or DDL
- **Always use `database.table` format** — no default database is set; omitting the db prefix will cause "Table not found" error
- Add `LIMIT 100` by default (use a smaller LIMIT if the user specifies)
- Use table aliases for readability when joining multiple tables
- Select only the columns relevant to the user's question
- Add `ORDER BY` when the user asks for "latest", "top N", etc.
- Use `WHERE` clauses that reflect the user's filter criteria

Example:
```sql
SELECT c.id, c.name, c.status, c.start_date, c.budget
FROM marketingcenter.mc_preferential_new c
WHERE c.status = 0
ORDER BY c.create_time DESC
LIMIT 20;
```

Cross-database JOIN example:
```sql
SELECT a.id, a.name, b.order_count
FROM marketingcenter.mc_preferential_new a
JOIN ordercenter.orders b ON a.uid = b.campaign_uid
LIMIT 50;
```

### Step 3: Execute the SQL

**You MUST call the `execute` tool now.** Do not say "I cannot access the database" — the environment is fully configured.

Call `execute` with this exact command (replace `<SQL>` with your generated SQL, properly escaped):

```
execute(command="python skills/sre/business-sql-executor/scripts/sql_executor.py '<SQL>'")
```

Real example:
```
execute(command="python skills/sre/business-sql-executor/scripts/sql_executor.py 'SELECT COUNT(*) AS total FROM marketingcenter.mc_preferential_new WHERE del=0'")
```

The script outputs a JSON string:
```json
{"columns": ["total"], "rows": [[10080]], "count": 1}
```

If the output contains `"error"`, fix the SQL and call `execute` again.

### Step 4: Format as Markdown Table

Convert the JSON result into a Markdown table:

1. Use `columns` as the header row
2. Use each array in `rows` as a data row
3. Add a summary line: `共 N 条记录`

**Example output:**

```markdown
| id | name | status |
|----|------|--------|
| 1 | Summer Sale | active |

共 1 条记录
```

If the result has 0 rows, respond: "未查询到符合条件的数据。"

## Output Format

```markdown
**SQL:**
```sql
SELECT ...
```

**结果：**

| col1 | col2 | col3 |
|------|------|------|
| val1 | val2 | val3 |

共 N 条记录
```

## When to Use

Use this skill when the user:
- Asks to "查询" (query) business data
- Wants to know "有哪些" (list) records in a business system
- Asks about marketing campaigns, orders, customers, users, or other business entities
- Requests data like "最近的活动", "本月的订单", "活跃用户数" etc.
