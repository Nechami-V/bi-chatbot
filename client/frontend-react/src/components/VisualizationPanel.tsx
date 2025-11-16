import React, { useState } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Table as TableIcon } from 'lucide-react';

interface VisualizationPanelProps {
  data: any[];
  type?: 'line' | 'bar' | 'pie' | 'table';
  availableTypes?: ('line' | 'bar' | 'pie' | 'table')[];
}

export function VisualizationPanel({ 
  data, 
  type: initialType = 'bar',
  availableTypes = ['bar', 'line', 'pie', 'table']
}: VisualizationPanelProps) {
  const [selectedType, setSelectedType] = useState(initialType);

  const COLORS = ['#5b7ff5', '#60a5fa', '#818cf8', '#a78bfa', '#c084fc'];

  const renderVisualization = () => {
    switch (selectedType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#5b7ff5" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip />
              <Bar dataKey="value" fill="#5b7ff5" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      
      case 'table':
        return (
          <div className="overflow-auto h-full">
            <table className="w-full text-sm border-collapse">
              <thead className="bg-muted/50">
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
      
      default:
        return null;
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'line': return <LineChartIcon className="w-4 h-4" />;
      case 'bar': return <BarChart3 className="w-4 h-4" />;
      case 'pie': return <PieChartIcon className="w-4 h-4" />;
      case 'table': return <TableIcon className="w-4 h-4" />;
      default: return null;
    }
  };

  return (
    <div className="h-full flex flex-col bg-card border-r border-border">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
          {availableTypes.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`
                flex items-center justify-center gap-2 px-3 py-2 rounded-md flex-1 transition-all
                ${selectedType === type 
                  ? 'bg-card shadow-sm' 
                  : 'hover:bg-card/50'
                }
              `}
            >
              {getIcon(type)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 p-6">
        {renderVisualization()}
      </div>
    </div>
  );
}