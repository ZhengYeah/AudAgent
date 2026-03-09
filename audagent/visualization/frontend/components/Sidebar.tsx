import {type Edge} from '@xyflow/react';
import { Tooltip } from 'react-tooltip'
import 'react-tooltip/dist/react-tooltip.css'
import {motion} from "framer-motion";
import * as React from 'react';
import {useMemo, useState} from 'react';
import {LuChevronDown, LuChevronRight, LuLink2, LuLink2Off, LuCircleHelp} from 'react-icons/lu';
import '../sidebar.css'

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

const Sidebar: React.FC<SidebarProps> = ({edges, selectedNodes, isConnected}) => {
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  // Remove the user-app edge, which contains no extra information
  const purified_edges = useMemo(
    () => edges.filter(edge => edge.source !== 'user' && edge.target !== 'user'), [edges]
  )
  // Sort edges by createdAt timestamp (newest first)
  const sortedEdges = [...purified_edges].sort((a, b) => {
    return (b.createdAt || 0) - (a.createdAt || 0);
  });

  const getTime = (epochTime: number) => {
    const date = new Date(epochTime * 1000); // Convert epoch time to milliseconds
    const hours = String(date.getUTCHours()).padStart(2, '0'); // @ts-ignore
    const minutes = String(date.getUTCMinutes()).padStart(2, '0'); // @ts-ignore
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  };

  const toggleRow = (id: string) => {
    setExpandedRows(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Hide redundant keys from metadata display
  const HIDDEN_KEYS: Record<string, true> = {
    created_at: true,
    source_node_id: true,
    target_node_id: true,
  };

  const getVisibleData = (data?: Record<string, any>) => {
    if (!data) return {};
    const entries = Object.entries(data).filter(([key, value]) => {
      if (key in HIDDEN_KEYS) return false;
      return !(value === undefined || value === null);
    });
    return Object.fromEntries(entries);
  };

  return (
    <div className="col-12 col-lg-3 bg-dark text-white border-left border-secondary h-100 overflow-auto">
      <h2 className="h5 p-4 border-bottom border-secondary w-100" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
        <span style={{display: 'flex', alignItems: 'center'}}>
          AudAgent trace&nbsp;
          {isConnected ? (
            <LuLink2 className="text-green-500 ml-2" title="Receiving events"/>
          ) : (
            <LuLink2Off className="text-red-500 ml-2" title="Disconnected from events server"/>
          )}
        </span>
        <span>
          <LuCircleHelp data-tooltip-id="doc-tooltip"
                        data-tooltip-html="
                          <em>Left panel:</em> <br/>
                          Nodes □ represents the user, LLM, and third-party tools; <br/>
                          edges → represents request/response interactions.
                          <br/><br/>
                          <em>Right panel:</em> <br/>
                          Data practices for each interaction (edge), <br/>
                          potential violation highlighted in <span class='text-red-500'>red</span>.
                          <br/><br/>
                          Full documentation: <a href='https://github.com/ZhengYeah/AudAgent' target='_blank' class='text-blue-500 underline'>https://github.com/ZhengYeah/AudAgent</a>
                        "
                        className="text-black-500 ml-2"
                        style={{marginLeft: 'auto', display: 'flex', alignItems: 'center'}}/>
        </span>
        <Tooltip id="doc-tooltip" />
      </h2>

      <div className="table-responsive">
        <table className="table table-dark table-striped table-hover">
          <thead>
          <tr>
            <th className="text-muted small" style={{width: '40px'}}></th>
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
            const visibleData = getVisibleData(edge.data);
            const hasMetadataItems = Object.keys(visibleData).length > 0;
            // Check if violation_info exists in visibleData
            const hasViolation = Object.prototype.hasOwnProperty.call(visibleData, 'violation_info');

            return (
              <React.Fragment key={edge.id}>
                <tr
                  className={`${isHighlighted ? 'table-primary' : ''} ${hasViolation ? 'bg-danger' : ''}`}
                >
                  <td className="text-center">
                    {hasMetadataItems && (
                      <span
                        onClick={() => toggleRow(edge.id)}
                        style={{cursor: 'pointer'}}
                      >
                        {isExpanded ? <LuChevronDown size={16}/> : <LuChevronRight size={16}/>}
                      </span>
                    )}
                  </td>
                  <td>{edge.createdAt ? getTime(edge.createdAt) : 'N/A'}</td>
                  <td>{edge.source}</td>
                  <td>{edge.target}</td>
                </tr>
                {isExpanded && (
                  <motion.tr
                    className={hasViolation ? 'bg-danger' : ''}
                    initial={{opacity: 0, height: 0}}
                    animate={{opacity: 1, height: "auto"}}
                    exit={{opacity: 0, height: 0}}
                    transition={{duration: 0.3, ease: "easeInOut"}}
                  >
                    <td></td>
                    <td colSpan={3} className="border-0 pt-0">
                      <div className="p-2 bg-dark border border-secondary rounded">
                        <div className="d-flex align-items-center justify-content-between mb-2">
                          <small className="text-muted text-metadata">Metadata:</small>
                        </div>
                        {edge.data &&
                          Object.entries(visibleData).map(([key, value]) => (
                            !!(value) && <div key={key} className="mb-2">
                              <div className="d-flex align-items-center justify-content-between">
                                <small className="text-muted font-weight-bold">{key}</small>
                              </div>
                              <div
                                className="small mt-1 text-wrap"
                                style={{wordWrap: "break-word", whiteSpace: "pre-wrap", overflowWrap: "break-word", maxWidth: "100%"}} // Ensure text does not overflow
                              >
                                {typeof value === "string" ? (
                                  value || "-"
                                ) : (
                                  <pre
                                    className="text-white-50 mb-0"
                                    style={{fontSize: "0.75rem", wordWrap: "break-word", whiteSpace: "pre-wrap", overflowWrap: "break-word", maxWidth: "100%", margin: 0, padding: 0}}
                                  >
                                  {JSON.stringify(value, null, 2)}
                                </pre>
                                )}
                              </div>
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
