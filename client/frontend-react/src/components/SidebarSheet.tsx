import React from 'react';
import { Trash2, Play, ChevronLeft, ChevronRight, User, Bug, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface SavedQuery {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
}

interface SidebarSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  queries: SavedQuery[];
  onNewChat: () => void;
  onSelectQuery: (query: SavedQuery) => void;
  onDeleteQuery: (id: string) => void;
  recentlySaved?: string | null;
  userName?: string;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
}

export function SidebarSheet({
  open,
  onOpenChange,
  queries,
  onNewChat,
  onSelectQuery,
  onDeleteQuery,
  recentlySaved,
  userName = 'מרים פרייס',
  isDarkMode = false,
  onToggleDarkMode,
}: SidebarSheetProps) {
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);

  return (
    <div
      className={`h-full bg-card border-l border-border shadow-lg flex-shrink-0 transition-all duration-300 overflow-hidden ${
        open ? 'w-80' : 'w-16'
      }`}
      dir="rtl"
    >
      <div className="w-80 h-full flex flex-col">
        {/* Toggle Button at Top */}
        <div className="p-4 border-b border-border flex items-center justify-center">
          <button
            onClick={() => onOpenChange(!open)}
            className="p-2 hover:bg-primary/10 rounded-lg transition-colors flex-shrink-0 group relative"
          >
            {open ? (
              <ChevronLeft className="w-5 h-5 text-primary" />
            ) : (
              <ChevronRight className="w-5 h-5 text-primary" />
            )}
            <span className="absolute left-full ml-2 px-2 py-1 bg-primary text-primary-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              {open ? 'סגור פאנל' : 'פתח פאנל'}
            </span>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-3 border-b border-border">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1 text-right">שיחה חדשה</span>
          </button>
        </div>

        {/* Saved Queries Section */}
        <div className="flex-1 overflow-y-auto p-4">
          {queries.length > 0 ? (
            <div className="space-y-2">
              <h3 className="text-sm text-muted-foreground px-2 mb-3">שאילתות שמורות</h3>
              <AnimatePresence>
                {queries.map((query) => (
                  <motion.div
                    key={query.id}
                    initial={recentlySaved === query.id ? { scale: 0.9, opacity: 0 } : false}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="relative group"
                    onMouseEnter={() => setHoveredId(query.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  >
                    <div
                      className={`
                        p-3 rounded-lg border border-border hover:bg-accent transition-all flex items-center gap-2 justify-between
                        ${recentlySaved === query.id ? 'bg-primary/5 border-primary/20' : ''}
                      `}
                    >
                      {/* Run Button - Left Side */}
                      <button
                        onClick={() => {
                          onSelectQuery(query);
                        }}
                        className="px-2.5 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-xs flex items-center gap-1 flex-shrink-0"
                      >
                        <Play className="w-3 h-3" />
                        <span>הרץ</span>
                      </button>

                      {/* Query Text - Center */}
                      <p className="text-sm flex-1 line-clamp-2 text-right px-2">{query.title}</p>

                      {/* Delete Button - Right Side (on hover) */}
                      {hoveredId === query.id && (
                        <motion.button
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteQuery(query.id);
                          }}
                          className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors flex-shrink-0"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </motion.button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground text-sm">אין שאילתות שמורות</p>
            </div>
          )}
        </div>

        {/* User Profile at Bottom */}
        <div className="p-4 border-t border-border mt-auto">
          <div className="flex items-center gap-3 mb-3">
            <User className="w-5 h-5 text-muted-foreground flex-shrink-0" />
            <span className="text-sm truncate">{userName}</span>
          </div>

          {/* Dark Mode Toggle - Segmented Control */}
          <div className="bg-muted/50 rounded-full p-1 flex gap-1 mb-3">
            <button
              onClick={() => onToggleDarkMode?.()}
              className={`flex-1 px-4 py-2 rounded-full text-sm transition-all duration-300 ${
                isDarkMode
                  ? 'bg-background shadow-sm text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              כהה
            </button>
            <button
              onClick={() => onToggleDarkMode?.()}
              className={`flex-1 px-4 py-2 rounded-full text-sm transition-all duration-300 ${
                !isDarkMode
                  ? 'bg-background shadow-sm text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              בהיר
            </button>
          </div>

          {/* Bug Report */}
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors text-sm">
            <Bug className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <span className="flex-1 text-right">דיווח על באג</span>
          </button>
        </div>
      </div>
    </div>
  );
}