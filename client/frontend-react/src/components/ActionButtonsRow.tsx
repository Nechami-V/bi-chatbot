import React from 'react';
import { Sparkles, Download, Save, Code } from 'lucide-react';

interface ActionButtonsRowProps {
  onInsights: () => void;
  onExport: () => void;
  onSaveQuery: () => void;
  onShowSQL: () => void;
  showSQL: boolean;
}

export function ActionButtonsRow({
  onInsights,
  onExport,
  onSaveQuery,
  onShowSQL,
  showSQL
}: ActionButtonsRowProps) {
  return (
    <div className="flex items-center gap-2 flex-wrap mt-3 mr-11">
      <button
        onClick={onInsights}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-muted hover:bg-muted/80 transition-colors"
      >
        <Sparkles className="w-3.5 h-3.5" />
        <span>תובנות חכמות</span>
      </button>

      <button
        onClick={onExport}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-muted hover:bg-muted/80 transition-colors"
      >
        <Download className="w-3.5 h-3.5" />
        <span>ייצוא</span>
      </button>

      <button
        onClick={onSaveQuery}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-muted hover:bg-muted/80 transition-colors"
      >
        <Save className="w-3.5 h-3.5" />
        <span>שמור שאילתה</span>
      </button>

      <button
        onClick={onShowSQL}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-muted hover:bg-muted/80 transition-colors"
      >
        <Code className="w-3.5 h-3.5" />
        <span>{showSQL ? 'הסתר SQL' : 'הצג SQL'}</span>
      </button>
    </div>
  );
}
