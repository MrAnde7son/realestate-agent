export type HexColorToken =
  | 'brandTeal'
  | 'brandTealLight'
  | 'brandTealDark'
  | 'brandSlate'
  | 'brandSlateLight'
  | 'brandSlateDark'
  | 'brandBlue'
  | 'brandGreen'
  | 'brandOrange'
  | 'brandRed'
  | 'brandGray'
  | 'text'
  | 'sub'
  | 'chip'
  | 'border'
  | 'panel';

export type HslColorToken =
  | 'background'
  | 'foreground'
  | 'card'
  | 'cardForeground'
  | 'popover'
  | 'popoverForeground'
  | 'primary'
  | 'primaryForeground'
  | 'secondary'
  | 'secondaryForeground'
  | 'muted'
  | 'mutedForeground'
  | 'accent'
  | 'accentForeground'
  | 'destructive'
  | 'destructiveForeground'
  | 'input'
  | 'ring'
  | 'success'
  | 'successForeground'
  | 'warning'
  | 'warningForeground'
  | 'error'
  | 'errorForeground'
  | 'info'
  | 'infoForeground'
  | 'chart1'
  | 'chart2'
  | 'chart3'
  | 'chart4'
  | 'chart5';

const HEX_COLOR_TOKENS: Record<HexColorToken, { cssVar: string; fallback: string }> = {
  brandTeal: { cssVar: '--brand-teal', fallback: '#12b3a6' },
  brandTealLight: { cssVar: '--brand-teal-light', fallback: '#5eead4' },
  brandTealDark: { cssVar: '--brand-teal-dark', fallback: '#0d9488' },
  brandSlate: { cssVar: '--brand-slate', fallback: '#0f172a' },
  brandSlateLight: { cssVar: '--brand-slate-light', fallback: '#475569' },
  brandSlateDark: { cssVar: '--brand-slate-dark', fallback: '#020617' },
  brandBlue: { cssVar: '--brand-blue', fallback: '#2563eb' },
  brandGreen: { cssVar: '--brand-green', fallback: '#16a34a' },
  brandOrange: { cssVar: '--brand-orange', fallback: '#ea580c' },
  brandRed: { cssVar: '--brand-red', fallback: '#dc2626' },
  brandGray: { cssVar: '--brand-gray', fallback: '#6b7280' },
  text: { cssVar: '--text', fallback: '#1f2937' },
  sub: { cssVar: '--sub', fallback: '#6b7280' },
  chip: { cssVar: '--chip', fallback: '#f3f4f6' },
  border: { cssVar: '--border', fallback: '#e5e7eb' },
  panel: { cssVar: '--panel', fallback: '#f8f9fa' }
};

const HSL_COLOR_TOKENS: Record<
  HslColorToken,
  { cssVar: string; fallback: string }
> = {
  background: { cssVar: '--background', fallback: '0 0% 100%' },
  foreground: { cssVar: '--foreground', fallback: '0 0% 3.9%' },
  card: { cssVar: '--card', fallback: '0 0% 100%' },
  cardForeground: { cssVar: '--card-foreground', fallback: '0 0% 3.9%' },
  popover: { cssVar: '--popover', fallback: '0 0% 100%' },
  popoverForeground: { cssVar: '--popover-foreground', fallback: '0 0% 3.9%' },
  primary: { cssVar: '--primary', fallback: '175 82% 39%' },
  primaryForeground: { cssVar: '--primary-foreground', fallback: '0 0% 100%' },
  secondary: { cssVar: '--secondary', fallback: '0 0% 96.1%' },
  secondaryForeground: { cssVar: '--secondary-foreground', fallback: '0 0% 9%' },
  muted: { cssVar: '--muted', fallback: '0 0% 96.1%' },
  mutedForeground: { cssVar: '--muted-foreground', fallback: '0 0% 45.1%' },
  accent: { cssVar: '--accent', fallback: '0 0% 96.1%' },
  accentForeground: { cssVar: '--accent-foreground', fallback: '0 0% 9%' },
  destructive: { cssVar: '--destructive', fallback: '0 84.2% 60.2%' },
  destructiveForeground: { cssVar: '--destructive-foreground', fallback: '0 0% 98%' },
  input: { cssVar: '--input', fallback: '0 0% 89.8%' },
  ring: { cssVar: '--ring', fallback: '0 0% 3.9%' },
  success: { cssVar: '--success', fallback: '142 76% 36%' },
  successForeground: { cssVar: '--success-foreground', fallback: '0 0% 100%' },
  warning: { cssVar: '--warning', fallback: '25 95% 53%' },
  warningForeground: { cssVar: '--warning-foreground', fallback: '0 0% 100%' },
  error: { cssVar: '--error', fallback: '0 84% 60%' },
  errorForeground: { cssVar: '--error-foreground', fallback: '0 0% 100%' },
  info: { cssVar: '--info', fallback: '213 94% 68%' },
  infoForeground: { cssVar: '--info-foreground', fallback: '0 0% 100%' },
  chart1: { cssVar: '--chart-1', fallback: '12 76% 61%' },
  chart2: { cssVar: '--chart-2', fallback: '173 58% 39%' },
  chart3: { cssVar: '--chart-3', fallback: '197 37% 24%' },
  chart4: { cssVar: '--chart-4', fallback: '43 74% 66%' },
  chart5: { cssVar: '--chart-5', fallback: '27 87% 67%' }
};

