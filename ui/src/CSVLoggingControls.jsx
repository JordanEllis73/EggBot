import { useState, useEffect } from "react";

export default function CSVLoggingControls() {
  const [isLogging, setIsLogging] = useState(false);
  const [filename, setFilename] = useState('');
  const [interval, setInterval] = useState(5);
  const [logStatus, setLogStatus] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [error, setError] = useState('');

  // Generate default filename based on current date/time
  const generateDefaultFilename = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hour = String(now.getHours()).padStart(2, '0');
    const minute = String(now.getMinutes()).padStart(2, '0');
    return `eggbot_log_${year}${month}${day}_${hour}${minute}`;
  };

  // Initialize with default filename
  useEffect(() => {
    if (!filename) {
      setFilename(generateDefaultFilename());
    }
  }, [filename]);

  // Check logging status on component mount and periodically
  useEffect(() => {
    checkLoggingStatus();
    const interval = setInterval(checkLoggingStatus, 2000); // Check every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const checkLoggingStatus = async () => {
    try {
      const response = await fetch('/api/pi/csv-logging/status');
      if (response.ok) {
        const status = await response.json();
        setLogStatus(status);
        setIsLogging(status.enabled);
      }
    } catch (error) {
      console.error('Failed to check logging status:', error);
    }
  };

  const startLogging = async () => {
    if (!filename.trim()) {
      setError('Please enter a filename');
      return;
    }

    setIsStarting(true);
    setError('');

    try {
      const response = await fetch('/api/pi/csv-logging/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: filename.trim(),
          interval_seconds: interval
        })
      });

      if (response.ok) {
        const result = await response.json();
        setIsLogging(true);
        setLogStatus(result.status);
        console.log('CSV logging started:', result);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to start logging');
      }
    } catch (error) {
      console.error('Error starting CSV logging:', error);
      setError('Network error starting logging');
    } finally {
      setIsStarting(false);
    }
  };

  const stopLogging = async () => {
    setIsStopping(true);
    setError('');

    try {
      const response = await fetch('/api/pi/csv-logging/stop', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        setIsLogging(false);
        setLogStatus(null);
        console.log('CSV logging stopped:', result);
        // Generate new default filename for next session
        setFilename(generateDefaultFilename());
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to stop logging');
      }
    } catch (error) {
      console.error('Error stopping CSV logging:', error);
      setError('Network error stopping logging');
    } finally {
      setIsStopping(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      background: "#1a1a1a",
      padding: 16,
      borderRadius: 8,
      marginBottom: 20
    }}>
      <h3 style={{ margin: "0 0 12px 0" }}>CSV Data Logging</h3>

      {error && (
        <div style={{
          background: "#ff1a1a",
          color: "white",
          padding: 8,
          borderRadius: 4,
          marginBottom: 12,
          fontSize: 12
        }}>
          {error}
        </div>
      )}

      {isLogging && logStatus && (
        <div style={{
          background: "#0d4f3c",
          color: "#4ecdc4",
          padding: 8,
          borderRadius: 4,
          marginBottom: 12,
          fontSize: 12
        }}>
          <div>📁 <strong>{logStatus.file_path}</strong></div>
          <div>⏱️ {formatDuration(logStatus.duration_seconds)} | 🔄 Every {logStatus.interval_seconds}s</div>
        </div>
      )}

      <div style={{ fontSize: 14, lineHeight: 1.6 }}>
        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
            Log Filename:
          </label>
          <input
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            disabled={isLogging}
            placeholder="Enter filename (without .csv)"
            style={{
              width: '100%',
              padding: 8,
              borderRadius: 4,
              border: '1px solid #555',
              background: isLogging ? '#333' : '#222',
              color: '#eaeaea',
              fontSize: 12
            }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
            Log Interval (seconds):
          </label>
          <input
            type="number"
            value={interval}
            onChange={(e) => setInterval(Number(e.target.value))}
            disabled={isLogging}
            min="1"
            max="300"
            style={{
              width: '100%',
              padding: 8,
              borderRadius: 4,
              border: '1px solid #555',
              background: isLogging ? '#333' : '#222',
              color: '#eaeaea',
              fontSize: 12
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {!isLogging ? (
            <button
              onClick={startLogging}
              disabled={isStarting || !filename.trim()}
              style={{
                flex: 1,
                padding: 10,
                borderRadius: 4,
                border: 'none',
                background: isStarting || !filename.trim() ? '#555' : '#4ecdc4',
                color: isStarting || !filename.trim() ? '#999' : '#000',
                fontWeight: 'bold',
                cursor: isStarting || !filename.trim() ? 'not-allowed' : 'pointer'
              }}
            >
              {isStarting ? 'Starting...' : '▶️ Start Logging'}
            </button>
          ) : (
            <button
              onClick={stopLogging}
              disabled={isStopping}
              style={{
                flex: 1,
                padding: 10,
                borderRadius: 4,
                border: 'none',
                background: isStopping ? '#555' : '#ff6b35',
                color: isStopping ? '#999' : '#fff',
                fontWeight: 'bold',
                cursor: isStopping ? 'not-allowed' : 'pointer'
              }}
            >
              {isStopping ? 'Stopping...' : '⏹️ Stop Logging'}
            </button>
          )}
        </div>

        <div style={{
          marginTop: 8,
          fontSize: 11,
          color: '#999',
          lineHeight: 1.4
        }}>
          Logs all temperature data, setpoints, and control state to a CSV file.
          Files are saved in the logs/ directory.
        </div>
      </div>
    </div>
  );
}