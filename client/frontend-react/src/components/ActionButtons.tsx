import React, { useState } from 'react';
import { Lightbulb, Download, Save, ChevronDown, Database, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ActionButtonsProps {
  onInsights: () => void;
  onSaveQuery: () => void;
  onExport: (format: 'pdf' | 'excel' | 'csv') => void;
  onShowSQL?: () => void;
  isSaved?: boolean;
}

export function ActionButtons({ onInsights, onSaveQuery, onExport, onShowSQL, isSaved = false }: ActionButtonsProps) {
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [showSavedIndicator, setShowSavedIndicator] = useState(false);

  const handleSaveQuery = () => {
    onSaveQuery();
    setShowSavedIndicator(true);
    setTimeout(() => setShowSavedIndicator(false), 2000);
  };

  const handleExport = (format: 'pdf' | 'excel' | 'csv') => {
    onExport(format);
    setShowExportMenu(false);
  };

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {onShowSQL && (
        <button
          onClick={onShowSQL}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors text-sm whitespace-nowrap"
        >
          <Database className="w-3.5 h-3.5 flex-shrink-0" />
          <span>הצג שאילתת SQL</span>
        </button>
      )}
      
      <button
        onClick={onInsights}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors text-sm whitespace-nowrap"
      >
        <Lightbulb className="w-3.5 h-3.5 flex-shrink-0" />
        <span>תובנות חכמות</span>
      </button>
      
      <div className="relative">
        <button
          onClick={() => setShowExportMenu(!showExportMenu)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors text-sm whitespace-nowrap"
        >
          <Download className="w-3.5 h-3.5 flex-shrink-0" />
          <span>ייצוא</span>
          <ChevronDown className="w-3 h-3 flex-shrink-0" />
        </button>
        
        {showExportMenu && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setShowExportMenu(false)}
            />
            <div className="absolute left-0 top-full mt-1 bg-card border border-border rounded-lg shadow-lg overflow-hidden z-20 min-w-[120px]">
              <button
                onClick={() => handleExport('csv')}
                className="w-full px-4 py-2 text-right text-sm hover:bg-accent transition-colors"
              >
                CSV
              </button>
              <button
                onClick={() => handleExport('excel')}
                className="w-full px-4 py-2 text-right text-sm hover:bg-accent transition-colors"
              >
                Excel
              </button>
            </div>
          </>
        )}
      </div>
      
      <button
        onClick={handleSaveQuery}
        className="relative flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors text-sm whitespace-nowrap"
      >
        <Save className="w-3.5 h-3.5 flex-shrink-0" />
        <span>שמור שאילתה</span>
        <AnimatePresence>
          {showSavedIndicator && (
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.2 }}
              className="absolute left-0 top-0 translate-x-1/2 -translate-y-1/2 bg-green-500 text-white rounded-full w-4 h-4 flex items-center justify-center"
            >
              <Check className="w-3 h-3" />
            </motion.div>
          )}
        </AnimatePresence>
      </button>
    </div>
  );
}