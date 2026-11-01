# AutoHeal Phase 8: Performance, Optimization and Accessibility

## 1. Executive Summary

Enterprise SOC platforms must balance visual richness with operational responsiveness. Phase 8 pairs an optimized 60 FPS Three.js WebGL engine with a **WCAG 2.1 AA-compliant 2D Accessible Ledger Fallback**, ensuring operators on all hardware tiers and accessibility requirements can investigate threats seamlessly.

---

## 2. 3D WebGL Performance Engineering

### 2.1 Rendering Pipeline Optimizations
- **Geometry Caching**: Reusable primitive geometries (`OctahedronGeometry`, `CylinderGeometry`, `DodecahedronGeometry`, `BoxGeometry`) are instantiated once in memory and shared across identical entity types.
- **Batched Edge Rendering**: Graph edges are drawn using indexed line segments with dynamic buffer updates, minimizing OpenGL draw calls ($< 40\text{ draw calls}$ for a 200-node graph).
- **Frustum & Distance Culling**: Billboard text labels and high-detail wireframes outside the camera view frustum or beyond $Z = 600$ world units are automatically hidden.
- **Throttled Raycasting**: Raycasting against interactive meshes is throttled to 30 Hz (once every 2 animation frames) during camera movements, preventing UI frame jitter.
- **Memory Reclamation**: When switching away from the 3D tab or applying new filters, unused geometries, materials, textures, and event listeners are explicitly disposed of (`geometry.dispose()`, `material.dispose()`) to prevent GPU memory leaks.

### 2.2 Target Benchmark Metrics
- **Frame Rate**: Steady $60\text{ FPS}$ on standard integrated GPUs (Intel Iris Xe, Apple M-series, AMD Radeon) with up to 300 active nodes and 600 edges.
- **Initialization Latency**: $< 350\text{ms}$ from DOM mount to first complete render.
- **SSE Delta Latency**: $< 50\text{ms}$ from SSE event arrival to 3D node insertion and pulse.

---

## 3. 2D Accessible Security Ledger Fallback

For analysts with visual impairments, motion sensitivities, or low-specification thin-client workstations, the module provides a full-featured **2D Accessible Ledger View**:

```
+-----------------------------------------------------------------------------------------+
| [3D Spatial Topology]  |  [* 2D Accessible Security Ledger *]                           |
+-----------------------------------------------------------------------------------------+
| Filter: [All Severities v] [All Types v] Search: [ 198.51.100.99              ]         |
+-----------------------------------------------------------------------------------------+
| Entity ID       | Type        | Severity | Status  | Connected Nodes | Quick Action     |
|-----------------+-------------+----------+---------+-----------------+------------------|
| IP-198.51.100.99| SOURCE_IP   | CRITICAL | BLOCKED | 8 edges         | [Inspect] [Chat] |
| EP-/api/cart    | TARGET_ENDP | HIGH     | ACTIVE  | 14 edges        | [Inspect] [Chat] |
| INC-1004        | INCIDENT    | CRITICAL | OPEN    | 6 edges         | [Investigate]    |
+-----------------------------------------------------------------------------------------+
```

### 3.1 Seamless Toggle
Operators can toggle between 3D Spatial View and 2D Ledger View at any time using:
- The top-right mode toggle button (`#btnToggleTopology2D`).
- The keyboard shortcut `T`.
- Automatic detection of `prefers-reduced-motion: reduce` or absence of WebGL context.

---

## 4. Accessibility & WCAG 2.1 AA Compliance

### 4.1 Contrast Ratios
All text and interactive borders strictly conform to the **Obsidian Sentinel** high-contrast design specifications:
- Primary text (`#F1F5F9` on `#090D14` and `#101722`): **Contrast Ratio 15.2:1** (exceeds AAA requirement of 7.0:1).
- Secondary muted text (`#94A3B8` on `#101722`): **Contrast Ratio 7.8:1** (exceeds AA requirement of 4.5:1).
- Interactive focus outlines (`#38BDF8` sky blue): **Contrast Ratio 9.4:1**.

### 4.2 Semantic Markup & ARIA Roles
- All data tables feature explicit `<th scope="col">` headers and accessible captions.
- 3D Canvas includes `role="img"` with dynamic `aria-label` describing the active graph state (e.g., *"3D Threat Topology displaying 24 nodes and 36 relationships"*).
- The Copilot chat feed uses `role="log"` with `aria-live="polite"` so screen readers announce incoming AI responses without interrupting the analyst.

### 4.3 Full Keyboard Navigation
Every operation in the 3D Threat Topology and AI Copilot can be executed without a mouse via standard keyboard focus rings, `Tab`, `Shift+Tab`, `Enter`, and dedicated single-key shortcuts (`R`, `F`, `T`, `1-5`).
