## SwiftUI policy — iOS/iPadOS/macOS 27.0+

Scope: SwiftUI work in `vinoguessr-app`. Read the available SwiftUI Expert Skill; project requirements override generic older-OS fallback advice. Verify availability against the deployment target and selected SDK. Do not impose an architecture or adopt Liquid Glass automatically.

### Layout

Start with standard containers. Select `Layout` for placement, `onGeometryChange` for observation, `alignmentGuide` for relationships, Subview APIs for containers, `ArrangementView` for custom two-region relationships. Check `ViewThatFits`/`fixedSize` sizing. `if` removes; `opacity`/`hidden` reserve space. Check invisible accessibility/hit testing. `GeometryReader` needs a geometry-driven purpose; prevent feedback loops. `Layout` is not lazy virtualization. [User reference](https://zenn.dev/zunda_pixel/articles/2cc489b4168a5a)

### Two-region arrangements

Prefer standard adaptive navigation/content containers when they fit. Consider `ArrangementView` for custom split or foreground/background relationships; it does not supply navigation. Follow Apple's container-nesting guidance.

Before choosing a style, decide which content can disappear and which belongs in front. A constrained split may show only primary; a stacked overlay places primary above secondary. These roles are not interchangeable. Keep needed secondary information/actions reachable through another presentation. Sizing preferences do not prove the final layout.

Keep state that must survive conditional style/container branches above those identity boundaries. Verify continuity rather than assuming hidden content or a style switch preserves state. Do not infer complete visibility from `splitArrangementAxis`, `overlayArrangementZIndex` or reserved-region signals alone.

The article's Xcode 27.1 beta animation/API observations are context, not permanent platform guarantees. Recheck the selected SDK before adding a workaround. [User reference](https://fatbobman.com/zh/posts/arrangementview-think-before-you-arrange/), [Apple arrangements](https://developer.apple.com/documentation/swiftui/arrangementview), [Apple design guidance](https://developer.apple.com/videos/play/tech-talks/111463/).

### Identity and ownership

Identity controls state lifetime; changing initializer arguments does not reset existing state. Use stable model IDs. Change `.id` or conditional containers only for intentional lifetime changes. Do not treat inferred List caches as API contracts. [User reference](https://zenn.dev/zunda_pixel/articles/ea826f888d05ed)

Keep primitive view-local `@State` private. Preserve owned observable models with `@State`; use `@Bindable` for injected edits and plain values for read-only inputs. An initial value seeds that identity's storage; `View.init` may run again. Later parent updates need values or bindings. UI-owned observable models/routers use explicit `@MainActor` under our nonisolated default.

### Observation

Prefer property-granular `@Observable` models and small dependency boundaries. A class alone does not guarantee faster rendering. Measure actual UI updates rather than generalizing old benchmark counts; do not eliminate appropriate primitive state. [User reference](https://zenn.dev/zunda_pixel/articles/9ce01609d0d234)

### Navigation

Default to an exhaustive `Hashable` route enum with stable IDs and `[Route]`; use `NavigationPath` when heterogeneous types are needed. Own the router at its scope and inject through `@Environment`. Modernize legacy wrappers. Never derive a retroactive `Binding: Hashable` from mutable wrapped values. [User reference](https://zenn.dev/zunda_pixel/articles/ebf2a079cbf68b)

Own routers per scene/account/profile; key private presentation caches by environment/facility too. Clear authenticated presentation on logout, revocation or identity changes; discard late results from a previous identity/scope. Keep token/CSRF handling in the existing session layer, not UI state or navigation persistence. Routes contain IDs, not credentials or full private models. Authorized display models remain allowed. Restored IDs/deep links require API authorization; UI state grants no access. Preserve redacted errors.

### Actions and toolbars

Define an action's purpose before its position. Prefer suitable semantic toolbar placements; reconsider competing actions before fixing physical edges. Choose `ButtonRole` to match behavior: `.close` preserves progress, `.cancel` abandons the pending operation, `.confirm` confirms, and `.destructive` identifies destructive work. Roles do not implement application save/discard logic or grant API authorization; handlers and presentation policy must implement the promised behavior. Use system role labels when appropriate and clear contextual labels when needed. Custom placement or content actions remain valid when justified. Verify unsaved-change dismissal, required destructive confirmation/undo, accessibility and compact/expanded toolbar overflow. [User reference](https://zenn.dev/zunda_pixel/articles/7ed1e0d8456e7c), [Apple ButtonRole](https://developer.apple.com/documentation/swiftui/buttonrole), [semantic placements](https://developer.apple.com/documentation/swiftui/toolbaritemplacement).

### Verification

For UI changes, build/test on the target SDK and check iPhone/iPad resizing, Dynamic Type, accessibility, state lifetime and back navigation. For arrangements, check applicable primary-only, split and overlay outcomes, secondary access and state continuity. Profile performance when needed. Document-only changes verify policy parity/links; do not claim unexecuted UI or Instruments checks.

Apple contracts: [Observation migration](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro), [State](https://developer.apple.com/documentation/swiftui/state), [NavigationStack](https://developer.apple.com/documentation/swiftui/navigationstack), [Layout](https://developer.apple.com/documentation/swiftui/layout), [ArrangementView](https://developer.apple.com/documentation/swiftui/arrangementview). Skill: [SwiftUI Agent Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill).
