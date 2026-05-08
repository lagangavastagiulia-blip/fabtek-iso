```md
# Ultimate Paranoia-Level Global Audit Checklist  
Full-stack audit across Authentication, Map, Profile, Booking, Help Tickets, and Core Infrastructure.  
30 checks total, numbered, grouped into 5 priority slots.

---

# 🎰 SLOT 1: GLOBAL SECURITY & DATA INTEGRITY  
**Priority:** Critical  

**1. Global Secrets & Keys Scan**  
**Agent:** SENTINEL  
**Prompt:** ACT AS SENTINEL. Perform a recursive scan of the entire `lib/` directory and `pubspec.yaml`. Search for regex signatures of API Keys, Bearer Tokens, AWS Secrets, Google Maps Keys. Confirm no hardcoded secrets in Dart. All keys must come from `flutter_dotenv` or compile-time vars.

**2. Secure Storage Enforcement (PII & Tokens)**  
**Agent:** CYBER OFFICER  
**Prompt:** ACT AS CYBER OFFICER. Audit `lib/core/auth` and `lib/features/auth`. Confirm `SharedPreferences` is never used for tokens or PII. Confirm `flutter_secure_storage` is the only credential storage mechanism.

**3. Production Logging Hygiene**  
**Agent:** SENTINEL  
**Prompt:** ACT AS SENTINEL. Grep the entire `lib/` directory for `print(`. List all files using prints. Require removal or replacement with a Logger.

**4. Global Network Security (TLS/HTTPS)**  
**Agent:** CYBER OFFICER  
**Prompt:** ACT AS CYBER OFFICER. Audit `lib/core/api`. Confirm base URL uses `https://`. Check `AndroidManifest.xml` to ensure `android:usesCleartextTraffic="false"`.

**5. Input Sanitization (XSS/Injection)**  
**Agent:** CYBER OFFICER  
**Prompt:** ACT AS CYBER OFFICER. Review all forms (Help Ticket, Booking, Profile Edit). Confirm controllers have length limits and backend submission escapes input.

**6. User Verification & Expiry Logic**  
**Agent:** CYBER OFFICER  
**Prompt:** ACT AS CYBER OFFICER. Audit membership/verification logic. Confirm `expiry_date` is enforced every app launch. Expired “Cabin Crew” access must be blocked instantly.

---

# 🎰 SLOT 2: ARCHITECTURE & STABILITY  
**Priority:** High  

**7. Domain Layer Isolation (Clean Architecture)**  
**Agent:** ARCHITECT  
**Prompt:** ACT AS ARCHITECT. Scan `lib/features/*/domain`. Domain must not import `flutter/material.dart` or `flutter_bloc`. Pure Dart only.

**8. Global Error Handling Boundary**  
**Agent:** ARCHITECT  
**Prompt:** ACT AS ARCHITECT. Check `main.dart` and root App. Ensure `FlutterError.onError` override or error boundary exists.

**9. GPS/Location Fallback Logic**  
**Agent:** TEST RIG  
**Prompt:** ACT AS TEST RIG. Verify error handling for permission denied, service disabled, timeout, imprecise location.

**10. Dependency Injection Graph**  
**Agent:** ARCHITECT  
**Prompt:** ACT AS ARCHITECT. Review `lib/injected_container.dart`. UseCases must be `LazySingleton`. Bloc/Cubit must be `Factory`. Check for circular deps.

**11. Memory Leak Prevention (Streams)**  
**Agent:** PERFORMANCE ANALYST  
**Prompt:** ACT AS PERFORMANCE ANALYST. Search for `.listen(`. Confirm each subscription is stored and canceled in `dispose()` or `close()`.

**12. Null Safety Compliance**  
**Agent:** DEVOPS  
**Prompt:** ACT AS DEVOPS. Run `dart analyze`. Flag implicit dynamic types in business logic. Flag unsafe `!` null assertions.

---

# 🎰 SLOT 3: PERFORMANCE & COST EFFICIENCY  
**Priority:** Medium  

**13. Global Image Optimization**  
**Agent:** PERFORMANCE ANALYST  
**Prompt:** ACT AS PERFORMANCE ANALYST. Audit `Image.network` usage. Enforce `CachedNetworkImage`. Flag PNG/JPG >500KB in `assets/`.

**14. API Cost Optimization (Batching/Caching)**  
**Agent:** COST OPTIMIZER  
**Prompt:** ACT AS COST OPTIMIZER. Review repository caching (Hive/memory). Ensure static data (venues, events) isn’t refetched on tab switch.

**15. Build Method Purity**  
**Agent:** PERFORMANCE ANALYST  
**Prompt:** ACT AS PERFORMANCE ANALYST. Ensure no API calls or heavy logic inside `build()`. Move to `initState()` or BLoC.

**16. Unnecessary Repaints**  
**Agent:** PERFORMANCE ANALYST  
**Prompt:** ACT AS PERFORMANCE ANALYST. Identify broad `setState()` usage. Propose splitting large widgets and using `const` widgets.

**17. List View Performance**  
**Agent:** PERFORMANCE ANALYST  
**Prompt:** ACT AS PERFORMANCE ANALYST. Confirm all lists use `ListView.builder`. Avoid `shrinkWrap: true` inside scrollable parents.

**18. Subscription Cleanup (Cost)**  
**Agent:** COST OPTIMIZER  
**Prompt:** ACT AS COST OPTIMIZER. Confirm Firebase/WebSocket listeners close when user leaves screen.

---

# 🎰 SLOT 4: STORE COMPLIANCE & NATIVE  
**Priority:** Standard  

**19. iOS Privacy Manifest Compliance**  
**Agent:** PLATFORM EXPERT  
**Prompt:** ACT AS PLATFORM EXPERT. Check for `PrivacyInfo.xcprivacy`. Ensure all system APIs used (UserDefaults, FileTimestamp, BootTime) have matching disclosures.

**20. Permission Minimization**  
**Agent:** PLATFORM EXPERT  
**Prompt:** ACT AS PLATFORM EXPERT. Audit Android/iOS permission lists. Remove unused ones. Ensure user-facing permission descriptions are explicit.

**21. App Icon & Launch Screen**  
**Agent:** STYLIST  
**Prompt:** ACT AS STYLIST. Verify JetLag branding on launch screen and correct icon resolution for all densities.

**22. Code Obfuscation Prep**  
**Agent:** SENTINEL  
**Prompt:** ACT AS SENTINEL. Ensure build scripts use `--obfuscate` and `--split-debug-info`.

**23. Dependency Version Locking**  
**Agent:** LIBRARIAN  
**Prompt:** ACT AS LIBRARIAN. Scan `pubspec.yaml` for `^` caret versions. Replace with pinned explicit versions.

---

# 🎰 SLOT 5: UX, LOCALIZATION & POLISH  
**Priority:** Low  

**24. Hardcoded String Embargo**  
**Agent:** LINGUIST  
**Prompt:** ACT AS LINGUIST. Search for user-visible string literals. Enforce `AppLocalizations` everywhere.

**25. RTL Readiness**  
**Agent:** LINGUIST  
**Prompt:** ACT AS LINGUIST. Check for `EdgeInsetsDirectional` instead of `EdgeInsets` in UI.

**26. Semantic Versioning Update**  
**Agent:** SCRIBE  
**Prompt:** ACT AS SCRIBE. Ensure `pubspec.yaml` version bump. Update `CHANGELOG.md` with new modules.

**27. Empty States Global Audit**  
**Agent:** STYLIST  
**Prompt:** ACT AS STYLIST. Ensure every list has a branded empty state, not a blank page.

**28. Tap Target Accessibility**  
**Agent:** STYLIST  
**Prompt:** ACT AS STYLIST. Random check for minimum 44x44px tap areas. Check contrast on black background.

**29. Keyboard Handling**  
**Agent:** STYLIST  
**Prompt:** ACT AS STYLIST. Audit `HelpTicketView` and `ProfileEdit` for keyboard dismiss and scroll-into-view behavior.

**30. Final Linter Zero-Tolerance**  
**Agent:** DEVOPS  
**Prompt:** ACT AS DEVOPS. Run `flutter analyze`. Require zero warnings, zero infos, zero errors.

---
```
