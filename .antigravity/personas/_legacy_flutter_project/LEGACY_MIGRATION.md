# Legacy Persona Migration Strategy

## The Conflict
You currently have personas (e.g., `DEVOPS`, `STYLIST`) imported from a specific Flutter project. They contain hardcoded rules:
- **Project-Specific:** Flutter versioning (`1.7.1+40`), `build_runner` commands, specific file paths (`lib/design_system/palette.dart`).
- **Limitation:** If we keep these as the "Main" agents, your Dream Team will be **biased** towards that one old project. A generic `DEVOPS` agent shouldn't always assume it's working on a Flutter app (it might be React, Python, etc.).

## The Solution: "Archive & Upgrade"
To build a truly universal "Dream Team" while preserving your past logic:

1.  **Archive Legacy:** Move specific personas to `.antigravity/personas/_legacy_flutter_project/`.
2.  **Create Universal:** Generate the new 80+ personas in the main folder. These will be "Project Agnostic" (capable of *learning* rules, not hardcoded with them).
3.  **Inject Context:** When working on the Flutter app, we will simple tell the Master: "Use the rules from `_legacy_flutter_project`."

**Recommendation:**
Proceed with archiving the old files and creating the new, clean "Dream Team".
