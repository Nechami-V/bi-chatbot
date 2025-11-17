import React, { useState } from 'react';
import { User, Lock } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import KTLogo from '../assets/kt-logo.png';

interface LoginScreenProps {
  onLogin: (email: string, password: string) => void;
  onSkip: () => void;
}

export function LoginScreen({ onLogin, onSkip }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isNewUser, setIsNewUser] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      onLogin(email, password);
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gradient-to-br from-background via-muted/20 to-background" dir="rtl">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <img src={KTLogo} alt="KT Logo" className="h-20" />
          </div>

          <div className="space-y-3">
            <h1 className="text-3xl">ברוכים הבאים ל-BI Chatbot</h1>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm block text-right" htmlFor="username">אימייל</label>
            <div className="relative">
              <User className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="username"
                type="email"
                placeholder="הזן אימייל"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="text-right pr-10 rounded-full h-12"
                dir="rtl"
                autoFocus
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm block text-right" htmlFor="password">סיסמה</label>
            <div className="relative">
              <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="password"
                type="password"
                placeholder="הזן סיסמה"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="text-right pr-10 rounded-full h-12"
                dir="rtl"
              />
            </div>
          </div>

          <div className="pt-2">
            <Button 
              type="submit" 
              className="w-full h-12 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              כניסה
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}