import React from 'react';

interface ChipProps {
  children: React.ReactNode;
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export function Chip({ children, icon, onClick, className = '' }: ChipProps) {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-2 px-4 py-2.5 
        rounded-full border border-border bg-card
        hover:bg-accent hover:border-accent-foreground/10
        transition-all duration-200
        ${className}
      `}
    >
      {icon && <span className="opacity-60">{icon}</span>}
      <span>{children}</span>
    </button>
  );
}
