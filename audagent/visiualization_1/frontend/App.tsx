import {
  addEdge,
  Controls,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type OnConnect
} from '@xyflow/react';

import * as React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { LuAtom, LuBrainCog, LuCloud, LuCodesandbox, LuDrill, LuServerCog } from 'react-icons/lu';

import '@xyflow/react/dist/base.css';

import CustomEdge from './components/CustomEdge';
import Sidebar from './components/Sidebar';
import TurboNode, { type TurboNodeData } from './components/TurboNode';

const graphNodes: Node<TurboNodeData>[] = []

const graphEdges: Edge[] = []
const nodeTypes = {
  turbo: TurboNode,
};

const edgeTypes = {
  turbo: CustomEdge
};

const defaultEdgeOptions = {
  type: 'turbo',
  markerEnd: 'edge-circle',
};

interface WebSocketMessage {
  type: 'add_node' | 'update_node' | 'add_edge';
  data: any;
}

// Define initial nodes: app and llm
const initialNodes = [
  {
    id: 'llama3.1-very-long-model-name',
    position: { x: 0, y: 0 },
    data: { icon: <LuBrainCog />, title: 'llm', subline: '1', topIcon: <LuCloud /> },
    type: 'turbo'
  },
  {
    id: 'app',
    position: { x: 250, y: 0 },
    data: { icon: <LuAtom />, title: 'app', subline: '2', topIcon: <LuCodesandbox /> },
    type: 'turbo'
  },
  {
    id: 'retrieve_user_emails-and-a-long-long-function-name',
    position: { x: 250, y: 0 },
    data: { icon: <LuAtom />, title: 'tool', subline: '2', topIcon: <LuCodesandbox /> },
    type: 'turbo'
  }
];

// define initial edges: from app to llm
const initialEdges = [
  {
    id: 'eapp-llm',
    source: 'app',
    target: 'llama3.1-very-long-model-name',
    type: 'turbo',
    createdAt: 1629782400,
    data: { prompt: 'Prompt 1 lorem ipsum ha ha meh po la asdkj asldkjajsd kljasdjkl asd w  ads sad asd asd adskljdaskjas kljasdjklasd kljdasjkasdl jasdjklasd', tool_input: 'Tool input 1', kaka: 'pipi' }
  },
  {
    id: 'e2-3',
    source: 'llama3.1-very-long-model-name',
    target: 'retrieve_user_emails-and-a-long-long-function-name',
    type: 'turbo',
    createdAt: 1629782400,
    data: { prompt: 'Prompt 1', tool_input: 'Tool input 1' }
  },
];

