import {getBezierPath, getEdgeCenter, EdgeLabelRenderer} from '@xyflow/react';
import * as React from 'react';
import {useEffect, useState} from 'react';
import {LuPackageOpen, LuPackageSearch, LuX} from 'react-icons/lu';

const CustomEdge = ({
                      id,
                      sourceX,
                      sourceY,
                      targetX,
                      targetY,
                      sourcePosition,
                      targetPosition,
                      style = {},
                      markerEnd,
                      source,
                      target,
                      data,
                      setSelectedNodes, // New prop to communicate with parent
                    }) => {
  const [isHovering, setIsHovering] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const xEqual = sourceX === targetX;
  const yEqual = sourceY === targetY;

  const [edgePath] = getBezierPath({
    // we need this little hack in order to display the gradient for a straight line
    sourceX: xEqual ? sourceX + 0.0001 : sourceX,
    sourceY: yEqual ? sourceY + 0.0001 : sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Get the center point of the edge for positioning the icon
  const [edgeCenterX, edgeCenterY] = getEdgeCenter({sourceX, sourceY, targetX, targetY});

  // Hide the icon for user-to-app edges
  const hideIcon = Boolean(data?.hideIcon) || (source === 'user' && target === 'app');

  // Flag icon red when edge.data has 'violation_info'
  const violationInfo = data?.violation_info;
  const hasViolation = !!data && Object.prototype.hasOwnProperty.call(data, 'violation_info') && data.violation_info;
  const iconColor = hasViolation ? '#dc3545' /* bootstrap danger */ : '#198754';

  const handleIconClick = (e) => {
    e.stopPropagation();
    setShowPopup(!showPopup);
    // Highlight relevant rows in the sidebar
    setSelectedNodes({source, target});
  };

  const handleMouseEnter = () => {
    setIsHovering(true);
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
  };

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (showPopup) {
        setShowPopup(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showPopup]);

  const popupWidth = 250;
  const popupHeight = 160;
  const popupX = edgeCenterX + 15;
  const popupY = edgeCenterY - popupHeight / 2;

  return (
    <>
      <path id={id} style={style} className="react-flow__edge-path" d={edgePath} markerEnd={markerEnd}/>

      <EdgeLabelRenderer>
        {!hideIcon && (
          <div
            style={{ position: 'absolute', transform: `translate(-50%, -50%) translate(${edgeCenterX}px, ${edgeCenterY}px)`, pointerEvents: 'auto', zIndex: 1000 }}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            onClick={handleIconClick}
          >
            {isHovering ? (
              <LuPackageOpen size={20} style={{ color: iconColor, cursor: 'pointer' }} />
            ) : (
              <LuPackageSearch size={20} style={{ color: iconColor, cursor: 'pointer' }} />
            )}

            {showPopup && hasViolation && (
              <div
                role="dialog"
                aria-label="violation info"
                className="violation-box"
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ color: 'black' }}>violation_info</span>
                  <button
                    onClick={() => setShowPopup(false)}
                    style={{ background: 'transparent', border: 0, cursor: 'pointer', color: 'black', fontSize: 18, paddingRight: 0.5 }}
                    aria-label="Close"
                  >
                    ×
                  </button>
                </div>
                <div
                  className="violation-content"
                  style={{color: 'red', fontSize: 12, maxHeight: 100, overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                >
                  {typeof violationInfo === 'string' ? violationInfo : JSON.stringify(violationInfo, null, 2)}
                </div>
              </div>
            )}
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
};

export default CustomEdge;
