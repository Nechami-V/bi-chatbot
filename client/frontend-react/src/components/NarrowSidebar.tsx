import React from 'react';
import { MessageSquare, Save, ChevronLeft, ChevronRight, User, Bug, Plus, Trash2, Play } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import { NewUserProfileMenu } from './NewUserProfileMenu';
import { motion, AnimatePresence } from 'motion/react';
import panelIcon from 'figma:asset/693b327b20c301b1632efb14e838cd1551d3acb3.png';

interface SavedQuery {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
}

interface NarrowSidebarProps {
  onTogglePanel: () => void;
  onNewChat: () => void;
  onOpenQueries: () => void;
  user: { name: string; email: string } | null;
  onLogout: () => void;
  onReportBug: (description: string, image?: File) => void;
  isDarkMode?: boolean;
  onToggleDarkMode?: () => void;
  currentColor?: string;
  onColorSelect?: (color: string) => void;
  isExpanded?: boolean;
  savedQueries?: SavedQuery[];
  onSelectQuery?: (query: SavedQuery) => void;
  onDeleteQuery?: (id: string) => void;
  recentlySaved?: string | null;
  hasUnreadQueries?: boolean;
}

export function NarrowSidebar({
  onTogglePanel,
  onNewChat,
  onOpenQueries,
  user,
  onLogout,
  onReportBug,
  isDarkMode,
  onToggleDarkMode,
  currentColor,
  onColorSelect,
  isExpanded = false,
  savedQueries = [],
  onSelectQuery,
  onDeleteQuery,
  recentlySaved,
  hasUnreadQueries = false,
}: NarrowSidebarProps) {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = React.useState(false);
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);

  return (
    <TooltipProvider delayDuration={300}>
      {/* Mobile Overlay Backdrop */}
      {isExpanded && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={onTogglePanel}
        />
      )}
      
      <div 
        className={`h-full bg-card border-l border-border flex-shrink-0 transition-all duration-300 overflow-hidden ${
          isExpanded ? 'fixed right-0 top-0 bottom-0 z-50 w-80 lg:relative lg:z-auto' : 'w-16'
        }`}
        dir={isExpanded ? 'rtl' : 'ltr'}
      >
        {!isExpanded ? (
          // Collapsed State - Icon Mode
          <div className="w-16 h-full flex flex-col items-center py-4 gap-2">
            {/* Toggle Panel Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onTogglePanel}
                  className="w-10 h-10 rounded-lg hover:bg-primary/10 transition-all flex items-center justify-center group relative"
                >
                  <ChevronRight className="w-5 h-5 text-foreground" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="left" className="bg-primary text-primary-foreground">
                <p>פתח פאנל</p>
              </TooltipContent>
            </Tooltip>

            {/* New Chat Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onNewChat}
                  className="w-10 h-10 rounded-lg hover:bg-accent transition-all flex items-center justify-center"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>שאלה חדשה</p>
              </TooltipContent>
            </Tooltip>

            {/* Saved Queries Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onOpenQueries}
                  className="w-10 h-10 rounded-lg hover:bg-accent transition-all flex items-center justify-center relative"
                >
                  <Save className="w-5 h-5" />
                  {hasUnreadQueries && (
                    <span className="absolute top-1 left-1 w-2.5 h-2.5 bg-primary rounded-full ring-2 ring-card"></span>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="left" className="bg-primary text-primary-foreground">
                <p>שאילתות שמורות</p>
              </TooltipContent>
            </Tooltip>

            {/* Spacer */}
            <div className="flex-1"></div>

            {/* User Profile */}
            {!isExpanded && (
              <Tooltip open={isProfileMenuOpen ? false : undefined}>
                <TooltipTrigger asChild>
                  <div>
                    <NewUserProfileMenu
                      user={user}
                      onLogout={onLogout}
                      onReportBug={onReportBug}
                      isDarkMode={isDarkMode}
                      onToggleDarkMode={onToggleDarkMode}
                      currentColor={currentColor}
                      onColorSelect={onColorSelect}
                      compact={true}
                      onOpenChange={setIsProfileMenuOpen}
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="left" className="bg-primary text-primary-foreground">
                  <p>פרופיל משתמש</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        ) : (
          // Expanded State - Full Panel
          <div className="w-80 h-full flex flex-col">
            {/* Toggle Button at Top - Aligned Left */}
            <div className="p-4 border-b border-border flex items-center justify-end">
              <button
                onClick={onTogglePanel}
                className="p-2 hover:bg-accent rounded-lg transition-colors flex-shrink-0"
              >
                <ChevronLeft className="w-5 h-5 text-foreground" />
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
              {savedQueries.length > 0 ? (
                <div className="space-y-2">
                  <h3 className="text-sm text-muted-foreground px-2 mb-3">שאילתות שמורות</h3>
                  <AnimatePresence>
                    {savedQueries.map((query) => (
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
                              onSelectQuery?.(query);
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
                                onDeleteQuery?.(query.id);
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
              {/* User Profile Menu */}
              <div className="mb-3">
                <NewUserProfileMenu
                  user={user}
                  onLogout={onLogout}
                  onReportBug={onReportBug}
                  isDarkMode={isDarkMode}
                  onToggleDarkMode={onToggleDarkMode}
                  currentColor={currentColor}
                  onColorSelect={onColorSelect}
                  compact={false}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}