import React, { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { BookOpen, Map, Sparkles, Search, Plus, Check } from 'lucide-react';
import Mermaid from './Mermaid';
import api from '../utils/api';

const NotesView = ({ notes, onTopicClick, docId, onNotesUpdated }) => {
    const [pageIndex, setPageIndex] = useState(0);
    const pageSize = 5000;

    // Web search state
    const [searchQuery, setSearchQuery] = useState('');
    const [webResult, setWebResult] = useState(null);
    const [webLoading, setWebLoading] = useState(false);
    const [webError, setWebError] = useState(null);
    const [addedToNotes, setAddedToNotes] = useState(false);

    const handleWebSearch = async () => {
        const q = searchQuery.trim();
        if (!q) return;
        setWebLoading(true);
        setWebError(null);
        setWebResult(null);
        setAddedToNotes(false);
        try {
            const res = await api.post('/web-search', { concept: q });
            setWebResult(res.data);
        } catch (err) {
            setWebError(err?.response?.data?.error || err.message);
        } finally {
            setWebLoading(false);
        }
    };

    const handleAddToNotes = async () => {
        if (!docId || !webResult?.summary) return;
        try {
            await api.post(`/notes/${docId}/append`, {
                content: `## 🌐 Web Notes: ${webResult.concept}\n\n${webResult.summary}`
            });
            setAddedToNotes(true);
            if (onNotesUpdated) onNotesUpdated();
        } catch (err) {
            setWebError('Failed to add to notes');
        }
    };

    const pages = useMemo(() => {
        if (!notes) return [''];
        const paragraphs = notes.split(/\n\s*\n/).filter(Boolean);
        const paged = [];
        let current = '';
        for (const paragraph of paragraphs) {
            const next = current ? `${current}\n\n${paragraph}` : paragraph;
            if (next.length > pageSize && current) {
                paged.push(current);
                current = paragraph;
            } else {
                current = next;
            }
        }
        if (current) {
            paged.push(current);
        }
        return paged.length > 0 ? paged : [''];
    }, [notes]);

    const totalPages = pages.length;
    const currentPage = Math.min(pageIndex, totalPages - 1);
    return (
        <div className="h-full flex flex-col glass-panel overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-accent/20 text-accent">
                    <BookOpen className="w-5 h-5" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Smart Notes</h3>
                    <p className="text-xs text-gray-400">AI Generated • Subject Specific</p>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                {/* ── Web Search Bar ── */}
                <div className="mb-4 flex gap-2">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleWebSearch()}
                            placeholder="Search web for a concept…"
                            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-slate-800 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                        />
                    </div>
                    <button
                        onClick={handleWebSearch}
                        disabled={webLoading || !searchQuery.trim()}
                        className="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50 transition-colors"
                    >
                        {webLoading ? '…' : '🔍'}
                    </button>
                </div>

                {/* Web search results */}
                {webError && <p className="text-xs text-red-400 mb-3">{webError}</p>}
                {webResult && (
                    <div className="mb-6 p-4 rounded-lg bg-blue-900/20 border border-blue-500/30">
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-blue-400">
                                🌐 Web: {webResult.concept}
                            </h4>
                            <div className="flex gap-2">
                                {docId && !addedToNotes && (
                                    <button
                                        onClick={handleAddToNotes}
                                        className="flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-green-600 hover:bg-green-500 text-white transition-colors"
                                    >
                                        <Plus className="w-3 h-3" /> Add to Notes
                                    </button>
                                )}
                                {addedToNotes && (
                                    <span className="flex items-center gap-1 text-xs text-green-400">
                                        <Check className="w-3 h-3" /> Added
                                    </span>
                                )}
                                <button
                                    onClick={() => { setWebResult(null); setSearchQuery(''); setAddedToNotes(false); }}
                                    className="text-xs px-2 py-1 text-gray-400 hover:text-white"
                                >
                                    ✕
                                </button>
                            </div>
                        </div>
                        <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
                            {webResult.summary}
                        </div>
                        {webResult.search_results?.length > 0 && (
                            <details className="mt-2 text-xs">
                                <summary className="text-gray-400 cursor-pointer hover:text-gray-200">
                                    {webResult.search_results.length} sources
                                </summary>
                                <ul className="mt-1 space-y-1 pl-3">
                                    {webResult.search_results.map((r, i) => (
                                        <li key={i}>
                                            <a href={r.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                                                {r.title}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </details>
                        )}
                    </div>
                )}
                <div className="flex items-center justify-between mb-4">
                    <div className="text-xs text-gray-400">
                        Page {totalPages === 0 ? 0 : currentPage + 1} of {totalPages}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPageIndex((prev) => Math.max(prev - 1, 0))}
                            disabled={currentPage === 0}
                            className="text-xs px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-white disabled:opacity-50"
                        >
                            Prev
                        </button>
                        <button
                            onClick={() => setPageIndex((prev) => Math.min(prev + 1, totalPages - 1))}
                            disabled={currentPage >= totalPages - 1}
                            className="text-xs px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-white disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
                <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown
                        components={{
                            h1: ({ node, ...props }) => <h1 className="text-2xl font-bold bg-linear-to-r from-white to-accent bg-clip-text text-transparent mb-4 border-b border-white/10 pb-2" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-xl font-semibold text-white mt-6 mb-3 flex items-center gap-2" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-lg font-medium text-accent mt-4 mb-2" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc pl-5 space-y-1 text-gray-300" {...props} />,
                            strong: ({ node, ...props }) => <strong className="text-white font-semibold" {...props} />,
                            blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-accent/50 pl-4 py-1 my-4 bg-accent/5 rounded-r-lg italic text-gray-300" {...props} />,
                            code: ({ node, inline, className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '')
                                const isMermaid = match && match[1] === 'mermaid';
                                if (!inline && isMermaid) {
                                    return <Mermaid chart={String(children).replace(/\n$/, '')} />
                                }
                                return <code className={`${className} bg-white/10 px-1 rounded`} {...props}>{children}</code>
                            },
                            li: ({ node, ...props }) => (
                                <li
                                    className="pl-1 hover:text-accent cursor-pointer transition-colors"
                                    onClick={() => onTopicClick && onTopicClick(props.children)}
                                    title="Click to learn more with AI Tutor"
                                    {...props}
                                />
                            ),
                        }}
                    >
                        {pages[currentPage]}
                    </ReactMarkdown>
                </div>

                <div className="mt-8 p-4 rounded-xl bg-linear-to-br from-green-500/10 to-blue-500/10 border border-white/10">
                    <div className="flex items-center gap-2 mb-2 text-green-400">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-sm font-semibold">Adaptive Learning Path Detected</span>
                    </div>
                    <p className="text-xs text-gray-400">Based on your progress, the AI recommends these next steps.</p>
                </div>

                <div className="flex items-center justify-between mt-6">
                    <div className="text-xs text-gray-400">
                        Page {totalPages === 0 ? 0 : currentPage + 1} of {totalPages}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPageIndex((prev) => Math.max(prev - 1, 0))}
                            disabled={currentPage === 0}
                            className="text-xs px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-white disabled:opacity-50"
                        >
                            Prev
                        </button>
                        <button
                            onClick={() => setPageIndex((prev) => Math.min(prev + 1, totalPages - 1))}
                            disabled={currentPage >= totalPages - 1}
                            className="text-xs px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-white disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NotesView;
