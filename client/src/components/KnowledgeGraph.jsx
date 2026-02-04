import React, { useCallback, useEffect, useState, useMemo } from 'react';
import ReactFlow, { Background, Controls, useNodesState, useEdgesState, addEdge, MarkerType } from 'reactflow';
import { useLayoutedElements } from '../hooks/useLayoutedElements';
import 'reactflow/dist/style.css';

const KnowledgeGraph = ({ data, onNodeClick }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const { nodes: layoutNodes, edges: layoutEdges } = useLayoutedElements(nodes, edges);
    
    // Memoize node types to avoid React Flow warning
    const nodeTypes = useMemo(() => ({}), []);
    const edgeTypes = useMemo(() => ({}), []);

    useEffect(() => {
        if (data) {
            const initialNodes = (data.nodes || []).map((n) => ({
                id: String(n.id),
                position: { x: 0, y: 0 },
                data: { label: n.label },
                type: 'default',
                style: {
                    background: selectedNode?.id === n.id ? '#6366f1' : '#1e293b',
                    color: '#e2e8f0',
                    border: selectedNode?.id === n.id ? '3px solid #818cf8' : '2px solid #8b5cf6',
                    borderRadius: '12px',
                    padding: '12px 16px',
                    boxShadow: selectedNode?.id === n.id 
                        ? '0 0 30px rgba(99, 102, 241, 0.5)' 
                        : '0 0 20px rgba(139, 92, 246, 0.3)',
                    fontSize: '14px',
                    fontWeight: '500',
                    minWidth: '120px',
                    textAlign: 'center',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                }
            }));

            const initialEdges = (data.edges || []).map(e => ({
                id: String(e.id),
                source: String(e.source),
                target: String(e.target),
                label: e.label,
                animated: true,
                style: { stroke: '#7c3aed', strokeWidth: 2 },
                labelStyle: { fill: '#cbd5e1', fontSize: '12px', fontWeight: '500' },
                markerEnd: { type: MarkerType.ArrowClosed, color: '#7c3aed' }
            }));

            setNodes(initialNodes);
            setEdges(initialEdges);
        }
    }, [data, selectedNode, setNodes, setEdges]);

    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    const handleNodeClick = useCallback((event, node) => {
        setSelectedNode(node);
        if (onNodeClick) {
            onNodeClick(node);
        }
    }, [onNodeClick]);

    return (
        <div className="w-full h-full min-h-[500px] glass-panel p-4 relative overflow-hidden">
            <div className="absolute top-4 left-4 z-10 px-3 py-1 bg-accent/20 rounded-full border border-accent/50 text-xs text-accent text-center">
                Interactive Knowledge Graph
            </div>
            
            {selectedNode && (
                <div className="absolute top-16 left-4 z-20 bg-slate-800 border border-purple-500 rounded-lg p-4 max-w-xs">
                    <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-accent text-sm">{selectedNode.data.label}</h3>
                        <button 
                            onClick={() => setSelectedNode(null)}
                            className="text-gray-400 hover:text-white text-lg"
                        >
                            ✕
                        </button>
                    </div>
                    <p className="text-xs text-gray-300">ID: {selectedNode.id}</p>
                    <p className="text-xs text-gray-400 mt-2">Click to explore details →</p>
                </div>
            )}
            
            <ReactFlow
                nodes={layoutNodes}
                edges={layoutEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={handleNodeClick}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                fitView
            >
                <Background color="#475569" gap={20} size={1} />
                <Controls className="bg-slate-800 border-none fill-white text-white" />
            </ReactFlow>
        </div>
    );
};

export default KnowledgeGraph;
