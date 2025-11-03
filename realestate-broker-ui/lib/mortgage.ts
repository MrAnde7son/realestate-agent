// Mortgage engine for IL market – multi-track, CPI, resets, grace, APR
// All rates in percent (annual). Amounts in NIS. Months = integers.

export type TrackType =
  | 'FIXED_LINKED'        // קבועה צמודה
  | 'FIXED_UNLINKED'      // קבועה לא-צמודה
  | 'PRIME'               // פריים = BOI + 1.5 + margin
  | 'VARIABLE_BOND'       // משתנה צמודה לעוגן אג"ח
  | 'VARIABLE_BOI';       // משתנה לעוגן ריבית בנק ישראל

export type RepaymentMethod = 'ANNUITY' | 'EQUAL_PRINCIPAL';
export type GraceType = 'NONE' | 'INTEREST_ONLY' | 'FULL';

export interface TrancheInput {
  name: string;
  amount: number;                // NIS
  termMonths: number;            // 240 / 300 / 360 ...
  track: TrackType;
  // Anchor today (e.g., BOI today, GovBond(5Y) yield, Prime today)
  anchorAnnual: number;          // %
  marginAnnual: number;          // e.g., for P-0.9 => margin = -0.9
  resetEveryMonths?: number;     // for VARIABLE_* (e.g., 60)
  indexation?: 'CPI' | 'NONE';
  cpiAnnualAssumption?: number;  // % expected average CPI (e.g., 2.0)
  repayment: RepaymentMethod;    // ANNUITY (שפיצר) / EQUAL_PRINCIPAL (קרן שווה)
  graceType?: GraceType;
  graceMonths?: number;          // 0 if none
  feesUpfront?: number;          // opening fees etc.
}

export interface PortfolioInput {
  tranches: TrancheInput[];
  // For Prime math: Prime = boiAnnual + 1.5
  boiAnnual: number;             // current BOI (from API)
  primeSpread: number;           // usually 1.5 in IL
  // Stress/scenario knobs (optional)
  boiShock?: number;             // +/- in %pts applied to future resets for BOI/PRIME
  bondShock?: number;            // +/- for bond-anchored resets
  cpiShock?: number;             // +/- for CPI assumption
  monthlyIncome?: number;        // for affordability
}

export interface PaymentRow {
  month: number;
  rateMonthly: number;
  cpiMonthly: number;
  interestPortion: number;
  principalPortion: number;
  indexationAdded: number; // CPI uplift to balance
  balanceAfter: number;
  payment: number;
}

export interface TrancheResult {
  input: TrancheInput;
  schedule: PaymentRow[];
  firstPayment: number;
  maxPayment: number;
  totalPaid: number;
  totalInterest: number;
  totalIndexation: number;
  aprApprox: number; // IRR-like with fees
}

export interface PortfolioResult {
  tranches: TrancheResult[];
  blendedFirstPayment: number;
  blendedMaxPayment: number;
  blendedMonthlyAt(month: number): number;
  totals: { paid: number; interest: number; indexation: number; fees: number };
  affordability?: { ratioPct: number; ok: boolean };
}

// ---------- helpers ----------
const pctToMonthly = (annualPct: number) => (annualPct / 100) / 12;
const annuityPayment = (pv: number, r: number, n: number) =>
  r === 0 ? pv / n : pv * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);

// crude APR/IRR approx (Newton). Good enough for UI.
function irrMonthly(cashflows: number[], guess = 0.005): number {
  let r = guess;
  for (let i = 0; i < 50; i++) {
    let f = 0, df = 0;
    for (let t = 0; t < cashflows.length; t++) {
      const denom = Math.pow(1 + r, t);
      f += cashflows[t] / denom;
      df += -t * cashflows[t] / Math.pow(1 + r, t + 1);
    }
    const step = f / df;
    r -= step;
    if (Math.abs(step) < 1e-8) break;
  }
  return r;
}

