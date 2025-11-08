import { chartColorPalette, colorVar, hslColorVarWithAlpha } from './design-tokens'

const [series1, series2, series3, series4, series5] = chartColorPalette()

export const chartPalette = {
  series1,
  series2,
  series3,
  series4,
  series5,
  area: hslColorVarWithAlpha('chart1', 0.25),
  grid: colorVar('border'),
  mutedGrid: colorVar('chip'),
}
