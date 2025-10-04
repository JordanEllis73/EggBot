export default function PIDChart({ points, width = 800, height = 400 }) {
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
        No PID data available
      </div>
    );
  }

  const padding = { top: 20, right: 60, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Extract PID data
  const proportionalData = points.map(p => p.pid_proportional || 0);
  const integralData = points.map(p => p.pid_integral || 0);
  const derivativeData = points.map(p => p.pid_derivative || 0);
  const damperData = points.map(p => p.damper_percent || 0);
  const timestamps = points.map(p => p.timestamp);

  // Find data ranges for scaling
  const allPIDValues = [...proportionalData, ...integralData, ...derivativeData];
  const pidMin = Math.min(...allPIDValues);
  const pidMax = Math.max(...allPIDValues);
  const pidRange = pidMax - pidMin;

  // Damper is in percentage (0-100)
  const damperMin = 0;
  const damperMax = 100;

  // Add some padding to the ranges
  const pidMinPadded = pidMin - pidRange * 0.1;
  const pidMaxPadded = pidMax + pidRange * 0.1;

  // Scale functions
  const scaleX = (index) => (index / (points.length - 1)) * chartWidth;
  const scalePID = (value) => chartHeight - ((value - pidMinPadded) / (pidMaxPadded - pidMinPadded)) * chartHeight;
  const scaleDamper = (value) => chartHeight - ((value - damperMin) / (damperMax - damperMin)) * chartHeight;

  // Generate SVG path for a data series
  const generatePath = (data, scaleFunc) => {
    if (data.length === 0) return "";

    const pathData = data.map((value, index) => {
      const x = scaleX(index);
      const y = scaleFunc(value);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    return pathData;
  };

  // Generate grid lines for PID scale
  const pidGridLines = [];
  const numGridLines = 5;
  for (let i = 0; i <= numGridLines; i++) {
    const value = pidMinPadded + (pidMaxPadded - pidMinPadded) * (i / numGridLines);
    const y = scalePID(value);
    pidGridLines.push(
      <g key={`pid-grid-${i}`}>
        <line
          x1={0}
          y1={y}
          x2={chartWidth}
          y2={y}
          stroke="#333"
          strokeWidth={0.5}
        />
        <text
          x={-10}
          y={y + 4}
          fill="#888"
          fontSize="12"
          textAnchor="end"
        >
          {value.toFixed(1)}
        </text>
      </g>
    );
  }

  // Generate grid lines for damper scale (right side)
  const damperGridLines = [];
  for (let i = 0; i <= 5; i++) {
    const value = damperMin + (damperMax - damperMin) * (i / 5);
    const y = scaleDamper(value);
    damperGridLines.push(
      <g key={`damper-grid-${i}`}>
        <text
          x={chartWidth + 10}
          y={y + 4}
          fill="#888"
          fontSize="12"
          textAnchor="start"
        >
          {value.toFixed(0)}%
        </text>
      </g>
    );
  }

  // Generate time labels
  const timeLabels = [];
  const numTimeLabels = 6;
  for (let i = 0; i < numTimeLabels && i < points.length; i++) {
    const index = Math.floor((i / (numTimeLabels - 1)) * (points.length - 1));
    const timestamp = timestamps[index];
    const x = scaleX(index);

    // Format time (show only time part)
    const timeStr = new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });

    timeLabels.push(
      <g key={`time-${i}`}>
        <line
          x1={x}
          y1={chartHeight}
          x2={x}
          y2={chartHeight + 5}
          stroke="#888"
          strokeWidth={1}
        />
        <text
          x={x}
          y={chartHeight + 18}
          fill="#888"
          fontSize="12"
          textAnchor="middle"
        >
          {timeStr}
        </text>
      </g>
    );
  }

  return (
    <div style={{ background: "#111", borderRadius: 8, padding: "16px" }}>
      <h3 style={{ color: "#fff", margin: "0 0 16px 0", fontSize: "18px" }}>
        PID Controller Output
      </h3>

      <svg width={width} height={height} style={{ background: "#111" }}>
        <g transform={`translate(${padding.left}, ${padding.top})`}>
          {/* Grid lines for PID values */}
          {pidGridLines}

          {/* Grid lines for damper values */}
          {damperGridLines}

          {/* Time labels */}
          {timeLabels}

          {/* Chart border */}
          <rect
            x={0}
            y={0}
            width={chartWidth}
            height={chartHeight}
            fill="none"
            stroke="#444"
            strokeWidth={1}
          />

          {/* Proportional component (solid blue line) */}
          <path
            d={generatePath(proportionalData, scalePID)}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={2}
          />

          {/* Integral component (solid green line) */}
          <path
            d={generatePath(integralData, scalePID)}
            fill="none"
            stroke="#10b981"
            strokeWidth={2}
          />

          {/* Derivative component (solid red line) */}
          <path
            d={generatePath(derivativeData, scalePID)}
            fill="none"
            stroke="#ef4444"
            strokeWidth={2}
          />

          {/* Damper percentage (dashed orange line) */}
          <path
            d={generatePath(damperData, scaleDamper)}
            fill="none"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5,5"
          />
        </g>

        {/* Left Y-axis label (PID Values) */}
        <text
          x={20}
          y={height / 2}
          fill="#888"
          fontSize="14"
          textAnchor="middle"
          transform={`rotate(-90, 20, ${height / 2})`}
        >
          PID Contribution
        </text>

        {/* Right Y-axis label (Damper %) */}
        <text
          x={width - 20}
          y={height / 2}
          fill="#888"
          fontSize="14"
          textAnchor="middle"
          transform={`rotate(90, ${width - 20}, ${height / 2})`}
        >
          Damper %
        </text>

        {/* X-axis label */}
        <text
          x={width / 2}
          y={height - 10}
          fill="#888"
          fontSize="14"
          textAnchor="middle"
        >
          Time
        </text>
      </svg>

      {/* Legend */}
      <div style={{
        display: "flex",
        gap: "20px",
        marginTop: "16px",
        flexWrap: "wrap",
        justifyContent: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "20px",
            height: "2px",
            background: "#3b82f6"
          }}></div>
          <span style={{ color: "#888", fontSize: "14px" }}>Proportional</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "20px",
            height: "2px",
            background: "#10b981"
          }}></div>
          <span style={{ color: "#888", fontSize: "14px" }}>Integral</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "20px",
            height: "2px",
            background: "#ef4444"
          }}></div>
          <span style={{ color: "#888", fontSize: "14px" }}>Derivative</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "20px",
            height: "2px",
            background: "#f59e0b",
            backgroundImage: "repeating-linear-gradient(to right, #f59e0b 0, #f59e0b 5px, transparent 5px, transparent 10px)"
          }}></div>
          <span style={{ color: "#888", fontSize: "14px" }}>Damper %</span>
        </div>
      </div>
    </div>
  );
}