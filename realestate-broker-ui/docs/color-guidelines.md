# Color Usage Guidelines

This project centralizes all color usage into CSS custom properties (design tokens) defined in `app/globals.css` and exposed through helper utilities in `lib/design-tokens.ts`.

## Design Tokens

- **Brand colors** are available as CSS variables such as `--brand-teal`, `--brand-blue`, etc., with corresponding RGB helpers (for alpha usage) like `--brand-teal-rgb`.
- **Semantic colors** (backgrounds, borders, text) follow the ShadCN/Tailwind `hsl(var(--token))` convention. Use `hslColorVar('<token>')` or `colorVar('<token>')` from `lib/design-tokens.ts` to reference them in TypeScript/React files.
- **Chart palettes** should come from `chartColorPalette()` or `chartPalette` so that both light and dark themes stay in sync.

## Usage Rules

1. **Do not hardcode hex or RGB values** in components or styles. Always reference a design token or derive from one using the helpers provided.
2. **Prefer semantic tokens** (`--foreground`, `--muted-foreground`, etc.) when styling UI copy so that accessibility is maintained automatically across themes.
3. **For alpha variations**, use the pre-defined RGB variables (e.g., `rgb(var(--brand-slate-rgb) / 0.65)`) or the `hslColorVarWithAlpha` helper.
4. **PDF/Export contexts** must embed the resolved token values. Use `buildResolvedCssVariableDeclaration()` to inject the current theme into generated documents.
5. Ensure all new colors meet **WCAG AA** contrast ratios. When in doubt, reuse existing semantic tokens or consult design for new tokens before adding them.

Following these rules keeps theming consistent and makes large-scale brand updates safe and predictable.
