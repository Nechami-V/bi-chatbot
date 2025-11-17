import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { BarChart3, Gauge, LineChart as LineChartIcon, PieChart as PieChartIcon, Table as TableIcon } from 'lucide-react';
import { CustomTooltip } from './CustomTooltip';

type ChartType = 'line' | 'bar' | 'pie' | 'table' | 'metric';

interface InlineVisualizationProps {
  data: any[];
  type?: ChartType;
  valuePrefix?: string;
  valueSuffix?: string;
  isFullView?: boolean;
}

export function InlineVisualization({ 
  data, 
  type: initialType = 'bar',
  valuePrefix = '',
  valueSuffix = '',
  isFullView = false
}: InlineVisualizationProps) {
  const [selectedType, setSelectedType] = useState<ChartType>(initialType);
  const [primaryColor, setPrimaryColor] = useState('#8b5cf6');
  const supportsMetric = initialType === 'metric' || (Array.isArray(data) && data.length <= 1);

  const formatNumber = (value: number) => {
    try {
      return new Intl.NumberFormat('he-IL', {
        maximumFractionDigits: 2,
      }).format(value);
    } catch (error) {
      console.error('Error formatting number:', error);
      return value.toString();
    }
  };

  useEffect(() => {
    setSelectedType(initialType);
  }, [initialType]);
  
  // Debug logging
  console.log('InlineVisualization props:', { data, type: initialType, valuePrefix, valueSuffix, isFullView });
  
  // Guard: if no data, show message
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground">
        אין נתונים להצגה
      </div>
    );
  }
  
  // Convert HSL to HEX for recharts
  const hslToHex = (h: number, s: number, l: number): string => {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = (n: number) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  };
  
  // Read primary color from CSS variable
  const getPrimaryColor = (): string => {
    try {
      const root = document.documentElement;
      const primaryHSL = getComputedStyle(root).getPropertyValue('--primary').trim();
      
      if (primaryHSL) {
        // Parse HSL values (format: "262 83% 58%")
        const parts = primaryHSL.split(' ');
        if (parts.length === 3) {
          const h = parseFloat(parts[0]);
          const s = parseFloat(parts[1].replace('%', ''));
          const l = parseFloat(parts[2].replace('%', ''));
          return hslToHex(h, s, l);
        }
      }
    } catch (e) {
      console.error('Error reading primary color:', e);
    }
    return '#8b5cf6'; // fallback
  };
  
  // Update color when component mounts and when it changes
  useEffect(() => {
    const updateColor = () => {
      const newColor = getPrimaryColor();
      // Only update if color actually changed
      if (newColor !== primaryColor) {
        setPrimaryColor(newColor);
      }
    };
    
    updateColor();
    
    // Listen for custom color change event
    const handleColorChange = () => {
      updateColor();
    };
    
    window.addEventListener('primaryColorChange', handleColorChange);
    
    return () => {
      window.removeEventListener('primaryColorChange', handleColorChange);
    };
  }, [primaryColor]);
  
  // Generate color variations based on primary color
  const generateColorVariations = (baseColor: string) => {
    return [
      baseColor,
      baseColor + 'dd',
      baseColor + 'bb',
      baseColor + '99',
      baseColor + '77'
    ];
  };
  
  const COLORS = generateColorVariations(primaryColor);

  const chartTypes = [
    ...((supportsMetric || selectedType === 'metric') ? [{ type: 'metric' as ChartType, icon: Gauge, label: 'מדד' }] : []),
    { type: 'bar' as ChartType, icon: BarChart3, label: 'עמודות' },
    { type: 'line' as ChartType, icon: LineChartIcon, label: 'קו' },
    { type: 'pie' as ChartType, icon: PieChartIcon, label: 'עוגה' },
    { type: 'table' as ChartType, icon: TableIcon, label: 'טבלה' }
  ];

  const renderVisualization = () => {
    // Use 100% to fill parent container (which has aspect-ratio defined)
    const height = isFullView ? 500 : '100%';
    
    switch (selectedType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id={`colorGradient-${primaryColor}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={primaryColor} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={primaryColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.15} />
              <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '11px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} />
              <Tooltip content={<CustomTooltip valuePrefix={valuePrefix} valueSuffix={valueSuffix} />} />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke={primaryColor}
                strokeWidth={3}
                fill={`url(#colorGradient-${primaryColor})`}
                dot={{ fill: primaryColor, r: 6, strokeWidth: 0 }}
                activeDot={{ r: 8, fill: primaryColor, strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height} key={`bar-${primaryColor}`}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.15} />
              <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '11px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} />
              <Tooltip content={<CustomTooltip valuePrefix={valuePrefix} valueSuffix={valueSuffix} />} />
              <Bar dataKey="value" fill={primaryColor} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={isFullView ? 160 : 80}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip valuePrefix={valuePrefix} valueSuffix={valueSuffix} />} />
            </PieChart>
          </ResponsiveContainer>
        );
      
      case 'table':
        return (
          <div className="overflow-auto max-h-full">
            <table className="w-full text-sm border-collapse">
              <thead className="bg-muted/50 sticky top-0">
                <tr>
                  {Object.keys(data[0] || {}).map((key) => (
                    <th key={key} className="px-4 py-3 text-right border-b border-border">{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, index) => (
                  <tr 
                    key={index} 
                    className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                  >
                    {Object.values(row).map((value: any, i) => (
                      <td key={i} className="px-4 py-3 text-right">{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );

      case 'metric': {
        const metric = data[0] || { value: 0 };
        const value = typeof metric.value === 'number' ? metric.value : Number(metric.value) || 0;
        const label = metric.name || Object.keys(metric)[0] || 'ערך';
        return (
          <div className={`w-full h-full flex flex-col items-center justify-center gap-2 ${isFullView ? 'py-10' : 'py-4'}`}>
            <span className="text-sm text-muted-foreground">{label}</span>
            <span className={`font-bold text-primary ${isFullView ? 'text-6xl' : 'text-4xl'}`}>
              {valuePrefix}{formatNumber(value)}{valueSuffix}
            </span>
          </div>
        );
      }
      
      default:
        return null;
    }
  };

  return (
    <div className="w-full h-full flex flex-col overflow-auto">
      {/* Chart Type Selector - Compact, Top Right */}
      <div className="flex items-center justify-start mb-2 relative z-10 flex-shrink-0">
        <div className="flex items-center gap-0.5 bg-background/95 backdrop-blur-sm rounded-lg p-0.5 border border-border shadow-sm">
          {chartTypes.map(({ type, icon: Icon, label }) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`
                p-1.5 rounded-md transition-all
                ${selectedType === type 
                  ? 'bg-primary text-primary-foreground shadow-sm' 
                  : 'hover:bg-muted text-muted-foreground'
                }
              `}
              title={label}
            >
              <Icon className="w-3.5 h-3.5" />
            </button>
          ))}
        </div>
      </div>

      {/* Visualization */}
      <div className="flex-1 min-h-0">
        {renderVisualization()}
      </div>
    </div>
  );
}