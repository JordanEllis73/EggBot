import { getDisplayTemperature, formatTemperature } from './utils/temperature';

// Fixed viewBox dimensions - SVG scales via CSS
const WIDTH = 900;
const HEIGHT = 400;

export default function TemperatureChart({ points, status, meaterStatus, meaterHistory = [], temperatureUnit = 'C' }) {
  const width = WIDTH;
  const height = HEIGHT;

  if (!points?.length) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
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

  const padding = { top: 20, right: 80, bottom: 50, left: 60 };
  const chartWidth = Math.max(width - padding.left - padding.right, 100);
  const chartHeight = Math.max(height - padding.top - padding.bottom, 100);

  const convertTemp = (temp) => getDisplayTemperature(temp, temperatureUnit);

  const pitTemps = points.map(p => convertTemp(p.pit_temp_c)).filter(t => t != null);
  const meat1Temps = points.map(p => convertTemp(p.meat_temp_1_c || p.meat_temp_c)).filter(t => t != null);
  const meat2Temps = points.map(p => convertTemp(p.meat_temp_2_c)).filter(t => t != null);
  const setpointTemps = points.map(p => convertTemp(p.setpoint_c)).filter(t => t != null);
  const meatSetpointTemps = points.map(p => convertTemp(p.meat_setpoint_c)).filter(t => t != null);

  let meaterProbeTemps = [];
  let meaterAmbientTemps = [];

  if (meaterHistory.length > 0) {
    const timeSpan = points.length * 2;
    const chartStartTime = Date.now() - (timeSpan * 1000);

    meaterProbeTemps = points.map((_, index) => {
      const pointTime = chartStartTime + (index * 2000);
      let closestReading = null;
      let minTimeDiff = Infinity;

      for (const meaterPoint of meaterHistory) {
        const timeDiff = Math.abs(meaterPoint.timestamp - pointTime);
        if (timeDiff < minTimeDiff && timeDiff < 10000) {
          minTimeDiff = timeDiff;
          closestReading = meaterPoint;
        }
      }

      if (closestReading) {
        const tempC = closestReading.probe_temp_c;
        return tempC != null ? convertTemp(tempC) : null;
      }
      return null;
    });

    meaterAmbientTemps = points.map((_, index) => {
      const pointTime = chartStartTime + (index * 2000);
      let closestReading = null;
      let minTimeDiff = Infinity;

      for (const meaterPoint of meaterHistory) {
        const timeDiff = Math.abs(meaterPoint.timestamp - pointTime);
        if (timeDiff < minTimeDiff && timeDiff < 10000) {
          minTimeDiff = timeDiff;
          closestReading = meaterPoint;
        }
      }

      if (closestReading) {
        const tempC = closestReading.ambient_temp_c;
        return tempC != null ? convertTemp(tempC) : null;
      }
      return null;
    });
  }

  const allTemps = [...pitTemps, ...meat1Temps, ...meat2Temps, ...setpointTemps, ...meatSetpointTemps, ...meaterProbeTemps.filter(t => t != null), ...meaterAmbientTemps.filter(t => t != null)];

  if (allTemps.length === 0) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        background: "#111",
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#666"
      }}>
        No temperature data
      </div>
    );
  }

  const minTemp = Math.min(...allTemps) - 5;
  const maxTemp = Math.max(...allTemps) + 5;
  const tempRange = maxTemp - minTemp || 1;

  const timeSpan = points.length * 2;
  const startTime = Date.now() - (timeSpan * 1000);

  const getX = (index) => padding.left + (index / (points.length - 1)) * chartWidth;
  const getY = (temp) => padding.top + ((maxTemp - temp) / tempRange) * chartHeight;

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).toLowerCase();
  };

  const createPath = (temps) => {
    const pathSegments = [];
    let currentSegment = [];

    temps.forEach((temp, i) => {
      if (temp != null) {
        const x = getX(i);
        const y = getY(temp);
        currentSegment.push({ x, y, isFirst: currentSegment.length === 0 });
      } else {
        if (currentSegment.length > 0) {
          pathSegments.push(currentSegment);
          currentSegment = [];
        }
      }
    });

    if (currentSegment.length > 0) {
      pathSegments.push(currentSegment);
    }

    return pathSegments.map(segment =>
      segment.map((point, i) =>
        `${i === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`
      ).join(' ')
    ).join(' ');
  };

  const pitPath = createPath(points.map(p => convertTemp(p.pit_temp_c)));
  const meat1Path = createPath(points.map(p => convertTemp(p.meat_temp_1_c || p.meat_temp_c)));
  const meat2Path = createPath(points.map(p => convertTemp(p.meat_temp_2_c)));
  const pitSetPath = createPath(points.map(p => convertTemp(p.setpoint_c)));
  const meatSetPath = createPath(points.map(p => convertTemp(p.meat_setpoint_c)));
  const meaterProbePath = meaterProbeTemps.length > 0 ? createPath(meaterProbeTemps) : null;
  const meaterAmbientPath = meaterAmbientTemps.length > 0 ? createPath(meaterAmbientTemps) : null;

  const tempTicks = [];
  const tempStep = Math.ceil(tempRange / 8 / 10) * 10;
  for (let temp = Math.ceil(minTemp / tempStep) * tempStep; temp <= maxTemp; temp += tempStep) {
    tempTicks.push({
      temp: temp,
      y: getY(temp),
      label: `${temp}°${temperatureUnit}`
    });
  }

  const timeTicks = [];
  const numTimeTicks = Math.min(6, points.length);
  const timeStep = Math.max(1, Math.floor(points.length / numTimeTicks));
  for (let i = 0; i < points.length; i += timeStep) {
    const timestamp = startTime + (i * 2000);
    timeTicks.push({
      x: getX(i),
      label: formatTime(timestamp)
    });
  }
  if (points.length > 1) {
    const lastTimestamp = startTime + ((points.length - 1) * 2000);
    const lastTick = timeTicks[timeTicks.length - 1];
    if (lastTick && getX(points.length - 1) - lastTick.x > 50) {
      timeTicks.push({
        x: getX(points.length - 1),
        label: formatTime(lastTimestamp)
      });
    }
  }

  const isPitConnected = pitTemps.length > 0;
  const isMeat1Connected = meat1Temps.length > 0;
  const isMeat2Connected = meat2Temps.length > 0;
  const isMeaterProbeConnected = meaterProbeTemps.some(t => t != null);
  const isMeaterAmbientConnected = meaterAmbientTemps.some(t => t != null);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        style={{
          width: '100%',
          height: '100%',
          background: "#111",
          borderRadius: 8,
          display: 'block'
        }}
      >
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

        {isPitConnected && pitPath && (
          <path
            d={pitPath}
            stroke="#ff6b35"
            fill="none"
            strokeWidth="3"
          />
        )}

        {isMeat1Connected && meat1Path && (
          <path
            d={meat1Path}
            stroke="#4ecdc4"
            fill="none"
            strokeWidth="3"
          />
        )}

        {isMeat2Connected && meat2Path && (
          <path
            d={meat2Path}
            stroke="#4ecdc4"
            fill="none"
            strokeWidth="3"
            strokeDasharray="3,3"
          />
        )}

        {isMeaterProbeConnected && meaterProbePath && (
          <path
            d={meaterProbePath}
            stroke="#c44ecb"
            fill="none"
            strokeWidth="3"
            strokeDasharray="5,3"
          />
        )}

        {isMeaterAmbientConnected && meaterAmbientPath && (
          <path
            d={meaterAmbientPath}
            stroke="#ff9500"
            fill="none"
            strokeWidth="3"
            strokeDasharray="5,3"
          />
        )}

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
            y={height - padding.bottom + 18}
            fill="#aaa"
            fontSize="11"
            textAnchor="middle"
          >
            {tick.label}
          </text>
        ))}

        <text
          x={padding.left / 2}
          y={height / 2}
          fill="#aaa"
          fontSize="13"
          textAnchor="middle"
          transform={`rotate(-90 ${padding.left / 2} ${height / 2})`}
        >
          Temperature (°{temperatureUnit})
        </text>

        <text
          x={(width - padding.right + padding.left) / 2}
          y={height - 6}
          fill="#aaa"
          fontSize="13"
          textAnchor="middle"
        >
          Time
        </text>

        {isPitConnected && points.length > 0 && points[points.length - 1].pit_temp_c != null && (
          <circle
            cx={getX(points.length - 1)}
            cy={getY(convertTemp(points[points.length - 1].pit_temp_c))}
            r="4"
            fill="#ff6b35"
            stroke="#111"
            strokeWidth="2"
          />
        )}

        {isMeat1Connected && points.length > 0 && (points[points.length - 1].meat_temp_1_c != null || points[points.length - 1].meat_temp_c != null) && (
          <circle
            cx={getX(points.length - 1)}
            cy={getY(convertTemp(points[points.length - 1].meat_temp_1_c || points[points.length - 1].meat_temp_c))}
            r="4"
            fill="#4ecdc4"
            stroke="#111"
            strokeWidth="2"
          />
        )}

        {isMeat2Connected && points.length > 0 && points[points.length - 1].meat_temp_2_c != null && (
          <circle
            cx={getX(points.length - 1)}
            cy={getY(convertTemp(points[points.length - 1].meat_temp_2_c))}
            r="4"
            fill="#4ecdc4"
            stroke="#111"
            strokeWidth="2"
          />
        )}

        {isMeaterProbeConnected && meaterProbeTemps.length > 0 && meaterProbeTemps[meaterProbeTemps.length - 1] != null && (
          <circle
            cx={getX(points.length - 1)}
            cy={getY(meaterProbeTemps[meaterProbeTemps.length - 1])}
            r="4"
            fill="#c44ecb"
            stroke="#111"
            strokeWidth="2"
          />
        )}

        {isMeaterAmbientConnected && meaterAmbientTemps.length > 0 && meaterAmbientTemps[meaterAmbientTemps.length - 1] != null && (
          <circle
            cx={getX(points.length - 1)}
            cy={getY(meaterAmbientTemps[meaterAmbientTemps.length - 1])}
            r="4"
            fill="#ff9500"
            stroke="#111"
            strokeWidth="2"
          />
        )}
      </svg>

      <div style={{
        position: 'absolute',
        top: 12,
        right: 12,
        background: 'rgba(20, 20, 20, 0.95)',
        padding: 10,
        borderRadius: 6,
        border: '1px solid #333',
        maxWidth: 180
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11 }}>
          {isPitConnected && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 16, height: 3, background: '#ff6b35', flexShrink: 0 }}></div>
              <span style={{ color: '#ddd' }}>Pit: {points.length > 0 && points[points.length - 1].pit_temp_c != null
                ? formatTemperature(convertTemp(points[points.length - 1].pit_temp_c), temperatureUnit) : '—'}</span>
            </div>
          )}
          {status?.setpoint_c && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 16,
                height: 3,
                background: '#ff6b35',
                backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 3px, #111 3px, #111 5px)',
                flexShrink: 0
              }}></div>
              <span style={{ color: '#999' }}>Target: {formatTemperature(convertTemp(status.setpoint_c), temperatureUnit)}</span>
            </div>
          )}
          {isMeat1Connected && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 16, height: 3, background: '#4ecdc4', flexShrink: 0 }}></div>
                <span style={{ color: '#ddd' }}>Meat 1: {points.length > 0 && (points[points.length - 1].meat_temp_1_c != null || points[points.length - 1].meat_temp_c != null)
                  ? formatTemperature(convertTemp(points[points.length - 1].meat_temp_1_c || points[points.length - 1].meat_temp_c), temperatureUnit) : '—'}</span>
              </div>
              {status?.meat_setpoint_c && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{
                    width: 16,
                    height: 3,
                    background: '#4ecdc4',
                    backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 3px, #111 3px, #111 5px)',
                    flexShrink: 0
                  }}></div>
                  <span style={{ color: '#999' }}>Target: {formatTemperature(convertTemp(status.meat_setpoint_c), temperatureUnit)}</span>
                </div>
              )}
            </>
          )}
          {isMeat2Connected && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 16,
                height: 3,
                background: '#4ecdc4',
                backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 1.5px, #111 1.5px, #111 3px)',
                flexShrink: 0
              }}></div>
              <span style={{ color: '#ddd' }}>Meat 2: {points.length > 0 && points[points.length - 1].meat_temp_2_c != null
                ? formatTemperature(convertTemp(points[points.length - 1].meat_temp_2_c), temperatureUnit) : '—'}</span>
            </div>
          )}
          {isMeaterProbeConnected && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 16,
                height: 3,
                background: '#c44ecb',
                backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 2px, #111 2px, #111 4px)',
                flexShrink: 0
              }}></div>
              <span style={{ color: '#ddd' }}>Meater: {meaterProbeTemps[meaterProbeTemps.length - 1] != null
                ? formatTemperature(meaterProbeTemps[meaterProbeTemps.length - 1], temperatureUnit)
                : '—'}</span>
            </div>
          )}
          {isMeaterAmbientConnected && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 16,
                height: 3,
                background: '#ff9500',
                backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 2px, #111 2px, #111 4px)',
                flexShrink: 0
              }}></div>
              <span style={{ color: '#ddd' }}>Ambient: {meaterAmbientTemps[meaterAmbientTemps.length - 1] != null
                ? formatTemperature(meaterAmbientTemps[meaterAmbientTemps.length - 1], temperatureUnit)
                : '—'}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
