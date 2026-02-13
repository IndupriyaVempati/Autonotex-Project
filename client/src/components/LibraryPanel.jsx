import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import { Trash2, Eye, RefreshCcw } from 'lucide-react';

const LibraryPanel = ({ isAdmin, onLoadDocument, onLoadCombined }) => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const formatDate = (value) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString();
  };

  const fetchNotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/notes', { params: { limit: 50 } });
      setNotes(response.data.notes || []);
    } catch {
      setError('Failed to load library.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, []);

  const handleDelete = async (docId, scope) => {
    if (scope === 'shared' && !isAdmin) {
      return;
    }
    const ok = window.confirm('Delete this document?');
    if (!ok) return;

    try {
      await api.delete(`/notes/${docId}`);
      await fetchNotes();
    } catch {
      alert('Delete failed.');
    }
  };

  if (loading) {
    return (
      <div className="glass-panel p-6 rounded-lg border border-white/10">
        <div className="text-sm text-gray-400">Loading library...</div>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6 rounded-lg border border-white/10 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Library</h3>
        <div className="flex items-center gap-2">
          {onLoadCombined && (
            <>
              <button
                onClick={() => onLoadCombined('shared')}
                className="text-xs px-3 py-1 rounded-lg bg-accent/10 text-accent border border-accent/30"
              >
                Study Admin
              </button>
              <button
                onClick={() => onLoadCombined('private')}
                className="text-xs px-3 py-1 rounded-lg bg-white/5 text-gray-200 border border-white/10"
              >
                Study Mine
              </button>
            </>
          )}
          <button
            onClick={fetchNotes}
            className="text-xs px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 flex items-center gap-2"
          >
            <RefreshCcw className="w-3 h-3" />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-300 mb-4">{error}</div>
      )}

      {notes.length === 0 ? (
        <div className="text-sm text-gray-400">No documents found yet.</div>
      ) : (
        <div className="space-y-3">
          {notes.map((note) => {
            const scope = note.scope || 'shared';
            const canDelete = isAdmin || scope === 'private';
            return (
              <div
                key={note.doc_id}
                className="p-4 rounded-lg border border-white/10 bg-white/5 flex items-center justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-white">
                    {note.subject || 'Untitled'}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {scope === 'shared' ? 'Admin Library' : 'My Library'}
                  </div>
                  {formatDate(note.updated_at || note.created_at) && (
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDate(note.updated_at || note.created_at)}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onLoadDocument(note.doc_id)}
                    className="text-xs px-3 py-1 rounded-lg bg-accent/20 text-accent border border-accent/40 flex items-center gap-2"
                  >
                    <Eye className="w-3 h-3" />
                    Open
                  </button>
                  <button
                    onClick={() => handleDelete(note.doc_id, scope)}
                    disabled={!canDelete}
                    className={`text-xs px-3 py-1 rounded-lg border flex items-center gap-2 ${
                      canDelete
                        ? 'bg-red-500/10 text-red-200 border-red-500/30 hover:bg-red-500/20'
                        : 'bg-white/5 text-gray-500 border-white/10 cursor-not-allowed'
                    }`}
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default LibraryPanel;
