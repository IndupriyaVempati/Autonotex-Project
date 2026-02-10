import React, { useState, useEffect } from 'react';
import { Loader, BookOpen, Play } from 'lucide-react';
import api from '../utils/api';

const QuizSelection = ({ onQuizStart }) => {
    const [subjects, setSubjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [scope, setScope] = useState('shared');
    const [questionCount, setQuestionCount] = useState(15);

    useEffect(() => {
        fetchSubjects();
    }, [scope]);

    const fetchSubjects = async () => {
        try {
            const response = await api.get('/subjects', { params: { scope } });
            setSubjects(response.data.subjects || []);
        } catch (error) {
            console.error("Failed to fetch subjects", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="h-full flex flex-col glass-panel overflow-hidden">
            <div className="p-4 border-b border-white/10 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-accent/20 text-accent">
                    <BookOpen className="w-5 h-5" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Subject Quizzes</h3>
                    <p className="text-xs text-gray-400">Test Your Knowledge</p>
                </div>
            </div>

            <div className="px-6 pt-4 flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
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
                </div>

                <div className="flex items-center gap-2 ml-auto">
                    <span className="text-xs text-gray-400">Questions:</span>
                    <input
                        type="number"
                        min="5"
                        max="30"
                        value={questionCount}
                        onChange={(e) => setQuestionCount(Number(e.target.value) || 15)}
                        className="w-20 px-2 py-1 rounded-lg bg-slate-900/70 border border-white/10 text-white text-xs"
                    />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                {loading ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader className="w-8 h-8 text-accent animate-spin" />
                    </div>
                ) : subjects.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <BookOpen className="w-12 h-12 text-gray-500 mb-4" />
                        <p className="text-gray-400">No subjects found. Upload notes first!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {subjects.map((subject) => (
                            <button
                                key={subject}
                                onClick={() => onQuizStart(subject, scope, questionCount)}
                                className="p-4 rounded-lg border border-accent/30 bg-accent/5 hover:bg-accent/15 transition-all group"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <h4 className="text-white font-semibold text-left">{subject}</h4>
                                    <Play className="w-4 h-4 text-accent group-hover:translate-x-1 transition-transform" />
                                </div>
                                <p className="text-xs text-gray-400 text-left">Start Quiz</p>
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default QuizSelection;
