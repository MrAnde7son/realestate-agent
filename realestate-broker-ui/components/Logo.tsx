
import * as React from 'react';

type Props = {
  variant?: 'symbol' | 'horizontal';
  size?: number;
  color?: string;
  title?: string;
};

export default function Logo({ variant='symbol', size=48, color='#12b3a6', title='נדל״נר' }: Props) {
  if (variant === 'horizontal') {
    const width = size * (1200/320);
    return (
      <svg viewBox="0 0 1200 320" width={width} height={size} role="img" aria-label={title}>
        <g transform="translate(20,20)" stroke={color} strokeWidth={20} strokeLinecap="round" strokeLinejoin="round" fill="none">
          <path d="M40 0 H200 a40 40 0 0 1 40 40 V200 a40 40 0 0 1 -40 40 H40 a40 40 0 0 1 -40 -40 V40 a40 40 0 0 1 40 -40 Z" />
          <path d="M75 135 L120 80 L165 135" />
          <path d="M95 120 L120 98 L145 120" />
          <path d="M95 175 L145 175" />
        </g>
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 256 256" width={size} height={size} role="img" aria-label={title}>
      <g stroke={color} strokeWidth={18} strokeLinecap="round" strokeLinejoin="round" fill="none">
        <path d="M40 8 H216 a32 32 0 0 1 32 32 V216 a32 32 0 0 1 -32 32 H40 a32 32 0 0 1 -32 -32 V40 a32 32 0 0 1 32 -32 Z"/>
        <path d="M60 128 L128 74 L196 128"/>
        <path d="M104 136 L128 114 L152 136"/>
        <path d="M96 176 L160 176"/>
      </g>
    </svg>
  );
}
