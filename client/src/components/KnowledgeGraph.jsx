import React, { useCallback, useEffect } from 'react';
import ReactFlow, { Background, Controls, useNodesState, useEdgesState, addEdge } from 'reactflow';
import 'reactflow/dist/style.css';

const KnowledgeGraph = ({ data }) => {
    // Transform backend data to React Flow format if needed
    // Assuming backend returns { nodes: [{id, label, type}], edges: [{id, source, target, label}] }

    // Initialize state with data
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        if (data) {
            const initialNodes = (data.nodes || []).map((n) => ({
                id: n.id,
                position: { x: Math.random() * 600, y: Math.random() * 400 }, // Random layout for MVP
                data: { label: n.label },
                type: 'default',
                style: {
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid #8b5cf6',
                    borderRadius: '8px',
                    padding: '10px',
                    boxShadow: '0 0 10px rgba(139, 92, 246, 0.2)'
                }
            }));

            const initialEdges = (data.edges || []).map(e => ({
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.label,
                animated: true,
                style: { stroke: '#8b5cf6' },
                labelStyle: { fill: '#cbd5e1' }
            }));

            setNodes(initialNodes);
            setEdges(initialEdges);
        }
    }, [data, setNodes, setEdges]);


    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    return (
        <div className="w-full h-full min-h-[500px] glass-panel p-4 relative overflow-hidden">
            <div className="absolute top-4 left-4 z-10 px-3 py-1 bg-accent/20 rounded-full border border-accent/50 text-xs text-accent text-center">
                Interactive Knowledge Graph
            </div>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
            >
                <Background color="#475569" gap={20} size={1} />
                <Controls className="bg-slate-800 border-none fill-white text-white" />
            </ReactFlow>
        </div>
    );
};

export default KnowledgeGraph;
