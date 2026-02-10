import React, { useEffect, useState } from 'react';
import { Loader, BookOpen } from 'lucide-react';
import api from '../utils/api';

const SubjectNotesPanel = ({ onAnalysisComplete }) => {
    const [subjectInput, setSubjectInput] = useState('');
    const [isFetching, setIsFetching] = useState(false);
    const [subjects, setSubjects] = useState([]);
    const [subjectsLoading, setSubjectsLoading] = useState(true);
    const [subjectsError, setSubjectsError] = useState(null);
    const [scope, setScope] = useState('shared');
    const [hint, setHint] = useState(null);

    useEffect(() => {
        let active = true;
        const fetchSubjects = async () => {
            setSubjectsLoading(true);
            setSubjectsError(null);
            try {
                const response = await api.get('/subjects', { params: { scope } });
                if (!active) return;
                setSubjects(response.data.subjects || []);
            } catch {
                if (!active) return;
                setSubjectsError('Unable to load subjects.');
            } finally {
                if (active) {
                    setSubjectsLoading(false);
                }
            }
        };

        fetchSubjects();
        return () => {
            active = false;
        };
    }, [scope]);

    useEffect(() => {
        setHint(null);
    }, [scope]);

    const fetchSubjectNotes = async () => {
        if (!subjectInput.trim()) {
            alert('Please enter a subject.');
            return;
        }

        setIsFetching(true);
        setHint(null);
        try {
            const response = await api.post('/generate/notes/subject', {
                subject: subjectInput.trim(),
                scope
            });
            onAnalysisComplete(response.data);
        } catch (error) {
            console.error("Subject notes fetch failed", error);
            const status = error?.response?.status;
            if (status === 404 && scope === 'private') {
                setHint('No notes found in My Library. Try the Admin Library.');
            } else {
                alert("No notes found for this subject or backend is not running.");
            }
        } finally {
            setIsFetching(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-8 h-full">
            <div className="w-full max-w-3xl p-6 rounded-2xl border border-white/10 bg-white/5">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-accent/20 text-accent">
                        <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Subject Notes</h3>
                        <p className="text-xs text-gray-400">
                            {scope === 'shared' ? 'Fetch from Admin Library' : 'Fetch from My Library'}
                        </p>
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    <input
                        type="text"
                        value={subjectInput}
                        onChange={(e) => setSubjectInput(e.target.value)}
                        placeholder="e.g., DBMS, Operating Systems, Machine Learning"
                        className="flex-1 px-4 py-2 rounded-lg bg-slate-900/70 border border-white/10 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/40"
                    />
                    <button
                        onClick={fetchSubjectNotes}
                        disabled={isFetching}
                        className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {isFetching ? (
                            <span className="inline-flex items-center gap-2">
                                <Loader className="w-4 h-4 animate-spin" />
                                Fetching...
                            </span>
                        ) : (
                            'Fetch Notes'
                        )}
                    </button>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-gray-400">Source:</span>
                    <button
                        type="button"
                        onClick={() => setScope('shared')}
                        className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                            scope === 'shared'
                                ? 'bg-accent/20 text-accent border-accent/40'
                                : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
                        }`}
                    >
                        Admin Library
                    </button>
                    <button
                        type="button"
                        onClick={() => setScope('private')}
                        className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                            scope === 'private'
                                ? 'bg-accent/20 text-accent border-accent/40'
                                : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
                        }`}
                    >
                        My Library
                    </button>
                    {hint && (
                        <div className="ml-auto flex items-center gap-2">
                            <div className="text-xs text-yellow-300">{hint}</div>
                            <button
                                type="button"
                                onClick={() => setScope('shared')}
                                className="text-xs px-2 py-1 rounded-full border border-yellow-400/40 text-yellow-200 hover:bg-yellow-500/10"
                            >
                                Switch to Admin
                            </button>
                        </div>
                    )}
                </div>

                <div className="mt-4">
                    <div className="text-xs text-gray-400 mb-2">Available subjects</div>
                    {subjectsLoading ? (
                        <div className="text-xs text-gray-500">Loading subjects...</div>
                    ) : subjectsError ? (
                        <div className="text-xs text-red-300">{subjectsError}</div>
                    ) : subjects.length === 0 ? (
                        <div className="text-xs text-gray-500">No subjects found yet.</div>
                    ) : (
                        <div className="flex flex-wrap gap-2">
                            {subjects.map((subject) => (
                                <button
                                    key={subject}
                                    type="button"
                                    onClick={() => setSubjectInput(subject)}
                                    className="text-xs px-3 py-1 rounded-full border border-white/10 bg-white/5 text-gray-300 hover:bg-white/10"
                                >
                                    {subject}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SubjectNotesPanel;
