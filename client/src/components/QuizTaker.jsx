import React, { useState, useEffect } from 'react';
import { Loader, ChevronRight, ChevronLeft, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

const QuizTaker = ({ subject, onQuizComplete, onBack }) => {
    const [questions, setQuestions] = useState([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [userAnswers, setUserAnswers] = useState({});
    const [showFeedback, setShowFeedback] = useState(false);

    useEffect(() => {
        fetchQuizQuestions();
    }, [subject]);

    const fetchQuizQuestions = async () => {
        try {
            const response = await axios.get(`http://localhost:5001/quiz/questions/${subject}`);
            setQuestions(response.data.questions || []);
            setLoading(false);
        } catch (error) {
            console.error("Failed to fetch quiz questions", error);
            alert("Failed to load quiz questions");
            onBack();
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader className="w-8 h-8 text-accent animate-spin" />
            </div>
        );
    }

    if (questions.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full">
                <p className="text-gray-400 mb-4">No quiz questions available for this subject</p>
                <button
                    onClick={onBack}
                    className="px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg"
                >
                    Go Back
                </button>
            </div>
        );
    }

    const currentQuestion = questions[currentQuestionIndex];
    const currentAnswer = userAnswers[currentQuestionIndex];
    const isAnswered = currentAnswer !== undefined;
    const isCorrect = isAnswered && currentAnswer === currentQuestion.correct_answer;

    const handleSelectAnswer = (optionIndex) => {
        if (!isAnswered) {
            setUserAnswers({
                ...userAnswers,
                [currentQuestionIndex]: optionIndex
            });
            setShowFeedback(true);
        }
    };

    const handleNext = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setShowFeedback(false);
        } else {
            // Quiz completed
            const score = Object.entries(userAnswers).filter(([idx, answer]) => {
                return answer === questions[idx].correct_answer;
            }).length;
            onQuizComplete({
                subject,
                totalQuestions: questions.length,
                correctAnswers: score,
                userAnswers,
                questions
            });
        }
    };

    const handlePrevious = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(currentQuestionIndex - 1);
            setShowFeedback(false);
        }
    };

    const options = currentQuestion.options || [];
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

    return (
        <div className="h-full flex flex-col glass-panel overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-white/10">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-white">{subject} Quiz</h3>
                    <span className="text-sm text-gray-400">
                        Question {currentQuestionIndex + 1}/{questions.length}
                    </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                    <div
                        className="bg-gradient-to-r from-accent to-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto">
                    {/* Question */}
                    <h2 className="text-xl font-semibold text-white mb-6">
                        {currentQuestion.question}
                    </h2>

                    {/* Options */}
                    {options.length === 0 ? (
                        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/50 mb-6">
                            <p className="text-red-400 font-semibold mb-2">Error: No options found</p>
                            <p className="text-gray-400 text-sm">Question: {currentQuestion.question}</p>
                            <p className="text-gray-400 text-sm mt-1">Raw data: {JSON.stringify(currentQuestion).substring(0, 150)}...</p>
                        </div>
                    ) : (
                        <div className="space-y-3 mb-6">
                            {options.map((option, idx) => {
                                const isSelected = currentAnswer === idx;
                                const isCorrectOption = idx === currentQuestion.correct_answer;
                                let bgColor = 'bg-white/5 border-white/10 hover:bg-white/10';

                                if (isAnswered) {
                                    if (isCorrectOption) {
                                        bgColor = 'bg-green-500/10 border-green-500/50';
                                    } else if (isSelected && !isCorrect) {
                                        bgColor = 'bg-red-500/10 border-red-500/50';
                                    }
                                } else if (isSelected) {
                                    bgColor = 'bg-accent/20 border-accent/50';
                                }

                                return (
                                    <button
                                        key={idx}
                                        onClick={() => handleSelectAnswer(idx)}
                                        disabled={isAnswered}
                                        className={`w-full p-4 rounded-lg border text-left transition-all ${bgColor} ${
                                            isAnswered ? 'cursor-default' : 'cursor-pointer'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="flex-1">
                                                <p className="text-white font-medium">{option}</p>
                                            </div>
                                            {isAnswered && isCorrectOption && (
                                                <CheckCircle className="w-5 h-5 text-green-400" />
                                            )}
                                            {isAnswered && isSelected && !isCorrect && (
                                                <XCircle className="w-5 h-5 text-red-400" />
                                            )}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    )}

                    {/* Feedback */}
                    {showFeedback && (
                        <div
                            className={`p-4 rounded-lg mb-6 ${
                                isCorrect
                                    ? 'bg-green-500/10 border border-green-500/50'
                                    : 'bg-red-500/10 border border-red-500/50'
                            }`}
                        >
                            <p className={`font-semibold mb-2 ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>
                                {isCorrect ? '✓ Correct!' : '✗ Incorrect'}
                            </p>
                            <p className="text-gray-300 text-sm">
                                {currentQuestion.explanation || 'Good try! Keep learning.'}
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Navigation */}
            <div className="p-4 border-t border-white/10 flex items-center justify-between">
                <button
                    onClick={handlePrevious}
                    disabled={currentQuestionIndex === 0}
                    className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                </button>

                <button
                    onClick={handleNext}
                    disabled={!isAnswered || options.length === 0}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    {currentQuestionIndex === questions.length - 1 ? 'Complete' : 'Next'}
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
};

export default QuizTaker;
