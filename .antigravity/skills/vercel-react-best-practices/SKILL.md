---
name: vercel-react-best-practices
description: React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements.
---

# Vercel React Best Practices

Comprehensive performance optimization guide for React and Next.js applications, maintained by Vercel. Contains 57 rules across 8 categories, prioritized by impact to guide automated refactoring and code generation.

## When to Apply

Reference these guidelines when:
- Writing new React components or Next.js pages
- Optimizing existing data fetching logic
- Debugging performance bottlenecks or "jank"
- Reviewing PRs for architectural alignment
- Implementing complex UI patterns (modals, lists, forms)
- Configuring build-time optimizations

## Core Principles

### 1. Server Components First
- Default to Server Components for data fetching.
- Use `use client` only for interactivity (hooks, event listeners).

### 2. Image Optimization
- Always use `next/image` instead of `<img>`.
- Define `sizes` prop for responsive images.

### 3. Fonts
- Use `next/font` to optimize font loading and prevent layout shift (CLS).
