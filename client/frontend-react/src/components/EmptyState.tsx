import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { motion } from 'motion/react';

interface EmptyStateProps {
  onQuestionClick: (question: string) => void;
  userName?: string;
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function EmptyState({ onQuestionClick, userName, onSend, disabled = false }: EmptyStateProps) {
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
    <div className="w-full h-full flex items-center justify-center relative overflow-hidden px-8">
      {/* Professional Data Visualization Background - Much More Sophisticated */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-[0.05]">
        {/* Advanced Multi-Line Chart with Multiple Trends */}
        <motion.svg
          className="absolute top-[8%] right-[5%] w-[350px] h-[200px]"
          animate={{
            y: [0, -25, 0],
            opacity: [0.4, 0.7, 0.4]
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {/* Grid lines for professional look */}
          <line x1="0" y1="50" x2="350" y2="50" stroke="currentColor" strokeWidth="0.5" className="text-primary" opacity="0.2" />
          <line x1="0" y1="100" x2="350" y2="100" stroke="currentColor" strokeWidth="0.5" className="text-primary" opacity="0.2" />
          <line x1="0" y1="150" x2="350" y2="150" stroke="currentColor" strokeWidth="0.5" className="text-primary" opacity="0.2" />
          
          {/* Multiple trend lines */}
          <path
            d="M20,140 L70,110 L120,125 L170,90 L220,105 L270,75 L320,85"
            stroke="currentColor"
            strokeWidth="2.5"
            fill="none"
            className="text-primary"
            opacity="0.7"
          />
          <path
            d="M20,160 L70,135 L120,145 L170,115 L220,130 L270,100 L320,110"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            className="text-primary"
            opacity="0.5"
          />
          <path
            d="M20,120 L70,95 L120,105 L170,75 L220,85 L270,60 L320,70"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            className="text-primary"
            opacity="0.6"
          />
          
          {/* Data points */}
          {[20, 70, 120, 170, 220, 270, 320].map((x, i) => (
            <circle key={i} cx={x} cy={140 - i * 8} r="3" fill="currentColor" className="text-primary" opacity="0.6" />
          ))}
        </motion.svg>

        {/* Sophisticated Bar Chart with Grouped Bars */}
        <motion.svg
          className="absolute bottom-[12%] left-[3%] w-[280px] h-[160px]"
          animate={{
            y: [0, 20, 0],
            opacity: [0.35, 0.65, 0.35]
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {/* Base line */}
          <line x1="20" y1="140" x2="270" y2="140" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.3" />
          
          {/* Grouped bars pattern */}
          {[0, 1, 2, 3, 4, 5].map((group) => (
            <g key={group}>
              <rect 
                x={25 + group * 42} 
                y={140 - (60 + Math.sin(group) * 20)} 
                width="10" 
                height={60 + Math.sin(group) * 20} 
                fill="currentColor" 
                className="text-primary" 
                opacity="0.6" 
              />
              <rect 
                x={37 + group * 42} 
                y={140 - (45 + Math.cos(group) * 15)} 
                width="10" 
                height={45 + Math.cos(group) * 15} 
                fill="currentColor" 
                className="text-primary" 
                opacity="0.5" 
              />
            </g>
          ))}
        </motion.svg>

        {/* Complex Network Graph / Data Nodes */}
        <motion.svg
          className="absolute top-[20%] left-[8%] w-[240px] h-[180px]"
          animate={{
            scale: [1, 1.05, 1],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{
            duration: 11,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {/* Connection lines forming a network */}
          <line x1="40" y1="40" x2="120" y2="70" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          <line x1="120" y1="70" x2="180" y2="50" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          <line x1="40" y1="40" x2="80" y2="120" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          <line x1="80" y1="120" x2="160" y2="130" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          <line x1="180" y1="50" x2="160" y2="130" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          <line x1="120" y1="70" x2="80" y2="120" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.4" />
          
          {/* Nodes with different sizes indicating importance */}
          <circle cx="40" cy="40" r="8" fill="currentColor" className="text-primary" opacity="0.6" />
          <circle cx="120" cy="70" r="10" fill="currentColor" className="text-primary" opacity="0.7" />
          <circle cx="180" cy="50" r="6" fill="currentColor" className="text-primary" opacity="0.5" />
          <circle cx="80" cy="120" r="7" fill="currentColor" className="text-primary" opacity="0.6" />
          <circle cx="160" cy="130" r="9" fill="currentColor" className="text-primary" opacity="0.65" />
        </motion.svg>

        {/* Advanced Pie/Donut Chart */}
        <motion.svg
          className="absolute top-[45%] right-[8%] w-[200px] h-[200px]"
          animate={{
            rotate: [0, 360],
          }}
          transition={{
            duration: 60,
            repeat: Infinity,
            ease: "linear"
          }}
        >
          {/* Donut chart segments */}
          <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="20" className="text-primary" opacity="0.4" strokeDasharray="150 440" />
          <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="20" className="text-primary" opacity="0.5" strokeDasharray="110 440" strokeDashoffset="-150" />
          <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="20" className="text-primary" opacity="0.45" strokeDasharray="90 440" strokeDashoffset="-260" />
          <circle cx="100" cy="100" r="70" fill="none" stroke="currentColor" strokeWidth="20" className="text-primary" opacity="0.35" strokeDasharray="90 440" strokeDashoffset="-350" />
        </motion.svg>

        {/* Scatter Plot with Correlation */}
        <motion.svg
          className="absolute bottom-[18%] right-[15%] w-[260px] h-[180px]"
          animate={{
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {/* Axis lines */}
          <line x1="30" y1="150" x2="240" y2="150" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.3" />
          <line x1="30" y1="20" x2="30" y2="150" stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.3" />
          
          {/* Trend line */}
          <line x1="30" y1="130" x2="240" y2="40" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 4" className="text-primary" opacity="0.4" />
          
          {/* Scatter points with varying sizes */}
          {[
            [50, 120], [70, 110], [90, 95], [110, 85], [130, 80], 
            [150, 70], [170, 60], [190, 55], [210, 45], [230, 50]
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={3 + Math.random() * 2} fill="currentColor" className="text-primary" opacity="0.5" />
          ))}
        </motion.svg>

        {/* Candlestick / Financial Chart Pattern */}
        <motion.svg
          className="absolute top-[35%] left-[20%] w-[200px] h-[140px]"
          animate={{
            y: [0, -15, 0],
            opacity: [0.35, 0.6, 0.35]
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {[0, 1, 2, 3, 4, 5, 6].map((i) => {
            const x = 30 + i * 25;
            const high = 30 + Math.random() * 20;
            const low = high + 40 + Math.random() * 30;
            const open = high + Math.random() * 20;
            const close = open + (Math.random() - 0.5) * 25;
            
            return (
              <g key={i}>
                {/* Wick */}
                <line x1={x} y1={high} x2={x} y2={low} stroke="currentColor" strokeWidth="1" className="text-primary" opacity="0.5" />
                {/* Body */}
                <rect 
                  x={x - 6} 
                  y={Math.min(open, close)} 
                  width="12" 
                  height={Math.abs(close - open) + 1} 
                  fill="currentColor" 
                  className="text-primary" 
                  opacity={close > open ? "0.6" : "0.4"} 
                />
              </g>
            );
          })}
        </motion.svg>

        {/* Heatmap Grid Pattern */}
        <motion.svg
          className="absolute bottom-[25%] left-[12%] w-[180px] h-[140px]"
          animate={{
            opacity: [0.3, 0.55, 0.3]
          }}
          transition={{
            duration: 14,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          {[0, 1, 2, 3, 4].map((row) =>
            [0, 1, 2, 3, 4, 5].map((col) => (
              <rect
                key={`${row}-${col}`}
                x={20 + col * 26}
                y={20 + row * 26}
                width="22"
                height="22"
                fill="currentColor"
                className="text-primary"
                opacity={0.2 + Math.random() * 0.4}
                rx="2"
              />
            ))
          )}
        </motion.svg>

        {/* Area Chart with Gradient Effect */}
        <motion.svg
          className="absolute top-[55%] left-[28%] w-[280px] h-[150px]"
          animate={{
            x: [0, -20, 0],
            opacity: [0.3, 0.6, 0.3]
          }}
          transition={{
            duration: 16,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.4" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          
          {/* Area fill */}
          <path
            d="M20,130 L50,90 L90,100 L130,70 L170,85 L210,60 L250,75 L260,75 L260,130 Z"
            fill="url(#areaGradient)"
            className="text-primary"
          />
          
          {/* Line on top */}
          <path
            d="M20,130 L50,90 L90,100 L130,70 L170,85 L210,60 L250,75"
            stroke="currentColor"
            strokeWidth="2"
            fill="none"
            className="text-primary"
            opacity="0.6"
          />
        </motion.svg>
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
                  <ArrowLeft className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                </span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
