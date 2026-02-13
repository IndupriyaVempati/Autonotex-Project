import React, { useState } from 'react';
import { Search, Loader2, ExternalLink, ImageIcon, Plus, Check, Trash2 } from 'lucide-react';
import Mermaid from './Mermaid';
import api from '../utils/api';

/**
 * Build a Mermaid graph-TD string from the knowledge-graph JSON
 * so there is always at least one diagram to show.
 */
const buildGraphDiagram = (graphData) => {
    if (!graphData) return null;
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    if (nodes.length === 0) return null;

    const lines = ['graph TD'];
    const safeId = (id) => String(id).replace(/[^a-zA-Z0-9_]/g, '_');
    const safeLabel = (l) => String(l).replace(/"/g, "'").substring(0, 40);

    nodes.forEach((n) => {
        lines.push(`    ${safeId(n.id)}["${safeLabel(n.label)}"]`);
    });

    const nodeIds = new Set(nodes.map((n) => String(n.id)));
    edges.forEach((e) => {
        const src = safeId(e.source);
        const tgt = safeId(e.target);
        if (nodeIds.has(String(e.source)) && nodeIds.has(String(e.target))) {
            const lbl = e.label ? ` -->|${safeLabel(e.label)}|` : ' -->';
            lines.push(`    ${src}${lbl} ${tgt}`);
        }
    });

    return lines.join('\n');
};

const DiagramsView = ({ notes, sourceDiagrams = [], graphData, docId, webDiagrams = [], onWebDiagramsUpdated }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [webImages, setWebImages] = useState([]);
    const [imageLoading, setImageLoading] = useState(false);
    const [imageError, setImageError] = useState('');
    const [selectedImage, setSelectedImage] = useState(null);
    const [addedUrls, setAddedUrls] = useState(new Set());
    const [savingUrl, setSavingUrl] = useState(null);

    const handleAddToDiagrams = async (img) => {
        if (!docId) return;
        setSavingUrl(img.image_url);
        try {
            const res = await api.post(`/notes/${docId}/web-diagrams`, {
                title: img.title,
                image_url: img.image_url,
                thumbnail: img.thumbnail,
                source: img.source,
            });
            setAddedUrls((prev) => new Set(prev).add(img.image_url));
            if (onWebDiagramsUpdated) {
                onWebDiagramsUpdated(res.data.web_diagrams || []);
            }
        } catch (err) {
            console.error('Failed to save diagram:', err);
        } finally {
            setSavingUrl(null);
        }
    };

    const handleRemoveWebDiagram = async (idx) => {
        if (!docId) return;
        try {
            const res = await api.delete(`/notes/${docId}/web-diagrams/${idx}`);
            if (onWebDiagramsUpdated) {
                onWebDiagramsUpdated(res.data.web_diagrams || []);
            }
        } catch (err) {
            console.error('Failed to remove diagram:', err);
        }
    };

    // Already-saved URLs for quick lookup
    const savedUrls = new Set(webDiagrams.map((d) => d.image_url));

    const handleImageSearch = async () => {
        const q = searchQuery.trim();
        if (!q) return;
        setImageLoading(true);
        setImageError('');
        setWebImages([]);
        try {
            const res = await api.post('/image-search', { query: q, max_results: 12 });
            setWebImages(res.data.images || []);
            if ((res.data.images || []).length === 0) {
                setImageError('No diagrams found. Try a different search term.');
            }
        } catch (err) {
            setImageError(err.response?.data?.error || 'Image search failed.');
        } finally {
            setImageLoading(false);
        }
    };

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

    // Build a fallback diagram from the knowledge graph when notes contain no mermaid blocks
    const graphDiagram = buildGraphDiagram(graphData);
    const hasAnyDiagram = diagrams.length > 0 || sourceDiagrams.length > 0 || graphDiagram;

    return (
        <div className="h-full overflow-y-auto space-y-8">
            {/* ─── Web Diagram Search ─── */}
            <div className="glass-panel p-5 rounded-lg border border-white/10 bg-slate-800/40">
                <div className="flex items-center gap-2 mb-3">
                    <ImageIcon className="w-4 h-4 text-accent" />
                    <span className="text-sm font-semibold text-accent">Search Diagrams from the Web</span>
                </div>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleImageSearch()}
                        placeholder="e.g. Von Neumann Architecture diagram"
                        className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent/50"
                    />
                    <button
                        onClick={handleImageSearch}
                        disabled={imageLoading || !searchQuery.trim()}
                        className="px-4 py-2 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent border border-accent/30 text-sm flex items-center gap-2 disabled:opacity-40"
                    >
                        {imageLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        Search
                    </button>
                </div>

                {imageError && (
                    <p className="text-xs text-red-400 mt-2">{imageError}</p>
                )}

                {webImages.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {webImages.map((img, idx) => {
                            const alreadySaved = savedUrls.has(img.image_url) || addedUrls.has(img.image_url);
                            const isSaving = savingUrl === img.image_url;
                            return (
                            <div
                                key={idx}
                                className="rounded-lg border border-white/10 overflow-hidden bg-slate-900/50 hover:border-accent/40 transition-colors cursor-pointer group"
                                onClick={() => setSelectedImage(selectedImage === idx ? null : idx)}
                            >
                                <img
                                    src={img.thumbnail || img.image_url}
                                    alt={img.title}
                                    className="w-full h-32 object-cover"
                                    loading="lazy"
                                    onError={(e) => { e.target.style.display = 'none'; }}
                                />
                                <div className="p-2">
                                    <p className="text-xs text-gray-300 truncate" title={img.title}>
                                        {img.title}
                                    </p>
                                    <div className="flex items-center justify-between mt-1">
                                        <a
                                            href={img.source || img.image_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-[10px] text-accent/70 hover:text-accent flex items-center gap-1"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            <ExternalLink className="w-3 h-3" /> Source
                                        </a>
                                        {docId && (
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleAddToDiagrams(img); }}
                                                disabled={alreadySaved || isSaving}
                                                className={`text-[10px] px-2 py-0.5 rounded flex items-center gap-1 border transition-colors ${
                                                    alreadySaved
                                                        ? 'bg-green-500/20 text-green-400 border-green-500/30'
                                                        : 'bg-accent/10 text-accent border-accent/30 hover:bg-accent/20'
                                                } disabled:opacity-60`}
                                            >
                                                {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : alreadySaved ? <Check className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                                                {alreadySaved ? 'Saved' : 'Add'}
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {selectedImage === idx && (
                                    <div className="p-2 border-t border-white/10">
                                        <a
                                            href={img.image_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-xs text-accent hover:underline flex items-center gap-1"
                                        >
                                            <ExternalLink className="w-3 h-3" /> Open Full Image
                                        </a>
                                    </div>
                                )}
                            </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* ─── Source Diagrams (from upload) ─── */}
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

            {/* ─── Saved Web Diagrams ─── */}
            {webDiagrams.length > 0 && (
                <div className="space-y-5">
                    <div className="text-sm text-accent font-semibold">Saved Web Diagrams</div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {webDiagrams.map((wd, idx) => (
                            <div key={`wd-${idx}`} className="glass-panel p-4 rounded-lg border border-white/10 bg-slate-800/40">
                                <div className="flex items-start justify-between mb-2">
                                    <p className="text-xs text-gray-300 truncate flex-1 mr-2" title={wd.title}>
                                        {wd.title || `Web Diagram ${idx + 1}`}
                                    </p>
                                    <div className="flex items-center gap-2 shrink-0">
                                        {wd.source && (
                                            <a
                                                href={wd.source}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-[10px] text-accent/70 hover:text-accent flex items-center gap-1"
                                            >
                                                <ExternalLink className="w-3 h-3" />
                                            </a>
                                        )}
                                        <button
                                            onClick={() => handleRemoveWebDiagram(idx)}
                                            className="text-[10px] text-red-400/70 hover:text-red-400 p-0.5"
                                            title="Remove from saved diagrams"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                </div>
                                <div className="bg-slate-900/40 p-2 rounded-md border border-white/10">
                                    <img
                                        src={wd.image_url}
                                        alt={wd.title || `Web Diagram ${idx + 1}`}
                                        className="w-full rounded-md object-contain max-h-64"
                                        loading="lazy"
                                        onError={(e) => {
                                            e.target.onerror = null;
                                            e.target.src = wd.thumbnail || '';
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ─── Mermaid Diagrams from Notes ─── */}
            {diagrams.map((diagram, idx) => (
                <div key={idx} className="glass-panel p-5 rounded-lg border border-white/10 bg-slate-800/40">
                    <div className="text-xs text-gray-300 mb-3">
                        {titles[idx] ? `${titles[idx]}` : `Diagram ${idx + 1}`}
                    </div>
                    <Mermaid chart={diagram} />
                </div>
            ))}

            {/* ─── Knowledge Graph Fallback ─── */}
            {diagrams.length === 0 && graphDiagram && (
                <div className="space-y-5">
                    <div className="text-sm text-accent font-semibold">AI Generated Diagram</div>
                    <div className="glass-panel p-5 rounded-lg border border-white/10 bg-slate-800/40">
                        <div className="text-xs text-gray-300 mb-3">
                            Concept map auto-generated by AI from your notes
                        </div>
                        <Mermaid chart={graphDiagram} />
                    </div>
                </div>
            )}

            {/* ─── Empty State ─── */}
            {!hasAnyDiagram && webImages.length === 0 && (
                <div className="glass-panel p-6 rounded-lg border border-white/10 text-center">
                    <p className="text-sm text-gray-400">No diagrams yet. Use the search bar above to find diagrams from the web.</p>
                </div>
            )}
        </div>
    );
};

export default DiagramsView;
