import { useRef, useState, useEffect } from 'react';

export default function PIDChart({ points }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const { width, height } = dimensions;

  if (!points?.length) {
    return (
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: 250,
          background: "#111",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#666"
        }}
      >
        No PID data available
      </div>
    );
  }

  const padding = { top: 20, right: 60, bottom: 50, left: 60 };
  const chartWidth = Math.max(width - padding.left - padding.right, 100);
  const chartHeight = Math.max(height - padding.top - padding.bottom - 50, 100);

  const proportionalData = points.map(p => p.pid_proportional || 0);
  const integralData = points.map(p => p.pid_integral || 0);
  const derivativeData = points.map(p => p.pid_derivative || 0);
  const damperData = points.map(p => p.damper_percent || 0);

  const allPIDValues = [...proportionalData, ...integralData, ...derivativeData];
  const pidMin = Math.min(...allPIDValues);
  const pidMax = Math.max(...allPIDValues);
  const pidRange = pidMax - pidMin || 1;

  const damperMin = 0;
  const damperMax = 100;

  const pidMinPadded = pidMin - pidRange * 0.1;
  const pidMaxPadded = pidMax + pidRange * 0.1;

  const scaleX = (index) => (index / (points.length - 1)) * chartWidth;
  const scalePID = (value) => chartHeight - ((value - pidMinPadded) / (pidMaxPadded - pidMinPadded)) * chartHeight;
  const scaleDamper = (value) => chartHeight - ((value - damperMin) / (damperMax - damperMin)) * chartHeight;

  const generatePath = (data, scaleFunc) => {
    if (data.length === 0) return "";
    return data.map((value, index) => {
      const x = scaleX(index);
      const y = scaleFunc(value);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).toLowerCase();
  };

  const pidGridLines = [];
  const numGridLines = 5;
  for (let i = 0; i <= numGridLines; i++) {
    const value = pidMinPadded + (pidMaxPadded - pidMinPadded) * (i / numGridLines);
    const y = scalePID(value);
    pidGridLines.push({ value, y });
  }

  const damperGridLines = [];
  for (let i = 0; i <= 5; i++) {
    const value = damperMin + (damperMax - damperMin) * (i / 5);
    const y = scaleDamper(value);
    damperGridLines.push({ value, y });
  }

  const timeSpan = points.length * 2;
  const startTime = Date.now() - (timeSpan * 1000);

  const timeLabels = [];
  const numTimeLabels = Math.min(6, points.length);
  for (let i = 0; i < numTimeLabels; i++) {
    const index = Math.floor((i / (numTimeLabels - 1)) * (points.length - 1));
    const timestamp = startTime + (index * 2000);
    const x = scaleX(index);
    timeLabels.push({ x, label: formatTime(timestamp) });
  }

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        minHeight: 250,
        background: "#111",
        borderRadius: 8,
        padding: 16,
        boxSizing: 'border-box'
      }}
    >
      <svg width={width - 32} height={height - 82} style={{ background: "#111" }}>
        <g transform={`translate(${padding.left}, ${padding.top})`}>
          {pidGridLines.map((line, i) => (
            <g key={`pid-grid-${i}`}>
              <line
                x1={0}
                y1={line.y}
                x2={chartWidth}
                y2={line.y}
                stroke="#333"
                strokeWidth={0.5}
              />
              <text
                x={-10}
                y={line.y + 4}
                fill="#888"
                fontSize="11"
                textAnchor="end"
              >
                {line.value.toFixed(1)}
              </text>
            </g>
          ))}

          {damperGridLines.map((line, i) => (
            <text
              key={`damper-grid-${i}`}
              x={chartWidth + 10}
              y={line.y + 4}
              fill="#888"
              fontSize="11"
              textAnchor="start"
            >
              {line.value.toFixed(0)}%
            </text>
          ))}

          {timeLabels.map((label, i) => (
            <g key={`time-${i}`}>
              <line
                x1={label.x}
                y1={chartHeight}
                x2={label.x}
                y2={chartHeight + 5}
                stroke="#888"
                strokeWidth={1}
              />
              <text
                x={label.x}
                y={chartHeight + 18}
                fill="#888"
                fontSize="11"
                textAnchor="middle"
              >
                {label.label}
              </text>
            </g>
          ))}

          <rect
            x={0}
            y={0}
            width={chartWidth}
            height={chartHeight}
            fill="none"
            stroke="#444"
            strokeWidth={1}
          />

          <path
            d={generatePath(proportionalData, scalePID)}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={2}
          />

          <path
            d={generatePath(integralData, scalePID)}
            fill="none"
            stroke="#10b981"
            strokeWidth={2}
          />

          <path
            d={generatePath(derivativeData, scalePID)}
            fill="none"
            stroke="#ef4444"
            strokeWidth={2}
          />

          <path
            d={generatePath(damperData, scaleDamper)}
            fill="none"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5,5"
          />
        </g>

        <text
          x={20}
          y={(height - 82) / 2}
          fill="#888"
          fontSize="12"
          textAnchor="middle"
          transform={`rotate(-90, 20, ${(height - 82) / 2})`}
        >
          PID Contribution
        </text>

        <text
          x={width - 52}
          y={(height - 82) / 2}
          fill="#888"
          fontSize="12"
          textAnchor="middle"
          transform={`rotate(90, ${width - 52}, ${(height - 82) / 2})`}
        >
          Damper %
        </text>
      </svg>

      <div style={{
        display: "flex",
        gap: 16,
        marginTop: 12,
        flexWrap: "wrap",
        justifyContent: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 16, height: 2, background: "#3b82f6" }}></div>
          <span style={{ color: "#888", fontSize: 12 }}>Proportional</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 16, height: 2, background: "#10b981" }}></div>
          <span style={{ color: "#888", fontSize: 12 }}>Integral</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 16, height: 2, background: "#ef4444" }}></div>
          <span style={{ color: "#888", fontSize: 12 }}>Derivative</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{
            width: 16,
            height: 2,
            background: "#f59e0b",
            backgroundImage: "repeating-linear-gradient(to right, #f59e0b 0, #f59e0b 4px, transparent 4px, transparent 8px)"
          }}></div>
          <span style={{ color: "#888", fontSize: 12 }}>Damper %</span>
        </div>
      </div>
    </div>
  );
}
