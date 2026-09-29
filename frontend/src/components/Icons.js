import { Refrigerator, Wrench } from 'lucide-react';

// Lucide has no dishwasher; this one is drawn to match its 24px / 2px-stroke style.
export function DishwasherIcon({ size = 24, strokeWidth = 2, ...props }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <rect x="4" y="2" width="16" height="20" rx="2" />
      <path d="M4 7h16" />
      <path d="M7.5 4.5h.01" />
      <path d="M10.5 4.5h.01" />
      <path d="M9 11h6" />
    </svg>
  );
}

export function ApplianceIcon({ type, ...props }) {
  if (type === 'dishwasher') return <DishwasherIcon {...props} />;
  if (type === 'refrigerator') return <Refrigerator {...props} />;
  return <Wrench {...props} />;
}
