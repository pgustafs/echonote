# EchoNote Styling Guide

This guide explains how to customize the visual appearance of your EchoNote application.

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Quick Start](#quick-start)
4. [Common Customizations](#common-customizations)
5. [Color Palette Reference](#color-palette-reference)
6. [Component Breakdown](#component-breakdown)
7. [Rebuilding After Changes](#rebuilding-after-changes)

---

## Overview

EchoNote uses three styling approaches:

1. **Global CSS Classes** (`frontend/src/index.css`) - Reusable utility classes
2. **Inline Styles** (Component files) - Component-specific styling with `style={{}}` props
3. **Tailwind CSS** (Component files) - Utility-first CSS framework classes

---

## File Structure

```
frontend/src/
├── index.css                           # Global styles & utility classes
├── App.tsx                             # Main app layout, header, footer, filters
├── components/
│   ├── AudioRecorder.tsx               # Recording interface styles
│   └── TranscriptionList.tsx           # Transcription cards & list styles
└── tailwind.config.js                  # Tailwind configuration (optional customization)
```

---

## Quick Start

### Change the Main Background Color

**File:** `frontend/src/index.css` (Line 8)

```css
@layer base {
  body {
    @apply min-h-screen;
    background: #1a1a1a;  /* ← Change this color */
  }
}
```

**Example:** For a darker background
```css
background: #0a0a0a;
```

---

### Change the Button Gradient

**File:** `frontend/src/index.css` (Lines 24-30)

```css
.btn-vite {
  @apply relative overflow-hidden text-white font-semibold py-3 px-6 rounded-2xl transition-all duration-300 shadow-lg hover:scale-105;
  background: linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%);  /* ← Change this */
  box-shadow: 0 4px 20px rgba(107, 159, 237, 0.3);
}

.btn-vite:hover {
  background: linear-gradient(90deg, #5A8FDD 0%, #8B5FDD 100%);  /* ← And this */
  box-shadow: 0 6px 24px rgba(107, 159, 237, 0.4);
}
```

**Example:** Green to teal gradient
```css
background: linear-gradient(90deg, #10b981 0%, #14b8a6 100%);
```

---

### Change Card Background Colors

**File:** `frontend/src/index.css` (Lines 13-25)

```css
.glass-card {
  @apply backdrop-blur-xl border rounded-3xl shadow-2xl;
  background: rgba(42, 42, 42, 0.6);              /* ← Semi-transparent cards */
  border-color: rgba(107, 159, 237, 0.2);         /* ← Border color */
  box-shadow: 0 8px 32px 0 rgba(107, 159, 237, 0.15);
}

.glass-card-solid {
  @apply backdrop-blur-xl border rounded-3xl shadow-2xl;
  background: rgba(38, 38, 38, 0.95);             /* ← Solid cards */
  border-color: rgba(107, 159, 237, 0.25);        /* ← Border color */
  box-shadow: 0 8px 32px 0 rgba(107, 159, 237, 0.2);
}
```

**Example:** Lighter cards with purple borders
```css
.glass-card-solid {
  background: rgba(60, 60, 70, 0.95);
  border-color: rgba(168, 85, 247, 0.25);
  box-shadow: 0 8px 32px 0 rgba(168, 85, 247, 0.2);
}
```

---

## Common Customizations

### 1. Change Microphone Circle Color

**File:** `frontend/src/components/AudioRecorder.tsx` (Lines 248-252)

```tsx
style={{
  background: isRecording
    ? 'linear-gradient(135deg, #ef4444 0%, #ec4899 100%)'  // Recording (red)
    : 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)'   // Idle (blue)
}}
```

**Example:** Change idle state to green gradient
```tsx
: 'linear-gradient(90deg, #10b981 0%, #14b8a6 100%)'
```

---

### 2. Change Priority Badge Colors

**File:** `frontend/src/components/TranscriptionList.tsx` (Lines 71-82)

```tsx
const getPriorityColor = (priority: Priority): string => {
  switch (priority) {
    case 'high':
      return 'bg-red-500/80 text-white border-red-400'
    case 'medium':
      return 'bg-yellow-500/80 text-white border-yellow-400'
    case 'low':
      return 'bg-green-500/80 text-white border-green-400'
    default:
      return 'bg-slate-500/80 text-white border-slate-400'
  }
}
```

**Example:** Change high priority to orange
```tsx
case 'high':
  return 'bg-orange-500/80 text-white border-orange-400'
```

---

### 3. Change Header Logo Gradient

**File:** `frontend/src/App.tsx` (Lines 73-75)

```tsx
style={{
  background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
  boxShadow: '0 20px 40px rgba(107, 159, 237, 0.4)'
}}
```

---

### 4. Change Play Button Gradient

**File:** `frontend/src/components/TranscriptionList.tsx` (Lines 203-206)

```tsx
style={{
  background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
  boxShadow: '0 4px 20px rgba(107, 159, 237, 0.3)'
}}
```

---

### 5. Change ID Badge Gradient

**File:** `frontend/src/components/TranscriptionList.tsx` (Lines 145-148)

```tsx
style={{
  background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
  boxShadow: '0 4px 20px rgba(107, 159, 237, 0.3)'
}}
```

---

### 6. Change Filter Button Colors

**File:** `frontend/src/App.tsx` (Lines 135-165)

**"All" button (active):**
```tsx
style={priorityFilter === null ? {
  background: 'linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)',
  boxShadow: '0 4px 20px rgba(107, 159, 237, 0.3)'
} : undefined}
```

**High priority button:**
```tsx
className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
  priorityFilter === 'high'
    ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 scale-105'       // Active
    : 'bg-red-500/20 text-red-300 hover:bg-red-500/30 hover:text-red-200' // Inactive
}`}
```

---

### 7. Change Delete Button Color

**File:** `frontend/src/components/TranscriptionList.tsx` (Line 320)

```tsx
className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-xl transition-all duration-200 disabled:opacity-50 font-medium hover:scale-105"
```

**Example:** Change to orange delete button
```tsx
className="px-4 py-2 bg-orange-500/10 hover:bg-orange-500/20 text-orange-600 dark:text-orange-400 rounded-xl transition-all duration-200 disabled:opacity-50 font-medium hover:scale-105"
```

---

### 8. Change Pause/Resume Button Style

**File:** `frontend/src/index.css` (Lines 38-40)

```css
.btn-ghost {
  @apply bg-white/20 hover:bg-white/30 backdrop-blur-md border-2 border-white/50 hover:border-white/70 text-white font-semibold py-3 px-6 rounded-2xl transition-all duration-300 hover:scale-105 shadow-lg;
}
```

---

### 9. Change Stop & Transcribe Button

**File:** `frontend/src/index.css` (Lines 42-44)

```css
.btn-danger {
  @apply relative overflow-hidden bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white font-semibold py-3 px-6 rounded-2xl transition-all duration-300 shadow-lg shadow-red-500/50 hover:shadow-red-500/70 hover:scale-105;
}
```

**Example:** Change to orange gradient
```css
.btn-danger {
  @apply relative overflow-hidden bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-semibold py-3 px-6 rounded-2xl transition-all duration-300 shadow-lg shadow-orange-500/50 hover:shadow-orange-500/70 hover:scale-105;
}
```

---

### 10. Change Loading Spinner Color

**File:** `frontend/src/App.tsx` (Lines 187-188)

```tsx
<div className="absolute inset-0 rounded-full border-4" style={{ borderColor: 'rgba(107, 159, 237, 0.2)' }}></div>
<div className="absolute inset-0 rounded-full border-4 border-transparent animate-spin" style={{ borderTopColor: '#6B9FED' }}></div>
```

---

## Color Palette Reference

### Current Default Colors

| Color | Hex Code | RGBA | Usage |
|-------|----------|------|-------|
| **Primary Blue** | `#6B9FED` | `rgba(107, 159, 237, 1)` | Main gradient start, icons, borders |
| **Primary Purple** | `#9B6FED` | `rgba(155, 111, 237, 1)` | Main gradient end |
| **Background Dark** | `#1a1a1a` | `rgba(26, 26, 26, 1)` | Page background |
| **Card Dark** | - | `rgba(38, 38, 38, 0.95)` | Solid cards |
| **Card Semi** | - | `rgba(42, 42, 42, 0.6)` | Semi-transparent cards |
| **Red (High)** | `#ef4444` | - | High priority, recording state |
| **Pink** | `#ec4899` | - | Recording gradient, stop button |
| **Yellow (Medium)** | `#eab308` | - | Medium priority |
| **Green (Low)** | `#22c55e` | - | Low priority |
| **White** | `#ffffff` | - | Text, icons |
| **Slate 300** | `#cbd5e1` | - | Secondary text |

### Gradient Formulas

```css
/* Main gradient (blue to purple) */
linear-gradient(90deg, #6B9FED 0%, #9B6FED 100%)

/* Recording gradient (red to pink) */
linear-gradient(135deg, #ef4444 0%, #ec4899 100%)

/* Stop button gradient (red to pink) */
linear-gradient(to right, #ef4444, #ec4899)
```

---

## Component Breakdown

### AudioRecorder Component (`frontend/src/components/AudioRecorder.tsx`)

| UI Element | Lines | What to Change |
|------------|-------|----------------|
| Main card background | 210 | `.glass-card-solid` class |
| Microphone circle (idle) | 248-252 | Blue-purple gradient |
| Microphone circle (recording) | 248-252 | Red-pink gradient |
| Recording time indicator | 223 | `.glass-card` class |
| URL checkbox border | 279-282 | `borderColor: '#6B9FED'` |
| URL input border | 294-299 | `borderColor: 'rgba(107, 159, 237, 0.3)'` |
| Start Recording button | Uses `.btn-vite` | Edit in `index.css` |
| Pause/Resume buttons | Uses `.btn-ghost` | Edit in `index.css` |
| Stop button | Uses `.btn-danger` | Edit in `index.css` |
| Transcribing spinner | 359-367 | `.glass-card` class |

---

### TranscriptionList Component (`frontend/src/components/TranscriptionList.tsx`)

| UI Element | Lines | What to Change |
|------------|-------|----------------|
| Empty state icon circle | 89-91 | Blue-purple gradient |
| Transcription card | 138 | `.glass-card-solid` class |
| Expanded card ring | 139 | Box shadow with blue color |
| ID badge | 145-148 | Blue-purple gradient |
| Priority badges | 71-82 | `getPriorityColor()` function |
| Expand arrow background | 174-176 | `backgroundColor: 'rgba(107, 159, 237, 0.2)'` |
| Border separator | 201 | `borderColor: 'rgba(107, 159, 237, 0.2)'` |
| Play button | 203-206 | Blue-purple gradient |
| URL icon | 261 | `color: '#6B9FED'` |
| URL link | 268-277 | Text decoration color |
| File info section | 287 | `.glass-card` class |
| Priority dropdown | 309-312 | Border color |
| Priority spinner | 319 | Border color |
| Delete button | 320 | Red background/text |

---

### App Component (`frontend/src/App.tsx`)

| UI Element | Lines | What to Change |
|------------|-------|----------------|
| Header logo icon | 73-75 | Blue-purple gradient |
| Error message card | 100 | `.glass-card-solid` + red border |
| Filter section card | 124 | `.glass-card-solid` class |
| "All" filter button | 135-138 | Blue-purple gradient when active |
| High priority filter | 142-147 | Red colors |
| Medium priority filter | 148-156 | Yellow colors |
| Low priority filter | 159-167 | Green colors |
| Loading spinner | 187-188 | Blue border colors |
| Footer card | 198 | `.glass-card` class |
| Footer links | 205-232 | Blue underline colors |

---

## Rebuilding After Changes

After making any styling changes, you need to rebuild the frontend container:

### Step 1: Rebuild Frontend Container
```bash
podman build -t localhost/echonote-frontend:latest frontend/
```

### Step 2: Redeploy the Pod
```bash
podman kube down echonote-kube.yaml
podman kube play echonote-kube.yaml
```

### Step 3: Wait for Containers to Start
```bash
# Wait about 15 seconds, then check status
podman ps | grep echonote
```

You should see both containers with `(healthy)` status.

### Step 4: View Changes
Open your browser and navigate to:
```
http://localhost:5173
```

Hard refresh to clear cache: `Ctrl + Shift + R` (Linux/Windows) or `Cmd + Shift + R` (Mac)

---

## Tips & Best Practices

### 1. **Use Consistent Colors**
Keep a consistent color palette throughout the app. If you change the main blue gradient, update it in all locations for a cohesive look.

### 2. **Test with Different States**
After changing colors, test:
- Hover states
- Active/selected states
- Disabled states
- Loading states
- Empty states

### 3. **Maintain Contrast**
Ensure text remains readable on colored backgrounds. Use tools like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/).

### 4. **Keep Backups**
Before making major changes, copy the original files:
```bash
cp frontend/src/index.css frontend/src/index.css.backup
```

### 5. **Use RGBA for Transparency**
When you need semi-transparent colors, use RGBA:
```css
background: rgba(107, 159, 237, 0.2);  /* 20% opacity */
```

### 6. **Browser DevTools**
Use browser developer tools (F12) to test color changes live before editing files.

### 7. **Gradients Direction**
- `90deg` = Left to right
- `180deg` = Top to bottom
- `135deg` = Diagonal top-left to bottom-right

---

## Tailwind Color Reference

EchoNote uses Tailwind CSS. You can use these color utilities in `className` props:

```
bg-{color}-{shade}    → Background color
text-{color}-{shade}  → Text color
border-{color}-{shade}→ Border color

Colors: slate, gray, red, orange, yellow, green, blue, purple, pink
Shades: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900

Opacity: /10, /20, /30, /40, /50, /60, /70, /80, /90

Example: bg-blue-500/80 = Blue 500 with 80% opacity
```

---

## Example: Complete Theme Change (Blue → Green)

Here's how to change the entire theme from blue-purple to green-teal:

### 1. Update `index.css`
```css
.btn-vite {
  background: linear-gradient(90deg, #10b981 0%, #14b8a6 100%);
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}
```

### 2. Update `AudioRecorder.tsx` (Line 251)
```tsx
: 'linear-gradient(90deg, #10b981 0%, #14b8a6 100%)'
```

### 3. Update `App.tsx` (Line 74)
```tsx
background: 'linear-gradient(90deg, #10b981 0%, #14b8a6 100%)',
```

### 4. Update `TranscriptionList.tsx` (Line 146)
```tsx
background: 'linear-gradient(90deg, #10b981 0%, #14b8a6 100%)',
```

### 5. Update all RGBA references
Replace `rgba(107, 159, 237, ...)` with `rgba(16, 185, 129, ...)` throughout all files.

### 6. Rebuild
```bash
podman build -t localhost/echonote-frontend:latest frontend/
podman kube down echonote-kube.yaml && podman kube play echonote-kube.yaml
```

---

## Need Help?

If you encounter issues:
1. Check browser console (F12) for errors
2. Verify container logs: `podman logs echonote-frontend`
3. Ensure syntax is correct (missing commas, brackets, etc.)
4. Clear browser cache and hard refresh

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