// Prime & variable anchors
function effectiveAnnualRate(t: TrancheInput, month: number, env: PortfolioInput): number {
  const boi = env.boiAnnual + (env.boiShock ?? 0);
  const cBond = (t.anchorAnnual + (env.bondShock ?? 0));
  const prime = (env.boiAnnual + env.primeSpread) + (env.boiShock ?? 0);

  switch (t.track) {
    case 'PRIME':
      return prime + t.marginAnnual;
    case 'VARIABLE_BOI': {
      if (!t.resetEveryMonths) return boi + t.marginAnnual;
      const periods = Math.floor(month / t.resetEveryMonths);
      return (env.boiAnnual + (env.boiShock ?? 0)) + t.marginAnnual + 0 * periods; // flat shock for simplicity
    }
    case 'VARIABLE_BOND': {
      if (!t.resetEveryMonths) return cBond + t.marginAnnual;
      const periods = Math.floor(month / t.resetEveryMonths);
      return (t.anchorAnnual + (env.bondShock ?? 0)) + t.marginAnnual + 0 * periods;
    }
    case 'FIXED_LINKED':
    case 'FIXED_UNLINKED':
      return t.anchorAnnual + t.marginAnnual;
  }
}

function monthlyCpi(t: TrancheInput, env: PortfolioInput): number {
  const a = (t.cpiAnnualAssumption ?? 0) + (env.cpiShock ?? 0);
  return pctToMonthly(a);
}

// ---------- core amortization ----------
export function amortizeTranche(t: TrancheInput, env: PortfolioInput): TrancheResult {
  const n = t.termMonths;
  const gMonths = t.graceMonths ?? 0;
  const idx = t.indexation ?? 'NONE';
  const cpiM = idx === 'CPI' ? monthlyCpi(t, env) : 0;

  let balance = t.amount;
  const schedule: PaymentRow[] = [];
  let firstPayment = 0, maxPayment = 0;
  let totalPaid = 0, totalInt = 0, totalIdx = 0;

  // Precompute base payment for ANNUITY excluding CPI drift; we’ll recompute when rate changes.
  let currentRateM = pctToMonthly(effectiveAnnualRate(t, 0, env));
  let remaining = n;
  let annuity = t.repayment === 'ANNUITY' ? annuityPayment(balance, currentRateM, remaining - gMonths) : 0;

  for (let m = 1; m <= n; m++) {
    const monthIndex0 = m - 1;

    // Reset rate on reset boundaries
    const newAnnual = effectiveAnnualRate(t, monthIndex0, env);
    const newRateM = pctToMonthly(newAnnual);
    const rateChanged = Math.abs(newRateM - currentRateM) > 1e-10 &&
      (t.track === 'VARIABLE_BOI' || t.track === 'VARIABLE_BOND' || t.track === 'PRIME');
    if (rateChanged && t.repayment === 'ANNUITY' && m > gMonths) {
      currentRateM = newRateM;
      annuity = annuityPayment(balance, currentRateM, n - monthIndex0);
    } else {
      currentRateM = newRateM;
    }

    // Indexation: apply CPI to balance first (Israeli banks usually index monthly)
    let indexationAdded = 0;
    if (idx === 'CPI' && balance > 0) {
      indexationAdded = balance * cpiM;
      balance += indexationAdded;
      totalIdx += indexationAdded;
    }

    const interest = balance * currentRateM;

    let principal = 0, payment = 0;

    // Grace handling
    const inGrace = m <= gMonths && (t.graceType ?? 'NONE') !== 'NONE';
    if (inGrace) {
      if (t.graceType === 'INTEREST_ONLY') {
        payment = interest;
        principal = 0;
      } else { // FULL
        payment = 0;
        principal = 0;
      }
    } else {
      if (t.repayment === 'ANNUITY') {
        payment = annuity;
        principal = Math.max(0, payment - interest);
      } else { // EQUAL_PRINCIPAL
        const basePrincipal = t.amount / (n - gMonths);
        principal = basePrincipal;
        payment = principal + interest;
      }
    }

    balance = Math.max(0, balance - principal);

    if (m === 1) firstPayment = payment;
    if (payment > maxPayment) maxPayment = payment;
    totalPaid += payment;
    totalInt += interest;

    schedule.push({
      month: m,
      rateMonthly: currentRateM,
      cpiMonthly: cpiM,
      interestPortion: interest,
      principalPortion: principal,
      indexationAdded,
      balanceAfter: balance,
      payment
    });
  }

  // APR approx from cashflows (include upfront fees at t=0)
  const cfs = [-t.amount + (t.feesUpfront ?? 0) * -1, ...schedule.map(r => r.payment)];
  const apr = Math.pow(1 + irrMonthly(cfs), 12) * 100; // annual %

  return {
    input: t,
    schedule,
    firstPayment,
    maxPayment,
    totalPaid,
    totalInterest: totalInt,
    totalIndexation: totalIdx,
    aprApprox: apr
  };
}

