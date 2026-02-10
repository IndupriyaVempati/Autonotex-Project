import React from 'react';
import ReactMarkdown from 'react-markdown';
import { BookOpen, Map, Sparkles } from 'lucide-react';
import Mermaid from './Mermaid';

const NotesView = ({ notes, onTopicClick }) => {
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
                        {notes}
                    </ReactMarkdown>
                </div>

                <div className="mt-8 p-4 rounded-xl bg-linear-to-br from-green-500/10 to-blue-500/10 border border-white/10">
                    <div className="flex items-center gap-2 mb-2 text-green-400">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-sm font-semibold">Adaptive Learning Path Detected</span>
                    </div>
                    <p className="text-xs text-gray-400">Based on your progress, the AI recommends these next steps.</p>
                </div>
            </div>
        </div>
    );
};

export default NotesView;
