import React, { useState } from 'react';
import { Menu, MessageSquare, Trash2, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { UserProfileMenu } from './UserProfileMenu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';

interface SavedQuery {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
}

interface SidebarProps {
  queries: SavedQuery[];
  onNewChat: () => void;
  onSelectQuery: (query: SavedQuery) => void;
  onDeleteQuery: (id: string) => void;
  recentlySaved?: string | null;
  user: { name: string; email: string } | null;
  onLogout: () => void;
  onReportBug: () => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
  currentColor?: string;
  onColorSelect?: (color: string) => void;
}

export function Sidebar({ 
  queries, 
  onNewChat, 
  onSelectQuery, 
  onDeleteQuery, 
  recentlySaved,
  user,
  onLogout,
  onReportBug,
  isDarkMode,
  onToggleDarkMode,
  currentColor,
  onColorSelect
}: SidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <TooltipProvider delayDuration={300}>
      <motion.div
        initial={false}
        animate={{ width: isExpanded ? 280 : 64 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="h-full bg-card border-r border-border flex flex-col relative"
      >
        {/* Toggle Button */}
        <div className="p-3 border-b border-border flex items-center justify-center">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-2.5 rounded-lg hover:bg-accent transition-all"
              >
                <Menu className="w-5 h-5" />
              </button>
            </TooltipTrigger>
            {!isExpanded && (
              <TooltipContent side="left">
                <p>פתח תפריט</p>
              </TooltipContent>
            )}
          </Tooltip>
        </div>

        {/* User Section */}
        <div className="p-3 border-b border-border">
          {isExpanded ? (
            <UserProfileMenu 
              user={user}
              onLogout={onLogout}
              onReportBug={onReportBug}
              isDarkMode={isDarkMode}
              onToggleDarkMode={onToggleDarkMode}
              currentColor={currentColor}
              onColorSelect={onColorSelect}
            />
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <UserProfileMenu 
                    user={user}
                    onLogout={onLogout}
                    onReportBug={onReportBug}
                    isDarkMode={isDarkMode}
                    onToggleDarkMode={onToggleDarkMode}
                    currentColor={currentColor}
                    onColorSelect={onColorSelect}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>פרופיל משתמש</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Saved Queries */}
        <div className="flex-1 overflow-y-auto p-3">
          {isExpanded && (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={onNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 mb-4 rounded-lg border border-border hover:bg-accent transition-all"
            >
              <span className="text-sm">שיחה חדשה</span>
            </motion.button>
          )}

          {isExpanded && queries.length > 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-muted-foreground mb-2 px-2"
            >
              שאילתות שמורות
            </motion.p>
          )}

          <div className="space-y-1">
            <AnimatePresence>
              {queries.map((query) => (
                <motion.div
                  key={query.id}
                  initial={recentlySaved === query.id ? { scale: 0.8, opacity: 0, x: -20 } : false}
                  animate={{ scale: 1, opacity: 1, x: 0 }}
                  exit={{ scale: 0.8, opacity: 0, x: -20 }}
                  transition={{ duration: 0.4, type: 'spring' }}
                  className="relative group"
                  onMouseEnter={() => setHoveredId(query.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  {isExpanded ? (
                    <button
                      onClick={() => onSelectQuery(query)}
                      className={`
                        w-full text-right px-3 py-2.5 rounded-lg transition-all
                        hover:bg-accent relative overflow-hidden
                        ${recentlySaved === query.id ? 'bg-primary/10 border border-primary/20' : ''}
                      `}
                    >
                      <div className="flex items-start gap-2">
                        <MessageSquare className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span className="text-sm line-clamp-2 flex-1">{query.title}</span>
                      </div>

                      {hoveredId === query.id && (
                        <div className="absolute left-2 top-1/2 -translate-y-1/2 flex gap-1 bg-card">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteQuery(query.id);
                            }}
                            className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </button>
                  ) : (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          onClick={() => onSelectQuery(query)}
                          className={`
                            w-full p-2.5 rounded-lg transition-all hover:bg-accent
                            ${recentlySaved === query.id ? 'bg-primary/10 border border-primary/20' : ''}
                          `}
                        >
                          <MessageSquare className="w-4 h-4 mx-auto" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="left">
                        <p className="max-w-xs">{query.title}</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </TooltipProvider>
  );
}