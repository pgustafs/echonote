# EchoNote Styling Guide
**Version:** 3.0 - 2025 Theme System
**Last Updated:** November 2025
**Design Language:** Borderless, Shadow-Free, Theme-Aware

---

## Table of Contents

1. [Overview](#overview)
2. [Theme Architecture](#theme-architecture)
3. [Color Palette](#color-palette)
4. [Component Classes](#component-classes)
5. [Usage Guidelines](#usage-guidelines)
6. [Migration Guide](#migration-guide)
7. [Quick Reference](#quick-reference)

---

## Overview

EchoNote uses a modern **2025 design system** with full dark/light theme support. Key principles:

✅ **No borders** (or minimal 5-8% opacity strokes)
✅ **No shadows**
✅ **Opacity-based elevation**
✅ **AI-first accent colors** (mint/cyan trending)
✅ **Theme-aware** (dark/light mode)
✅ **Tailwind CSS** (no inline styles)

---

## Theme Architecture

### CSS Custom Properties

All colors are defined as CSS variables in `frontend/src/index.css`:

```css
/* Dark Theme (Default) */
:root {
  --color-bg: #0B0B0D;
  --color-bg-secondary: #111113;
  --color-bg-tertiary: #1A1A1C;
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #A7A7AA;
  --color-text-tertiary: #6F6F73;
  --color-icon: #D8D8DB;
  --color-stroke-subtle: rgba(255, 255, 255, 0.05);
  --color-accent-blue: #3A7BFF;
  --color-accent-violet: #B48CFF;
  --color-accent-mint: #72F1C4;
  --color-ai-button: #72F1C4;
  --color-ai-button-hover: #5BDDAE;
  --color-ai-button-text: #0B0B0D;
}

/* Light Theme */
.light {
  --color-bg: #FBFBFD;
  --color-bg-secondary: #F3F3F6;
  --color-bg-tertiary: #EAEAED;
  --color-text-primary: #0B0B0D;
  --color-text-secondary: #5E5E63;
  --color-text-tertiary: #8A8A90;
  --color-icon: #4F4F55;
  --color-stroke-subtle: rgba(0, 0, 0, 0.08);
  --color-accent-blue: #3A7BFF;
  --color-accent-violet: #B48CFF;
  --color-accent-mint: #16C39A;
  --color-ai-button: #16C39A;
  --color-ai-button-hover: #0FAE87;
  --color-ai-button-text: #FFFFFF;
}
```

### Tailwind Integration

Tailwind config (`tailwind.config.js`) maps CSS variables to utility classes:

```javascript
colors: {
  bg: {
    DEFAULT: 'var(--color-bg)',
    secondary: 'var(--color-bg-secondary)',
    tertiary: 'var(--color-bg-tertiary)',
  },
  text: {
    primary: 'var(--color-text-primary)',
    secondary: 'var(--color-text-secondary)',
    tertiary: 'var(--color-text-tertiary)',
  },
  icon: {
    DEFAULT: 'var(--color-icon)',
  },
  stroke: {
    subtle: 'var(--color-stroke-subtle)',
  },
  accent: {
    blue: 'var(--color-accent-blue)',
    violet: 'var(--color-accent-violet)',
    mint: 'var(--color-accent-mint)',
  },
  ai: {
    DEFAULT: 'var(--color-ai-button)',
    hover: 'var(--color-ai-button-hover)',
    text: 'var(--color-ai-button-text)',
  },
}
```

### Theme Context

React context manages theme state:

```tsx
import { useTheme } from './contexts/ThemeContext'

function MyComponent() {
  const { theme, toggleTheme, setTheme } = useTheme()
  // theme = 'dark' | 'light'

  return (
    <button onClick={toggleTheme}>
      {theme === 'dark' ? <Sun /> : <Moon />}
    </button>
  )
}
```

**Files:**
- Context: `frontend/src/contexts/ThemeContext.tsx`
- Provider: `frontend/src/main.tsx`

---

## Color Palette

### Background Colors

| Token | Dark | Light | Tailwind Class |
|-------|------|-------|----------------|
| Primary | `#0B0B0D` | `#FBFBFD` | `bg-bg` |
| Secondary | `#111113` | `#F3F3F6` | `bg-bg-secondary` |
| Tertiary | `#1A1A1C` | `#EAEAED` | `bg-bg-tertiary` |

### Text Colors

| Token | Dark | Light | Tailwind Class |
|-------|------|-------|----------------|
| Primary | `#FFFFFF` | `#0B0B0D` | `text-text-primary` |
| Secondary | `#A7A7AA` | `#5E5E63` | `text-text-secondary` |
| Tertiary | `#6F6F73` | `#8A8A90` | `text-text-tertiary` |

### Accent Colors

| Token | Dark | Light | Tailwind Class | Usage |
|-------|------|-------|----------------|-------|
| Blue | `#3A7BFF` | `#3A7BFF` | `accent-blue` | Primary actions |
| Violet | `#B48CFF` | `#B48CFF` | `accent-violet` | Secondary accents |
| Mint | `#72F1C4` | `#16C39A` | `accent-mint` | AI features |

### AI Button (Trending 2025)

| Token | Dark | Light | Tailwind Class |
|-------|------|-------|----------------|
| Background | `#72F1C4` | `#16C39A` | `bg-ai` |
| Hover | `#5BDDAE` | `#0FAE87` | `bg-ai-hover` |
| Text | `#0B0B0D` | `#FFFFFF` | `text-ai-text` |

**Why Mint/Cyan?**
This color immediately signals AI, automation, and smart features. Used by OpenAI, Notion AI, Midjourney, Perplexity. High contrast without looking "salesy".

### Semantic Colors

| Token | Value | Tailwind Class |
|-------|-------|----------------|
| Success | `#16C39A` | `text-success` |
| Warning | `#F59E0B` | `text-warning` |
| Error | `#EF4444` | `text-error` |

---

## Component Classes

### Buttons

#### Primary Button
```html
<button className="btn-primary">
  Click me
</button>
```

- Background: 4% white/black opacity
- Text: theme-aware primary
- No border, no shadow
- Hover: 5% opacity + translateY(-1px)

#### AI Button ⭐ (Recommended for AI features)
```html
<button className="btn-ai">
  Generate with AI
</button>
```

- Background: Mint/cyan (`#72F1C4` / `#16C39A`)
- High contrast, attention-grabbing
- Perfect for AI actions

#### Other Button Variants
```html
<button className="btn-secondary">Secondary</button>
<button className="btn-accent-blue">Accent</button>
<button className="btn-danger">Delete</button>
<button className="btn-success">Confirm</button>
<button className="btn-ghost">Subtle</button>
<button className="icon-button"><Icon /></button>
```

**File:** `frontend/src/index.css` (Lines 92-222)

### Form Inputs

#### Text Input / Textarea
```html
<input type="text" className="input-field" placeholder="Enter text" />
<textarea className="input-field" rows="3"></textarea>
```

- Background: Theme-aware opacity
- Border: Subtle stroke
- Focus: Blue accent ring
- Auto-adapts to dark/light

#### Select Dropdown
```html
<select className="select-field">
  <option>Option 1</option>
</select>
```

#### Checkbox
```html
<input type="checkbox" className="checkbox-field" />
```

**File:** `frontend/src/index.css` (Lines 224-294)

### Cards

#### Basic Card
```html
<div className="card">
  Content here
</div>
```

- Background: `bg-secondary`
- Rounded: 12px (`rounded-card`)
- No border, no shadow

#### Interactive Card
```html
<div className="card-interactive">
  Clickable content
</div>
```

- Adds hover state
- Transitions to `bg-tertiary`

**File:** `frontend/src/index.css` (Lines 296-317)

### Modals & Drawers

```html
<!-- Modal overlay -->
<div className="modal-overlay" />

<!-- Modal content -->
<div className="modal-content">
  <!-- Your content -->
</div>

<!-- Drawer (glass effect) -->
<div className="drawer-glass">
  <!-- Drawer content -->
</div>
```

**File:** `frontend/src/index.css` (Lines 319-341)

### Alerts

```html
<div className="alert-error">
  <div className="flex items-start gap-3">
    <svg className="w-5 h-5 text-error">...</svg>
    <div>
      <p className="alert-error-title">Error</p>
      <p className="alert-error-text">Something went wrong</p>
    </div>
  </div>
</div>
```

**File:** `frontend/src/index.css` (Lines 364-383)

### Badges

```html
<span className="badge badge-high">High Priority</span>
<span className="badge badge-medium">Medium Priority</span>
<span className="badge badge-low">Low Priority</span>
```

**File:** `frontend/src/index.css` (Lines 343-362)

### Loading Spinner

```html
<div className="spinner w-12 h-12"></div>
```

**File:** `frontend/src/index.css` (Lines 387-392)

---

## Usage Guidelines

### ✅ DO

1. **Use Tailwind theme classes**
   ```jsx
   <h1 className="text-text-primary">Title</h1>
   <p className="text-text-secondary">Description</p>
   <div className="bg-bg-secondary">Card</div>
   ```

2. **Use standardized button classes**
   ```jsx
   <button className="btn-ai">AI Action</button>
   <button className="btn-primary">Submit</button>
   ```

3. **Use standardized radii**
   ```jsx
   <button className="rounded-button">Button</button>
   <div className="rounded-card">Card</div>
   <div className="rounded-modal">Modal</div>
   ```

4. **Leverage hover states via Tailwind**
   ```jsx
   <a className="text-accent-blue hover:text-accent-mint transition-colors">
     Link
   </a>
   ```

5. **Use the ThemeContext**
   ```jsx
   import { useTheme } from '../contexts/ThemeContext'

   const { theme, toggleTheme } = useTheme()
   ```

### ❌ DON'T

1. **Don't use inline styles for colors**
   ```jsx
   // ❌ Bad
   <div style={{ color: '#E6E8EB', background: '#111113' }}>Text</div>

   // ✅ Good
   <div className="text-text-primary bg-bg-secondary">Text</div>
   ```

2. **Don't use hardcoded hex colors**
   ```jsx
   // ❌ Bad
   <div className="bg-[#111113] text-[#E6E8EB]">Content</div>

   // ✅ Good
   <div className="bg-bg-secondary text-text-primary">Content</div>
   ```

3. **Don't use onMouseEnter/onMouseLeave for colors**
   ```jsx
   // ❌ Bad
   <button
     onMouseEnter={(e) => e.currentTarget.style.color = '#4ADEDE'}
     onMouseLeave={(e) => e.currentTarget.style.color = '#5C7CFA'}
   >

   // ✅ Good
   <button className="text-accent-blue hover:text-accent-mint transition-colors">
   ```

4. **Don't add borders or shadows (2025 trend)**
   ```jsx
   // ❌ Bad
   <div className="shadow-lg border border-gray-300">

   // ✅ Good
   <div className="card">
   ```

---

## Migration Guide

### From Old System to New

| Old | New |
|-----|-----|
| `style={{ color: '#E6E8EB' }}` | `className="text-text-primary"` |
| `style={{ color: '#9BA4B5' }}` | `className="text-text-secondary"` |
| `style={{ color: '#6F6F73' }}` | `className="text-text-tertiary"` |
| `style={{ background: 'rgba(255,255,255,0.04)' }}` | `className="card"` |
| `className="bg-white/10"` | `className="card"` |
| `className="enterprise-card-dark"` | `className="card"` |
| `className="input-field-dark"` | `className="input-field"` |
| `className="select-dark"` | `className="select-field"` |
| `className="checkbox-dark"` | `className="checkbox-field"` |

### Example Migration

**Before:**
```jsx
<div style={{
  background: 'rgba(255, 255, 255, 0.04)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: '1rem',
  padding: '1rem'
}}>
  <h2 style={{ color: '#E6E8EB' }}>Title</h2>
  <p style={{ color: '#9BA4B5' }}>Description</p>
</div>
```

**After:**
```jsx
<div className="card p-4">
  <h2 className="text-text-primary">Title</h2>
  <p className="text-text-secondary">Description</p>
</div>
```

---

## Theme Toggle Implementation

### Desktop (Header)

```jsx
import { useTheme } from '../contexts/ThemeContext'
import { Sun, Moon } from 'lucide-react'

function Header() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button onClick={toggleTheme} className="icon-button">
      {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  )
}
```

**File:** `frontend/src/App.tsx` (Lines 315-327)

### Mobile (Bottom Nav)

```jsx
import { useTheme } from '../contexts/ThemeContext'
import { Sun, Moon } from 'lucide-react'

function BottomNav() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button onClick={toggleTheme} className="flex flex-col items-center gap-1">
      {theme === 'dark' ? (
        <Sun size={24} className="text-icon" />
      ) : (
        <Moon size={24} className="text-icon" />
      )}
      <span className="text-xs text-text-primary">Theme</span>
    </button>
  )
}
```

**File:** `frontend/src/components/BottomNav.tsx` (Lines 31-44)

---

## Quick Reference

### File Structure

```
frontend/
├── src/
│   ├── contexts/
│   │   └── ThemeContext.tsx        # Theme provider & hook
│   ├── main.tsx                    # ThemeProvider integration
│   ├── index.css                   # CSS custom properties + component classes
│   └── components/
│       ├── Login.tsx               # Theme-aware login
│       ├── App.tsx                 # Theme toggle (desktop)
│       ├── BottomNav.tsx           # Theme toggle (mobile)
│       ├── AIChat.tsx              # AI chat with theme
│       ├── AIResultModal.tsx       # AI result modal
│       └── ...
└── tailwind.config.js              # Tailwind theme config
```

### Border Radius Standards

| Class | Value | Usage |
|-------|-------|-------|
| `rounded-button` | 10px | All buttons |
| `rounded-card` | 12px | Cards, containers |
| `rounded-modal` | 16px | Modals, overlays |

### Opacity Standards

| Purpose | Dark Mode | Light Mode |
|---------|-----------|------------|
| Hover layer | 5% white | 6% black |
| Active layer | 10% white | 12% black |
| Card background | 4% white | 4% black |
| Disabled state | 40% opacity | 40% opacity |

### Testing Themes

**Via Browser Console:**
```javascript
document.documentElement.classList.toggle('light')
```

**Via UI:**
- Desktop: Click Sun/Moon icon in header (top-right)
- Mobile: Tap "Theme" button in bottom nav

---

## Component-Specific Guidelines

### Login Page
- Use `.card` for login form container
- Use `.input-field` for all inputs
- Use `.btn-accent-blue` for submit button
- Add theme toggle in top-right corner

### AI Components
- Use `.btn-ai` for all AI action triggers
- Use `.drawer-glass` for modals/drawers
- Use `.alert-error` for error states
- Use `.spinner` for loading states

### Cards & Lists
- Use `.card` for all cards
- Use `.badge-high`, `.badge-medium`, `.badge-low` for priority
- Theme-aware text colors automatically

---

## FAQ

**Q: Can I add custom colors?**
A: Yes, extend the theme in `tailwind.config.js` and `index.css` CSS variables. Don't use inline styles.

**Q: What about animations?**
A: Use Tailwind's `transition-*` utilities. Avoid custom keyframes unless necessary.

**Q: Can I use shadows?**
A: Avoid shadows per 2025 design trends. Use opacity-based elevation instead.

**Q: How do I debug theme issues?**
A: Check DevTools → Computed styles to see which CSS custom properties are applied.

**Q: Why isn't my theme switching?**
A: Ensure ThemeProvider wraps your app in `main.tsx` and you're using theme classes, not hardcoded colors.

---

## Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [2025 Design Trends](https://www.figma.com/community)

---

**Last Updated:** 2025-11-28
**Version:** 3.0 (2025 Theme System)
**Maintained by:** EchoNote Team
