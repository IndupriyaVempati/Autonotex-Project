import React, { useState, useEffect } from 'react';
import api from '../utils/api';

const ConceptDetailsPanel = ({ conceptLabel, docId, onClose, onNotesUpdated }) => {
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Web search state
    const [webResult, setWebResult] = useState(null);
    const [webLoading, setWebLoading] = useState(false);
    const [webError, setWebError] = useState(null);
    const [addedToNotes, setAddedToNotes] = useState(false);

    useEffect(() => {
        if (!conceptLabel) return;

        const fetchConceptDetails = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/concept/${encodeURIComponent(conceptLabel)}`, {
                    params: docId ? { doc_id: docId } : {}
                });
                const data = response.data;
                setDetails(data);
                setError(null);
            } catch (err) {
                setError(err.message);
                setDetails(null);
            } finally {
                setLoading(false);
            }
        };

        fetchConceptDetails();
    }, [conceptLabel, docId]);

    if (loading) {
        return (
            <div className="fixed right-4 top-20 w-96 bg-slate-800 border border-purple-500 rounded-lg p-6 shadow-lg z-30">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-accent font-bold">Loading...</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
                </div>
                <div className="animate-pulse space-y-2">
                    <div className="h-4 bg-gray-700 rounded"></div>
                    <div className="h-4 bg-gray-700 rounded w-5/6"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="fixed right-4 top-20 w-96 bg-slate-800 border border-red-500 rounded-lg p-6 shadow-lg z-30">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-red-400 font-bold">Error</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
                </div>
                <p className="text-sm text-gray-300">{error}</p>
            </div>
        );
    }

    if (!details) return null;

    return (
        <div className="fixed right-4 top-20 w-96 bg-slate-800 border border-purple-500 rounded-lg p-6 shadow-lg z-30 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h2 className="text-accent font-bold text-lg">{details.concept || conceptLabel}</h2>
                    {details.explanation?.importance && (
                        <span className="text-xs bg-purple-900 text-purple-200 px-2 py-1 rounded mt-2 inline-block">
                            {details.explanation.importance}
                        </span>
                    )}
                </div>
                <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">✕</button>
            </div>

            {details.explanation?.explanation && (
                <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-200 mb-2">Overview</h3>
                    <p className="text-xs text-gray-300 leading-relaxed">{details.explanation.explanation}</p>
                </div>
            )}

            {details.explanation?.examples && details.explanation.examples.length > 0 && (
                <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-200 mb-2">Examples</h3>
                    <ul className="text-xs text-gray-300 space-y-1">
                        {details.explanation.examples.map((example, idx) => (
                            <li key={idx} className="flex items-start">
                                <span className="text-purple-400 mr-2">•</span>
                                <span>{example}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {details.explanation?.relatedConcepts && details.explanation.relatedConcepts.length > 0 && (
                <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-200 mb-2">Related Concepts</h3>
                    <div className="flex flex-wrap gap-2">
                        {details.explanation.relatedConcepts.map((concept, idx) => (
                            <span key={idx} className="text-xs bg-slate-700 text-gray-200 px-2 py-1 rounded border border-slate-600">
                                {concept}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {details.explanation?.commonMisunderstandings && (
                <div className="mb-4">
                    <h3 className="text-sm font-semibold text-yellow-400 mb-2">⚠️ Common Misunderstandings</h3>
                    <p className="text-xs text-gray-300">{details.explanation.commonMisunderstandings}</p>
                </div>
            )}

            {details.related_content && details.related_content.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-gray-200 mb-2">Related Content</h3>
                    <div className="text-xs text-gray-400 space-y-2">
                        {details.related_content.slice(0, 2).map((content, idx) => (
                            <p key={idx} className="p-2 bg-slate-700 rounded border-l-2 border-purple-500 truncate">
                                {content.content.substring(0, 100)}...
                            </p>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Web Search Section ── */}
            <div className="mt-4 pt-4 border-t border-white/10">
                {!webResult && !webLoading && (
                    <button
                        onClick={async () => {
                            setWebLoading(true);
                            setWebError(null);
                            try {
                                const res = await api.post('/web-search', { concept: conceptLabel });
                                setWebResult(res.data);
                            } catch (err) {
                                setWebError(err?.response?.data?.error || err.message);
                            } finally {
                                setWebLoading(false);
                            }
                        }}
                        className="w-full text-sm px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        🔍 Search Web for "{conceptLabel}"
                    </button>
                )}

                {webLoading && (
                    <div className="text-xs text-gray-400 text-center py-2 animate-pulse">
                        Searching the web…
                    </div>
                )}

                {webError && (
                    <p className="text-xs text-red-400 mt-2">{webError}</p>
                )}

                {webResult && (
                    <div className="mt-3 space-y-3">
                        <h3 className="text-sm font-semibold text-blue-400">🌐 Web Insights</h3>

                        {/* Summary */}
                        <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap bg-slate-900/60 p-3 rounded-lg border border-white/10 max-h-48 overflow-y-auto">
                            {webResult.summary}
                        </div>

                        {/* Source links */}
                        {webResult.search_results?.length > 0 && (
                            <details className="text-xs">
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

                        {/* Add to Notes button */}
                        {docId && !addedToNotes && (
                            <button
                                onClick={async () => {
                                    try {
                                        await api.post(`/notes/${docId}/append`, {
                                            content: `## 🌐 Web Notes: ${conceptLabel}\n\n${webResult.summary}`
                                        });
                                        setAddedToNotes(true);
                                        if (onNotesUpdated) onNotesUpdated();
                                    } catch {
                                        setWebError('Failed to add to notes');
                                    }
                                }}
                                className="w-full text-xs px-3 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white font-medium transition-colors"
                            >
                                ➕ Add to My Notes
                            </button>
                        )}
                        {addedToNotes && (
                            <p className="text-xs text-green-400 text-center">✓ Added to notes</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ConceptDetailsPanel;
