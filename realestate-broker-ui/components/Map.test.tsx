/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Map from './Map';

describe('Map', () => {
  it('shows placeholder when Mapbox token is missing', async () => {
    delete (process.env as any).NEXT_PUBLIC_MAPBOX_TOKEN;
    render(<Map />);
    expect(await screen.findByText(/Mapbox placeholder/)).toBeInTheDocument();
  });
});
