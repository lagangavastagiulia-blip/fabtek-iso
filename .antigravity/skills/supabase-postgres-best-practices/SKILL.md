---
name: supabase-postgres-best-practices
description: Best practices for designing and optimizing PostgreSQL databases within the Supabase ecosystem. Covers schema design, indexing strategies, RLS security, and query performance. Use this skill when creating or modifying database schemas, writing complex SQL queries, or optimizing database performance in Supabase projects.
---

# Supabase Postgres Best Practices

A structured guide for creating and maintaining high-performance PostgreSQL databases on Supabase.

## Rule Categories

1. Schema Design (CRITICAL)
   - Use `uuid` (v4) for primary keys.
   - Use `timestamptz` for all timestamps.
   - Use correct data types (e.g., `text` over `varchar`).

2. Indexing (CRITICAL)
   - Index all foreign keys.
   - Use GIN indexes for JSONB columns.
   - Check usage stats before adding indexes.

3. Row-Level Security (HIGH)
   - Enable RLS on all tables (`ALTER TABLE table ENABLE ROW LEVEL SECURITY;`).
   - Create policies for `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
   - Use `auth.uid()` for user-based access.

4. Query Optimization (HIGH)
   - Avoid `SELECT *`.
   - Use `.select()` filters in JS client instead of client-side filtering.
