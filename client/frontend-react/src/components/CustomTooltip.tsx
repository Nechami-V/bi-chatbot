import React from 'react';

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  valuePrefix?: string;
  valueSuffix?: string;
}

export function CustomTooltip({ 
  active, 
  payload, 
  label,
  valuePrefix = '',
  valueSuffix = ''
}: CustomTooltipProps) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const value = payload[0].value;

  return (
    <div className="bg-card border border-border rounded-xl px-4 py-3 shadow-lg">
      <p className="text-sm text-muted-foreground mb-1">{label}</p>
      <p className="font-medium">
        {valuePrefix}{value}{valueSuffix}
      </p>
    </div>
  );
}
