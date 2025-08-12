import { useEffect, useMemo, useState } from "react";
import { getStatus, getTelemetry, setDamper, setSetpoint } from "./api";

function MiniSparkline({ points, width = 600, height = 120 }) {
  if (!points?.length) return <svg width={width} height={height} />;
  
  const temps = points.map(p => p.pit_temp_c);
  const min = Math.min(...temps) - 2;
  const max = Math.max(...temps) + 2;
  const xs = points.map((_, i) => (i / (points.length - 1)) * (width - 10) + 5);
  const ys = temps.map(t => height - ((t - min) / (max - min || 1)) * (height - 10) - 5);
  const d = xs.map((x, i) => `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(" ");
  
  return (
    <svg width={width} height={height} style={{ background: "#111", borderRadius: 6 }}>
      <path d={d} stroke="#5bd" fill="none" strokeWidth="2"/>
    </svg>
  );
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  
  // Separate current values from input values
  const [currentSetpoint, setCurrentSetpoint] = useState(110);
  const [currentDamper, setCurrentDamper] = useState(0);
  
  // Input states
  const [setpointInput, setSetpointInput] = useState('110');
  const [damperInput, setDamperInput] = useState('0');
  
  // Editing states to prevent overwriting user input
  const [isEditingSetpoint, setIsEditingSetpoint] = useState(false);
  const [isEditingDamper, setIsEditingDamper] = useState(false);
  
  // Submitting states for better UX
  const [isSubmittingSetpoint, setIsSubmittingSetpoint] = useState(false);
  const [isSubmittingDamper, setIsSubmittingDamper] = useState(false);

  const last = useMemo(() => status, [status]);

  useEffect(() => {
    let t1, t2;
    
    const pollStatus = async () => {
      try {
        setStatus(await getStatus());
      } catch (error) {
        console.error('Failed to get status:', error);
      }
    };
    
    const pollTelemetry = async () => {
      try {
        setTelemetry((await getTelemetry()).points || []);
      } catch (error) {
        console.error('Failed to get telemetry:', error);
      }
    };
    
    pollStatus();
    pollTelemetry();
    
    t1 = setInterval(pollStatus, 1000);
    t2 = setInterval(pollTelemetry, 2000);
    
    return () => { 
      clearInterval(t1); 
      clearInterval(t2); 
    };
  }, []);

  // Update current values and input values only when not editing
  useEffect(() => {
    if (last?.setpoint_c) {
      const newSetpoint = Math.round(last.setpoint_c);
      setCurrentSetpoint(newSetpoint);
      
      // Only update input if user isn't editing
      if (!isEditingSetpoint) {
        setSetpointInput(newSetpoint.toString());
      }
    }
    
    if (typeof last?.damper_percent === "number") {
      const newDamper = last.damper_percent;
      setCurrentDamper(newDamper);
      
      // Only update input if user isn't editing
      if (!isEditingDamper) {
        setDamperInput(newDamper.toString());
      }
    }
  }, [last, isEditingSetpoint, isEditingDamper]);

  const onSetpointSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingSetpoint(true);
    
    try {
      const value = Number(setpointInput);
      if (isNaN(value)) {
        alert('Please enter a valid number for setpoint');
        return;
      }
      
      await setSetpoint(value);
      setCurrentSetpoint(value);
      setIsEditingSetpoint(false);
    } catch (error) {
      console.error('Failed to set setpoint:', error);
      alert('Failed to set setpoint. Please try again.');
    } finally {
      setIsSubmittingSetpoint(false);
    }
  };

  const onDamperSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingDamper(true);
    
    try {
      const value = Number(damperInput);
      if (isNaN(value)) {
        alert('Please enter a valid number for damper');
        return;
      }
      
      await setDamper(value);
      setCurrentDamper(value);
      setIsEditingDamper(false);
    } catch (error) {
      console.error('Failed to set damper:', error);
      alert('Failed to set damper. Please try again.');
    } finally {
      setIsSubmittingDamper(false);
    }
  };

  const handleSetpointChange = (e) => {
    setIsEditingSetpoint(true);
    setSetpointInput(e.target.value);
  };

  const handleDamperChange = (e) => {
    setIsEditingDamper(true);
    setDamperInput(e.target.value);
  };

  const handleSetpointCancel = () => {
    setSetpointInput(currentSetpoint.toString());
    setIsEditingSetpoint(false);
  };

  const handleDamperCancel = () => {
    setDamperInput(currentDamper.toString());
    setIsEditingDamper(false);
  };

  return (
    <div style={{ 
      fontFamily: "Inter, system-ui, sans-serif", 
      padding: 16, 
      color: "#eaeaea", 
      background: "#0a0a0a", 
      minHeight: "100vh" 
    }}>
      <h1>BGE Controller</h1>
      
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", 
        gap: 16 
      }}>
        {/* Current Status */}
        <div style={{ background: "#141414", padding: 12, borderRadius: 8 }}>
          <h3>Now</h3>
          <p>Pit: {last?.pit_temp_c?.toFixed(1) ?? "—"} °C</p>
          <p>Meat: {last?.meat_temp_c?.toFixed?.(1) ?? "—"} °C</p>
          <p>Setpoint: {last?.setpoint_c?.toFixed(1) ?? "—"} °C</p>
          <p>Damper: {last?.damper_percent ?? 0}%</p>
        </div>
        
        {/* Controls */}
        <div style={{ background: "#141414", padding: 12, borderRadius: 8 }}>
          <h3>Setpoint</h3>
          <form onSubmit={onSetpointSubmit}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
              <input 
                type="number" 
                value={setpointInput}
                onChange={handleSetpointChange}
                onFocus={() => setIsEditingSetpoint(true)}
                disabled={isSubmittingSetpoint}
                min="0" 
                max="400"
                style={{ 
                  padding: 4, 
                  borderRadius: 4, 
                  border: isEditingSetpoint ? '2px solid #5bd' : '1px solid #333',
                  background: '#222',
                  color: '#eaeaea'
                }}
              />
              <span>°C</span>
            </div>
            
            {isEditingSetpoint && (
              <div style={{ display: "flex", gap: 8 }}>
                <button 
                  type="submit" 
                  disabled={isSubmittingSetpoint}
                  style={{ 
                    padding: '4px 12px', 
                    borderRadius: 4, 
                    border: 'none',
                    background: '#5bd',
                    color: '#000'
                  }}
                >
                  {isSubmittingSetpoint ? 'Setting...' : 'Apply'}
                </button>
                <button 
                  type="button" 
                  onClick={handleSetpointCancel}
                  style={{ 
                    padding: '4px 12px', 
                    borderRadius: 4, 
                    border: '1px solid #666',
                    background: 'transparent',
                    color: '#eaeaea'
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
          
          <h3 style={{ marginTop: 20 }}>Damper</h3>
          <form onSubmit={onDamperSubmit}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
              <input 
                type="number" 
                value={damperInput}
                onChange={handleDamperChange}
                onFocus={() => setIsEditingDamper(true)}
                disabled={isSubmittingDamper}
                min="0" 
                max="100"
                style={{ 
                  padding: 4, 
                  borderRadius: 4, 
                  border: isEditingDamper ? '2px solid #5bd' : '1px solid #333',
                  background: '#222',
                  color: '#eaeaea'
                }}
              />
              <span>%</span>
            </div>
            
            {isEditingDamper && (
              <div style={{ display: "flex", gap: 8 }}>
                <button 
                  type="submit" 
                  disabled={isSubmittingDamper}
                  style={{ 
                    padding: '4px 12px', 
                    borderRadius: 4, 
                    border: 'none',
                    background: '#5bd',
                    color: '#000'
                  }}
                >
                  {isSubmittingDamper ? 'Setting...' : 'Apply'}
                </button>
                <button 
                  type="button" 
                  onClick={handleDamperCancel}
                  style={{ 
                    padding: '4px 12px', 
                    borderRadius: 4, 
                    border: '1px solid #666',
                    background: 'transparent',
                    color: '#eaeaea'
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
        </div>
        
        {/* Chart */}
        <div style={{ 
          gridColumn: "1/-1", 
          background: "#141414", 
          padding: 12, 
          borderRadius: 8 
        }}>
          <h3>Pit temperature (last ~30 min)</h3>
          <MiniSparkline points={telemetry} />
        </div>
      </div>
    </div>
  );
}