export function pricePortfolio(env: PortfolioInput): PortfolioResult {
  const results = env.tranches.map(t => amortizeTranche(t, env));
  const blendedFirstPayment = results.reduce((s, r) => s + r.firstPayment, 0);
  const totalsPaid = results.reduce((s, r) => s + r.totalPaid, 0);
  const totalsInt = results.reduce((s, r) => s + r.totalInterest, 0);
  const totalsIdx = results.reduce((s, r) => s + r.totalIndexation, 0);
  const fees = env.tranches.reduce((s, t) => s + (t.feesUpfront ?? 0), 0);

  let blendedMaxPayment = 0;
  const maxMonths = results.reduce((m, r) => Math.max(m, r.schedule.length), 0);
  for (let monthIndex = 0; monthIndex < maxMonths; monthIndex++) {
    const totalAtMonth = results.reduce((s, r) => s + (r.schedule[monthIndex]?.payment ?? 0), 0);
    if (totalAtMonth > blendedMaxPayment) blendedMaxPayment = totalAtMonth;
  }

  const blendedMonthlyAt = (month: number) =>
    results.reduce((s, r) => s + (r.schedule[month - 1]?.payment ?? 0), 0);

  let affordability: { ratioPct: number; ok: boolean } | undefined;
  if (env.monthlyIncome) {
    const ratio = (blendedFirstPayment / env.monthlyIncome) * 100;
    affordability = { ratioPct: ratio, ok: ratio <= 30 };
  }

  return {
    tranches: results,
    blendedFirstPayment,
    blendedMaxPayment,
    blendedMonthlyAt,
    totals: { paid: totalsPaid + fees, interest: totalsInt, indexation: totalsIdx, fees },
    affordability
  };
}

// -------- BOI & Prime helpers ----------
export interface BOIRateData { baseRate: number; lastUpdated: string; }
const DEFAULT_BOI_RATE = 4.5;

export async function fetchBOIRate(): Promise<BOIRateData> {
  try {
    const res = await fetch('https://www.boi.org.il/PublicApi/GetInterest');
    const data = await res.json();
    const rate = Number(data?.currentInterest);
    const nextDate = data?.nextInterestDate ?? new Date().toISOString();
    if (Number.isFinite(rate)) return { baseRate: rate, lastUpdated: nextDate };
  } catch {}
  return { baseRate: DEFAULT_BOI_RATE, lastUpdated: new Date().toISOString() };
}

// Prime today for UI: prime = boi + primeSpread
export const calcPrime = (boiAnnual: number, primeSpread = 1.5) => boiAnnual + primeSpread;

// Additional helpers preserved from legacy utilities
export function calculateLTV(loanAmount: number, propertyValue: number): number {
  if (propertyValue === 0) return 0;
  return (loanAmount / propertyValue) * 100;
}

export function calculateAffordability(monthlyIncome: number, monthlyPayment: number): {
  ratio: number;
  isAffordable: boolean;
} {
  const ratio = monthlyIncome === 0 ? 0 : (monthlyPayment / monthlyIncome) * 100;
  const isAffordable = ratio <= 30;
  return { ratio, isAffordable };
}
