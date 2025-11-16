import React from 'react';
import { X, Download, Save, Sparkles, Code } from 'lucide-react';
import { InlineVisualization } from './InlineVisualization';
import { motion, AnimatePresence } from 'motion/react';

interface AnalyticsPanelProps {
  isExpanded: boolean;
  activeMessageId: string | null;
  visualization?: {
    data: any[];
    type: 'line' | 'bar' | 'pie';
    valuePrefix?: string;
    valueSuffix?: string;
  };
  userQuestion?: string;
  onClose: () => void;
  onInsights: () => void;
  onSaveQuery: () => void;
  onExport: (format: 'pdf' | 'excel' | 'csv') => void;
  onShowSQL: () => void;
  showSQL: boolean;
  sql?: string;
}

export function AnalyticsPanel({
  isExpanded,
  activeMessageId,
  visualization,
  userQuestion,
  onClose,
  onInsights,
  onSaveQuery,
  onExport,
  onShowSQL,
  showSQL,
  sql
}: AnalyticsPanelProps) {
  if (!activeMessageId || !visualization) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className={`flex flex-col bg-card lg:border-l border-border h-full lg:h-full overflow-hidden`}
        style={{ height: window.innerWidth < 1024 ? '100vh' : '100%' }}
      >
        {/* Mobile Full Screen Header */}
        <div className="lg:hidden flex flex-col p-4 border-b border-border">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="flex-1 text-right">
              <h3 className="font-semibold text-right">{userQuestion || 'תצוגת גרף מלאה'}</h3>
              <p className="text-sm text-muted-foreground mt-1 text-right">מסך מלא</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-muted/50 transition-colors flex-shrink-0"
              title="סגור"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Mobile Controls - Icons Only */}
        <div className="lg:hidden flex items-center justify-end gap-2 p-4 border-b border-border">
          {/* Action Buttons - Icons Only */}
          <button
            onClick={onInsights}
            className="p-2.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors border border-primary/20 hover:border-primary/30"
            title="תובנות חכמות"
          >
            <Sparkles className="w-5 h-5" />
          </button>
          
          <button
            onClick={onShowSQL}
            className="p-2.5 rounded-lg bg-muted hover:bg-muted/80 transition-colors border border-border hover:border-border/80"
            title={showSQL ? 'הסתר SQL' : 'הצג SQL'}
          >
            <Code className="w-5 h-5" />
          </button>

          <button
            onClick={() => onExport('excel')}
            className="p-2.5 rounded-lg bg-muted hover:bg-muted/80 transition-colors border border-border hover:border-border/80"
            title="ייצוא"
          >
            <Download className="w-5 h-5" />
          </button>

          <button
            onClick={onSaveQuery}
            className="p-2.5 rounded-lg bg-muted hover:bg-muted/80 transition-colors border border-border hover:border-border/80"
            title="שמור שאילתה"
          >
            <Save className="w-5 h-5" />
          </button>
        </div>

        {/* Desktop Close Button - Top right corner */}
        <div className="hidden lg:flex items-center justify-end p-4">
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
            title="סגור"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* SQL Display */}
        {showSQL && sql && (
          <div className="p-4 border-b border-border bg-muted/30">
            <div className="bg-background/50 rounded-lg p-4 font-mono text-sm overflow-x-auto" dir="ltr">
              <pre className="whitespace-pre-wrap break-words">{sql}</pre>
            </div>
          </div>
        )}

        {/* Chart Area - Full Screen on Mobile */}
        <div className="flex-1 p-4 sm:p-6 relative">
          <div className="h-full w-full">
            <InlineVisualization
              data={visualization.data}
              type={visualization.type}
              valuePrefix={visualization.valuePrefix}
              valueSuffix={visualization.valueSuffix}
              isFullView={true}
            />
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}