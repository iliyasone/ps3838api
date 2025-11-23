**Version 1.0.0 – Client Architecture Release**

This release introduces a stable client-driven design that replaces the previous module-level API helpers. The new `PinnacleClient` serves as the central entry point for all interactions with the PS3838 (Pinnacle) API, providing clearer structure, improved reliability, and a foundation suitable for long-term maintenance.

The internal layout has been reshaped to focus on explicit, typed responses and predictable method behavior. Broken legacy utilities that conflicted with the new architecture have been removed to ensure the codebase is consistent and free of unmaintained or misleading functionality. Logging has been added to make request/response flow traceable, which is especially important for debugging betting workflows.

Deprecated interfaces still exist for compatibility but are no longer part of the public API direction. The library is now aligned with practices expected from a 1.x release: stable interface, predictable behavior, and a coherent structure ready for iterative improvements.

### Added

* New client-based architecture with `PinnacleClient` as the unified interface.
* Integrated logging system with configurable verbosity levels.
* Typed response models based on official PS3838/Pinnacle documentation.

### Changed

* Internal modules reorganized around client-centric design.
* Examples updated to demonstrate the new workflow.

### Removed

* Outdated and broken helper functions that conflicted with the client architecture.
* Legacy interfaces that were incomplete or misleading.

### Notes
* A future release will introduce higher-level helpers, such as `magic_find_event`.