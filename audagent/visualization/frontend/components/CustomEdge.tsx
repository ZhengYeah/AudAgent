import {getBezierPath, getEdgeCenter} from '@xyflow/react';
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
      <path
        id={id}
        style={style}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />

      {/* Icon in the middle of the edge */}
      {!hideIcon && (
        <foreignObject
          width={20}
          height={20}
          x={edgeCenterX - 10}
          y={edgeCenterY - 10}
          className="edge-icon-container"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleIconClick}
          style={{overflow: 'visible'}}
        >
          <div className="flex items-center justify-center h-full z-50">
            {isHovering ?
              <LuPackageOpen
                size={20}
                className={`cursor-pointer text-blue-500 transition-all duration-200 ${isHovering ? 'animate-pulse' : ''}`}
                style={{color: iconColor}}
              /> :
              <LuPackageSearch
                size={20}
                className={`cursor-pointer text-blue-500 transition-all duration-200 ${isHovering ? 'animate-pulse' : ''}`}
                style={{color: iconColor}}
              />
            }
          </div>
        </foreignObject>
      )}

      {/* Popup on icon click */}
      {!hideIcon && showPopup && hasViolation && (
        <foreignObject
          width={popupWidth}
          height={popupHeight}
          x={popupX}
          y={popupY}
          className="edge-popup-container"
          style={{overflow: 'visible', pointerEvents: 'auto'}}
        >
          <div
            role="dialog"
            aria-label="violation info"
            onClick={(e) => e.stopPropagation()}
            className="violation-box"
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6}}>
              <strong style={{color: 'black'}}>violation_info</strong>
              <button
                onClick={() => setShowPopup(false)}
                style={{
                  background: 'transparent',
                  border: 0,
                  color: 'black',
                  cursor: 'pointer',
                  fontSize: 16,
                  lineHeight: 1,
                }}
                aria-label="Close"
                title="Close"
              >
                <i style={{fontSize: 20}}>×</i>
              </button>
            </div>
            <div
              style={{color: 'red', fontSize: 12, maxHeight: popupHeight - 40, overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word'}}>
              {typeof violationInfo === 'string' ? (
                violationInfo
              ) : (
                <pre style={{margin: 0, color: 'white'}}>{JSON.stringify(violationInfo, null, 2)}</pre>
              )}
            </div>
          </div>
        </foreignObject>
      )}
    </>
  );
};

export default CustomEdge;
