# O Conselho - Design Guidelines (Apple-Inspired Minimalism)

## Design Approach
**Apple Store Minimalism**: Inspired by Apple Store, iOS design language, and premium tech showrooms. Philosophy of "radical simplicity" where every element serves a clear purpose with maximum breathing room.

**Design Philosophy**: Clean, sophisticated, and restrained. Subtle rounded corners, generous whitespace, invisible design that gets out of the way. Effects are functional, never decorative. Space and clarity are the protagonists.

---

## Core Design Elements

### A. Color Palette - Refined Neutrals

**Dark Mode (Primary)**
- Background: hsl(20 14% 4%) - Deep warm charcoal
- Card Surface: hsl(20 14% 8%) - Elevated card background
- Input/Border: hsl(20 14% 18%) - Subtle borders
- Text Primary: hsl(45 25% 91%) - Warm off-white
- Text Secondary: hsl(45 15% 46%) - Muted gray
- **Accent Coral**: hsl(9 75% 42%) - Darkened for WCAG contrast (5.83:1 with white)
- **Accent Text**: hsl(0 0% 100%) - White text on dark coral
- Border Default: hsl(20 14% 15%)
- Dividers: hsl(20 14% 15%) / 0.5

**Light Mode**
- Background: hsl(0 0% 98%) - Clean white base
- Card: hsl(0 0% 100%) - Pure white elevation
- Input/Border: hsl(0 0% 88%) - Subtle borders
- Text Primary: hsl(0 0% 10%) - Near-black text
- Text Secondary: hsl(0 0% 46%) - Muted gray
- **Accent Coral**: hsl(9 75% 61%) - Vibrant coral for CTAs
- **Accent Text**: hsl(0 0% 9%) - Dark text on coral (7:1 contrast)

**WCAG Accessibility**
- All accent colors meet WCAG AA contrast requirements (≥4.5:1)
- Dark mode CTA: 5.83:1 contrast (coral bg + white text)
- Light mode CTA: 5.48:1 contrast (coral bg + dark text)

**Color Usage Rules**
- Accent coral: Only for primary CTAs, active states, and critical UI feedback
- Neutral grays: 95% of interface elements
- Backgrounds: Minimal contrast between layers (4% to 8% lightness)
- No gradients, no multi-color schemes, no decorative overlays

### B. Typography

**Font Stack**
- Primary: 'Inter', sans-serif (via Google Fonts)
- Weights: 400 (Regular), 500 (Medium), 600 (Semibold)

**Hierarchy - Clean & Light**
- Hero Headlines: text-6xl lg:text-7xl, font-semibold, tracking-tight, leading-tight
- Page Headers: text-4xl, font-semibold, tracking-tight
- Section Headers: text-2xl, font-medium
- Expert Names: text-xl, font-medium
- Body Text: text-base, font-normal, leading-relaxed
- Captions: text-sm, font-normal, text-muted-foreground
- Labels: text-xs, font-medium, uppercase tracking-wide

**Typography Rules**
- Never use font-bold - maximum weight is font-semibold for headlines only
- Default to font-normal for maximum readability
- Generous line-height (leading-relaxed) for body text
- Tight tracking (tracking-tight) only for display text

### C. Layout System

**Spacing Primitives - Apple-Generous**
- Micro: p-2, gap-2
- Standard: p-4, gap-4
- Component: p-6, p-8
- Section vertical: py-24, py-32
- Grid gaps: gap-6, gap-8
- Container padding: px-6 lg:px-8

**Containers**
- Max widths: max-w-7xl for full sections, max-w-4xl for content, max-w-2xl for forms
- Always mx-auto with generous px-6 lg:px-8

### D. Component Library

**Navigation**
- Ultra-minimal horizontal header, h-16, border-b border-border/50
- Logo left, nav center, user actions right
- Text-based navigation with text-sm font-medium
- Hover: text-foreground transition-colors duration-200

**Expert Cards - Minimal & Spacious**
- Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
- Card: bg-card, rounded-2xl, p-6, border border-border/50
- Avatar: w-20 h-20, rounded-full, mb-4
- Name: text-xl font-medium, mb-1
- Expertise: text-sm text-muted-foreground, mb-3
- Tags: Inline text-xs text-muted-foreground separated by • (no pills)
- CTA: Simple text link or outline button, text-sm font-medium
- Hover: translateY(-2px), shadow-md, duration-200

**Chat Interface**
- Sidebar: w-72, bg-card, border-r border-border/50
- Message bubbles: Simple rounded-2xl, p-4, no asymmetric design
- User: bg-accent/10, text-foreground, ml-auto, max-w-[80%]
- AI: bg-card, text-foreground, mr-auto, max-w-[80%]
- Avatar: w-8 h-8 rounded-full before AI messages
- Input: border border-border, rounded-xl, p-3, focus:ring-2 ring-accent