const Flow = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(graphNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graphEdges);
  const [selectedNodes, setSelectedNodes] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const onConnect: OnConnect = useCallback(
    (params) => setEdges((els) => addEdge(params, els)),
    [],
  );

  useEffect(() => {
    // Initialize WebSocket connection
    const socket = new WebSocket('ws://127.0.0.1:8000/ws');
    socketRef.current = socket;

    // Connection opened
    socket.addEventListener('open', (event) => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
    });

    // Listen for messages
    socket.addEventListener('message', (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        console.log('Message from server:', message);
        
        switch (message.type) {
          case 'add_node':
            handleAddNode(message.data);
            break;
          case 'update_node':
            handleUpdateNode(message.data);
            break;
          case 'add_edge':
            handleAddEdge(message.data);
            break;
          default:
            console.warn('Unknown message type:', message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    // Connection closed
    socket.addEventListener('close', (event) => {
      console.log('Disconnected from WebSocket server');
      setIsConnected(false);
    });

    // Handle errors
    socket.addEventListener('error', (event) => {
      console.error('WebSocket error:', event);
      setIsConnected(true);
    });

    // Clean up WebSocket on component unmount
    return () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
    };
  }, []);

  const calculateAlternatingYCoordinate = (index) => {
    // Base multiplier
    const baseMultiplier = 200;
    
    // Alternate between negative and positive
    const sign = index % 2 === 0 ? 1 : -1;
    
    // Increase magnitude with each index
    const magnitude = baseMultiplier * Math.floor(index / 2);
    
    // Calculate final y coordinate
    return sign * magnitude;
  };

  const calculateYCoordinate = (index) => {
    // Base multiplier
    const baseMultiplier = 150;
    
    // Special case for 0
    if (index === 0) return 0;
    
    // Determine sign and magnitude
    const sign = index % 2 === 1 ? -1 : 1;
    const magnitude = baseMultiplier * Math.ceil(index / 2);
    
    return sign * magnitude;
  };

  const handleAddNode = (nodeData) => {
    console.log('Adding nodes:', nodeData);

    nodeData.forEach(n => {
      setNodes(currentNodes => {
        let x = 0
        let y = 0
        let icon = <LuBrainCog />;
        let topIcon = <LuCloud />;
        
        switch (n.node_type) {
          case 'llm':
            icon = <LuBrainCog />;  
            topIcon = <LuCloud />;  
            y = 300;
            break;
          case 'mcp_server':
            icon = <LuServerCog />;
            y = -200;
            break;
          case 'app':
            icon = <LuAtom />;
            topIcon = <LuCodesandbox />;  
            break;
          case 'tool':
            x = 600
            let n = currentNodes.filter(n => n.data.title === 'tool').length;
            if (n == 0) {
              y = 0;
            } else {
              y = calculateYCoordinate(n);
            }

            icon = <LuDrill />;
            topIcon = <LuCodesandbox />;  
            break;
          default:
            break;
        }

        const node = {
          id: n.node_id,
          position: { x, y },
          data: { icon, title: n.node_type, subline: n.node_id, topIcon },
          type: 'turbo',
          className: 'fade-in-anim'
        };
  
        return [...currentNodes, node];
      });
    });
  };

  const handleUpdateNode = (nodeData: Partial<Node<TurboNodeData>> & { id: string }) => {
    setNodes((nds) => 
      nds.map((node) => 
        node.id === nodeData.id ? { ...node, ...nodeData } : node
      )
    );
  };

  const handleAddEdge = (edgeData) => {
    edgeData.forEach(e => {
      console.log('Adding edge:', e);
      
      // TODO: Some times the user uses a labeled model (i.e claude-3.5-latest) which in turn
      // resolves to the tagged model i.e claude-3.5-20210901. So make sure we find the correct node
      const findSimilarNode = (nodes, nodeId) => 
        nodes.find(node => node.id.startsWith(nodeId.slice(0, 6)))?.id || nodeId;
      
      // Ensure the target node exists or find a similar one
      let targetNodeId = e.target_node_id;
      if (!nodes.some(node => node.id === e.target_node_id)) {
        targetNodeId = findSimilarNode(nodes, e.target_node_id);
      }
      
      // Ensure the source node exists or find a similar one
      let sourceNodeId = e.source_node_id;
      if (!nodes.some(node => node.id === e.source_node_id)) {
        sourceNodeId = findSimilarNode(nodes, e.source_node_id);
      }
  
      // Using updated sourceNodeId and targetNodeId
      const edgeId = `e${sourceNodeId}-${targetNodeId}-${e.created_at}`;
      
      setEdges(currentEdges => {
        // Check if edge already exists
        const edgeExists = currentEdges.some(edge => edge.id === edgeId);
        
        if (edgeExists) {
          console.log(`Edge ${edgeId} already exists, skipping.`);
          return currentEdges;
        }
        
        // Create the new edge
        const newEdge = {
          id: edgeId,
          createdAt: e.created_at,
          type: 'turbo',
          source: sourceNodeId,
          target: targetNodeId,
          data: {
            ...e
          },
          className: 'fade-in-anim'
        };
        
        // Return the updated edges array
        return [...currentEdges, newEdge];
      });
    });
  };

  // Pass setSelectedNodes to the edges
  const edgeWithProps = useCallback(
    (props) => <CustomEdge {...props} setSelectedNodes={setSelectedNodes} />,
    []
  );

  // Update edgeTypes with the callback
  const customEdgeTypes = {
    ...edgeTypes,
    turbo: edgeWithProps
  };

  // Reset selected nodes when clicking on the flow background
  const onPaneClick = useCallback(() => {
    setSelectedNodes(null);
  }, []);

  return (
    <div className="container">
      <div className="main">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onPaneClick={onPaneClick}
          fitView
          nodeTypes={nodeTypes}
          edgeTypes={customEdgeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
        >
          <div className="logo-overlay">
            <img 
              src="public/vite.svg"
              alt="AudAgent Logo"
              className="logo" 
            />
          </div>
          <Controls showInteractive={true} />
          <svg>
            <defs>
              <linearGradient id="edge-gradient">
                <stop offset="0%" stopColor="#ae53ba" />
                <stop offset="100%" stopColor="#2a8af6" />
              </linearGradient>
  
              <marker
                id="edge-circle"
                viewBox="-5 -5 10 10"
                refX="0"
                refY="0"
                markerUnits="strokeWidth"
                markerWidth="10"
                markerHeight="10"
                orient="auto"
              >
                <circle stroke="#2a8af6" strokeOpacity="0.75" r="2" cx="0" cy="0" />
              </marker>
            </defs>
          </svg>
        </ReactFlow>
        </div>
        <div className="sidebar react-flow">
          <Sidebar edges={edges} selectedNodes={selectedNodes} isConnected={isConnected} />
        </div>
    </div>
  );  
};  

export default Flow;