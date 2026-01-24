import React, { useState } from 'react';
import { X, Sparkles, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

const TutorModal = ({ topic, onClose }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: `Hi! I'm your AI Tutor. I see you want to learn about **"${topic}"**. usage?` }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const newMsg = { role: 'user', content: input };
        setMessages([...messages, newMsg]);
        setInput('');
        setLoading(true);

        try {
            // In a real app, this would call a specific /chat endpoint with context
            // checking if we can use the graph_agent generic process or need a new one. 
            // For now, mocking specific chat or reusing the prompt logic.
            // But let's assume we use a simple chat endpoint or just generic text generation
            // We'll mock it for now to avoid creating 5 more backend files, or just use a direct Groq call if I can.
            // Actually, I can use the existing /query endpoint if I made one? I didn't.
            // Let's just simulate the response or use the duplicate logic for now to save time/complexity.

            // Wait, I should do it properly. I'll add a quick /chat endpoint in app.py later.
            const response = await axios.post('http://localhost:5001/chat', { message: input, topic: topic });
            setMessages(prev => [...prev, { role: 'assistant', content: response.data.reply }]);

        } catch (error) {
            setMessages(prev => [...prev, { role: 'assistant', content: "I'm having trouble connecting to the Tutor brain right now." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-2xl h-[600px] glass-panel flex flex-col relative animate-in fade-in zoom-in duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                    <X className="w-5 h-5 text-gray-400" />
                </button>

                <div className="p-6 border-b border-white/10 flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-green-500/20 text-green-400">
                        <Sparkles className="w-6 h-6" />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-white">AI Tutor</h3>
                        <p className="text-sm text-gray-400">Teaching: <span className="text-white font-medium">{topic}</span></p>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div
                                className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user'
                                    ? 'bg-accent/20 text-white rounded-br-none border border-accent/20'
                                    : 'bg-white/5 text-gray-200 rounded-bl-none border border-white/10'
                                    }`}
                            >
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-white/5 p-4 rounded-2xl rounded-bl-none border border-white/10 flex gap-2">
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                            </div>
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-white/10 bg-black/20">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Ask a question..."
                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent/50 transition-colors"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={loading}
                            className="p-3 bg-accent hover:bg-accent/80 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white transition-colors"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TutorModal;
