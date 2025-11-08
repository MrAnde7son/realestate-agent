# Card design guidelines

This project exposes a shared `Card` component under `@/components/ui/Card`. Cards support a
single layout API for rendering headings, content, and footers while enforcing consistent visual
hierarchy across the application.

## Variants

| Variant   | Visual treatment                               | Recommended usage                         |
|-----------|-------------------------------------------------|-------------------------------------------|
| `default` | Subtle shadow with a light border and blur.     | Dashboards, list containers, summaries.   |
| `elevated`| Stronger shadow with a softer border treatment. | Featured widgets and highlighted assets.  |
| `outlined`| Two-pixel border with no shadow.                | Nested cards and secondary groupings.     |

Use the `variant` prop instead of custom `className` overrides for elevation. When additional
interaction feedback is required (for example, clickable cards), pass the `interactive` prop to
apply shared hover and focus states.

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

<Card variant="elevated" interactive>
  <CardHeader>
    <CardTitle>Featured listing</CardTitle>
  </CardHeader>
  <CardContent>
    Card body content
  </CardContent>
</Card>
```

The exported `cardVariants` helper can be used for advanced styling scenarios (such as styling
`asChild` wrappers) while keeping the same visual vocabulary.
