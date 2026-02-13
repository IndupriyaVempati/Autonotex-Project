import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter',
});

let mermaidCounter = 0;

const Mermaid = ({ chart }) => {
    const containerRef = useRef(null);
    const [svg, setSvg] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!chart || !containerRef.current) return;

        const id = `mermaid-${++mermaidCounter}`;
        let cancelled = false;

        (async () => {
            try {
                const { svg: renderedSvg } = await mermaid.render(id, chart.trim());
                if (!cancelled) {
                    setSvg(renderedSvg);
                    setError(null);
                }
            } catch (err) {
                if (!cancelled) {
                    console.warn('Mermaid render error:', err);
                    setError(err?.message || 'Diagram rendering failed');
                    setSvg('');
                }
                // Clean up any orphan element mermaid may have injected
                const orphan = document.getElementById(id);
                if (orphan) orphan.remove();
            }
        })();

        return () => { cancelled = true; };
    }, [chart]);

    if (error) {
        return (
            <div className="bg-slate-900 p-4 rounded-lg my-4 border border-red-500/30">
                <p className="text-xs text-red-400 mb-2">Diagram could not be rendered</p>
                <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-x-auto">{chart}</pre>
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            className="bg-slate-900 p-4 rounded-lg my-4 flex justify-center overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

export default Mermaid;
