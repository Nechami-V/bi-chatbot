import React from 'react';
import { Play, Edit, Trash2, Save } from 'lucide-react';

interface SavedQuery {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
}

interface SavedQueriesProps {
  queries: SavedQuery[];
  onRun: (query: SavedQuery) => void;
  onEdit: (query: SavedQuery) => void;
  onDelete: (id: string) => void;
}

export function SavedQueries({ queries, onRun, onEdit, onDelete }: SavedQueriesProps) {
  if (queries.length === 0) {
    return (
      <div className="h-full bg-card border-l border-border p-6 flex items-center justify-center">
        <div className="text-center space-y-3">
          <Save className="w-12 h-12 text-muted-foreground/40 mx-auto" />
          <p className="text-muted-foreground text-sm">אין שאילתות שמורות</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-card border-l border-border overflow-y-auto">
      <div className="p-4 border-b border-border sticky top-0 bg-card z-10">
        <h3 className="flex items-center gap-2">
          <Save className="w-5 h-5" />
          שאילתות שמורות
        </h3>
      </div>

      <div className="p-4 space-y-3">
        {queries.map((query) => (
          <div
            key={query.id}
            className="p-4 rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all group"
          >
            <div className="space-y-3">
              <div>
                <h4 className="text-sm mb-1">{query.title}</h4>
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {query.query}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onRun(query)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm"
                >
                  <Play className="w-3.5 h-3.5" />
                  הרץ
                </button>

                <button
                  onClick={() => onEdit(query)}
                  className="p-1.5 rounded-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
                >
                  <Edit className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onDelete(query.id)}
                  className="p-1.5 rounded-lg hover:bg-destructive/10 transition-colors text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}