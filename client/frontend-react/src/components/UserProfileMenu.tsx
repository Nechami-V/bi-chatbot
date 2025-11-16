import React from 'react';
import { LogOut, Bug, Palette, Moon, Sun, Check } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
} from './ui/dropdown-menu';

interface UserProfileMenuProps {
  user: { name: string; email: string } | null;
  onLogout: () => void;
  onReportBug: () => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
  currentColor?: string;
  onColorSelect?: (color: string) => void;
}

const colorOptions = [
  { name: 'כחול', value: '#5b7ff5' },
  { name: 'ירוק', value: '#10b981' },
  { name: 'כתום', value: '#f59e0b' },
  { name: 'ורוד', value: '#ec4899' },
  { name: 'סגול', value: '#8b5cf6' },
];

export function UserProfileMenu({ 
  user, 
  onLogout, 
  onReportBug, 
  isDarkMode = false,
  onToggleDarkMode,
  currentColor = '#5b7ff5',
  onColorSelect
}: UserProfileMenuProps) {
  if (!user) return null;

  const firstName = user.name.split(' ')[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-accent transition-all w-full">
          <div 
            className="w-8 h-8 rounded-full text-white flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: currentColor }}
          >
            <span className="text-sm">{firstName.charAt(0)}</span>
          </div>
          <span className="text-sm truncate">{firstName}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="left" className="w-64" dir="rtl">
        <div className="px-3 py-2.5 border-b border-border">
          <p className="text-sm">{user.name}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
        </div>
        
        <div className="py-1">
          {/* Dark Mode Toggle */}
          {onToggleDarkMode && (
            <DropdownMenuItem onClick={onToggleDarkMode}>
              {isDarkMode ? (
                <Sun className="ml-2 h-4 w-4" />
              ) : (
                <Moon className="ml-2 h-4 w-4" />
              )}
              <span>{isDarkMode ? 'מצב בהיר' : 'מצב כהה'}</span>
            </DropdownMenuItem>
          )}

          {/* Color Selection Submenu */}
          {onColorSelect && (
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Palette className="ml-2 h-4 w-4" />
                <span>בחר צבע ראשי</span>
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {colorOptions.map((color) => (
                  <DropdownMenuItem
                    key={color.value}
                    onClick={() => onColorSelect(color.value)}
                  >
                    <div className="flex items-center gap-2 w-full">
                      <div 
                        className="w-4 h-4 rounded-full border-2 border-border"
                        style={{ backgroundColor: color.value }}
                      />
                      <span className="flex-1">{color.name}</span>
                      {currentColor === color.value && (
                        <Check className="h-4 w-4" />
                      )}
                    </div>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          )}
          
          <DropdownMenuItem onClick={onReportBug}>
            <Bug className="ml-2 h-4 w-4" />
            <span>דווח על באג</span>
          </DropdownMenuItem>
        </div>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={onLogout} className="text-destructive">
          <LogOut className="ml-2 h-4 w-4" />
          <span>התנתק</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
