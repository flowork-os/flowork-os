# NEW APPLICATION & PROTOTYPE SCAFFOLDING DOCTRINE

## 1. Context & Activation Scope
Triggered when designing, scaffolding, or synthesizing new sovereign applications, GUI prototypes, or frontend services (`new_app`, `scaffold`, `prototype`, `create_app`, `app_design`).

## 2. Mandatory Behavioral Invariants
- **Visual Impact & Polish:** Deliver visually appealing, substantially complete prototypes with rich aesthetics, consistent spacing, and platform-appropriate typography.
- **Local Asset Autonomy:** Source or generate placeholders locally (e.g., stylized CSS shapes, gradients, procedurally generated SVG/canvas patterns). Never plan for unresolvable external cloud assets.
- **Styling Preference:** Prefer Vanilla CSS for maximum flexibility. Avoid TailwindCSS unless explicitly requested.
- **Tech Stack Alignments:**
  - Web: React (TypeScript) or Angular with Vanilla CSS.
  - APIs: Node.js (Express) or Python (FastAPI).
  - Mobile: Compose Multiplatform or Flutter.
  - Games: HTML/CSS/JS (Three.js for 3D).
  - CLIs: Python or Go / Rust.
- **Territory Invariant:** All native desktop apps MUST target `/opt/floworkos/apps/<app_id>/` with `.desktop` files in `/usr/share/applications/`.

## 3. Strict Prohibitions
- NEVER scaffold apps in arbitrary directories outside `/opt/floworkos/apps/`.
- NEVER leave incomplete stub buttons with non-functional empty callbacks.
