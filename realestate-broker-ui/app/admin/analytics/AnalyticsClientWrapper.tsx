'use client'

import React, { useState } from 'react'
import dynamic from 'next/dynamic'

const AnalyticsClient = dynamic(() => import("./AnalyticsClient"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center py-12">
      <div className="text-muted-foreground">טוען נתוני אנליטיקה...</div>
    </div>
  ),
});

// Prefetch analytics charts on hover
let analyticsPrefetched = false;

interface AnalyticsClientWrapperProps {
  daily: any[]
  topFailures: any[]
}

export function AnalyticsClientWrapper({ daily, topFailures }: AnalyticsClientWrapperProps) {
  const handleMouseEnter = () => {
    if (typeof window !== 'undefined' && !analyticsPrefetched) {
      analyticsPrefetched = true;
      import("./AnalyticsClient");
    }
  };

  const handleTouchStart = () => {
    if (typeof window !== 'undefined' && !analyticsPrefetched) {
      analyticsPrefetched = true;
      import("./AnalyticsClient");
    }
  };

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onTouchStart={handleTouchStart}
    >
      <AnalyticsClient daily={daily} topFailures={topFailures} />
    </div>
  );
}