**Buttons - Minimal Hierarchy**
- Primary: bg-accent text-white, rounded-xl, px-6 py-2.5, font-medium, shadow-sm
- Secondary: border border-border, bg-transparent, same padding
- Ghost: No border, hover:bg-accent/10
- Icon: p-2, rounded-lg, hover:bg-card
- All: transition-all duration-200, active:scale-98

**Form Inputs**
- Design: border border-border, rounded-xl, p-3, bg-transparent
- Focus: ring-2 ring-accent, border-accent, outline-none
- Labels: text-sm font-medium mb-1.5, above inputs

**Data Display**
- Stats: Large number text-4xl font-semibold, small label text-sm text-muted-foreground
- Tags: Inline text with separators, no background pills
- Badges: Small text-xs px-2 py-0.5 rounded bg-accent/10 when absolutely necessary

### E. Animations - Fast & Natural

**Apple Animation Principles**
- Speed: 200-300ms for all transitions
- Easing: ease-out for entrances, ease-in for exits
- Subtlety: Minimal movement, maximum clarity
- Purpose: Only animate for feedback or state changes

**Animation Library**
- Hover: translateY(-2px), shadow-md, duration-200
- Click: active:scale-98, duration-100
- Page transitions: fade only, 300ms
- Modal entrances: scale-95 to scale-100 + fade, 200ms
- No floating, no pulse, no shimmer, no glow effects

**Component Animations**
- Cards: Hover lift 2px, subtle shadow, 200ms
- Buttons: Scale 98% on click, 100ms
- Inputs: Ring appears on focus, 150ms
- Messages: Slide-in minimal (10px), 200ms
- Navigation: Color transitions only, 200ms

---

## Page-Specific Layouts

**Landing Page - Feature-Rich Yet Clean**
- Hero: min-h-[600px], centered content with large background image (abstract tech/connectivity), semi-transparent overlay (bg-background/80), headline text-6xl, primary CTA + secondary CTA stacked vertically on mobile
- Trust Bar: py-8, client logos or stats in single row, subtle opacity
- Features: 3-column grid (grid-cols-1 md:grid-cols-3 gap-8), icon + heading + description, py-24
- Expert Showcase: Featured expert cards, 3 across desktop, bg-card section with py-32
- How It Works: 3 steps, vertical on mobile, horizontal on desktop with connecting lines, icons above numbers
- Social Proof: 4-stat grid, large numbers with labels, py-20
- CTA Section: py-32, centered headline + description + primary button, subtle bg-card background
- Footer: py-16, multi-column links, newsletter signup, social icons, minimalist

**Expert Gallery**
- Header: Search bar (max-w-2xl mx-auto), filter chips below, py-8
- Grid: 3 columns desktop, 2 tablet, 1 mobile, gap-6
- Sidebar (optional): Category filters, w-64, sticky
- Pagination: Simple numbers, hover states, centered

**Chat Interface**
- Split: Sidebar (w-72) + Main (flex-1)
- Sidebar: Conversation list, each with avatar + name + preview, active state bg-accent/10
- Main header: Expert info, avatar + name + tags
- Messages: Scrollable area, flex-1, py-4
- Input area: Fixed bottom, bg-card, border-t, p-4
- Suggested prompts: Horizontal scroll chips above input

**Create Expert**
- Single column form, max-w-2xl mx-auto, py-12
- Sections: Separated by py-8 gaps
- Avatar upload: Large circular preview, dashed border dropzone
- Text inputs: Full width, stacked with clear labels
- Multi-select: Checkbox grid for expertise areas
- Preview: Sticky card on desktop showing live expert card
- Actions: Fixed bottom bar with Save + Publish buttons

---

## Images

**Hero Section**: High-quality abstract image showing neural networks, data visualization, or modern tech workspace. Dark overlay (bg-background/80) for text contrast. Image should be 1920x1080 minimum, optimized for web.

**Expert Avatars**: Professional headshots, circular crop, consistent quality. 200x200px minimum. Neutral backgrounds preferred.

**Feature Icons**: Heroicons outlined style via CDN, size-6 (24px), text-muted-foreground color.

**Optional Sections**: Abstract tech imagery for feature sections (neural networks, data patterns), subtle and non-distracting.

---

## Key Principles

**Radical Simplification**
- Remove all decorative elements
- Every pixel serves a function
- White space is a design element, not empty space
- Clarity over cleverness

**Minimal Visual Hierarchy**
- Use size and weight, not color, for hierarchy
- Accent color only for primary actions
- Borders are subtle (opacity 0.5)
- Shadows are functional, not decorative

**Speed & Responsiveness**
- All animations 200-300ms maximum
- No loading states that feel sluggish
- Instant feedback on interactions
- Smooth scrolling, no parallax

**Content First**
- Typography does the heavy lifting
- Images are purposeful, not decorative
- Navigation is invisible until needed
- Focus on user's task, not the interface

**Apple-Level Polish**
- Rounded corners: rounded-xl (12px) standard, rounded-2xl (16px) for cards
- Consistent 8px spacing grid
- Perfect vertical rhythm
- Intentional use of micro-interactions