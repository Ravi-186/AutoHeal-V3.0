# ShopSphere Premium Design System Specification
## Phase 9: Commercial Modern E-Commerce Visual Identity

### 1. Visual Identity & Brand Philosophy
ShopSphere is a consumer e-commerce marketplace engineered to present a consumer shopping experience while functioning as the live target for AutoHeal's autonomous cybersecurity platform.

Unlike AutoHeal's dark cybersecurity aesthetic (Deep Navy `#030712`, Charcoal `#111827`, and Neon Cyan/Emerald indicators), **ShopSphere** features an e-commerce visual system:
- **Clean white and warm-neutral surfaces**: Crisp, spacious canvas prioritizing product photography and typography.
- **Deep navy and charcoal typography**: Readable font stack (`Inter`) with high contrast (WCAG 2.2 AA compliant).
- **Royal Sapphire primary accent (`#2563EB`)**: Trustworthy, energetic brand identity for buttons, active tabs, and primary actions.
- **Commercial Green (`#059669`)**: Highlights discounts, savings toasts, and successful order placements.
- **Amber Warning (`#D97706`)**: Highlights low-stock thresholds and critical stock alerts.
- **Rose Alert (`#E11D48`)**: Out-of-stock indicators, input errors, and cancellations.

---

### 2. Design Tokens

#### 2.1 Color Palette
```css
:root {
    /* Surfaces */
    --bg-page: #F8FAFC;         /* Warm slate background */
    --bg-surface: #FFFFFF;      /* Pure white card and container surface */
    --bg-muted: #F1F5F9;        /* Subtle inset backgrounds */
    --bg-inset: #F8FAFC;
    
    /* Typography */
    --text-heading: #0F172A;    /* Deep navy-charcoal for headings */
    --text-body: #1E293B;       /* Neutral slate for body copy */
    --text-secondary: #475569;  /* Muted metadata */
    --text-muted: #64748B;      /* Captions and secondary labels */
    --text-disabled: #94A3B8;   /* Inactive controls */

    /* Brand & Accent Colors */
    --primary: #2563EB;         /* Royal Sapphire */
    --primary-hover: #1D4ED8;   /* Darker hover state */
    --primary-active: #1E40AF;
    --primary-light: #EFF6FF;   /* Subtle tint for badges and highlights */
    --primary-border: #BFDBFE;

    /* Semantic Commerce Accents */
    --emerald: #059669;         /* Savings & in-stock confirmation */
    --emerald-light: #ECFDF5;
    --emerald-border: #A7F3D0;
    --amber: #D97706;           /* Low-stock & promotional tag */
    --amber-light: #FFFBEB;
    --amber-border: #FDE68A;
    --rose: #E11D48;            /* Stock depletion & cancellations */
    --rose-light: #FFF1F2;
    --rose-border: #FECDD3;

    /* Dividers & Borders */
    --border-subtle: #E2E8F0;
    --border-hover: #CBD5E1;
    --border-focus: #2563EB;
}
```

#### 2.2 Elevation & Shadows
- **Card Shadow (Resting):** `0 1px 3px 0 rgba(15, 23, 42, 0.08)`
- **Card Shadow (Hover):** `0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)`
- **Slide-Over Drawer Shadow:** `-4px 0 24px rgba(15, 23, 42, 0.15)`
- **Hero Elevation:** `0 20px 25px -5px rgba(15, 23, 42, 0.1)`

#### 2.3 Typography Scale
- **H1 (Hero):** 2.75rem (44px) / Weight 900 / Line-height 1.15
- **H2 (Section):** 1.5rem (24px) / Weight 800 / Line-height 1.25
- **H3 (Modal/Drawer Titles):** 1.25rem (20px) / Weight 800 / Line-height 1.3
- **H4 (Product Titles):** 0.9375rem (15px) / Weight 700 / Line-height 1.4
- **Body Regular:** 0.875rem (14px) / Weight 400 / Line-height 1.5
- **Caption / Badges:** 0.75rem (12px) / Weight 700 / Line-height 1.0

---

### 3. Component Architecture

#### 3.1 Product Card
- **Aspect Ratio:** Vertical commercial standard (Min 260px width).
- **Image Container:** 200px height with `#F8FAFC` background and smooth scale transition on card hover (`transform: scale(1.06)`).
- **Metadata Stack:** Category and brand label in small bold caps, 2-line clamped title, star rating badge (`★ 4.8`) with verified review count, pricing row (selling price, strike-through MRP, green savings badge), and stock status indicator.
- **Actions:** Wishlist heart toggle button, quick-action "Add to Cart" and "Buy Now".

#### 3.2 Slide-Over Drawers (Cart, Wishlist, Notifications)
- **Overlay:** Fixed full-screen with subtle blur (`backdrop-filter: blur(4px)`) and semi-transparent slate overlay (`rgba(15, 23, 42, 0.55)`).
- **Panel:** 460px fixed width anchored to the right viewport edge with `transform: translateX(100%)` entering via `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Cart Breakdown:** Includes free delivery qualification progress meter, promo code apply widget, and dynamic subtotal calculation.

#### 3.3 Multi-Step Checkout Modal
- **Progress Track:** 1. Address -> 2. Payment -> 3. Review -> 4. Confirmation.
- **Sandbox Testing Disclaimer:** Clear, prominent blue alert box stating that all transactions are simulated sandbox payments and no real card numbers or banking passwords are collected.

#### 3.4 Floating AutoHeal Testing Console
- Anchored to bottom right of viewport (`bottom: 24px; right: 24px; z-index: 4000`).
- Features a green/red pulsing sentinel dot and expandable 380px diagnostic dock for live bug injection, AST diagnosis, regression testing, and surgical patching.