function getComputedCssValue(cssVar: string): string | undefined {
  if (typeof window === 'undefined') {
    return undefined;
  }

  const value = getComputedStyle(document.documentElement).getPropertyValue(cssVar);
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function formatHsl(value: string): string {
  if (value.startsWith('hsl')) {
    return value;
  }
  return `hsl(${value})`;
}

export function colorVar(token: HexColorToken): string {
  const { cssVar, fallback } = HEX_COLOR_TOKENS[token];
  return `var(${cssVar}, ${fallback})`;
}

export function hslColorVar(token: HslColorToken): string {
  const { cssVar, fallback } = HSL_COLOR_TOKENS[token];
  return `hsl(var(${cssVar}, ${fallback}))`;
}

export function hslColorVarWithAlpha(token: HslColorToken, alpha: number): string {
  const { cssVar, fallback } = HSL_COLOR_TOKENS[token];
  const clampedAlpha = Math.min(1, Math.max(0, alpha));
  return `hsl(var(${cssVar}, ${fallback}) / ${clampedAlpha})`;
}

export function resolveColorValue(token: HexColorToken | HslColorToken): string {
  if (token in HEX_COLOR_TOKENS) {
    const { cssVar, fallback } = HEX_COLOR_TOKENS[token as HexColorToken];
    return getComputedCssValue(cssVar) ?? fallback;
  }

  const { cssVar, fallback } = HSL_COLOR_TOKENS[token as HslColorToken];
  const resolved = getComputedCssValue(cssVar) ?? fallback;
  return formatHsl(resolved);
}

export function chartColorPalette(): string[] {
  return [
    hslColorVar('chart1'),
    hslColorVar('chart2'),
    hslColorVar('chart3'),
    hslColorVar('chart4'),
    hslColorVar('chart5')
  ];
}

export function buildCssVariableDeclaration(): string {
  const declarations = [
    ...Object.values(HEX_COLOR_TOKENS).map(({ cssVar, fallback }) => `${cssVar}: ${fallback};`),
    ...Object.values(HSL_COLOR_TOKENS).map(({ cssVar, fallback }) => `${cssVar}: ${fallback};`)
  ];

  return `:root { ${declarations.join(' ')} }`;
}

export function buildResolvedCssVariableDeclaration(): string {
  const declarations = [
    ...Object.values(HEX_COLOR_TOKENS).map(({ cssVar, fallback }) => `${cssVar}: ${getComputedCssValue(cssVar) ?? fallback};`),
    ...Object.values(HSL_COLOR_TOKENS).map(({ cssVar, fallback }) => `${cssVar}: ${getComputedCssValue(cssVar) ?? fallback};`)
  ];

  return `:root { ${declarations.join(' ')} }`;
}

export const COLOR_TOKEN_NAMES = {
  ...Object.keys(HEX_COLOR_TOKENS).reduce<Record<string, HexColorToken>>((acc, key) => {
    const tokenKey = key as HexColorToken;
    acc[tokenKey] = tokenKey;
    return acc;
  }, {}),
  ...Object.keys(HSL_COLOR_TOKENS).reduce<Record<string, HslColorToken>>((acc, key) => {
    const tokenKey = key as HslColorToken;
    acc[tokenKey] = tokenKey;
    return acc;
  }, {})
} as const;

export const PDF_THEME_STYLE_BLOCK = buildCssVariableDeclaration();
