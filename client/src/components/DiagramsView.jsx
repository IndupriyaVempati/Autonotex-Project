import React from 'react';
import Mermaid from './Mermaid';

const DiagramsView = ({ notes, sourceDiagrams = [] }) => {
    if (!notes) {
        return (
            <div className="glass-panel p-6 rounded-lg border border-white/10">
                <h2 className="text-lg font-bold text-accent mb-2">Diagrams</h2>
                <p className="text-sm text-gray-400">No notes available yet.</p>
            </div>
        );
    }

    const blocks = notes.match(/```mermaid\s*[\s\S]*?```/g) || [];
    const diagrams = blocks.map((block) => block.replace(/```mermaid\s*|```/g, '').trim());

    const titles = blocks.map((block) => {
        const idx = notes.indexOf(block);
        const prefix = idx >= 0 ? notes.slice(Math.max(0, idx - 300), idx) : '';
        const match = prefix.match(/(#+\s*Visual Diagrams?\s*\d*[^\n]*|#+\s*Diagram[^\n]*|\*\*Visual Diagrams?\s*\d*[^\n]*\*\*|\*\*Diagram[^\n]*\*\*)/i);
        if (match && match[1]) {
            return match[1].replace(/[#*]/g, '').trim();
        }
        return null;
    });

    if (diagrams.length === 0 && sourceDiagrams.length === 0) {
        return (
            <div className="glass-panel p-6 rounded-lg border border-white/10">
                <h2 className="text-lg font-bold text-accent mb-2">Diagrams</h2>
                <p className="text-sm text-gray-400">No Mermaid diagrams found in the notes.</p>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto space-y-8">
            {sourceDiagrams.length > 0 && (
                <div className="space-y-5">
                    <div className="text-sm text-accent font-semibold">Original Diagrams</div>
                    {sourceDiagrams.map((diagram, idx) => (
                        <div key={`source-${idx}`} className="glass-panel p-5 rounded-lg border border-white/10 bg-slate-800/40">
                            <div className="text-xs text-gray-300 mb-3">
                                {diagram.title || `Source Diagram ${idx + 1}`}
                            </div>
                            <div className="bg-slate-900/40 p-3 rounded-md border border-white/10">
                                <img
                                    src={diagram.data_url}
                                    alt={diagram.title || `Source Diagram ${idx + 1}`}
                                    className="w-full rounded-md object-contain"
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {diagrams.map((diagram, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-lg border border-white/10 bg-slate-800/40">
                    <div className="text-xs text-gray-300 mb-3">
                        {titles[idx] ? `${titles[idx]}` : `Diagram ${idx + 1}`}
                    </div>
                    <Mermaid chart={diagram} />
                </div>
            ))}
        </div>
    );
};

export default DiagramsView;
