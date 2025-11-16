import React from 'react';
import { UserPlus, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface LoginPromptProps {
  show: boolean;
  onLogin: () => void;
  onDismiss: () => void;
}

export function LoginPrompt({ show, onLogin, onDismiss }: LoginPromptProps) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
        >
          <div className="bg-card border border-border rounded-2xl shadow-2xl p-4 pr-6 flex items-center gap-4 max-w-md">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <UserPlus className="w-5 h-5 text-primary" style={{ transform: 'scaleX(-1)' }} />
            </div>
            
            <div className="flex-1">
              <h4 className="text-sm mb-1">התחבר לשמירת היסטוריה</h4>
              <p className="text-xs text-muted-foreground">
                כדי לשמור את השאילתות וההיסטוריה שלך, התחבר עכשיו
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onLogin}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors text-sm"
              >
                התחבר
              </button>
              
              <button
                onClick={onDismiss}
                className="p-2 hover:bg-accent rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}