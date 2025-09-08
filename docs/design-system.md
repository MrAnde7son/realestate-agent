# Design System - Nadlaner

## Overview

This document outlines the design system for Nadlaner, a real estate intelligence platform. The design system is built on Tailwind CSS with custom design tokens and follows RTL-first principles for Hebrew content.

## Design Tokens

### Colors

#### Primary Palette
```css
/* Brand Colors */
--brand-teal: #12b3a6;           /* Primary brand color */
--brand-slate: #0f172a;          /* Dark text/backgrounds */
--brand-blue: #2563eb;           /* Secondary actions */
--brand-green: #16a34a;          /* Success states */
--brand-orange: #ea580c;         /* Warning states */
--brand-red: #dc2626;            /* Error states */
```

#### Semantic Colors
```css
/* Light Mode */
--background: 0 0% 100%;         /* Page background */
--foreground: 0 0% 3.9%;         /* Primary text */
--muted: 0 0% 96.1%;             /* Muted backgrounds */
--muted-foreground: 0 0% 45.1%;  /* Muted text */
--border: 0 0% 89.8%;            /* Borders */
--input: 0 0% 89.8%;             /* Input borders */
--ring: 0 0% 3.9%;               /* Focus rings */

/* Dark Mode */
--background: 0 0% 3.9%;         /* Page background */
--foreground: 0 0% 98%;          /* Primary text */
--muted: 0 0% 14.9%;             /* Muted backgrounds */
--muted-foreground: 0 0% 63.9%;  /* Muted text */
--border: 0 0% 14.9%;            /* Borders */
--input: 0 0% 14.9%;             /* Input borders */
--ring: 0 0% 83.1%;              /* Focus rings */
```

### Typography

#### Font Families
```css
--font-sans: 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif';
--font-hebrew: 'Noto Sans Hebrew', 'Arial Hebrew', sans-serif;
```

#### Font Sizes
```css
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */
```

#### Line Heights
```css
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### Spacing Scale

```css
--space-1: 0.25rem;      /* 4px */
--space-2: 0.5rem;       /* 8px */
--space-3: 0.75rem;      /* 12px */
--space-4: 1rem;         /* 16px */
--space-5: 1.25rem;      /* 20px */
--space-6: 1.5rem;       /* 24px */
--space-8: 2rem;         /* 32px */
--space-10: 2.5rem;      /* 40px */
--space-12: 3rem;        /* 48px */
--space-16: 4rem;        /* 64px */
--space-20: 5rem;        /* 80px */
--space-24: 6rem;        /* 96px */
```

### Border Radius

```css
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
--radius-full: 9999px;   /* Fully rounded */
```

### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

### Z-Index Scale

```css
--z-dropdown: 1000;
--z-sticky: 1020;
--z-fixed: 1030;
--z-modal-backdrop: 1040;
--z-modal: 1050;
--z-popover: 1060;
--z-tooltip: 1070;
--z-toast: 1080;
```

## Component Library

### Button

#### Variants
- `default`: Primary action button
- `destructive`: Delete/dangerous actions
- `outline`: Secondary actions
- `secondary`: Tertiary actions
- `ghost`: Subtle actions
- `link`: Text links

#### Sizes
- `sm`: Small buttons (h-8)
- `default`: Standard buttons (h-9)
- `lg`: Large buttons (h-10)
- `icon`: Icon-only buttons (size-9)

#### RTL Considerations
- Icons positioned with `ms-` and `me-` utilities
- Text alignment respects RTL direction
- Focus states work in both directions

### Card

#### Variants
- `default`: Standard card with border
- `elevated`: Card with shadow
- `outlined`: Card with prominent border
- `ghost`: Card with no border

#### Structure
- `Card`: Container
- `CardHeader`: Title and description area
- `CardContent`: Main content area
- `CardFooter`: Action area

### Badge

#### Variants
- `default`: Neutral information
- `success`: Positive states
- `warning`: Caution states
- `error`: Error states
- `info`: Informational states

### Input

#### States
- `default`: Normal state
- `focus`: Focused state with ring
- `error`: Error state with red border
- `disabled`: Disabled state

#### RTL Considerations
- Placeholder text right-aligned
- Icons positioned correctly for RTL
- Validation messages appear on correct side

### Table

#### Features
- Responsive design with horizontal scroll
- RTL-aware column alignment
- Sortable headers
- Row selection
- Sticky columns for important data

#### RTL Considerations
- Column headers right-aligned
- Data cells respect content type
- Sort indicators positioned correctly

## RTL Implementation

### Layout Direction
- All components respect `dir="rtl"`
- Flexbox and grid layouts use logical properties
- Spacing uses `ms-` and `me-` utilities

### Icon Positioning
- Icons use logical positioning
- Chevron icons mirror for RTL
- Action icons positioned consistently

### Text Alignment
- Hebrew text right-aligned by default
- Numbers and English text can be left-aligned
- Mixed content handled gracefully

## Dark Mode

### Implementation
- CSS custom properties for theme switching
- Automatic system preference detection
- Manual toggle available

### Color Adjustments
- All colors have dark mode variants
- Contrast ratios maintained
- Brand colors adapted for dark backgrounds

## Accessibility

### Keyboard Navigation
- All interactive elements keyboard accessible
- Logical tab order
- Focus indicators visible
- Escape key closes modals

### Screen Readers
- Proper ARIA labels
- Semantic HTML structure
- Live regions for dynamic content
- Descriptive alt text

### Color Contrast
- WCAG AA compliance
- High contrast mode support
- Color not the only indicator

## Usage Examples

### Basic Button
```tsx
<Button variant="default" size="lg">
  <Plus className="h-4 w-4" />
  הוסף נכס
</Button>
```

### Card with Content
```tsx
<Card>
  <CardHeader>
    <CardTitle>פרטי נכס</CardTitle>
    <CardDescription>מידע מפורט על הנכס</CardDescription>
  </CardHeader>
  <CardContent>
    <p>תוכן הכרטיס</p>
  </CardContent>
</Card>
```

### Form Input
```tsx
<div className="space-y-2">
  <Label htmlFor="address">כתובת</Label>
  <Input
    id="address"
    placeholder="הזן כתובת"
    className="text-right"
  />
</div>
```

## Migration Guide

### From Current Implementation
1. Replace hardcoded colors with CSS variables
2. Update spacing to use design tokens
3. Standardize component variants
4. Add RTL utilities where missing
5. Implement proper focus states

### Breaking Changes
- Some color values may change
- Spacing scale is more systematic
- Component APIs may be simplified
- RTL behavior may be more strict

## Future Enhancements

### Planned Features
- Animation system
- Advanced theming
- Component variants
- Design tokens for motion
- Advanced RTL features

### Considerations
- Performance impact of design tokens
- Bundle size optimization
- Browser compatibility
- Mobile-specific adaptations
