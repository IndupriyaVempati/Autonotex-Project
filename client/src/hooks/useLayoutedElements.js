import { useEffect, useState } from 'react';
import dagre from 'dagre';

export const useLayoutedElements = (nodes, edges) => {
    const [layoutedNodes, setLayoutedNodes] = useState(nodes);
    const [layoutedEdges, setLayoutedEdges] = useState(edges);

    useEffect(() => {
        if (!nodes || nodes.length === 0) {
            setLayoutedNodes(nodes);
            setLayoutedEdges(edges);
            return;
        }

        const g = new dagre.graphlib.Graph({ compound: true });
        g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 100 });
        g.setDefaultEdgeLabel(() => ({}));

        nodes.forEach(node => {
            g.setNode(node.id, { width: 150, height: 60 });
        });

        edges.forEach(edge => {
            g.setEdge(edge.source, edge.target);
        });

        dagre.layout(g);

        const newNodes = nodes.map(node => {
            const pos = g.node(node.id);
            return {
                ...node,
                position: {
                    x: pos.x - 75, // Center the node
                    y: pos.y - 30
                }
            };
        });

        setLayoutedNodes(newNodes);
        setLayoutedEdges(edges);
    }, [nodes, edges]);

    return { nodes: layoutedNodes, edges: layoutedEdges };
};
