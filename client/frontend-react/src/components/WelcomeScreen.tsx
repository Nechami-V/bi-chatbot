import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft } from 'lucide-react';

interface WelcomeScreenProps {
  onQuestionClick: (question: string) => void;
  onSend: (message: string) => void;
  userName?: string;
  disabled?: boolean;
}

export function WelcomeScreen({ onQuestionClick, onSend, userName, disabled }: WelcomeScreenProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage('');
    }
  };

  const suggestedQuestions = [
    'סיכום נתונים לתקופה',
    'שינויי ביצועים בחודש האחרון',
    'פילוח לפי קטגוריות',
    'מגמות מרכזיות',
    'נתונים חריגים שדורשים תשומת לב'
  ];

  return (
    <div className="relative flex items-center justify-center h-full px-8 overflow-hidden">
      {/* Modern Data Background - Full Screen */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        {/* Gradient base with blur */}
        <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5" />
        
        {/* Floating glass cards with real data metrics */}
        <motion.div
          className="absolute top-[8%] right-[12%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-6 shadow-2xl"
          style={{ width: '280px' }}
          animate={{
            y: [0, -20, 0],
            rotate: [0, 2, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>הכנסות חודשיות</span>
              <span className="text-emerald-500">+12.5%</span>
            </div>
            <div className="text-3xl font-bold">₪2.4M</div>
            <div className="flex gap-1 h-12 items-end">
              {[65, 72, 68, 85, 78, 92, 88, 95, 100, 98, 105, 112].map((h, i) => (
                <motion.div
                  key={i}
                  className="flex-1 bg-primary/60 rounded-t"
                  style={{ height: `${h}%` }}
                  animate={{
                    height: [`${h * 0.8}%`, `${h}%`, `${h * 0.8}%`]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.1
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-[45%] right-[8%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-6 shadow-2xl"
          style={{ width: '240px' }}
          animate={{
            y: [0, 15, 0],
            rotate: [0, -1, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-4">
            <div className="text-xs text-muted-foreground">התפלגות לקוחות</div>
            <div className="relative w-28 h-28 mx-auto">
              {[
                { percent: 35, color: 'text-primary', offset: 0 },
                { percent: 28, color: 'text-purple-500', offset: 35 },
                { percent: 22, color: 'text-blue-500', offset: 63 },
                { percent: 15, color: 'text-emerald-500', offset: 85 },
              ].map((segment, i) => (
                <motion.svg
                  key={i}
                  className="absolute inset-0 -rotate-90"
                  viewBox="0 0 100 100"
                >
                  <motion.circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    strokeWidth="16"
                    className={segment.color}
                    strokeDasharray={`${segment.percent * 2.51} 251`}
                    strokeDashoffset={-segment.offset * 2.51}
                    animate={{
                      strokeDasharray: [`${segment.percent * 2.3} 251`, `${segment.percent * 2.51} 251`, `${segment.percent * 2.3} 251`]
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      delay: i * 0.2
                    }}
                  />
                </motion.svg>
              ))}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold">2.8K</div>
                  <div className="text-xs text-muted-foreground">לקוחות</div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-[15%] right-[15%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-5 shadow-2xl"
          style={{ width: '200px' }}
          animate={{
            y: [0, -12, 0],
            x: [0, 8, 0],
          }}
          transition={{
            duration: 7,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="text-xs text-muted-foreground">סטטוס מערכת</div>
            {[
              { label: 'שרתים פעילים', value: '99.8%', color: 'bg-emerald-500' },
              { label: 'זמן תגובה', value: '45ms', color: 'bg-blue-500' },
              { label: 'CPU', value: '34%', color: 'bg-primary' },
            ].map((stat, i) => (
              <div key={i} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span>{stat.label}</span>
                  <span className="font-mono">{stat.value}</span>
                </div>
                <motion.div className="h-1.5 bg-muted/50 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${stat.color} rounded-full`}
                    initial={{ width: '0%' }}
                    animate={{ width: ['60%', '85%', '60%'] }}
                    transition={{
                      duration: 2.5,
                      repeat: Infinity,
                      delay: i * 0.3
                    }}
                  />
                </motion.div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="absolute top-[25%] left-[15%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-6 shadow-2xl"
          style={{ width: '260px' }}
          animate={{
            y: [0, 18, 0],
            rotate: [0, 1, 0],
          }}
          transition={{
            duration: 9,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="text-xs text-muted-foreground">טרנדים שבועיים</div>
            <div className="space-y-2">
              {[
                { metric: 'מכירות', value: '+18.2%', trend: 'up' },
                { metric: 'משתמשים חדשים', value: '+24.7%', trend: 'up' },
                { metric: 'זמן טעינה', value: '-12.3%', trend: 'down' },
              ].map((item, i) => (
                <motion.div
                  key={i}
                  className="flex items-center justify-between py-2 px-3 bg-muted/30 rounded-lg"
                  animate={{
                    backgroundColor: ['rgba(var(--muted) / 0.2)', 'rgba(var(--muted) / 0.4)', 'rgba(var(--muted) / 0.2)']
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.4
                  }}
                >
                  <span className="text-sm">{item.metric}</span>
                  <span className={`text-sm font-mono ${item.trend === 'up' ? 'text-emerald-500' : 'text-blue-500'}`}>
                    {item.value}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-[25%] left-[10%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-5 shadow-2xl"
          style={{ width: '300px' }}
          animate={{
            y: [0, -15, 0],
            x: [0, -10, 0],
          }}
          transition={{
            duration: 11,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">ביצועים שנתיים</span>
              <span className="text-xs text-emerald-500 font-mono">+47.3%</span>
            </div>
            <svg viewBox="0 0 300 80" className="w-full">
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="currentColor" stopOpacity="0.4" className="text-primary" />
                  <stop offset="100%" stopColor="currentColor" stopOpacity="0" className="text-primary" />
                </linearGradient>
              </defs>
              
              <motion.path
                d="M10,60 L40,55 L70,48 L100,52 L130,45 L160,38 L190,42 L220,32 L250,28 L280,20"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className="text-primary"
                animate={{
                  pathLength: [0, 1],
                  opacity: [0.5, 1, 0.5]
                }}
                transition={{
                  pathLength: { duration: 2, repeat: Infinity },
                  opacity: { duration: 3, repeat: Infinity }
                }}
              />
              
              <motion.path
                d="M10,60 L40,55 L70,48 L100,52 L130,45 L160,38 L190,42 L220,32 L250,28 L280,20 L280,80 L10,80 Z"
                fill="url(#lineGradient)"
                animate={{
                  opacity: [0.3, 0.6, 0.3]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity
                }}
              />
              
              {[10, 40, 70, 100, 130, 160, 190, 220, 250, 280].map((x, i) => {
                const y = [60, 55, 48, 52, 45, 38, 42, 32, 28, 20][i];
                return (
                  <motion.circle
                    key={i}
                    cx={x}
                    cy={y}
                    r="3"
                    fill="currentColor"
                    className="text-primary"
                    animate={{
                      r: [2, 4, 2],
                      opacity: [0.5, 1, 0.5]
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      delay: i * 0.15
                    }}
                  />
                );
              })}
            </svg>
          </div>
        </motion.div>

        <motion.div
          className="absolute top-[12%] left-[38%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-5 shadow-2xl"
          style={{ width: '220px' }}
          animate={{
            y: [0, 20, 0],
            rotate: [0, -2, 0],
          }}
          transition={{
            duration: 8.5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="text-xs text-muted-foreground">מטריקות בזמן אמת</div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'פניות', value: '1,247' },
                { label: 'המרות', value: '186' },
                { label: 'הכנסה', value: '₪45K' },
                { label: 'ROI', value: '3.2x' },
              ].map((metric, i) => (
                <motion.div
                  key={i}
                  className="text-center p-2 bg-muted/30 rounded-lg"
                  animate={{
                    scale: [1, 1.05, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.25
                  }}
                >
                  <div className="text-xs text-muted-foreground mb-1">{metric.label}</div>
                  <div className="text-lg font-bold font-mono">{metric.value}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="absolute bottom-[40%] left-[35%] bg-card/40 backdrop-blur-md border border-border/30 rounded-2xl p-5 shadow-2xl"
          style={{ width: '180px' }}
          animate={{
            y: [0, -18, 0],
            rotate: [0, 2, 0],
          }}
          transition={{
            duration: 9.5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <div className="space-y-3">
            <div className="text-xs text-muted-foreground">התראות</div>
            {[
              { text: 'עדכון מוצלח', time: '2 דק' },
              { text: 'גיבוי הושלם', time: '15 דק' },
              { text: 'דוח נוצר', time: '1 שעה' },
            ].map((alert, i) => (
              <motion.div
                key={i}
                className="flex items-center gap-2 text-xs"
                animate={{
                  opacity: [0.4, 1, 0.4]
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  delay: i * 0.8
                }}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <div className="flex-1">{alert.text}</div>
                <div className="text-muted-foreground">{alert.time}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Subtle animated grid */}
        <motion.div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(hsl(var(--primary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
          animate={{
            opacity: [0.02, 0.05, 0.02]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        {/* Floating particles - minimal and modern */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-primary/40 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -60, 0],
              opacity: [0, 0.6, 0],
            }}
            transition={{
              duration: 5 + Math.random() * 3,
              repeat: Infinity,
              delay: Math.random() * 5,
              ease: "easeInOut"
            }}
          />
        ))}
      </div>

      {/* Main Content */}
      <div className="max-w-4xl w-full space-y-12 relative z-10">
        {/* Hero Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-4 text-center"
        >
          <h1 className="text-4xl md:text-5xl leading-tight font-bold tracking-tight">
            קבלו תשובה ברורה מתוך הנתונים
          </h1>
          <p className="text-lg text-muted-foreground">
            כל שאלה מקבלת תשובה ישירות מתוך המידע שלך.
          </p>
        </motion.div>

        {/* Main Input - Large and Inviting */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
        >
          <form onSubmit={handleSubmit}>
            <div className="relative group">
              {/* Input Container */}
              <div className="flex items-center gap-3 bg-card/80 backdrop-blur-sm border-2 border-border rounded-2xl px-6 py-5 shadow-lg focus-within:border-primary focus-within:shadow-2xl focus-within:shadow-primary/10 transition-all duration-300 hover:shadow-xl hover:border-border/80">
                {/* Input Field */}
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="שאל אותי כל שאלה על הנתונים שלך"
                  disabled={disabled}
                  className="flex-1 bg-transparent outline-none text-lg placeholder:text-muted-foreground/60 text-right"
                  dir="rtl"
                  autoFocus
                />
                
                {/* Submit Button - Icon Only */}
                <button
                  type="submit"
                  disabled={!message.trim() || disabled}
                  className="bg-primary text-primary-foreground p-3 rounded-xl hover:bg-primary/90 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              </div>
            </div>
          </form>
        </motion.div>

        {/* Suggested Questions as Chips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="space-y-3"
        >
          <p className="text-sm text-muted-foreground text-center">שאלות לדוגמה:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {suggestedQuestions.map((question, index) => (
              <motion.button
                key={index}
                onClick={() => onQuestionClick(question)}
                className="px-4 py-2 bg-muted/50 hover:bg-muted border border-border rounded-lg text-sm transition-all duration-200 hover:shadow-md hover:border-primary/30 group"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.5 + index * 0.1 }}
                whileHover={{ scale: 1.02 }}
              >
                <span className="flex items-center gap-2">
                  {question}
                  <ArrowLeft className="w-3 h-3 hidden group-hover:inline-block transition-all duration-200" />
                </span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}