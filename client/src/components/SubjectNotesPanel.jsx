import React, { useState } from 'react';
import { Loader, BookOpen } from 'lucide-react';
import axios from 'axios';

const SubjectNotesPanel = ({ onAnalysisComplete }) => {
    const [subjectInput, setSubjectInput] = useState('');
    const [isFetching, setIsFetching] = useState(false);

    const fetchSubjectNotes = async () => {
        if (!subjectInput.trim()) {
            alert('Please enter a subject.');
            return;
        }

        setIsFetching(true);
        try {
            const response = await axios.post('http://localhost:5001/generate/notes/subject', {
                subject: subjectInput.trim()
            });
            onAnalysisComplete(response.data);
        } catch (error) {
            console.error("Subject notes fetch failed", error);
            alert("No notes found for this subject or backend is not running.");
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
                        <p className="text-xs text-gray-400">Fetch from your library</p>
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
            </div>
        </div>
    );
};

export default SubjectNotesPanel;
