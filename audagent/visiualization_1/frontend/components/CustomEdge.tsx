import { getBezierPath, getEdgeCenter } from '@xyflow/react';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { LuPackageOpen, LuPackageSearch } from 'react-icons/lu';

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
  const [edgeCenterX, edgeCenterY] = getEdgeCenter({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const handleIconClick = (e) => {
    e.stopPropagation();
    setShowPopup(!showPopup);
    
    // Highlight relevant rows in the sidebar
    setSelectedNodes({
      source,
      target
    });
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
      <foreignObject
        width={20}
        height={20}
        x={edgeCenterX - 10}
        y={edgeCenterY - 10}
        className="edge-icon-container"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleIconClick}
        style={{ overflow: 'visible' }}
      >
        <div className="flex items-center justify-center h-full z-50">
        {isHovering ? 
          <LuPackageOpen
            size={20} 
            className={`cursor-pointer text-blue-500 transition-all duration-200 ${isHovering ? 'animate-pulse' : ''}`} 
          /> :
          <LuPackageSearch 
            size={20} 
            className={`cursor-pointer text-blue-500 transition-all duration-200 ${isHovering ? 'animate-pulse' : ''}`} 
          />
        }  
        </div>
      </foreignObject>
    </>
  );
};

export default CustomEdge;