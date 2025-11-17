import React, { useState } from 'react';
import { Sparkles, Download, Save, Code, Maximize2, Database, FileSpreadsheet, FileText, ChevronDown, X, Copy } from 'lucide-react';
import image_94c3dac261df590bf85ea3a5c2b28e9b3ed2ea33 from 'figma:asset/94c3dac261df590bf85ea3a5c2b28e9b3ed2ea33.png';
import KTLogo from '../assets/kt-logo.png';
import { copyToClipboard } from '../utils/clipboard';

// Export Dropdown Component
function ExportDropdown({ isAnalyticsExpanded, onExport, data }: { isAnalyticsExpanded: boolean; onExport?: (format: 'pdf' | 'excel' | 'csv') => void; data?: any[] }) {
  const [isOpen, setIsOpen] = useState(false);

  const handleExport = (format: 'csv' | 'excel') => {
    onExport?.(format);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-background border border-border hover:border-primary/50 hover:bg-primary/5 transition-all ${isAnalyticsExpanded ? 'px-2' : ''}`}
        title="ייצוא"
      >
        <Download className="w-4 h-4" />
        {!isAnalyticsExpanded && (
          <>
            <span>ייצוא</span>
            <ChevronDown className="w-3 h-3" />
          </>
        )}
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown Menu */}
          <div className="absolute left-0 top-full mt-1 bg-background border border-border rounded-lg shadow-lg py-1 min-w-[120px] z-20">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleExport('csv');
              }}
              className="w-full px-4 py-2 text-sm hover:bg-muted transition-colors text-right"
            >
              CSV
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleExport('excel');
              }}
              className="w-full px-4 py-2 text-sm hover:bg-muted transition-colors text-right"
            >
              Excel
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface ChatBubbleProps {
  type: 'user' | 'ai';
  message: string;
  isThinking?: boolean;
  visualization?: React.ReactNode;
  visualizationData?: any[]; // Raw data for export
  userName?: string;
  hasVisualization?: boolean;
  onExpandChart?: () => void;
  isActive?: boolean;
  onClick?: () => void;
  showActions?: boolean;
  onInsights?: () => void;
  onSaveQuery?: () => void;
  onExport?: (format: 'pdf' | 'excel' | 'csv') => void;
  onShowSQL?: () => void;
  showSQL?: boolean;
  isAnalyticsExpanded?: boolean;
  sql?: string;
}

export function ChatBubble({ 
  type, 
  message, 
  isThinking = false, 
  visualization,
  visualizationData,
  userName = 'משתמש',
  hasVisualization = false,
  onExpandChart,
  isActive = false,
  onClick,
  showActions = false,
  onInsights,
  onSaveQuery,
  onExport,
  onShowSQL,
  showSQL,
  isAnalyticsExpanded = false,
  sql
}: ChatBubbleProps) {
  const isUser = type === 'user';
  
  // Format AI message with better typography
  const formatMessage = (text: string) => {
    const lines = text.split('\\n');
    return lines.map((line, index) => {
      // Check if line is a bullet point
      if (line.trim().startsWith('•')) {
        return (
          <div key={index} className="flex gap-2 mr-2">
            <span className="text-primary">•</span>
            <span>{line.trim().substring(1).trim()}</span>
          </div>
        );
      }
      
      // Check if line contains important data (numbers, percentages)
      const highlightedLine = line.replace(
        /(\\d+%|\\d+\\$|\\d+[,.\\d]*)/g,
        '<strong class="text-foreground">$1</strong>'
      );
      
      return (
        <p 
          key={index} 
          className={line.trim() === '' ? 'h-2' : ''}
          dangerouslySetInnerHTML={{ __html: highlightedLine }}
        />
      );
    });
  };
  
  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex gap-3 ${isUser ? 'max-w-[65%]' : 'w-full'}`}>
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center mt-1">
            <span className="text-primary-foreground text-xs font-semibold">BI</span>
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div
            className={`
              rounded-2xl transition-all overflow-visible
              ${isUser 
                ? 'bg-primary/10 text-primary px-3 py-2' 
                : 'bg-card border border-border'
              }
              ${isActive && !isUser ? 'ring-2 ring-primary/50 border-primary/50 shadow-lg' : ''}
              ${!isUser && hasVisualization ? 'cursor-pointer hover:border-primary/30' : ''}
            `}
            onClick={!isUser && hasVisualization ? onClick : undefined}
          >
            {isThinking ? (
              <div className="flex items-center gap-2 px-5 py-3.5">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-muted-foreground">בודק בנתונים שלך...</span>
              </div>
            ) : (
              <>
                {/* Content with side-by-side layout for visualization */}
                {visualization ? (
                  <div className="flex flex-col lg:flex-row gap-4 p-5">
                    {/* Mini Chart - Top on mobile, Left side on desktop, 1/3 width */}
                    <div className="w-full lg:w-1/3 lg:order-2 flex-shrink-0 relative">
                      {/* Mini Chart Container - with aspect ratio and rounded background */}
                      <div className="relative w-full rounded-xl bg-muted/30 border border-border/50 overflow-auto" style={{ aspectRatio: '4/3' }}>
                        {/* Expand Icon */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onExpandChart?.();
                          }}
                          className="absolute top-2 left-2 z-20 p-1.5 rounded-lg bg-background/95 backdrop-blur-sm border border-border hover:bg-primary/10 hover:border-primary/50 transition-all shadow-md group"
                          title="הרחבת גרף"
                        >
                          <Maximize2 className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </button>

                        {/* Content layer - absolute positioning to fill container */}
                        <div className="absolute inset-0 p-3">
                          {visualization}
                        </div>
                      </div>
                    </div>
                    
                    {/* Text content - Bottom on mobile, Right side on desktop, 2/3 width */}
                    <div className="lg:w-2/3 lg:order-1 whitespace-pre-wrap text-right space-y-2 leading-relaxed">
                      {isUser ? message : formatMessage(message)}
                    </div>
                  </div>
                ) : (
                  <div className="px-5 py-3.5 whitespace-pre-wrap text-right space-y-2 leading-relaxed">
                    {isUser ? message : formatMessage(message)}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Action Buttons - Only for AI messages with actions */}
          {!isUser && showActions && (
            <>
              <div className="flex items-center gap-2 mt-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onInsights?.();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-background border border-border hover:border-primary/50 hover:bg-primary/5 transition-all"
                  title="תובנות"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>תובנות</span>
                </button>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onShowSQL?.();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-background border border-border hover:border-primary/50 hover:bg-primary/5 transition-all"
                  title={showSQL ? 'הסתר שאילתה' : 'הצג שאילתה'}
                >
                  <Database className="w-4 h-4" />
                  <span>{showSQL ? 'הסתר שאילתה' : 'הצג שאילתה'}</span>
                </button>

                {/* Export with Dropdown */}
                <ExportDropdown isAnalyticsExpanded={isAnalyticsExpanded} onExport={onExport} data={visualizationData} />

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSaveQuery?.();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-background border border-border hover:border-primary/50 hover:bg-primary/5 transition-all"
                  title="שמור שאילתה"
                >
                  <Save className="w-4 h-4" />
                  <span>שמור שאילתה</span>
                </button>
              </div>

              {/* SQL Query Display */}
              {showSQL && sql && (
                <div className="mt-3 p-4 bg-muted/30 rounded-lg border border-border relative">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-right">שאילתת SQL</h4>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={async () => {
                          const success = await copyToClipboard(sql);
                          if (success) {
                            const event = new CustomEvent('showToast', { 
                              detail: { message: 'שאילתת SQL הועתקה ללוח' } 
                            });
                            window.dispatchEvent(event);
                          }
                        }}
                        className="p-1.5 rounded-md hover:bg-muted transition-colors"
                        title="העתק"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onShowSQL?.();
                        }}
                        className="p-1.5 rounded-md hover:bg-muted transition-colors"
                        title="סגור"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <pre className="text-sm text-left font-mono bg-background/50 p-3 rounded border border-border overflow-x-auto">
                    <code dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }} />
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
        
        {isUser && (
          <div className="flex-shrink-0 flex flex-col items-center gap-1">
            <img src={image_94c3dac261df590bf85ea3a5c2b28e9b3ed2ea33} alt="User" className="w-8 h-8 rounded-full object-cover" />
            <span className="text-xs text-muted-foreground">{userName}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// Function to highlight SQL keywords with colors
function highlightSQL(sql: string): string {
  // SQL Keywords
  const keywords = /\b(SELECT|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|AS|DISTINCT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TABLE|INDEX|AND|OR|NOT|IN|BETWEEN|LIKE|IS|NULL)\b/gi;
  
  // Functions
  const functions = /\b(COUNT|SUM|AVG|MAX|MIN|ROUND|CONCAT|SUBSTRING|UPPER|LOWER|TRIM|LENGTH|DATE|NOW|YEAR|MONTH|DAY)\b/gi;
  
  // Strings (single quotes)
  const strings = /('([^']|'')*')/g;
  
  // Numbers
  const numbers = /\b(\d+(\.\d+)?)\b/g;
  
  // Comments
  const comments = /(--[^\n]*)/g;
  
  let highlighted = sql;
  
  // Apply highlighting (order matters!)
  highlighted = highlighted.replace(comments, '<span style="color: #6b7280;">$1</span>');
  highlighted = highlighted.replace(strings, '<span style="color: #10b981;">$1</span>');
  highlighted = highlighted.replace(numbers, '<span style="color: #f59e0b;">$1</span>');
  highlighted = highlighted.replace(functions, '<span style="color: #8b5cf6; font-weight: 500;">$1</span>');
  highlighted = highlighted.replace(keywords, '<span style="color: #3b82f6; font-weight: 600;">$1</span>');
  
  return highlighted;
}