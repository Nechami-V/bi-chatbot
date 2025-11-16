import React, { useState, useRef, useEffect } from 'react';
import { ChatBubble } from './components/ChatBubble';
import { ChatInput } from './components/ChatInput';
import { EmptyState } from './components/EmptyState';
import { InlineVisualization } from './components/InlineVisualization';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { ResizableHandle } from './components/ResizableHandle';
import { NarrowSidebar } from './components/NarrowSidebar';
import { LoginScreen } from './components/LoginScreen';
import { LoginPrompt } from './components/LoginPrompt';
import { WelcomeScreen } from './components/WelcomeScreen';
import { toast } from 'sonner@2.0.3';
import { Toaster } from './components/ui/sonner';
import { askQuestion, APIError, logout as apiLogout, login, exportData } from './services/api';
import foxLogo from 'figma:asset/5eb1a03d8a66515a97bce7830fd04ba26410b27e.png';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  showActions?: boolean;
  sql?: string;
  showSQL?: boolean;
  visualization?: {
    data: any[];
    type: 'line' | 'bar' | 'pie';
    valuePrefix?: string;
    valueSuffix?: string;
  };
}

interface SavedQuery {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
}

function App() {
  const [showLoginScreen, setShowLoginScreen] = useState(true);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [recentlySavedId, setRecentlySavedId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [hasUnreadQueries, setHasUnreadQueries] = useState(false);
  const [primaryColor, setPrimaryColor] = useState('#8b5cf6');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null);
  const [isAnalyticsExpanded, setIsAnalyticsExpanded] = useState(false);
  const [userLockedChart, setUserLockedChart] = useState(false); // Track if user manually selected a chart
  const [analyticsPanelWidth, setAnalyticsPanelWidth] = useState(50); // Percentage width - 50% for split view
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const mainContainerRef = useRef<HTMLDivElement>(null);

  // נתוני דמה לויזואליזציה
  const mockData = [
    { name: 'ינואר', value: 120 },
    { name: 'פברואר', value: 150 },
    { name: 'מרץ', value: 180 },
    { name: 'אפריל', value: 140 },
    { name: 'מאי', value: 200 },
    { name: 'יוני', value: 170 }
  ];

  // Apply primary color to CSS variable and update all primary colors
  useEffect(() => {
    const root = document.documentElement;
    
    // Apply dark mode
    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    
    // Convert hex to HSL for better theming
    const hexToHSL = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      if (!result) return { h: 0, s: 0, l: 0 };
      
      let r = parseInt(result[1], 16) / 255;
      let g = parseInt(result[2], 16) / 255;
      let b = parseInt(result[3], 16) / 255;
      
      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      let h = 0, s = 0, l = (max + min) / 2;
      
      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        
        switch (max) {
          case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
          case g: h = ((b - r) / d + 2) / 6; break;
          case b: h = ((r - g) / d + 4) / 6; break;
        }
      }
      
      return {
        h: Math.round(h * 360),
        s: Math.round(s * 100),
        l: Math.round(l * 100)
      };
    };
    
    const { h, s, l } = hexToHSL(primaryColor);
    root.style.setProperty('--primary', `${h} ${s}% ${l}%`);
    
    // Dispatch custom event to notify charts
    window.dispatchEvent(new CustomEvent('primaryColorChange'));
  }, [primaryColor, isDarkMode]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  // Auto-update active message when panel is open and not locked by user
  useEffect(() => {
    if (isAnalyticsExpanded && !userLockedChart) {
      const lastAIMessageWithViz = [...messages]
        .reverse()
        .find(m => m.type === 'ai' && m.visualization);
      
      if (lastAIMessageWithViz) {
        setActiveMessageId(lastAIMessageWithViz.id);
      }
    }
  }, [messages, isAnalyticsExpanded, userLockedChart]);

  // Keyboard shortcut for new chat (Ctrl+Shift+O)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        handleNewChat();
      }
    };

    const handleToastEvent = (e: CustomEvent) => {
      toast.success(e.detail.message);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('showToast' as any, handleToastEvent as any);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('showToast' as any, handleToastEvent as any);
    };
  }, []);

  const handleLogin = async (email: string, password: string) => {
    try {
      console.log('Attempting login with:', email);
      const response = await login(email, password);
      console.log('Login successful:', response);
      
      // Extract user info from response
      const fullName = response.user_info.full_name || email;
      
      setUser({ name: fullName, email });
      setShowLoginScreen(false);
      toast.success('התחברת בהצלחה!');
    } catch (error) {
      console.error('Login error:', error);
      if (error instanceof APIError && error.status === 401) {
        toast.error('שם משתמש או סיסמה שגויים');
      } else {
        toast.error('אירעה שגיאה בהתחברות. אנא נסה שוב.');
      }
    }
  };

  const handleSkipLogin = () => {
    setShowLoginScreen(false);
  };

  const handleLogout = async () => {
    await apiLogout();
    setUser(null);
    setMessages([]);
    setSavedQueries([]);
    setShowLoginScreen(true);
    toast.success('התנתקת בהצלחה');
  };

  const handleReportBug = (description: string, image: File | null) => {
    toast.success('הדיווח נשלח בהצלחה!');
  };

  const handleSendMessage = async (content: string) => {
    console.log('handleSendMessage called with:', content);
    console.log('Current messages:', messages);
    
    // Show login prompt if user is not logged in (only once)
    if (!user && messages.length === 0) {
      setShowLoginPrompt(true);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content
    };

    console.log('Adding user message:', userMessage);
    setMessages(prev => {
      console.log('Previous messages:', prev);
      const newMessages = [...prev, userMessage];
      console.log('New messages after user:', newMessages);
      return newMessages;
    });
    setIsThinking(true);

    try {
      console.log('Calling askQuestion API...');
      // Call the real API
      const response = await askQuestion(content);
      console.log('API response:', response);
      
      setIsThinking(false);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.answer,
        showActions: true,
        sql: response.sql,
        showSQL: false,
      };

      // Add visualization if present
      if (response.visualization) {
        const viz = response.visualization;
        aiMessage.visualization = {
          data: viz.labels.map((label, i) => ({
            name: label,
            value: viz.values[i]
          })),
          type: viz.chart_type === 'pie' ? 'pie' : viz.chart_type === 'line' ? 'line' : 'bar',
          valuePrefix: '',
          valueSuffix: ''
        };
      }

      console.log('Adding AI message:', aiMessage);
      setMessages(prev => {
        console.log('Previous messages before AI:', prev);
        const newMessages = [...prev, aiMessage];
        console.log('New messages after AI:', newMessages);
        return newMessages;
      });
    } catch (error) {
      setIsThinking(false);
      console.error('Ask question error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: error instanceof APIError 
          ? `שגיאה: ${error.message}` 
          : 'מצטער, אירעה שגיאה בעיבוד השאלה. אנא נסה שוב.',
        showActions: false,
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('שגיאה בחיבור לשרת');
      }
    }
  };

  const handleQuestionClick = (question: string) => {
    handleSendMessage(question);
  };

  const handleSaveQuery = () => {
    const lastUserMessage = [...messages].reverse().find(m => m.type === 'user');
    if (lastUserMessage) {
      const newQuery: SavedQuery = {
        id: Date.now().toString(),
        title: lastUserMessage.content.length > 30 
          ? lastUserMessage.content.substring(0, 30) + '...' 
          : lastUserMessage.content,
        query: lastUserMessage.content,
        createdAt: new Date()
      };
      setSavedQueries(prev => [...prev, newQuery]);
      setRecentlySavedId(newQuery.id);
      setHasUnreadQueries(true);
      
      toast.success('השאילתה נשמרה בהצלחה!', {
        duration: 2000,
      });
      
      setTimeout(() => {
        setRecentlySavedId(null);
      }, 2000);
    }
  };

  const handleRunSavedQuery = (query: SavedQuery) => {
    handleSendMessage(query.query);
  };

  const handleDeleteQuery = (id: string) => {
    setSavedQueries(prev => prev.filter(q => q.id !== id));
    toast.success('השאילתה נמחקה');
  };

  const handleExport = async (format: 'excel' | 'csv' = 'excel') => {
    const lastUserMessage = [...messages].reverse().find(m => m.type === 'user');
    if (!lastUserMessage) {
      toast.error('אין שאלה לייצא');
      return;
    }

    try {
      toast.info('מייצא נתונים...');
      
      const blob = await exportData(lastUserMessage.content, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `export_${Date.now()}.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`הקובץ הורד בהצלחה (${format === 'excel' ? 'Excel' : 'CSV'})`);
    } catch (error) {
      console.error('Export error:', error);
      if (error instanceof APIError) {
        toast.error(`שגיאה בייצוא: ${error.message}`);
      } else {
        toast.error('אירעה שגיאה בייצוא הנתונים');
      }
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setActiveMessageId(null);
    setIsAnalyticsExpanded(false);
  };

  const handleBubbleClick = (messageId: string) => {
    setActiveMessageId(messageId);
    setIsAnalyticsExpanded(false);
  };

  const handleExpandChart = (messageId: string) => {
    setActiveMessageId(messageId);
    setIsAnalyticsExpanded(true);
    setUserLockedChart(true);
  };

  const handleCloseAnalytics = () => {
    setIsAnalyticsExpanded(false);
    setUserLockedChart(false);
  };

  const handleResizePanel = (delta: number) => {
    if (!mainContainerRef.current) return;
    
    const containerWidth = mainContainerRef.current.offsetWidth;
    setAnalyticsPanelWidth(prev => {
      // Calculate new width based on delta
      const newWidthPx = (prev / 100) * containerWidth + delta;
      const newWidthPercent = (newWidthPx / containerWidth) * 100;
      
      // Clamp between 30% and 80%
      return Math.max(30, Math.min(80, newWidthPercent));
    });
  };

  if (showLoginScreen) {
    return <LoginScreen onLogin={handleLogin} onSkip={handleSkipLogin} />;
  }

  const isEmpty = messages.length === 0;
  const firstName = user?.name.split(' ')[0] || 'משתמש';
  const activeMessage = messages.find(m => m.id === activeMessageId);
  
  // Find the user question that corresponds to the active AI message
  const getUserQuestionForMessage = (aiMessageId: string) => {
    const aiIndex = messages.findIndex(m => m.id === aiMessageId);
    if (aiIndex > 0) {
      // Get the previous message (should be the user's question)
      const userMessage = messages[aiIndex - 1];
      if (userMessage.type === 'user') {
        return userMessage.content;
      }
    }
    return undefined;
  };

  return (
    <div className="h-screen flex bg-background" dir="rtl">
      <Toaster position="top-center" />
      <LoginPrompt 
        show={showLoginPrompt} 
        onLogin={() => {
          setShowLoginPrompt(false);
          setShowLoginScreen(true);
        }}
        onDismiss={() => setShowLoginPrompt(false)}
      />
      
      {/* Narrow Sidebar - Right Side */}
      <NarrowSidebar
        onTogglePanel={() => {
          setSheetOpen(!sheetOpen);
          if (!sheetOpen) {
            setHasUnreadQueries(false);
          }
        }}
        onNewChat={handleNewChat}
        onOpenQueries={() => {
          setSheetOpen(!sheetOpen);
          if (!sheetOpen) {
            setHasUnreadQueries(false);
          }
        }}
        user={user}
        onLogout={handleLogout}
        onReportBug={(description, image) => {
          toast.success('הדיווח נשלח בהצלחה!');
        }}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => {
          setTimeout(() => {
            setIsDarkMode(!isDarkMode);
          }, 50);
        }}
        currentColor={primaryColor}
        onColorSelect={(color) => {
          setPrimaryColor(color);
          toast.success('הצבע עודכן בהצלחה');
        }}
        isExpanded={sheetOpen}
        savedQueries={savedQueries}
        onSelectQuery={handleRunSavedQuery}
        onDeleteQuery={handleDeleteQuery}
        recentlySaved={recentlySavedId}
        hasUnreadQueries={hasUnreadQueries}
      />

      {/* Main Content - Chat + Analytics Split */}
      <div className="flex-1 flex flex-col min-w-0" ref={mainContainerRef}>
        {/* Header */}
        <header className="border-b border-border bg-card px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="w-24"></div>
            <div className="flex items-center gap-2">
              <span className="text-primary text-sm">BI</span>
              <h2 className="text-sm">Chatbot</h2>
            </div>
            <img src={foxLogo} alt="FOX Logo" className="h-8" />
          </div>
        </header>

        {/* Split View: Chat Area + Analytics Panel */}
        {isEmpty ? (
          <div ref={chatContainerRef} className="flex-1 overflow-y-auto relative">
            <div className="h-full flex flex-col">
              <div className="flex-1 flex items-center justify-center">
                <div className="w-full">
                  <WelcomeScreen 
                    onQuestionClick={handleQuestionClick} 
                    userName={user?.name}
                    onSend={handleSendMessage}
                    disabled={isThinking}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex overflow-hidden flex-col lg:flex-row relative">
            {/* Chat Area - RIGHT SIDE */}
            <div className={`
              flex flex-col h-full order-2 lg:order-1
              ${isAnalyticsExpanded ? 'hidden lg:flex' : 'flex'}
            `}
            style={isAnalyticsExpanded && window.innerWidth >= 1024 ? { width: `${100 - analyticsPanelWidth}%` } : { width: '100%' }}
            >
              <div ref={chatContainerRef} className="flex-1 overflow-y-auto overflow-x-visible px-4 md:px-6">
                <div className="max-w-full mx-auto pt-2 md:pt-4 pb-12">
                  {messages.map((message) => (
                    <ChatBubble
                      key={message.id}
                      type={message.type}
                      message={message.content}
                      userName={firstName}
                      hasVisualization={!!message.visualization}
                      isActive={message.id === activeMessageId}
                      onClick={() => message.visualization && handleBubbleClick(message.id)}
                      onExpandChart={() => handleExpandChart(message.id)}
                      isAnalyticsExpanded={isAnalyticsExpanded}
                      showActions={message.type === 'ai' && message.showActions}
                      onInsights={() => toast.info('תובנות חכמות - בקרוב')}
                      onSaveQuery={handleSaveQuery}
                      onExport={(format) => handleExport(format as 'excel' | 'csv')}
                      onShowSQL={() => {
                        setMessages(prev => prev.map(m => 
                          m.id === message.id ? { ...m, showSQL: !m.showSQL } : m
                        ));
                      }}
                      showSQL={message.showSQL}
                      sql={message.sql}
                      visualizationData={message.visualization?.data}
                      visualization={
                        message.visualization ? (
                          <InlineVisualization
                            data={message.visualization.data}
                            type={message.visualization.type}
                            valuePrefix={message.visualization.valuePrefix}
                            valueSuffix={message.visualization.valueSuffix}
                          />
                        ) : undefined
                      }
                    />
                  ))}
                  {isThinking && (
                    <ChatBubble type="ai" message="" isThinking={true} />
                  )}
                </div>
              </div>
              
              <div className="flex-shrink-0 bg-background/95 backdrop-blur-sm border-t border-border">
                <ChatInput onSend={handleSendMessage} disabled={isThinking} hasMessages={true} />
              </div>
            </div>

            {/* Resizable Handle - Only shown on desktop when panel is open */}
            {isAnalyticsExpanded && activeMessageId && (
              <div className="hidden lg:block order-2">
                <ResizableHandle 
                  onResize={handleResizePanel} 
                />
              </div>
            )}

            {/* Analytics Panel - LEFT SIDE, Only shown when explicitly opened */}
            {isAnalyticsExpanded && activeMessageId && (
              <div 
                className="fixed inset-0 z-50 lg:relative lg:z-auto transition-all duration-300 bg-background order-3"
                style={window.innerWidth >= 1024 ? { width: `${analyticsPanelWidth}%` } : undefined}
              >
                <AnalyticsPanel
                  isExpanded={isAnalyticsExpanded}
                  activeMessageId={activeMessageId}
                  visualization={activeMessage?.visualization}
                  userQuestion={activeMessageId ? getUserQuestionForMessage(activeMessageId) : undefined}
                  onClose={handleCloseAnalytics}
                  onInsights={() => toast.info('תובנות חכמות - בקרוב')}
                  onSaveQuery={handleSaveQuery}
                  onExport={(format) => handleExport(format as 'excel' | 'csv')}
                  onShowSQL={() => {
                    if (activeMessage) {
                      setMessages(prev => prev.map(m => 
                        m.id === activeMessage.id ? { ...m, showSQL: !m.showSQL } : m
                      ));
                    }
                  }}
                  showSQL={activeMessage?.showSQL || false}
                  sql={activeMessage?.sql}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;