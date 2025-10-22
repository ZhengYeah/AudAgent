import { type Edge } from '@xyflow/react';
import { motion } from "framer-motion";
import React, { useState } from 'react';
import { LuChevronDown, LuChevronRight, LuClipboardCopy, LuLink2, LuLink2Off } from 'react-icons/lu';
import '../css/sidebar.css';

type EdgeData = Edge & {
  createdAt?: number;
  source: string;
  target: string;
  data?: {
    [key: string]: any;
  };
};

interface SidebarProps {
  edges: EdgeData[];
  selectedNodes: { source: string; target: string } | null;
  isConnected: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ edges, selectedNodes, isConnected }) => {
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  // Sort edges by createdAt timestamp (newest first)
  const sortedEdges = [...edges].sort((a, b) => {
    return (b.createdAt || 0) - (a.createdAt || 0);
  });

  const getTime = (epochTime) => {
    const date = new Date(epochTime * 1000); // Convert epoch time to milliseconds
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');

    return `${hours}:${minutes}:${seconds}`;
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text); // Optionally display copied feedback
    setTimeout(() => setCopiedText(null), 2000); // Reset copied feedback after 2 seconds
  };

  const toggleRow = (id: string) => {
    setExpandedRows(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const hasMetadata = (edge: EdgeData) => {
    return edge.data && Object.keys(edge.data).length > 0;
  };

  return (
    <div className="col-12 col-lg-3 bg-dark text-white border-left border-secondary h-100 overflow-auto">
      <h2 className="h5 p-4 border-bottom border-secondary">Agent trace {isConnected ? (
            <LuLink2 className="text-green-500 inline-block ml-2" title="Receiving events" />
          ) : (
            <LuLink2Off className="text-red-500 inline-block ml-2" title="Disconnected from events server"/>
          )}</h2>
      
      <div className="table-responsive">
        <table className="table table-dark table-striped table-hover">
          <thead>
            <tr>
              <th className="text-muted small" style={{ width: '40px' }}></th>
              <th className="text-muted small">Time</th>
              <th className="text-muted small">Source</th>
              <th className="text-muted small">Target</th>
            </tr>
          </thead>
          <tbody>
            {sortedEdges.map((edge) => {
              const isHighlighted = selectedNodes && 
                ((edge.source === selectedNodes.source && edge.target === selectedNodes.target) ||
                 (edge.source === selectedNodes.target && edge.target === selectedNodes.source));
              const isExpanded = expandedRows[edge.id] || false;
              const hasMetadataItems = hasMetadata(edge);

              return (
                <React.Fragment key={edge.id}>
                  <tr 
                    className={`${isHighlighted ? 'table-primary' : ''}`}
                  >
                    <td className="text-center">
                      {hasMetadataItems && (
                        <span 
                          onClick={() => toggleRow(edge.id)} 
                          style={{ cursor: 'pointer' }}
                        >
                          {isExpanded ? <LuChevronDown size={16} /> : <LuChevronRight size={16} />}
                        </span>
                      )}
                    </td>
                    <td>
                      {edge.createdAt ? getTime(edge.createdAt) : 'N/A'}
                    </td>
                    <td>
                      {edge.source}
                    </td>
                    <td>
                      {edge.target}
                    </td>
                  </tr>
                  {isExpanded && (
                  <motion.tr
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <td></td>
                  <td colSpan={3} className="border-0 pt-0">
                    <div className="p-2 bg-dark border border-secondary rounded">
                      <div className="d-flex align-items-center justify-content-between mb-2">
                        <small className="text-muted">Metadata</small>
                      </div>
                      {edge.data &&
                        Object.entries(edge.data).map(([key, value]) => (
                          !!(value) &&
                          <div key={key} className="mb-2">
                            <div className="d-flex align-items-center justify-content-between">
                              <small className="text-muted font-weight-bold">{key}</small>
                              <LuClipboardCopy
                                size={14}
                                className="text-muted"
                                style={{ cursor: "pointer" }}
                                onClick={() =>
                                  handleCopy(typeof value === "string" ? value : JSON.stringify(value, null, 2))
                                }
                              />
                            </div>
                            <div
                              className="small mt-1 text-wrap"
                              style={{
                                wordWrap: "break-word",
                                whiteSpace: "pre-wrap",
                                overflowWrap: "break-word",
                                maxWidth: "100%", // Ensure text does not overflow
                              }}
                            >
                              {typeof value === "string" ? (
                                value || "-"
                              ) : (
                                <pre
                                  className="text-white-50 mb-0"
                                  style={{
                                    fontSize: "0.75rem",
                                    wordWrap: "break-word",
                                    whiteSpace: "pre-wrap",
                                    overflowWrap: "break-word",
                                    maxWidth: "100%",
                                  }}
                                >
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                              )}
                            </div>
                            {copiedText === (typeof value === "string" ? value : JSON.stringify(value, null, 2)) && (
                              <small className="text-success">Copied!</small>
                            )}
                          </div>
                        ))}
                      {(!edge.data || Object.keys(edge.data).length === 0) && <div className="small">No metadata available</div>}
                    </div>
                  </td>
                </motion.tr>
                )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Sidebar;