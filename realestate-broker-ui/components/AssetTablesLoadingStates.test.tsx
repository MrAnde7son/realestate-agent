// @vitest-environment jsdom
import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';

import PlansTable from './PlansTable';
import PermitsTable from './PermitsTable';
import TransactionsTable from './TransactionsTable';
import DocumentsTable from './DocumentsTable';
import DecisiveAppraisalsTable from './DecisiveAppraisalsTable';
import RamiAppraisalsTable from './RamiAppraisalsTable';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

const tables = [
  {
    name: 'PlansTable',
    renderComponent: () => render(<PlansTable data={[]} loading />),
  },
  {
    name: 'PermitsTable',
    renderComponent: () =>
      render(
        <PermitsTable
          data={[]}
          loading
          filters={{}}
        />
      ),
  },
  {
    name: 'TransactionsTable',
    renderComponent: () => render(<TransactionsTable data={[]} loading />),
  },
  {
    name: 'DocumentsTable',
    renderComponent: () => render(<DocumentsTable data={[]} loading />),
  },
  {
    name: 'DecisiveAppraisalsTable',
    renderComponent: () => render(<DecisiveAppraisalsTable data={[]} loading />),
  },
  {
    name: 'RamiAppraisalsTable',
    renderComponent: () => render(<RamiAppraisalsTable data={[]} loading />),
  },
];

describe('Asset detail table loading states', () => {
  tables.forEach(({ name, renderComponent }) => {
    it(`${name} exposes busy state and skeleton rows while loading`, () => {
      const { container } = renderComponent();
      const busyContainer = container.querySelector('[aria-busy="true"]');
      expect(busyContainer).toBeTruthy();

      const skeletonRows = busyContainer?.querySelectorAll('[data-testid="table-skeleton-row"]');
      expect(skeletonRows && skeletonRows.length).toBeGreaterThan(0);
    });
  });

  it('clears busy state once loading completes', () => {
    const { container, rerender } = render(<PlansTable data={[]} loading />);
    expect(container.querySelector('[aria-busy="true"]')).toBeTruthy();

    rerender(<PlansTable data={[]} loading={false} />);
    const tableContainer = container.querySelector('[aria-busy]');
    expect(tableContainer).toBeTruthy();
    expect(tableContainer).toHaveAttribute('aria-busy', 'false');
  });
});
