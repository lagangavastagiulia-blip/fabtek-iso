---
name: shadcn
description: shadcn/ui component library best practices and patterns (formerly shadcn-ui). This skill should be used when writing, reviewing, or refactoring shadcn/ui components to ensure proper architecture, accessibility, and performance. Triggers on tasks involving Radix primitives, Tailwind styling, form validation with React Hook Form, data tables, theming, or component composition patterns.
---

# shadcn/ui Community Best Practices

Comprehensive best practices guide for shadcn/ui applications, maintained by the shadcn/ui community. Contains 58 rules across 10 categories, prioritized by impact to guide automated refactoring and code generation.

## Quick Reference

### 1. CLI & Project Setup (CRITICAL)
- `setup-components-json`: Configure components.json before adding components.
- `setup-cn-utility`: Create the cn utility before using components.

### 2. Component Architecture (CRITICAL)
- `arch-use-asChild-for-custom-triggers`: Use asChild prop for custom trigger elements.
- `arch-preserve-radix-primitive-structure`: Maintain Radix compound component hierarchy.

### 3. Accessibility (CRITICAL)
- `a11y-form-labels`: Ensure all form inputs have associated labels.
- `a11y-dialog-titles`: Dialog and Sheet content must have a Title for screen readers.

### 4. Styling Patterns
- `style-use-cn-for-merging`: Always use `cn()` to merge Tailwind classes, never template literals.
- `style-avoid-dynamic-classes`: Avoid dynamic class names that Tailwind cannot purge.
