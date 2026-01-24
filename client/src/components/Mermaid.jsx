import React, { useEffect } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: true,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter',
});

const Mermaid = ({ chart }) => {
    useEffect(() => {
        mermaid.contentLoaded();
    }, [chart]);

    return <div className="mermaid bg-slate-900 p-4 rounded-lg my-4 flex justify-center">{chart}</div>;
};

export default Mermaid;
