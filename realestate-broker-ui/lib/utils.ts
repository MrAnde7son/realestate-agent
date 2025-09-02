import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function fmtCurrency(amount: number): string {
  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function fmtNumber(num: number): string {
  return new Intl.NumberFormat('he-IL').format(num)
}

export function fmtPct(num?: number | null): string {
  if (typeof num !== 'number') return '—'
  return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`
}
