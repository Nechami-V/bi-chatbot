import React, { useState } from 'react';
import { GripVertical } from 'lucide-react';

interface ResizableHandleProps {
  onResize: (delta: number) => void;
}

export function ResizableHandle({ onResize }: ResizableHandleProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);

    const startX = e.clientX;
    let lastX = startX;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const currentDelta = moveEvent.clientX - lastX;
      onResize(currentDelta);
      lastX = moveEvent.clientX;
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);

    const startX = e.touches[0].clientX;
    let lastX = startX;

    const handleTouchMove = (moveEvent: TouchEvent) => {
      moveEvent.preventDefault();
      const currentDelta = moveEvent.touches[0].clientX - lastX;
      onResize(currentDelta);
      lastX = moveEvent.touches[0].clientX;
    };

    const handleTouchEnd = () => {
      setIsDragging(false);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };

    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd);
  };

  return (
    <div
      className={`
        relative w-2 hover:w-3 bg-transparent hover:bg-border/50 cursor-col-resize transition-all flex-shrink-0 group touch-none
        ${isDragging ? 'bg-primary/30 w-3' : ''}
      `}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
      style={{ cursor: 'col-resize' }}
    >
      {/* Visual indicator */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background border border-border rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-sm ${isDragging ? 'opacity-100' : ''}`}>
        <GripVertical className="w-3 h-3 text-muted-foreground" />
      </div>
    </div>
  );
}
