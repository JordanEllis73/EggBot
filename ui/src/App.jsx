import { useEffect, useMemo, useState } from "react";
import { getStatus, getTelemetry, setDamper, setSetpoint, setPIDGains, getPIDPresets, loadPIDPreset, savePIDPreset } from "./api";

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
  const [currentPIDGains, setCurrentPIDGains] = useState([1.0, 0.1, 0.05]); // Default P, I, D values
  
  // Input states
  const [setpointInput, setSetpointInput] = useState('110');
  const [damperInput, setDamperInput] = useState('0');
  const [pidGainsInput, setPidGainsInput] = useState(['1.0', '0.1', '0.05']);
  
  // Editing states to prevent overwriting user input
  const [isEditingSetpoint, setIsEditingSetpoint] = useState(false);
  const [isEditingDamper, setIsEditingDamper] = useState(false);
  const [isEditingPID, setIsEditingPID] = useState(false);
  
  // Submitting states for better UX
  const [isSubmittingSetpoint, setIsSubmittingSetpoint] = useState(false);
  const [isSubmittingDamper, setIsSubmittingDamper] = useState(false);
  const [isSubmittingPID, setIsSubmittingPID] = useState(false);

  // PID Preset states
  const [pidPresets, setPidPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isLoadingPreset, setIsLoadingPreset] = useState(false);
  const [isSavingPreset, setIsSavingPreset] = useState(false);
  const [savePresetName, setSavePresetName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

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

    const loadPresets = async () => {
      try {
        const presets = await getPIDPresets();
        setPidPresets(presets);
      } catch (error) {
        console.error('Failed to load PID presets:', error);
      }
    };
    
    pollStatus();
    pollTelemetry();
    loadPresets();
    
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

    // Update PID gains if they come from status (optional - depends on your API)
    if (last?.pid_gains && Array.isArray(last.pid_gains)) {
      setCurrentPIDGains(last.pid_gains);
      
      // Only update input if user isn't editing
      if (!isEditingPID) {
        setPidGainsInput(last.pid_gains.map(g => g.toString()));
      }
    }
  }, [last, isEditingSetpoint, isEditingDamper, isEditingPID]);

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

  const onPIDSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingPID(true);
    
    try {
      const values = pidGainsInput.map(Number);
      if (values.some(isNaN) || values.length !== 3) {
        alert('Please enter valid numbers for all three PID gains (P, I, D)');
        return;
      }
      
      await setPIDGains(values);
      setCurrentPIDGains(values);
      setIsEditingPID(false);
    } catch (error) {
      console.error('Failed to set PID gains:', error);
      alert('Failed to set PID gains. Please try again.');
    } finally {
      setIsSubmittingPID(false);
    }
  };

  const handleLoadPreset = async () => {
    if (!selectedPreset) return;
    
    setIsLoadingPreset(true);
    try {
      const gains = await loadPIDPreset(selectedPreset);
      setCurrentPIDGains(gains);
      setPidGainsInput(gains.map(g => g.toString()));
      
      // Apply the loaded gains immediately
      await setPIDGains(gains);
      
      // Clear selection after loading
      setSelectedPreset('');
    } catch (error) {
      console.error('Failed to load PID preset:', error);
      alert('Failed to load PID preset. Please try again.');
    } finally {
      setIsLoadingPreset(false);
    }
  };

  const handleSavePreset = async () => {
    if (!savePresetName.trim()) {
      alert('Please enter a name for the preset');
      return;
    }
    
    setIsSavingPreset(true);
    try {
      await savePIDPreset(savePresetName.trim(), currentPIDGains);
      
      // Refresh the presets list
      const presets = await getPIDPresets();
      setPidPresets(presets);
      
      // Close dialog and clear input
      setShowSaveDialog(false);
      setSavePresetName('');
      
      alert(`Preset "${savePresetName}" saved successfully!`);
    } catch (error) {
      console.error('Failed to save PID preset:', error);
      alert('Failed to save PID preset. Please try again.');
    } finally {
      setIsSavingPreset(false);
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

  const handlePIDChange = (index, value) => {
    setIsEditingPID(true);
    const newGains = [...pidGainsInput];
    newGains[index] = value;
    setPidGainsInput(newGains);
  };

  const handleSetpointCancel = () => {
    setSetpointInput(currentSetpoint.toString());
    setIsEditingSetpoint(false);
  };

  const handleDamperCancel = () => {
    setDamperInput(currentDamper.toString());
    setIsEditingDamper(false);
  };

  const handlePIDCancel = () => {
    setPidGainsInput(currentPIDGains.map(g => g.toString()));
    setIsEditingPID(false);
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
          <p>PID: [{currentPIDGains.map(g => g.toFixed(3)).join(', ')}]</p>
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
        
        {/* PID Gains Control */}
        <div style={{ background: "#141414", padding: 12, borderRadius: 8 }}>
          <h3>PID Gains</h3>
          <form onSubmit={onPIDSubmit}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 8 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <label style={{ minWidth: 20 }}>P:</label>
                <input 
                  type="number" 
                  step="0.001"
                  value={pidGainsInput[0]}
                  onChange={(e) => handlePIDChange(0, e.target.value)}
                  onFocus={() => setIsEditingPID(true)}
                  disabled={isSubmittingPID}
                  style={{ 
                    padding: 4, 
                    borderRadius: 4, 
                    border: isEditingPID ? '2px solid #5bd' : '1px solid #333',
                    background: '#222',
                    color: '#eaeaea',
                    flex: 1
                  }}
                />
              </div>
              
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <label style={{ minWidth: 20 }}>I:</label>
                <input 
                  type="number" 
                  step="0.001"
                  value={pidGainsInput[1]}
                  onChange={(e) => handlePIDChange(1, e.target.value)}
                  onFocus={() => setIsEditingPID(true)}
                  disabled={isSubmittingPID}
                  style={{ 
                    padding: 4, 
                    borderRadius: 4, 
                    border: isEditingPID ? '2px solid #5bd' : '1px solid #333',
                    background: '#222',
                    color: '#eaeaea',
                    flex: 1
                  }}
                />
              </div>
              
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <label style={{ minWidth: 20 }}>D:</label>
                <input 
                  type="number" 
                  step="0.001"
                  value={pidGainsInput[2]}
                  onChange={(e) => handlePIDChange(2, e.target.value)}
                  onFocus={() => setIsEditingPID(true)}
                  disabled={isSubmittingPID}
                  style={{ 
                    padding: 4, 
                    borderRadius: 4, 
                    border: isEditingPID ? '2px solid #5bd' : '1px solid #333',
                    background: '#222',
                    color: '#eaeaea',
                    flex: 1
                  }}
                />
              </div>
            </div>
            
            {isEditingPID && (
              <div style={{ display: "flex", gap: 8 }}>
                <button 
                  type="submit" 
                  disabled={isSubmittingPID}
                  style={{ 
                    padding: '4px 12px', 
                    borderRadius: 4, 
                    border: 'none',
                    background: '#5bd',
                    color: '#000'
                  }}
                >
                  {isSubmittingPID ? 'Setting...' : 'Apply'}
                </button>
                <button 
                  type="button" 
                  onClick={handlePIDCancel}
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

          {/* PID Presets Section */}
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #333' }}>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Presets</h4>
            
            {/* Load Preset */}
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <select 
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
                disabled={isLoadingPreset}
                style={{ 
                  padding: 4, 
                  borderRadius: 4, 
                  border: '1px solid #333',
                  background: '#222',
                  color: '#eaeaea',
                  flex: 1
                }}
              >
                <option value="">Select preset...</option>
                {pidPresets.map(preset => (
                  <option key={preset.name} value={preset.name}>
                    {preset.name}
                  </option>
                ))}
              </select>
              
              <button 
                onClick={handleLoadPreset}
                disabled={!selectedPreset || isLoadingPreset}
                style={{ 
                  padding: '4px 12px', 
                  borderRadius: 4, 
                  border: 'none',
                  background: selectedPreset ? '#5bd' : '#555',
                  color: selectedPreset ? '#000' : '#aaa',
                  cursor: selectedPreset ? 'pointer' : 'not-allowed'
                }}
              >
                {isLoadingPreset ? 'Loading...' : 'Load'}
              </button>
            </div>

            {/* Save Current Gains */}
            <div style={{ display: "flex", gap: 8 }}>
              <button 
                onClick={() => setShowSaveDialog(true)}
                style={{ 
                  padding: '4px 12px', 
                  borderRadius: 4, 
                  border: '1px solid #666',
                  background: 'transparent',
                  color: '#eaeaea',
                  flex: 1
                }}
              >
                Save Current
              </button>
            </div>

            {/* Save Dialog */}
            {showSaveDialog && (
              <div style={{ 
                marginTop: 12, 
                padding: 12, 
                background: '#222', 
                borderRadius: 6,
                border: '1px solid #444'
              }}>
                <div style={{ marginBottom: 8 }}>
                  <input 
                    type="text" 
                    placeholder="Preset name..."
                    value={savePresetName}
                    onChange={(e) => setSavePresetName(e.target.value)}
                    disabled={isSavingPreset}
                    style={{ 
                      width: '100%',
                      padding: 4, 
                      borderRadius: 4, 
                      border: '1px solid #333',
                      background: '#111',
                      color: '#eaeaea'
                    }}
                  />
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button 
                    onClick={handleSavePreset}
                    disabled={isSavingPreset || !savePresetName.trim()}
                    style={{ 
                      padding: '4px 12px', 
                      borderRadius: 4, 
                      border: 'none',
                      background: savePresetName.trim() ? '#5bd' : '#555',
                      color: savePresetName.trim() ? '#000' : '#aaa',
                      flex: 1
                    }}
                  >
                    {isSavingPreset ? 'Saving...' : 'Save'}
                  </button>
                  <button 
                    onClick={() => {
                      setShowSaveDialog(false);
                      setSavePresetName('');
                    }}
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
              </div>
            )}
          </div>
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
