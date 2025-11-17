import React, { useState } from 'react';
import { Upload, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';

interface BugReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (description: string, image?: File) => void;
}

export function BugReportDialog({ open, onOpenChange, onSubmit }: BugReportDialogProps) {
  const [description, setDescription] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (description.trim()) {
      onSubmit(description, images[0] || undefined);
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setDescription('');
        setImages([]);
        onOpenChange(false);
      }, 2000);
    }
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newImages = Array.from(e.target.files);
      setImages(prev => [...prev, ...newImages]);
    }
  };

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" dir="rtl">
        {submitted ? (
          <div className="py-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg mb-2">דיווח נשלח בהצלחה</h3>
            <p className="text-sm text-muted-foreground">אנחנו מטפלים בזה, תודה!</p>
          </div>
        ) : (
          <>
            <DialogHeader className="text-right flex flex-col items-start">
              <DialogTitle>דווח על באג</DialogTitle>
              <DialogDescription className="text-right">
                תאר את הבעיה שנתקלת בה ונטפל בה בהקדם
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm mb-2 block text-right">תיאור הבעיה</label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="תאר את הבעיה במפורט..."
                  className="min-h-[120px] resize-none text-right w-full max-w-full break-words"
                  style={{ fieldSizing: 'content' as any, overflowWrap: 'break-word' }}
                  dir="rtl"
                />
              </div>

              <div>
                <label className="text-sm mb-2 block text-right">צרף תמונות (אופציונלי)</label>
                
                {/* Image Preview Grid */}
                {images.length > 0 && (
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {images.map((img, index) => (
                      <div key={index} className="relative group rounded-lg overflow-hidden border border-border bg-muted/30">
                        <img 
                          src={URL.createObjectURL(img)} 
                          alt={`תמונה ${index + 1}`}
                          className="w-full h-24 object-cover"
                        />
                        <button
                          onClick={() => removeImage(index)}
                          className="absolute top-1 left-1 p-1 bg-destructive/90 text-white rounded-full hover:bg-destructive transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-2">
                          <p className="text-white text-xs truncate text-right">{img.name}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="hidden"
                  id="bug-image-upload"
                  multiple
                />
                <label
                  htmlFor="bug-image-upload"
                  className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-border rounded-lg hover:bg-accent transition-colors cursor-pointer"
                >
                  <Upload className="w-5 h-5 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {images.length > 0 ? `${images.length} תמונות נבחרו` : 'לחץ להעלאת תמונות'}
                  </span>
                </label>
              </div>

              <Button
                onClick={handleSubmit}
                disabled={!description.trim()}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                שלח דיווח
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}