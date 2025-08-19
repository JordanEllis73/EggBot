export default function TemperatureChart({ points, status, width = 800, height = 400 }) {
  if (!points?.length) {
    return (
      <div style={{ 
        width: width, 
        height: height, 
        background: "#111", 
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#666"
      }}>
        No telemetry data available
      </div>
    );
  }
  
  const padding = { top: 20, right: 60, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  // Extract temperature data
  const pitTemps = points.map(p => p.pit_temp_c).filter(t => t != null);
  const meatTemps = points.map(p => p.meat_temp_c).filter(t => t != null);
  const setpointTemps = points.map(p => p.setpoint_c).filter(t => t != null);
  const meatSetpointTemps = points.map(p => p.meat_setpoint_c).filter(t => t != null);
  const allTemps = [...pitTemps, ...meatTemps, ...setpointTemps, ...meatSetpointTemps];
  
  if (allTemps.length === 0) return <div>No temperature data</div>;
  
  // Calculate temperature range with some padding
  const minTemp = Math.min(...allTemps) - 5;
  const maxTemp = Math.max(...allTemps) + 5;
  const tempRange = maxTemp - minTemp || 1;
  
  // Time calculations - assuming points are evenly spaced in time
  const timeSpan = points.length * 2; // Assuming 2-second intervals based on your polling
  const startTime = Date.now() - (timeSpan * 1000);
  
  // Helper functions
  const getX = (index) => padding.left + (index / (points.length - 1)) * chartWidth;
  const getY = (temp) => padding.top + ((maxTemp - temp) / tempRange) * chartHeight;
  
  // Fixed path creation function to handle null values properly
  const createPath = (temps) => {
    const pathSegments = [];
    let currentSegment = [];
    
    temps.forEach((temp, i) => {
      if (temp != null) {
        const x = getX(i);
        const y = getY(temp);
        currentSegment.push({ x, y, isFirst: currentSegment.length === 0 });
      } else {
        // End current segment when we hit a null value
        if (currentSegment.length > 0) {
          pathSegments.push(currentSegment);
          currentSegment = [];
        }
      }
    });
    
    // Don't forget the last segment
    if (currentSegment.length > 0) {
      pathSegments.push(currentSegment);
    }
    
    // Convert segments to path strings
    return pathSegments.map(segment => 
      segment.map((point, i) => 
        `${i === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`
      ).join(' ')
    ).join(' ');
  };
  
  const pitPath = createPath(points.map(p => p.pit_temp_c));
  const meatPath = createPath(points.map(p => p.meat_temp_c));
  const pitSetPath = createPath(points.map(p => p.setpoint_c));
  const meatSetPath = createPath(points.map(p => p.meat_setpoint_c));
  
  // Setpoint lines
  const pitSetpointY = status?.setpoint_c ? getY(status.setpoint_c) : null;
  const meatSetpointY = status?.meat_setpoint_c ? getY(status.meat_setpoint_c) : null;
  
  // Generate tick marks for temperature axis
  const tempTicks = [];
  const tempStep = Math.ceil(tempRange / 8 / 10) * 10; // Round to nearest 10
  for (let temp = Math.ceil(minTemp / tempStep) * tempStep; temp <= maxTemp; temp += tempStep) {
    tempTicks.push({
      temp: temp,
      y: getY(temp),
      label: `${temp}°C`
    });
  }
  
  // Generate time ticks
  const timeTicks = [];
  const timeStep = Math.max(1, Math.floor(points.length / 6)); // About 6 ticks
  for (let i = 0; i < points.length; i += timeStep) {
    const minutesAgo = Math.round((points.length - 1 - i) * 2 / 60);
    timeTicks.push({
      x: getX(i),
      label: minutesAgo === 0 ? 'Now' : `-${minutesAgo}m`
    });
  }
  
  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height} style={{ background: "#111", borderRadius: 8 }}>
        {/* Grid lines */}
        {tempTicks.map((tick, i) => (
          <line 
            key={`temp-grid-${i}`}
            x1={padding.left} 
            y1={tick.y} 
            x2={width - padding.right} 
            y2={tick.y}
            stroke="#333" 
            strokeWidth="1"
            strokeDasharray="2,2"
          />
        ))}
        
        {timeTicks.map((tick, i) => (
          <line 
            key={`time-grid-${i}`}
            x1={tick.x} 
            y1={padding.top} 
            x2={tick.x} 
            y2={height - padding.bottom}
            stroke="#333" 
            strokeWidth="1"
            strokeDasharray="2,2"
          />
        ))}
        
        {/* Temperature axes */}
        <line 
          x1={padding.left} 
          y1={padding.top} 
          x2={padding.left} 
          y2={height - padding.bottom}
          stroke="#666" 
          strokeWidth="2"
        />
        <line 
          x1={padding.left} 
          y1={height - padding.bottom} 
          x2={width - padding.right} 
          y2={height - padding.bottom}
          stroke="#666" 
          strokeWidth="2"
        />
         
        {/* Temperature paths - Fixed to prevent fill issues */}
        {pitSetPath && (
          <path 
            d={pitSetPath} 
            stroke="#ff6b35"
            strokeWidth="2"
            strokeDasharray="8,4"
            fill="none"
          />
        )}
        
        {meatSetPath && (
          <path 
            d={meatSetPath} 
            stroke="#4ecdc4"
            strokeWidth="2"
            strokeDasharray="8,4"
            fill="none"
          />
        )}
 
        {pitPath && (
          <path 
            d={pitPath} 
            stroke="#ff6b35" 
            fill="none" 
            strokeWidth="3"
          />
        )}
        
        {meatPath && (
          <path 
            d={meatPath} 
            stroke="#4ecdc4" 
            fill="none" 
            strokeWidth="3"
          />
        )}
        
        {/* Axis labels */}
        {tempTicks.map((tick, i) => (
          <text 
            key={`temp-label-${i}`}
            x={padding.left - 8} 
            y={tick.y + 4} 
            fill="#aaa" 
            fontSize="12" 
            textAnchor="end"
          >
            {tick.label}
          </text>
        ))}
        
        {timeTicks.map((tick, i) => (
          <text 
            key={`time-label-${i}`}
            x={tick.x} 
            y={height - padding.bottom + 20} 
            fill="#aaa" 
            fontSize="12" 
            textAnchor="middle"
          >
            {tick.label}
          </text>
        ))}
        
        {/* Axis titles */}
        <text 
          x={padding.left / 2} 
          y={height / 2} 
          fill="#aaa" 
          fontSize="14" 
          textAnchor="middle"
          transform={`rotate(-90 ${padding.left / 2} ${height / 2})`}
        >
          Temperature (°C)
        </text>
        
        <text 
          x={width / 2} 
          y={height - 10} 
          fill="#aaa" 
          fontSize="14" 
          textAnchor="middle"
        >
          Time
        </text>
        
        {/* Current value indicators */}
        {points.length > 0 && points[points.length - 1].pit_temp_c != null && (
          <circle 
            cx={getX(points.length - 1)} 
            cy={getY(points[points.length - 1].pit_temp_c)} 
            r="4" 
            fill="#ff6b35"
            stroke="#111"
            strokeWidth="2"
          />
        )}
        
        {points.length > 0 && points[points.length - 1].meat_temp_c != null && (
          <circle 
            cx={getX(points.length - 1)} 
            cy={getY(points[points.length - 1].meat_temp_c)} 
            r="4" 
            fill="#4ecdc4"
            stroke="#111"
            strokeWidth="2"
          />
        )}
      </svg>
      
      {/* Legend */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        background: 'rgba(20, 20, 20, 0.9)',
        padding: 12,
        borderRadius: 6,
        border: '1px solid #333'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 20, height: 3, background: '#ff6b35' }}></div>
            <span>Pit Temp: {points.length > 0 && points[points.length - 1].pit_temp_c != null 
              ? `${points[points.length - 1].pit_temp_c.toFixed(1)}°C` : '—'}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ 
              width: 20, 
              height: 3, 
              background: '#ff6b35',
              backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 4px, #111 4px, #111 6px)'
            }}></div>
            <span>Pit Target: {status?.setpoint_c ? `${status.setpoint_c.toFixed(1)}°C` : '—'}</span>
          </div>
          {(points.some(p => p.meat_temp_c != null) || status?.meat_setpoint_c) && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 20, height: 3, background: '#4ecdc4' }}></div>
                <span>Meat Temp: {points.length > 0 && points[points.length - 1].meat_temp_c != null 
                  ? `${points[points.length - 1].meat_temp_c.toFixed(1)}°C` : '—'}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ 
                  width: 20, 
                  height: 3, 
                  background: '#4ecdc4',
                  backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 4px, #111 4px, #111 6px)'
                }}></div>
                <span>Meat Target: {status?.meat_setpoint_c ? `${status.meat_setpoint_c.toFixed(1)}°C` : '—'}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
