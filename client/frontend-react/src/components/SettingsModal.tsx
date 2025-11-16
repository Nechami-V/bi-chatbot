import React from 'react';
import { X, Check } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  currentColor: string;
  onColorChange: (color: string) => void;
}

const THEME_COLORS = [
  { name: 'סגול', value: '#5b7ff5', class: 'bg-[#5b7ff5]' },
  { name: 'כחול', value: '#3b82f6', class: 'bg-[#3b82f6]' },
  { name: 'ירוק', value: '#10b981', class: 'bg-[#10b981]' },
  { name: 'כתום', value: '#f59e0b', class: 'bg-[#f59e0b]' },
  { name: 'ורוד', value: '#ec4899', class: 'bg-[#ec4899]' },
];

export function SettingsModal({ open, onClose, currentColor, onColorChange }: SettingsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md" dir="rtl">
        <DialogHeader>
          <DialogTitle>הגדרות</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-3">
            <h3 className="text-sm">צבע ראשי</h3>
            <div className="grid grid-cols-5 gap-3">
              {THEME_COLORS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => onColorChange(color.value)}
                  className="relative group"
                >
                  <div
                    className={`
                      w-12 h-12 rounded-xl ${color.class}
                      hover:scale-110 transition-transform
                      ${currentColor === color.value ? 'ring-2 ring-offset-2 ring-foreground' : ''}
                    `}
                  >
                    {currentColor === color.value && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Check className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-center mt-1.5 text-muted-foreground">
                    {color.name}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
