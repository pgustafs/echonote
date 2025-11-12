# EchoNote Styling Guide

**Version:** 2.0 - Neo-Minimal Dark Mode  
**Last Updated:** November 2025  
**Design Language:** Modern Glass Morphism

---

## Table of Contents

1. [Overview](#overview)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Components](#components)
5. [Interactions & Animations](#interactions--animations)
6. [Spacing & Layout](#spacing--layout)
7. [Mobile Responsiveness](#mobile-responsiveness)
8. [Best Practices](#best-practices)
9. [Quick Reference](#quick-reference)

---

## Overview

EchoNote uses a **neo-minimal dark mode** design language inspired by modern applications like macOS Sonoma, Arc Browser, and other 2025-era interfaces. The design emphasizes:

- ✨ **Glass morphism** for depth and elegance
- 🎨 **Subtle gradients** for visual interest
- 🌑 **Muted, sophisticated colors** over saturated tones
- 💫 **Smooth animations** for premium feel
- 📱 **Touch-friendly interactions** for mobile support

---

## Color Palette

### Background Colors

#### Primary Background
```css
/* Charcoal gradient - smooth and rich */
background: linear-gradient(180deg, #0E1117 0%, #161B22 100%);
background-attachment: fixed;
```

#### Glass Cards
```css
/* Frosted glass effect */
background: rgba(255, 255, 255, 0.04);
backdrop-filter: blur(8px);
-webkit-backdrop-filter: blur(8px);
border: 1px solid rgba(255, 255, 255, 0.08);
border-radius: 1rem;
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
```

### Text Colors

| Usage | Color | Hex | Notes |
|-------|-------|-----|-------|
| Primary Text | Soft White | `#E6E8EB` | Easier on eyes than pure white |
| Secondary Text | Muted Gray | `#9BA4B5` | Labels, timestamps, meta info |
| Disabled Text | Very Muted | `rgba(255, 255, 255, 0.3)` | Disabled states |

### Accent Colors

#### Primary Accent (Electric Iris → Purple)
```css
/* Main brand color */
color: #5C7CFA;

/* Gradient version for CTAs */
background: linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%);
box-shadow: 0 4px 12px rgba(92, 124, 250, 0.25);
```

#### Secondary Accent (Cyan Glow)
```css
/* Hover states, highlights */
color: #4ADEDE;
```

### Semantic Colors

#### High Priority
```css
/* Soft coral - modern, not bright red */
color: #FF6B6B;
background: rgba(255, 107, 107, 0.15);
border: 1px solid rgba(255, 107, 107, 0.3);
```

#### Medium Priority
```css
/* Warm amber */
color: #F9A826;
background: rgba(249, 168, 38, 0.15);
border: 1px solid rgba(249, 168, 38, 0.3);
```

#### Low Priority
```css
/* Mint green */
color: #4ADE80;
background: rgba(74, 222, 128, 0.15);
border: 1px solid rgba(74, 222, 128, 0.3);
```

#### Error/Delete
```css
/* Modern crimson */
color: #E44C65;
background: #E44C65;
box-shadow: 0 4px 12px rgba(228, 76, 101, 0.25);
```

---

## Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Font Smoothing
```css
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
```

### Font Weights

- **Regular (400)**: Body text, descriptions
- **Medium (500)**: Badges, capsules, form labels
- **Semibold (600)**: Button text, important labels
- **Bold (700)**: Headings, emphasis

### Responsive Text Sizing

```css
/* Mobile-first approach */
.heading {
  font-size: 1.5rem;  /* 24px on mobile */
}

@media (min-width: 640px) {
  .heading {
    font-size: 1.875rem;  /* 30px on tablet */
  }
}

@media (min-width: 1024px) {
  .heading {
    font-size: 2.25rem;  /* 36px on desktop */
  }
}
```

---

## Components

### Buttons

#### Primary Button (Main CTA)
```css
.btn-primary {
  background: linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%);
  border-radius: 1.5rem;  /* 24px - smooth 2025 feel */
  box-shadow: 0 4px 12px rgba(92, 124, 250, 0.25);
  color: white;
  font-weight: 600;
  min-height: 44px;
  padding: 0.75rem 1.5rem;
  transition: all 0.2s;
}

.btn-primary:hover {
  box-shadow: 0 0 16px rgba(92, 124, 250, 0.5);
  transform: translateY(-1px);
}
```

**File:** `frontend/src/index.css` (Lines 45-55)

#### Danger Button (Delete)
```css
.btn-danger {
  background: #E44C65;
  border-radius: 1.5rem;
  box-shadow: 0 4px 12px rgba(228, 76, 101, 0.25);
  color: white;
  font-weight: 600;
  min-height: 44px;
  padding: 0.75rem 1.5rem;
  transition: all 0.2s;
}

.btn-danger:hover {
  background: #d43d56;  /* Darker on hover */
  box-shadow: 0 0 16px rgba(228, 76, 101, 0.4);
}
```

**File:** `frontend/src/index.css` (Lines 69-79)

### Cards

#### Glass Card
```css
.enterprise-card-dark {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}
```

**File:** `frontend/src/index.css` (Lines 31-38)

### Form Inputs

#### Input Field (Dark)
```css
.input-field-dark {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.75rem;
  color: #E6E8EB;
  min-height: 44px;
  padding: 0.75rem 1rem;
  transition: all 0.2s;
}

.input-field-dark:focus {
  outline: none;
  border-color: #5C7CFA;
  box-shadow: 0 0 0 3px rgba(92, 124, 250, 0.2);
}
```

**File:** `frontend/src/index.css` (Lines 136-153)

#### Custom Select/Dropdown (Dark)

Professional custom-styled dropdown with chevron icon, replacing default browser styles.

```css
.select-dark {
  background-color: rgba(15, 23, 42, 0.95);  /* Solid dark slate */
  background-image: url("data:image/svg+xml,...");  /* Custom chevron */
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.75rem;
  color: #E6E8EB;
  color-scheme: dark;  /* Hint browser to use dark theme */
  min-height: 44px;
  padding: 0.75rem 1rem;
  padding-right: 2.5rem;
  appearance: none;  /* Remove default arrow */
  cursor: pointer;
}

.select-dark:hover {
  background-color: rgba(15, 23, 42, 1);  /* Fully opaque on hover */
  border-color: rgba(255, 255, 255, 0.12);
}

.select-dark:focus {
  outline: none;
  border-color: #5C7CFA;
  box-shadow: 0 0 0 3px rgba(92, 124, 250, 0.2);
  background-color: rgba(15, 23, 42, 1);
}

.select-dark option {
  background-color: #0f172a;  /* Dark slate-900 for options */
  color: #E6E8EB;
  padding: 0.75rem 1rem;
}

.select-dark option:checked {
  background-color: #5C7CFA;  /* Blue for selected option */
  color: white;
}
```

**Features:**
- Removes default browser dropdown arrow with `appearance: none`
- Custom chevron icon in gray (`#9BA4B5`) positioned right
- **Solid dark background** - `rgba(15, 23, 42, 0.95)` instead of transparent
- **`color-scheme: dark`** - Tells browser to use dark native controls
- **Dark dropdown menu** - Options appear with `#0f172a` background
- Hover state becomes fully opaque
- Focus state shows blue ring
- Selected option highlighted in blue (`#5C7CFA`)

**File:** `frontend/src/index.css` (Lines 155-186)

#### Custom Checkbox (Dark)

Professional custom checkbox with gradient fill and checkmark, replacing default browser styles.

```css
.checkbox-dark {
  appearance: none;  /* Remove default checkbox */
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 0.375rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.checkbox-dark:hover {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.06);
}

.checkbox-dark:checked {
  background: linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%);
  border-color: #5C7CFA;
}

.checkbox-dark:checked::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  width: 0.35rem;
  height: 0.65rem;
  border: solid white;
  border-width: 0 2px 2px 0;  /* L-shape rotated = checkmark */
}
```

**Variants:**
```css
.checkbox-blue:checked {
  background: linear-gradient(135deg, #5C7CFA 0%, #4ADEDE 100%);
}

.checkbox-purple:checked {
  background: linear-gradient(135deg, #9775FA 0%, #7C3AED 100%);
}
```

**Features:**
- Removes default browser checkbox with `appearance: none`
- Custom checkmark created with CSS border trick (rotated L-shape)
- Gradient background when checked (matches brand colors)
- Smooth hover states
- Focus ring for accessibility
- Color variants for different sections (blue for URL, purple for diarization)

**Usage:**
```tsx
<input type="checkbox" className="checkbox-dark checkbox-purple" />
<input type="checkbox" className="checkbox-dark checkbox-blue" />
```

**File:** `frontend/src/index.css` (Lines 188-243)

### Badges

#### Priority Badge (Modern Capsule)
```css
.badge {
  border-radius: 9999px;  /* Fully rounded capsule */
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.2rem 0.7rem;
}

.badge-high {
  background: rgba(255, 107, 107, 0.15);
  color: #FF6B6B;
  border: 1px solid rgba(255, 107, 107, 0.3);
}
```

**File:** `frontend/src/index.css` (Lines 131-154)

### Recording Options Card

A visually distinct container that groups all recording settings (model selector, URL input, diarization options) to provide clear visual organization and prevent settings from floating in the middle of the page.

#### Card Structure
```tsx
<div className="bg-slate-800/40 backdrop-blur-sm border border-slate-600/50 rounded-xl p-5 sm:p-6 space-y-4 sm:space-y-5">
  {/* Card Header with Icon */}
  <div className="flex items-center space-x-2 pb-3 border-b border-slate-600/30">
    <svg className="w-5 h-5 text-blue-400">...</svg>
    <h3 className="text-lg font-semibold text-white">Recording Options</h3>
  </div>

  {/* Settings Content */}
  <div className="space-y-4">
    {/* Model selector, checkboxes, inputs */}
  </div>
</div>
```

#### Design Elements
- **Background**: `bg-slate-800/40` - Semi-transparent dark gray with 40% opacity
- **Backdrop Blur**: `backdrop-blur-sm` - Subtle blur effect for glass morphism
- **Border**: `border-slate-600/50` - Subtle border at 50% opacity
- **Border Radius**: `rounded-xl` - 0.75rem (12px) for smooth corners
- **Padding**: `p-5 sm:p-6` - 1.25rem mobile, 1.5rem tablet+
- **Header Separator**: Bottom border (`border-b border-slate-600/30`) divides header from content

#### Benefits
- **Visual Hierarchy**: Clear container separates settings from main recording action
- **Organization**: Grouped related controls with descriptive heading
- **Professional Look**: Intentional, structured appearance vs. floating elements
- **Focus Direction**: Helps users understand where to configure before recording

**File:** `frontend/src/components/AudioRecorder.tsx` (Lines 783-901)

### Microphone Ring Button (Recording CTA)

The microphone button is the **single primary interaction point** for recording. This unified approach eliminates confusion and creates a clear, focused user experience.

#### Design Philosophy
- **Single Point of Control**: One button handles both start and stop actions
- **Ring Design**: Circular outline (not filled) for modern, clean aesthetic
- **Fixed Position**: Button stays in same position; timer and pause button appear below when recording
- **Visual State Clarity**: Color and animation clearly indicate current state
- **No Redundant Controls**: Removed separate "Start Recording" and "Stop Recording" buttons to avoid split focus
- **Clear Instruction**: Subtitle guides users: "Adjust options below, then press the microphone to start."

#### Idle State (Purple Ring)
```tsx
style={{
  background: 'transparent',
  border: '6px solid #9775FA',  /* Solid purple ring */
  boxShadow: '0 8px 24px rgba(92, 124, 250, 0.4), inset 0 0 20px rgba(92, 124, 250, 0.1)',
  borderRadius: '50%',
  width: '10rem',   /* 160px on mobile */
  height: '10rem',
  /* 12rem on tablet+ (192px) */
  transition: 'all 0.3s',
  cursor: 'pointer'
}}
```

**Border Color**: `#9775FA` (Solid Purple - ensures perfect circular shape)
**Icon Color**: `#9775FA` (Purple)
**Action**: Click to start recording

**Note**: Using solid border instead of `borderImage` gradient to maintain perfect circular shape (borderImage is incompatible with border-radius)

#### Hover State (Idle)
```tsx
onMouseEnter={(e) => {
  e.currentTarget.style.boxShadow = '0 12px 32px rgba(92, 124, 250, 0.6), inset 0 0 30px rgba(92, 124, 250, 0.15)'
  e.currentTarget.style.transform = 'scale(1.05)'
}}
```

#### Recording State (Red Ring)
```tsx
style={{
  background: 'transparent',
  border: '6px solid #E44C65',  /* Solid red ring */
  boxShadow: '0 8px 24px rgba(228, 76, 101, 0.4), inset 0 0 20px rgba(228, 76, 101, 0.1)',
  transform: 'scale(1.05)',
  cursor: 'pointer'  /* Still clickable to stop */
}}
```

**Icon Color**: `#E44C65` (Crimson Red)
**Action**: Click to stop recording and transcribe

**Visual Feedback**:
- Pulsing red ring animation around button
- Enlarged scale (1.05)
- Red border (#E44C65)
- Red microphone icon
- Timer appears below button
- Pause/Resume button appears below timer

#### Hover State (Recording)
```tsx
onMouseEnter={(e) => {
  e.currentTarget.style.boxShadow = '0 12px 32px rgba(228, 76, 101, 0.6), inset 0 0 30px rgba(228, 76, 101, 0.15)'
  e.currentTarget.style.transform = 'scale(1.1)'  /* Slightly larger than idle hover */
}}
```

#### Layout Structure
```
┌─────────────────────────────────┐
│   Microphone Ring Button        │  ← Always in same position
│   (Purple/Red Ring + Icon)      │
└─────────────────────────────────┘
          ↓ (when recording)
┌─────────────────────────────────┐
│   Timer Display                 │  ← Appears below button
│   "0:45 Recording"              │
└─────────────────────────────────┘
          ↓
┌─────────────────────────────────┐
│   [Pause] or [Resume] Button    │  ← Appears below timer
└─────────────────────────────────┘
```

#### Button Behavior
```tsx
<button
  onClick={isRecording ? stopRecording : startRecording}
  disabled={isTranscribing || isStopping}
  aria-label={isRecording ? 'Stop recording and transcribe' : 'Start recording'}
>
```

**File:** `frontend/src/components/AudioRecorder.tsx` (Lines 627-771)

### DNA Spiral Background Animation

#### Overview
The recording area features an animated DNA-like double helix effect with glowing dots traveling along curved paths. Inspired by modern web animations (like vite.dev), this creates subtle "AI energy" visual interest.

**Key Feature**: The DNA spiral is **anchored to the microphone button**, not the card. This means it stays centered behind the button regardless of card size changes when recording indicators appear/disappear.

#### Positioning Strategy
```tsx
{/* Button Container with DNA Spiral */}
<div className="relative">
  {/* DNA Spiral - Absolutely positioned relative to button */}
  <div className="absolute pointer-events-none" style={{
    left: '50%',
    top: '50%',
    transform: 'translate(-50%, -50%)',
    width: '600px',
    height: '300px',
    zIndex: 0
  }}>
    <svg viewBox="0 0 800 400" preserveAspectRatio="xMidYMid meet">
      {/* DNA paths centered at x=400, y=150 */}
    </svg>
  </div>

  {/* Button positioned above spiral */}
  <button style={{ zIndex: 1 }}>
    {/* Button content */}
  </button>
</div>
```

This structure ensures:
- DNA spiral is always centered on button (via `transform: translate(-50%, -50%)`)
- Button stays above spiral (via `zIndex: 1`)
- When card height changes (recording indicators), button and spiral move together
- Fixed 600px × 300px spiral container provides consistent animation area

#### Two Crossing Curved Lines
```tsx
{/* First curved path - DNA helix top strand (centered at y=200) */}
<path
  d="M -50 200 Q 100 160, 200 190 Q 300 220, 400 200 Q 500 180, 600 210 Q 700 240, 850 210"
  stroke="url(#lineGradient1)"
  strokeWidth="1"
  fill="none"
  filter="url(#lineGlow)"
  opacity="0.7"
/>

{/* Second curved path - DNA helix bottom strand (inverse curve, crosses at y=200) */}
<path
  d="M -50 210 Q 100 240, 200 210 Q 300 180, 400 200 Q 500 220, 600 190 Q 700 160, 850 190"
  stroke="url(#lineGradient2)"
  strokeWidth="1"
  fill="none"
  filter="url(#lineGlow)"
  opacity="0.7"
/>
```

#### Color Scheme

**Idle State (Not Recording):**
- **Line 1 Gradient**: `#5C7CFA` (blue) → `#4ADEDE` (cyan) → `#9775FA` (purple)
- **Line 2 Gradient**: `#9775FA` (purple) → `#4ADEDE` (cyan) → `#5C7CFA` (blue) - inverse
- **Cold Dots** (2): `#4ADEDE` (cyan) - represents cool energy
- **Warm Dot** (1): `#F9A826` (amber) - represents warm energy

**Recording State:**
- **Line Gradients**: Same as idle (unchanged)
- **All Dots**: `#E44C65` (red) - all 3 dots turn red to match recording button
- **Visual Unity**: Creates cohesive red theme (button ring + icon + DNA dots)

```tsx
// Dots change color based on recording state
fill={isRecording ? "#E44C65" : "#4ADEDE"}  // Cold dots
fill={isRecording ? "#E44C65" : "#F9A826"}  // Warm dot
```

#### Traveling Glow Effect
Each dot has a radial gradient circle (radius 20) that follows it along the path, creating a "traveling glow" effect:

```tsx
{/* Glow area that travels with dot */}
<circle r="20" fill="url(#travelGlow)" opacity="0.3">
  <animateMotion dur="12s" repeatCount="indefinite">
    <mpath href="#motionPath1" />
  </animateMotion>
</circle>

{/* Radial gradient definition */}
<radialGradient id="travelGlow">
  <stop offset="0%" stopColor="white" stopOpacity="0.8"/>
  <stop offset="50%" stopColor="white" stopOpacity="0.4"/>
  <stop offset="100%" stopColor="white" stopOpacity="0"/>
</radialGradient>
```

#### Technical Details
- **Animation Duration**: 12 seconds per cycle
- **ViewBox**: 0 0 800 400 (800px wide, 400px tall)
- **Positioning**: Lines centered at y=200 (exact vertical center of 400px viewBox)
- **Crossing Point**: Both paths intersect at (400, 200) - perfect center of the viewBox
- **Dot Count**: 3 total (2 cold + 1 warm)
- **Convergence**: Dots slow down at end using spline timing `keyPoints="0;0.7;1"`
- **Z-Index**: Background layer (z-index: 0) with `pointer-events-none`
- **Anchoring**: Positioned absolutely relative to button container, not card

#### Key Features
1. **DNA Helix Shape**: Two lines with inverse curves create crossing pattern
2. **Multiple Small Curves**: 3-4 wave oscillations per path for dynamic flow
3. **Traveling Glow**: Radial halos follow dots, "lighting up" the line as they pass
4. **Color Temperature**: Mix of warm (amber) and cool (cyan) for visual depth
5. **Smooth Animation**: Spline-based easing for natural, organic motion

**File:** `frontend/src/components/AudioRecorder.tsx` (Lines 401-590)

---

## Interactions & Animations

### Header with Logo

The header features the EchoNote logo with a semi-transparent glass effect background that matches the footer design.

#### Logo Implementation
```tsx
{/* Logo */}
<div className="flex items-center">
  <img
    src="/econote_logo.png"
    alt="EchoNote Logo"
    className="h-12 sm:h-16 lg:h-20 w-auto"
    style={{ filter: 'drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3))' }}
  />
</div>
```

**File:** `frontend/src/App.tsx` (Lines 142-150)
**Logo Asset:** `frontend/public/econote_logo.png`

#### Header Background
```css
.gradient-header {
  /* Semi-transparent glass effect matching footer design */
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
```

**File:** `frontend/src/index.css` (Lines 289-294)

**Design Rationale:**
- Custom logo replaces generic icon and text for brand identity
- Responsive sizing: 48px (mobile) → 64px (tablet) → 80px (desktop)
- Drop shadow for depth and legibility against varying backgrounds
- Matches footer styling for visual consistency
- Semi-transparent glass effect creates depth
- Subtle border provides gentle separation
- Clean, professional appearance

### Loading Spinner

```css
.spinner {
  animation: spin 1s linear infinite;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top-color: #5C7CFA;
  border-radius: 50%;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

**File:** `frontend/src/index.css` (Lines 157-161)

### Hover Glow Effect

```css
/* Default state */
box-shadow: 0 4px 12px rgba(92, 124, 250, 0.25);
transition: all 0.2s;

/* On hover */
box-shadow: 0 0 16px rgba(92, 124, 250, 0.5);
```

---

## Spacing & Layout

### Touch Targets (Mobile)

**Minimum Height:** 44px (iOS/Android guideline)

```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
}
```

### Breakpoints

| Breakpoint | Size | Usage |
|------------|------|-------|
| `sm:` | 640px | Tablets and up |
| `md:` | 768px | Small desktops |
| `lg:` | 1024px | Large desktops |

### Mobile-First Grid (Filters)

```css
/* 2-column grid on mobile */
display: grid;
grid-template-columns: repeat(2, 1fr);
gap: 0.5rem;

/* Flex on desktop */
@media (min-width: 640px) {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
```

**File:** `frontend/src/App.tsx` (Line 192)

---

## Mobile Responsiveness

### Mobile-First Layout Philosophy

EchoNote implements a **dedicated mobile layout** for devices with viewport width < 768px, providing an optimized app-like experience:

#### Key Mobile Design Principles

1. **Maximum Content Space** - No header on mobile, full-width cards
2. **Contextual Controls** - Logout footer appears only when needed (on scroll)
3. **Touch-Optimized** - All interactive elements meet 44px minimum
4. **Progressive Enhancement** - Desktop layout adds more features

### Mobile Layout Changes (< 768px)

#### 1. Header Visibility
```tsx
{/* Header hidden on mobile devices */}
{!isMobile && (
  <header className="gradient-header shadow-xl relative overflow-hidden">
    {/* Desktop header content */}
  </header>
)}
```

**Rationale:** Mobile screens need maximum vertical space for content. Logo and branding less critical on small screens.

**File:** `frontend/src/App.tsx` (Lines 193-249)

#### 2. Full-Width Content

```tsx
{/* Mobile: remove padding, desktop: maintain max-width container */}
<main className={isMobile ? "px-0 py-0" : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12"}>
```

**Components with mobile-specific styling:**

- **Recording Card**: `isMobile ? "p-6" : "p-6 sm:p-8 lg:p-10"`
- **Transcription Cards**: `isMobile ? "p-4" : "p-5 sm:p-6"`
- **Filter Card**: `isMobile ? "p-4" : "p-4 sm:p-6"`

**File:** `frontend/src/App.tsx` (Line 252)

#### 3. Mobile Footer (Scroll-Triggered)

```tsx
{/* Mobile Footer - appears on scroll */}
{isMobile && showMobileFooter && (
  <div
    className="fixed bottom-0 left-0 right-0 z-50 transition-all duration-300"
    style={{
      background: 'rgba(255, 255, 255, 0.02)',
      backdropFilter: 'blur(10px)',
      borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.3)'
    }}
  >
    <div className="px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-white">...</svg>
        <span className="text-white text-sm font-medium">{user.username}</span>
      </div>
      <button onClick={logout} className="px-4 py-2 text-sm font-semibold rounded-xl">
        Logout
      </button>
    </div>
  </div>
)}
```

**Behavior:**
- **Appears:** When user scrolls (any direction)
- **Disappears:** After 2 seconds of no scrolling
- **Styling:** Glass morphism with blur effect, fixed to bottom
- **Content:** Username and logout button

**File:** `frontend/src/App.tsx` (Lines 577-607)

#### 4. Mobile Detection Implementation

```tsx
// State
const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
const [showMobileFooter, setShowMobileFooter] = useState(false)

// Resize listener
useEffect(() => {
  const handleResize = () => {
    setIsMobile(window.innerWidth < 768)
  }
  window.addEventListener('resize', handleResize)
  return () => window.removeEventListener('resize', handleResize)
}, [])

// Scroll handler for mobile footer
useEffect(() => {
  if (!isMobile) {
    setShowMobileFooter(false)
    return
  }

  let scrollTimeout: number | undefined
  const handleScroll = () => {
    setShowMobileFooter(true)

    if (scrollTimeout !== undefined) {
      window.clearTimeout(scrollTimeout)
    }
    scrollTimeout = window.setTimeout(() => {
      setShowMobileFooter(false)
    }, 2000)
  }

  window.addEventListener('scroll', handleScroll)
  return () => {
    window.removeEventListener('scroll', handleScroll)
    if (scrollTimeout !== undefined) {
      window.clearTimeout(scrollTimeout)
    }
  }
}, [isMobile])
```

**File:** `frontend/src/App.tsx` (Lines 28-29, 37-72)

### Responsive Breakpoints

| Breakpoint | Min Width | Usage |
|------------|-----------|-------|
| **Mobile** | < 640px | Phone portrait |
| **sm** | ≥ 640px | Large phones, tablets portrait |
| **md** | ≥ 768px | Tablets landscape, desktop threshold |
| **lg** | ≥ 1024px | Desktop |
| **xl** | ≥ 1280px | Large desktop |

**Mobile threshold:** 768px (where `isMobile` = true)

### Responsive Sizing Example

```tsx
{/* Icon with responsive sizing */}
<svg className="w-7 h-7 sm:w-8 sm:h-8" style={{ color: '#5C7CFA' }}>
  {/* ... */}
</svg>

{/* Text with responsive sizing */}
<h2 className="text-2xl sm:text-3xl lg:text-4xl" style={{ color: '#E6E8EB' }}>
  EchoNote
</h2>
```

### Audio Player (Mobile Fix)

```tsx
{/* Add min-w-0 to allow flex-shrink */}
<audio className="flex-1 min-w-0 h-10 sm:h-12" controls />
```

**File:** `frontend/src/components/TranscriptionList.tsx` (Line 238)

### Testing Mobile Layout

#### Browser DevTools
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M / Cmd+Shift+M)
3. Select a mobile device or set custom width < 768px
4. Refresh page to trigger mobile detection

#### What to Test
- ✅ Header should be hidden
- ✅ All cards span full width (edge-to-edge)
- ✅ Scroll to trigger footer appearance
- ✅ Footer disappears after 2 seconds
- ✅ Logout button functional in mobile footer
- ✅ PWA sync indicator visible
- ✅ Touch targets ≥ 44px

---

## Best Practices

### Interface Design Philosophy

**Single Point of Interaction**
- The microphone button is the sole control for recording start/stop
- Eliminates decision fatigue and split focus
- Clear visual states (blue gradient = start, red = stop)
- Subtitle provides contextual guidance before action

**Why We Removed Redundant Buttons:**
- **Problem**: Having both a large microphone icon AND separate "Start Recording" / "Stop & Transcribe" buttons split user attention
- **Solution**: One clear, large, impossible-to-miss control
- **Result**: Cleaner interface, faster user decisions, less visual clutter

**Guidance Text:**
- Changed from "Click the microphone to start recording your message" to "Adjust options below, then press the microphone to start."
- Emphasizes workflow: configure first, then act
- More concise and action-oriented

### DO ✅

1. **Use glass morphism** for cards
   - `rgba(255, 255, 255, 0.04)` + `backdrop-filter: blur(8px)`

2. **Round corners generously**
   - Buttons: `1.5rem` (24px)
   - Cards: `1rem` (16px)
   - Badges: `9999px` (fully rounded)

3. **Add subtle shadows** for elevation
   - Cards: `0 4px 12px rgba(0, 0, 0, 0.4)`
   - Buttons: `0 4px 12px rgba(92, 124, 250, 0.25)`

4. **Use gradients sparingly**
   - Primary CTA buttons (like the microphone)
   - Major interactive elements only

5. **Ensure 44px minimum** for touch targets

6. **Use soft colors** over saturated
   - `#FF6B6B` not `#FF0000`
   - `#5C7CFA` not `#0000FF`

7. **Add hover glows** for premium feel
   - `box-shadow: 0 0 16px rgba(92, 124, 250, 0.5)`

8. **Maintain single primary CTA per view**
   - Avoid duplicate controls for the same action
   - Make the primary action visually dominant

### DON'T ❌

1. Don't use pure white (`#FFFFFF`) for text → Use `#E6E8EB`
2. Don't use harsh borders → Use `rgba(255, 255, 255, 0.08)`
3. Don't use flat colors everywhere → Mix gradients and glass
4. Don't forget mobile → Always test on small screens
5. Don't overuse animations → Keep them subtle
6. Don't use small touch targets → 44px minimum
7. Don't use saturated colors → Muted tones feel premium
8. Don't ignore accessibility → Maintain contrast ratios
9. Don't create redundant controls → One button per action (e.g., don't have both a microphone icon AND a "Start Recording" button)

---

## Quick Reference

### File Locations

| Component | File | Lines |
|-----------|------|-------|
| **Base Styles** | `frontend/src/index.css` | 1-200 |
| **Header** | `frontend/src/App.tsx` | 99-138 |
| **Filter Buttons** | `frontend/src/App.tsx` | 183-306 |
| **DNA Spiral Animation** | `frontend/src/components/AudioRecorder.tsx` | 401-590 |
| **Microphone Button** | `frontend/src/components/AudioRecorder.tsx` | 592-630 |
| **Transcription Cards** | `frontend/src/components/TranscriptionList.tsx` | 138-360 |

### Common Color Changes

#### Change Header Background

**Current:** `#1a1f2e` (Static Dark Gray)
**File:** `frontend/src/index.css` (Line 196)

To change the header color:
```css
.gradient-header {
  background: #your-color-here;
}
```

For a gradient instead of solid color:
```css
.gradient-header {
  background: linear-gradient(135deg, #color1, #color2);
}
```

#### Change Main Accent Color

**From:** `#5C7CFA` (Electric Iris)
**To:** Your color

Files to update:
1. `frontend/src/index.css` - Lines 47, 122, 160, 170
2. `frontend/src/App.tsx` - Lines 104, 187, 197, 339, 351
3. `frontend/src/components/AudioRecorder.tsx` - Lines 404, 450
4. `frontend/src/components/TranscriptionList.tsx` - Various

#### Change Priority Colors

**File:** `frontend/src/index.css` (Lines 138-154)

```css
/* High Priority */
.badge-high {
  background: rgba(255, 107, 107, 0.15);
  color: #FF6B6B;
  border: 1px solid rgba(255, 107, 107, 0.3);
}
```

### Rebuild After Changes

```bash
# Rebuild frontend
podman build -t localhost/echonote-frontend:latest frontend/

# Redeploy
podman kube down echonote-kube.yaml
podman kube play echonote-kube.yaml

# Wait 10 seconds, then test
curl http://localhost:5173
```

---

## Component Examples

### Complete Button with Gradient

```tsx
<button
  className="px-6 py-3 font-semibold transition-all duration-200 min-h-[44px]"
  style={{
    background: 'linear-gradient(135deg, #5C7CFA 0%, #9775FA 100%)',
    borderRadius: '1.5rem',
    boxShadow: '0 4px 12px rgba(92, 124, 250, 0.25)',
    color: 'white'
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.boxShadow = '0 0 16px rgba(92, 124, 250, 0.5)'
    e.currentTarget.style.transform = 'translateY(-1px)'
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.boxShadow = '0 4px 12px rgba(92, 124, 250, 0.25)'
    e.currentTarget.style.transform = 'translateY(0)'
  }}
>
  Primary Action
</button>
```

### Complete Glass Card

```tsx
<div
  className="p-6 sm:p-8"
  style={{
    background: 'rgba(255, 255, 255, 0.04)',
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '1rem',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)'
  }}
>
  <h3 style={{ color: '#E6E8EB' }}>Card Title</h3>
  <p style={{ color: '#9BA4B5' }}>Card description</p>
</div>
```

### Customizing DNA Spiral Animation

The DNA spiral animation is highly customizable. Here are common tweaks:

#### Change Animation Speed
```tsx
// Faster (8 seconds)
<animateMotion dur="8s" repeatCount="indefinite">

// Slower (16 seconds)
<animateMotion dur="16s" repeatCount="indefinite">
```

#### Adjust Dot Colors
```tsx
// Cold dots (currently cyan)
fill="#4ADEDE"

// Warm dot (currently amber)
fill="#F9A826"

// Try other colors:
// Electric blue: #5C7CFA
// Purple: #9775FA
// Mint green: #4ADE80
```

#### Change Glow Intensity
```tsx
// Stronger glow (current: stdDeviation="6")
<filter id="dotGlowCold">
  <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
</filter>

// Subtle glow
<filter id="dotGlowCold">
  <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
</filter>
```

#### Adjust Number of Dots
```tsx
// Add more dots to first path
{[0, 0.33, 0.66].map((offset, index) => (
  // 3 dots instead of 2
))}

// Change timing offset for different spacing
{[0, 0.25, 0.5, 0.75].map((offset, index) => (
  // 4 evenly spaced dots
))}
```

#### Change Traveling Glow Size
```tsx
// Larger glow halo (current: r="20")
<circle r="30" fill="url(#travelGlow)" opacity="0.3">

// Smaller, tighter glow
<circle r="15" fill="url(#travelGlow)" opacity="0.3">
```

#### Disable Animation (Static Lines Only)
Remove all `<circle>` elements and keep only the `<path>` elements for static DNA lines without moving dots.

---

## Version History

- **v2.0** (November 2025) - Neo-minimal dark mode redesign
- **v1.0** (2024) - Initial blue gradient design

---

**Questions or suggestions?** Update this guide as the design evolves!
