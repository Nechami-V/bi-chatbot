import React, { useState } from 'react';
import { ArrowUp } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  hasMessages?: boolean;
}

export function ChatInput({ onSend, disabled = false, hasMessages = false }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className={hasMessages ? "p-4" : ""}>
      <div className="max-w-4xl mx-auto">
        <div className="relative flex items-center gap-3 bg-background border border-border rounded-3xl px-5 py-3 focus-within:border-primary/50 transition-colors shadow-sm hover:shadow-md">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="שאל כל שאלה על הנתונים שלך..."
            disabled={disabled}
            className="flex-1 bg-transparent outline-none text-right"
            dir="rtl"
          />
          
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className="bg-foreground text-background rounded-full p-2 hover:bg-foreground/90 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
      </div>
    </form>
  );
}