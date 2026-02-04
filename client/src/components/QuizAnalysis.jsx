import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle2, BookMarked } from 'lucide-react';

const QuizAnalysis = ({ quizResult, onRetake, onBack }) => {
    const [analysis, setAnalysis] = useState(null);

    useEffect(() => {
        generateAnalysis();
    }, [quizResult]);

    const generateAnalysis = () => {
        const { questions, userAnswers, totalQuestions, correctAnswers, subject } = quizResult;
        
        // Calculate metrics
        const score = (correctAnswers / totalQuestions) * 100;
        const weakTopics = [];
        const strongTopics = [];

        // Analyze by topics/categories
        const topicPerformance = {};

        Object.entries(userAnswers).forEach(([qIdx, answer]) => {
            const q = questions[parseInt(qIdx)];
            const topic = q.topic || q.category || 'General';
            
            if (!topicPerformance[topic]) {
                topicPerformance[topic] = { total: 0, correct: 0, questions: [] };
            }
            
            topicPerformance[topic].total += 1;
            topicPerformance[topic].questions.push(q);
            
            if (answer === q.correct_answer) {
                topicPerformance[topic].correct += 1;
            }
        });

        // Classify topics
        Object.entries(topicPerformance).forEach(([topic, data]) => {
            const topicScore = (data.correct / data.total) * 100;
            if (topicScore < 60) {
                weakTopics.push({ topic, score: topicScore, ...data });
            } else {
                strongTopics.push({ topic, score: topicScore, ...data });
            }
        });

        weakTopics.sort((a, b) => a.score - b.score);
        strongTopics.sort((a, b) => b.score - a.score);

        setAnalysis({
            score,
            correctAnswers,
            totalQuestions,
            topicPerformance,
            weakTopics,
            strongTopics,
            subject
        });
    };

    if (!analysis) return null;

    const getScoreColor = (score) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getScoreBg = (score) => {
        if (score >= 80) return 'bg-green-500/10 border-green-500/50';
        if (score >= 60) return 'bg-yellow-500/10 border-yellow-500/50';
        return 'bg-red-500/10 border-red-500/50';
    };

    return (
        <div className="h-full flex flex-col glass-panel overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-white/10">
                <h3 className="text-lg font-semibold text-white">Quiz Analysis - {analysis.subject}</h3>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                <div className="max-w-3xl mx-auto space-y-6">
                    {/* Score Card */}
                    <div className={`p-6 rounded-lg border ${getScoreBg(analysis.score)}`}>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-white font-semibold">Overall Performance</h4>
                            {analysis.score >= 80 && <TrendingUp className="w-5 h-5 text-green-400" />}
                            {analysis.score < 80 && analysis.score >= 60 && <AlertCircle className="w-5 h-5 text-yellow-400" />}
                            {analysis.score < 60 && <TrendingDown className="w-5 h-5 text-red-400" />}
                        </div>
                        <div className="flex items-end gap-4">
                            <div>
                                <p className={`text-4xl font-bold ${getScoreColor(analysis.score)}`}>
                                    {Math.round(analysis.score)}%
                                </p>
                                <p className="text-sm text-gray-400 mt-1">
                                    {analysis.correctAnswers} out of {analysis.totalQuestions} correct
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Weak Topics */}
                    {analysis.weakTopics.length > 0 && (
                        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/50">
                            <div className="flex items-center gap-2 mb-4">
                                <AlertCircle className="w-5 h-5 text-red-400" />
                                <h4 className="font-semibold text-white">Areas to Improve</h4>
                            </div>
                            <div className="space-y-3">
                                {analysis.weakTopics.map((item, idx) => (
                                    <div key={idx} className="p-3 rounded-lg bg-black/20">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="text-white font-medium">{item.topic}</p>
                                            <span className="text-red-400 text-sm font-semibold">
                                                {Math.round(item.score)}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-black/30 rounded-full h-1.5">
                                            <div
                                                className="bg-red-500 h-1.5 rounded-full"
                                                style={{ width: `${item.score}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-gray-400 mt-2">
                                            Focus on: Definitions, Examples, and Practice problems
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Strong Topics */}
                    {analysis.strongTopics.length > 0 && (
                        <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/50">
                            <div className="flex items-center gap-2 mb-4">
                                <CheckCircle2 className="w-5 h-5 text-green-400" />
                                <h4 className="font-semibold text-white">Strong Areas</h4>
                            </div>
                            <div className="space-y-3">
                                {analysis.strongTopics.map((item, idx) => (
                                    <div key={idx} className="p-3 rounded-lg bg-black/20">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="text-white font-medium">{item.topic}</p>
                                            <span className="text-green-400 text-sm font-semibold">
                                                {Math.round(item.score)}%
                                            </span>
                                        </div>
                                        <div className="w-full bg-black/30 rounded-full h-1.5">
                                            <div
                                                className="bg-green-500 h-1.5 rounded-full"
                                                style={{ width: `${item.score}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Suggestions */}
                    <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/50">
                        <div className="flex items-center gap-2 mb-3">
                            <BookMarked className="w-5 h-5 text-blue-400" />
                            <h4 className="font-semibold text-white">Recommendations</h4>
                        </div>
                        <ul className="space-y-2 text-sm text-gray-300">
                            {analysis.score < 60 && (
                                <li>• Review all fundamental concepts in this subject</li>
                            )}
                            {analysis.weakTopics.length > 0 && (
                                <li>• Spend extra time on: {analysis.weakTopics.slice(0, 2).map(t => t.topic).join(', ')}</li>
                            )}
                            {analysis.score < 80 && (
                                <li>• Take practice quizzes regularly to improve retention</li>
                            )}
                            {analysis.score >= 80 && (
                                <li>• Great job! Keep practicing to maintain your level</li>
                            )}
                            <li>• Review explanations for incorrect answers</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="p-4 border-t border-white/10 flex items-center justify-between">
                <button
                    onClick={onBack}
                    className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10"
                >
                    Back
                </button>
                <button
                    onClick={onRetake}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white"
                >
                    Retake Quiz
                </button>
            </div>
        </div>
    );
};

export default QuizAnalysis;
