import React, { useState } from 'react';
import api from '../utils/api';

const QuestionsView = ({ questions = [], docId }) => {
    const [selectedQuestion, setSelectedQuestion] = useState(null);
    const [answer, setAnswer] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [customQuestion, setCustomQuestion] = useState('');

    const handleAskQuestion = async (question) => {
        try {
            setLoading(true);
            setError(null);
            setAnswer(null);

            const response = await api.post('/question', {
                question,
                doc_id: docId
            });
            setAnswer(response.data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel p-6 rounded-lg border border-purple-500/30">
            <h2 className="text-lg font-bold text-accent mb-4">📚 Study Questions ({questions.length})</h2>

            <div className="mb-6 p-4 rounded-lg border border-white/10 bg-slate-900/40">
                <div className="text-sm font-semibold text-accent mb-2">Ask your own question</div>
                <div className="flex flex-col gap-3 sm:flex-row">
                    <input
                        type="text"
                        value={customQuestion}
                        onChange={(e) => setCustomQuestion(e.target.value)}
                        placeholder="Type a question about the document..."
                        className="flex-1 rounded-lg bg-slate-800/60 border border-white/10 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/40"
                    />
                    <button
                        onClick={() => {
                            const query = customQuestion.trim();
                            if (!query) return;
                            setSelectedQuestion(null);
                            handleAskQuestion(query);
                        }}
                        className="text-sm px-4 py-2 rounded-lg bg-accent/20 text-accent border border-accent/40 hover:bg-accent/30 transition-colors"
                    >
                        Ask
                    </button>
                </div>
                {!docId && (
                    <p className="text-xs text-gray-400 mt-2">Upload a document first to ask live questions.</p>
                )}
            </div>
            
            {(!questions || questions.length === 0) ? (
                <p className="text-gray-400 text-sm mb-6">No questions available. Upload a document to generate study questions.</p>
            ) : (
                <div className="space-y-3 mb-6">
                    {questions.map((q, idx) => (
                    <button
                        key={idx}
                        onClick={() => {
                            setSelectedQuestion(idx);
                            handleAskQuestion(q.question || q);
                        }}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                            selectedQuestion === idx
                                ? 'bg-purple-900/40 border-purple-500 shadow-lg'
                                : 'bg-slate-800/50 border-slate-700 hover:border-purple-500/50'
                        }`}
                    >
                        <div className="flex items-start justify-between">
                            <p className="text-sm text-gray-200 flex-1">{typeof q === 'string' ? q : q.question}</p>
                            {q.difficulty && (
                                <span className={`text-xs font-bold px-2 py-1 rounded ml-2 whitespace-nowrap ${
                                    q.difficulty === 'easy' ? 'bg-green-900/60 text-green-200' :
                                    q.difficulty === 'medium' ? 'bg-yellow-900/60 text-yellow-200' :
                                    'bg-red-900/60 text-red-200'
                                }`}>
                                    {q.difficulty}
                                </span>
                            )}
                        </div>
                    </button>
                    ))}
                </div>
            )}

            {loading && (
                <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                    <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-500 border-t-transparent"></div>
                        <p className="text-sm text-gray-300">Generating answer...</p>
                    </div>
                </div>
            )}

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-4">
                    <p className="text-sm text-red-200">Error: {error}</p>
                </div>
            )}

            {answer && (
                <div className="bg-linear-to-br from-slate-700/50 to-slate-800/50 rounded-lg p-4 border border-accent/30 space-y-4">
                    <div>
                        <h3 className="text-sm font-bold text-accent mb-2">📌 Question</h3>
                        <p className="text-sm text-gray-100 font-medium">{answer.question}</p>
                    </div>
                    
                    <div className="border-t border-white/10 pt-4">
                        <h3 className="text-sm font-bold text-accent mb-3">💡 Answer</h3>
                        <div className="text-sm text-gray-300 leading-relaxed space-y-2 max-h-60 overflow-y-auto">
                            {typeof answer.answer === 'string' ? (
                                answer.answer.split('\n').map((line, idx) => (
                                    line.trim() && (
                                        <p key={idx} className={`${line.startsWith('-') || line.startsWith('•') ? 'pl-4' : ''}`}>
                                            {line}
                                        </p>
                                    )
                                ))
                            ) : (
                                <p>{JSON.stringify(answer.answer)}</p>
                            )}
                        </div>
                    </div>

                    {answer.sources && answer.sources.length > 0 && (
                        <div className="border-t border-white/10 pt-4">
                            <h3 className="text-xs font-bold text-gray-400 mb-2">📖 Sources</h3>
                            <div className="space-y-1 max-h-24 overflow-y-auto">
                                {answer.sources.slice(0, 2).map((source, idx) => (
                                    <p key={idx} className="text-xs text-gray-400 p-2 bg-slate-900/50 rounded line-clamp-2 border border-white/5">
                                        {source.content?.substring(0, 80)}...
                                    </p>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {!loading && !answer && !error && selectedQuestion !== null && (
                <div className="text-center py-8">
                    <p className="text-gray-400 text-sm">Click a question to view the answer</p>
                </div>
            )}
        </div>
    );
};

export default QuestionsView;
