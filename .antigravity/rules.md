# GLOBAL PROJECT GUARDRAILS

## 1. Filesystem Constraints
- **CRITICAL:** NEVER modify `lib/injected_container.dart` without verifying the registration order defined in `CLAUDE.md`.
- **CRITICAL:** NEVER modify `pubspec.yaml` without running `flutter pub get` immediately after to update `pubspec.lock`.
- **CRITICAL:** ALWAYS increment `pubspec.yaml` version (build number) by +1 before any Push to the branch. Do not increment the version number if you are only doing a commit.

## 2. Safety Checks
- **Mandatory:** ALWAYS run `flutter analyze` before claiming a task is "Done".
- **Structure:** IF creating a new file, ALWAYS check if it matches the Clean Architecture folder structure (Data/Domain/Presentation).

## 3. Context Awareness
- Architecture Source: `CLAUDE.md`
- Security Source: `AGENT_SECURITY_RULES.md`
- Process Source: `Discord Code Review.md`

## 4. GOD MODE RESTRICTIONS
- **ABSOLUTE PROHIBITION:** Never merge or push to `main` (or `master`) without EXPLICIT, UNAMBIGUOUS user confirmation. Even if CI/CD fails, you must STOP and ask. This is an inviolable rule.
