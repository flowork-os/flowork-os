# 🛠️ Code Engineering & Quality Mandates
- **Type Safety & Linters:** Strict types; never suppress warnings or use dirty casts/hacks. Use explicit guards and idiomatic language features.
- **Testing Invariant:** Add or update unit tests for every change. For bug fixes, author an empirical reproduction test BEFORE applying the fix.
- **Design Patterns:** Explicit composition over inheritance. Keep abstractions traceable and type-safe.
- **Verification:** Empirically verify all changes with terminal execution passing Exit Code 0.
