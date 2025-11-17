import React from 'react';
import { X, Copy, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface SQLDisplayProps {
  sql: string;
  onClose: () => void;
}

// SQL syntax highlighting function
function highlightSQL(sql: string) {
  const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TABLE|DATABASE|INDEX|VIEW|AS|AND|OR|NOT|IN|BETWEEN|LIKE|IS|NULL|DISTINCT|COUNT|SUM|AVG|MAX|MIN|CASE|WHEN|THEN|ELSE|END)\b/gi;
  const strings = /('.*?'|".*?")/g;
  const numbers = /\b(\d+)\b/g;
  
  let highlighted = sql
    .replace(keywords, '<span class="text-[#569cd6]">$1</span>')
    .replace(strings, '<span class="text-[#ce9178]">$1</span>')
    .replace(numbers, '<span class="text-[#b5cea8]">$1</span>');
  
  return highlighted;
}

export function SQLDisplay({ sql, onClose }: SQLDisplayProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    // Fallback copy method for environments where clipboard API is blocked
    try {
      const textArea = document.createElement('textarea');
      textArea.value = sql;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (successful) {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="mb-4 overflow-hidden"
      >
        <div className="bg-muted/50 rounded-lg border border-border p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm flex items-center gap-2">
              <span>שאילתת SQL</span>
            </h4>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-md hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
                title="העתק"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={onClose}
                className="p-1.5 rounded-md hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
                title="סגור"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="bg-background rounded-md p-3 overflow-x-auto">
            <pre className="text-sm font-mono text-left" dir="ltr">
              <code dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }} />
            </pre>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}