/**
 * Color Contrast Checker
 * Analyzes design tokens for WCAG AA compliance
 */

// Convert HSL to RGB for contrast calculation
function hslToRgb(h, s, l) {
  h /= 360
  s /= 100
  l /= 100
  
  let r, g, b
  
  if (s === 0) {
    r = g = b = l
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1
      if (t > 1) t -= 1
      if (t < 1/6) return p + (q - p) * 6 * t
      if (t < 1/2) return q
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6
      return p
    }
    
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
  }
  
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
}

// Calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(val => {
    val = val / 255
    return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

// Calculate contrast ratio
function getContrastRatio(color1, color2) {
  const lum1 = getLuminance(...color1)
  const lum2 = getLuminance(...color2)
  const lighter = Math.max(lum1, lum2)
  const darker = Math.min(lum1, lum2)
  return (lighter + 0.05) / (darker + 0.05)
}

// Design tokens from globals.css (UPDATED with contrast fixes)
const lightMode = {
  background: [0, 0, 100], // hsl(0, 0%, 100%)
  foreground: [0, 0, 3.9], // hsl(0, 0%, 3.9%)
  mutedForeground: [0, 0, 45.1], // hsl(0, 0%, 45.1%)
  primary: [175, 82, 28], // hsl(175, 82%, 28%) - FIXED: darker for better contrast
  primaryForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  destructive: [0, 84.2, 48], // hsl(0, 84.2%, 48%) - FIXED: darker for better contrast
  destructiveForeground: [0, 0, 98], // hsl(0, 0%, 98%)
  success: [142, 76, 28], // hsl(142, 76%, 28%) - FIXED: darker for better contrast
  successForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  warning: [25, 95, 38], // hsl(25, 95%, 38%) - FIXED: darker for better contrast
  warningForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  error: [0, 84, 50], // hsl(0, 84%, 50%) - FIXED: darker for better contrast
  errorForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  border: [0, 0, 65], // hsl(0, 0%, 65%) - FIXED: darker for better contrast
}

const darkMode = {
  background: [0, 0, 3.9], // hsl(0, 0%, 3.9%)
  foreground: [0, 0, 98], // hsl(0, 0%, 98%)
  mutedForeground: [0, 0, 63.9], // hsl(0, 0%, 63.9%)
  primary: [175, 82, 28], // hsl(175, 82%, 28%) - FIXED: darker for better contrast
  primaryForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  destructive: [0, 62.8, 30.6], // hsl(0, 62.8%, 30.6%)
  destructiveForeground: [0, 0, 98], // hsl(0, 0%, 98%)
  success: [142, 76, 28], // hsl(142, 76%, 28%) - FIXED: darker for better contrast
  successForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  warning: [25, 95, 38], // hsl(25, 95%, 38%) - FIXED: darker for better contrast
  warningForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  error: [0, 84, 50], // hsl(0, 84%, 50%) - FIXED: darker for better contrast
  errorForeground: [0, 0, 100], // hsl(0, 0%, 100%)
  border: [0, 0, 35], // hsl(0, 0%, 35%) - FIXED: lighter for better contrast
}

function checkContrast(mode, modeName) {
  console.log(`\n=== ${modeName} Mode Contrast Check ===\n`)
  
  const issues = []
  const checks = [
    { name: 'Foreground on Background', fg: 'foreground', bg: 'background', minRatio: 4.5 },
    { name: 'Muted Foreground on Background', fg: 'mutedForeground', bg: 'background', minRatio: 4.5 },
    { name: 'Primary Foreground on Primary', fg: 'primaryForeground', bg: 'primary', minRatio: 4.5 },
    { name: 'Destructive Foreground on Destructive', fg: 'destructiveForeground', bg: 'destructive', minRatio: 4.5 },
    { name: 'Success Foreground on Success', fg: 'successForeground', bg: 'success', minRatio: 4.5 },
    { name: 'Warning Foreground on Warning', fg: 'warningForeground', bg: 'warning', minRatio: 4.5 },
    { name: 'Error Foreground on Error', fg: 'errorForeground', bg: 'error', minRatio: 4.5 },
    { name: 'Border on Background', fg: 'border', bg: 'background', minRatio: 3.0 },
  ]
  
  checks.forEach(check => {
    const fgRgb = hslToRgb(...mode[check.fg])
    const bgRgb = hslToRgb(...mode[check.bg])
    const ratio = getContrastRatio(fgRgb, bgRgb)
    const passed = ratio >= check.minRatio
    
    console.log(`${passed ? '✅' : '❌'} ${check.name}: ${ratio.toFixed(2)}:1 (min: ${check.minRatio}:1)`)
    
    if (!passed) {
      issues.push({
        check: check.name,
        ratio: ratio.toFixed(2),
        required: check.minRatio,
        fg: mode[check.fg],
        bg: mode[check.bg],
      })
    }
  })
  
  return issues
}

const lightIssues = checkContrast(lightMode, 'Light')
const darkIssues = checkContrast(darkMode, 'Dark')

console.log('\n=== Summary ===\n')
console.log(`Light Mode Issues: ${lightIssues.length}`)
console.log(`Dark Mode Issues: ${darkIssues.length}`)

if (lightIssues.length > 0 || darkIssues.length > 0) {
  console.log('\n⚠️  Some contrast ratios need adjustment for WCAG AA compliance.')
  console.log('\nRecommended fixes will be generated.')
} else {
  console.log('\n✅ All contrast ratios meet WCAG AA standards!')
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { checkContrast, getContrastRatio, hslToRgb, getLuminance }
}

