import React from 'react';
import { User, LogOut, LogIn } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

interface UserMenuProps {
  user: { name: string; email: string } | null;
  onLogin: () => void;
  onLogout: () => void;
  onSwitchAccount: () => void;
}

export function UserMenu({ user, onLogin, onLogout, onSwitchAccount }: UserMenuProps) {
  if (!user) {
    return (
      <button
        onClick={onLogin}
        className="flex items-center gap-2 px-4 py-2 bg-[#5b7ff5] text-white rounded-xl hover:bg-[#4a6de6] transition-colors"
      >
        <LogIn className="w-4 h-4" />
        התחבר
      </button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 px-3 py-2 rounded-xl bg-muted hover:bg-accent transition-colors">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
          <span className="text-sm max-w-[120px] truncate">{user.name}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <div className="px-2 py-1.5">
          <p className="text-sm">{user.name}</p>
          <p className="text-xs text-muted-foreground">{user.email}</p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onSwitchAccount}>
          <User className="ml-2 h-4 w-4" />
          <span>החלף חשבון</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onLogout} className="text-destructive">
          <LogOut className="ml-2 h-4 w-4" />
          <span>התנתק</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}