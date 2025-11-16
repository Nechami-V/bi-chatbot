import React, { useState } from 'react';
import { LogOut, Moon, Sun, Check, User, Bug } from 'lucide-react';
import { motion } from 'motion/react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { BugReportDialog } from './BugReportDialog';
import userAvatar from 'figma:asset/94c3dac261df590bf85ea3a5c2b28e9b3ed2ea33.png';

interface NewUserProfileMenuProps {
  user: { name: string; email: string } | null;
  onLogout: () => void;
  onReportBug: (description: string, image?: File) => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
  currentColor?: string;
  onColorSelect?: (color: string) => void;
  compact?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
}

const colorOptions = [
  { name: 'סגול', value: '#8b5cf6' },
  { name: 'כחול', value: '#5b7ff5' },
  { name: 'ירוק', value: '#10b981' },
  { name: 'כתום', value: '#f97316' },
  { name: 'ורוד', value: '#ec4899' },
  { name: 'אפור', value: '#64748b' },
];

export function NewUserProfileMenu({
  user,
  onLogout,
  onReportBug,
  isDarkMode = false,
  onToggleDarkMode,
  currentColor = '#8b5cf6',
  onColorSelect,
  compact = false,
  onOpenChange,
}: NewUserProfileMenuProps) {
  const [bugDialogOpen, setBugDialogOpen] = useState(false);

  if (!user) return null;

  const firstName = user.name.split(' ')[0];
  const initials = firstName.charAt(0);

  return (
    <>
      <DropdownMenu onOpenChange={onOpenChange}>
        <DropdownMenuTrigger asChild>
          {compact ? (
            <button className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:opacity-80 transition-opacity overflow-hidden">
              <img src={userAvatar} alt="Profile" className="w-full h-full object-cover" />
            </button>
          ) : (
            <button className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-accent transition-all w-full">
              <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 overflow-hidden">
                <img src={userAvatar} alt="Profile" className="w-full h-full object-cover" />
              </div>
              <span className="text-sm text-muted-foreground truncate flex-1 text-right">{user?.name || 'משתמש אורח'}</span>
            </button>
          )}
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="left" className="w-72" dir="rtl">
          {/* User Info */}
          <div className="px-3 py-3 border-b border-border text-right flex items-center gap-2">
            <User className="w-4 h-4 text-muted-foreground" />
            <p className="text-sm">{user.name}</p>
          </div>

          {/* Color Selection */}
          {onColorSelect && (
            <div className="p-3 border-b border-border text-right">
              <p className="text-xs text-muted-foreground mb-2">צבע ראשי</p>
              <div className="flex items-center gap-2">
                {colorOptions.map((color) => (
                  <button
                    key={color.value}
                    onClick={() => onColorSelect(color.value)}
                    className={`w-8 h-8 rounded-full relative transition-all hover:scale-110 ${
                      currentColor === color.value ? 'ring-2 ring-offset-2 ring-primary' : ''
                    }`}
                    style={{ backgroundColor: color.value }}
                    title={color.name}
                  >
                    {currentColor === color.value && (
                      <Check className="w-4 h-4 text-white absolute inset-0 m-auto" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Dark Mode Toggle - Segmented Control with Animated Slider */}
          {onToggleDarkMode && (
            <div className="p-3 border-b border-border text-right">
              <p className="text-xs text-muted-foreground mb-2">מצב תצוגה</p>
              <div className="relative flex items-center gap-1 p-1 bg-muted rounded-lg overflow-hidden">
                {/* Animated Background Slider */}
                <motion.div
                  className="absolute top-1 h-[calc(100%-8px)] bg-background rounded-md"
                  style={{
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 3px 0 rgba(0, 0, 0, 0.04)',
                    width: 'calc(50% - 4px)',
                  }}
                  initial={false}
                  animate={{
                    right: isDarkMode ? '4px' : 'calc(50% + 0px)',
                    opacity: 1,
                  }}
                  transition={{
                    right: {
                      type: 'tween',
                      ease: [0.4, 0, 0.2, 1],
                      duration: 0.5,
                    },
                    opacity: {
                      duration: 0.5,
                    }
                  }}
                />
                
                {/* Buttons - Fixed width to prevent text jumping */}
                <button
                  onClick={onToggleDarkMode}
                  className="relative z-10 flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md transition-colors"
                  style={{ minWidth: '0' }}
                >
                  <motion.div
                    animate={{
                      opacity: !isDarkMode ? 1 : 0.5,
                    }}
                    transition={{
                      duration: 0.5,
                      ease: [0.4, 0, 0.2, 1],
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <Sun className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm whitespace-nowrap">בהיר</span>
                  </motion.div>
                </button>
                
                <button
                  onClick={onToggleDarkMode}
                  className="relative z-10 flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md transition-colors"
                  style={{ minWidth: '0' }}
                >
                  <motion.div
                    animate={{
                      opacity: isDarkMode ? 1 : 0.5,
                    }}
                    transition={{
                      duration: 0.5,
                      ease: [0.4, 0, 0.2, 1],
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <Moon className="w-4 h-4 flex-shrink-0" />
                    <span className="text-sm whitespace-nowrap">כהה</span>
                  </motion.div>
                </button>
              </div>
            </div>
          )}

          {/* Bug Report */}
          <div className="py-1">
            <DropdownMenuItem onClick={() => setBugDialogOpen(true)} className="text-right flex items-center gap-2">
              <Bug className="w-4 h-4 text-muted-foreground" />
              <span>דווח על באג</span>
            </DropdownMenuItem>
          </div>

          <DropdownMenuSeparator />

          {/* Logout */}
          <DropdownMenuItem onClick={onLogout} className="text-right">
            <LogOut className="ml-2 h-4 w-4" />
            <span>התנתק</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <BugReportDialog
        open={bugDialogOpen}
        onOpenChange={setBugDialogOpen}
        onSubmit={(description, image) => {
          onReportBug(description, image);
          setBugDialogOpen(false);
        }}
      />
    </>
  );
}