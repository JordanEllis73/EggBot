import { useEffect, useMemo, useState } from "react";
import { 
  getStatus, 
  getTelemetry, 
  setDamper, 
  setSetpoint, 
  setMeatSetpoint,
  setPIDGains, 
  getPIDPresets, 
  loadPIDPreset, 
  savePIDPreset,
  getMeaterStatus 
} from "./api";
import { useDebounce } from "./hooks/useDebounce";
import { getApiTemperature, getDisplayTemperature } from "./utils/temperature";
import TemperatureChart from "./TemperatureChart";
import StatusDisplay from "./StatusDisplay";
import CookSettings from "./CookSettings";
import TemperatureControls from "./TemperatureControls";
import ManualControls from "./ManualControls";
import PIDControls from "./PIDControls";
import MeaterControls from "./MeaterControls";
import TemperatureToggle from "./TemperatureToggle";


export default function App() {
  const [status, setStatus] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [meaterStatus, setMeaterStatus] = useState(null);
  const [meaterHistory, setMeaterHistory] = useState([]);
  
  // Current values
  const [currentSetpoint, setCurrentSetpoint] = useState(110);
  const [currentMeatSetpoint, setCurrentMeatSetpoint] = useState(100);
  const [currentDamper, setCurrentDamper] = useState(0);
  const [currentPIDGains, setCurrentPIDGains] = useState([1.0, 0.1, 0.05]);
  
  // Add stability tracking for API responses
  const [apiValueStability, setApiValueStability] = useState({
    setpoint: { value: 110, count: 0, lastChange: Date.now() },
    meatSetpoint: { value: 100, count: 0, lastChange: Date.now() },
    damper: { value: 0, count: 0, lastChange: Date.now() }
  });
  
  // Input states with localStorage persistence
  const [setpointInput, setSetpointInput] = useState(() => {
    const saved = localStorage.getItem('eggbot_setpoint_input');
    return saved || '110';
  });
  const [meatSetpointInput, setMeatSetpointInput] = useState(() => {
    const saved = localStorage.getItem('eggbot_meat_setpoint_input');
    return saved || '100';
  });
  const [damperInput, setDamperInput] = useState(() => {
    const saved = localStorage.getItem('eggbot_damper_input');
    return saved || '0';
  });
  const [pidGainsInput, setPidGainsInput] = useState(() => {
    const saved = localStorage.getItem('eggbot_pid_gains_input');
    return saved ? JSON.parse(saved) : ['1.0', '0.1', '0.05'];
  });
  const [meatType, setMeatType] = useState('');
  const [meatWeight, setMeatWeight] = useState('');
  
  // Temperature unit preference
  const [temperatureUnit, setTemperatureUnit] = useState(() => {
    const saved = localStorage.getItem('eggbot_temperature_unit');
    return saved || 'C';
  });
  
  // Editing states
  const [isEditingSetpoint, setIsEditingSetpoint] = useState(false);
  const [isEditingMeatSetpoint, setIsEditingMeatSetpoint] = useState(false);
  const [isEditingDamper, setIsEditingDamper] = useState(false);
  const [isEditingPID, setIsEditingPID] = useState(false);
  
  // Submitting states
  const [isSubmittingSetpoint, setIsSubmittingSetpoint] = useState(false);
  const [isSubmittingMeatSetpoint, setIsSubmittingMeatSetpoint] = useState(false);
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
  
  // Debounce API status updates to reduce UI flicker
  const debouncedStatus = useDebounce(last, 500);

  useEffect(() => {
    let t1, t2;
    let isMemoryConstrained = false;
    
    // Check if we're in a memory-constrained environment (like Pi)
    const checkMemory = () => {
      try {
        if (navigator.deviceMemory && navigator.deviceMemory <= 2) {
          isMemoryConstrained = true;
          console.log('Detected memory-constrained environment, adjusting polling');
        }
      } catch (e) {
        // Fallback for older browsers
      }
    };
    
    checkMemory();
    
    const pollStatus = async () => {
      try {
        const statusData = await getStatus();
        console.log(`[${new Date().toISOString()}] API STATUS RESPONSE:`, {
          setpoint_c: statusData.setpoint_c,
          meat_setpoint_c: statusData.meat_setpoint_c,
          damper_percent: statusData.damper_percent,
          timestamp: statusData.timestamp
        });
        setStatus(statusData);
      } catch (error) {
        console.error('Failed to get status:', error);
        // On Pi, API errors might indicate memory pressure
        if (isMemoryConstrained) {
          console.log('Slowing down polling due to API error in memory-constrained environment');
        }
      }
    };
    
    const pollTelemetry = async () => {
      try {
        const telemetryData = await getTelemetry();
        setTelemetry(telemetryData.points || []);
      } catch (error) {
        console.error('Failed to get telemetry:', error);
      }
    };

    const pollMeaterStatus = async () => {
      try {
        const meaterData = await getMeaterStatus();
        setMeaterStatus(meaterData);
        
        // Store Meater data in history if connected and has valid data
        if (meaterData?.is_connected && meaterData?.data) {
          const timestamp = Date.now();
          const historyPoint = {
            timestamp,
            probe_temp_c: meaterData.data.probe_temp_c,
            ambient_temp_c: meaterData.data.ambient_temp_c,
            probe_temp_f: meaterData.data.probe_temp_f,
            ambient_temp_f: meaterData.data.ambient_temp_f,
            battery_percent: meaterData.data.battery_percent
          };
          
          setMeaterHistory(prev => {
            const newHistory = [...prev, historyPoint];
            // Keep only last 1000 points (similar to telemetry management)
            return newHistory.length > 1000 ? newHistory.slice(-1000) : newHistory;
          });
        }
      } catch (error) {
        console.error('Failed to get Meater status:', error);
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
    pollMeaterStatus();
    loadPresets();
    
    // Adjust polling intervals based on environment
    const statusInterval = isMemoryConstrained ? 2000 : 1000; // 2s on Pi vs 1s on dev
    const telemetryInterval = isMemoryConstrained ? 5000 : 2000; // 5s on Pi vs 2s on dev
    const meaterInterval = isMemoryConstrained ? 3000 : 2000; // 3s on Pi vs 2s on dev
    
    t1 = setInterval(pollStatus, statusInterval);
    t2 = setInterval(pollTelemetry, telemetryInterval);
    const t3 = setInterval(pollMeaterStatus, meaterInterval);
    
    return () => { 
      clearInterval(t1); 
      clearInterval(t2); 
      clearInterval(t3);
    };
  }, []);

  // Update input values when not editing and only if current values differ significantly
  useEffect(() => {
    const timestamp = new Date().toISOString();
    
    if (debouncedStatus?.setpoint_c && !isEditingSetpoint && !isSubmittingSetpoint) {
      const apiValue = debouncedStatus.setpoint_c;
      const displayValue = getDisplayTemperature(apiValue, temperatureUnit);
      const newValue = Math.round(displayValue).toString();
      const now = Date.now();
      
      // Check if this API value is stable (appears consistently for at least 3 calls or 2 seconds)
      setApiValueStability(prev => {
        const current = prev.setpoint;
        const isNewValue = Math.abs(current.value - apiValue) > 0.5;
        
        if (isNewValue) {
          // New value - reset stability counter
          return {
            ...prev,
            setpoint: { value: apiValue, count: 1, lastChange: now }
          };
        } else {
          // Same value - increment stability
          return {
            ...prev,
            setpoint: { ...current, count: current.count + 1 }
          };
        }
      });
      
      // Only update UI if value is stable (count >= 3) or has been stable for 2+ seconds
      const stability = apiValueStability.setpoint;
      const isStable = stability.count >= 3 || (now - stability.lastChange) > 2000;
      const shouldUpdate = setpointInput !== newValue && Math.abs(currentSetpoint - apiValue) > 0.5 && isStable;
      
      console.log(`[${timestamp}] SETPOINT CHECK:`, {
        apiValue,
        currentInput: setpointInput,
        newValue,
        currentSetpoint,
        stability,
        isStable,
        shouldUpdate,
        isEditing: isEditingSetpoint,
        isSubmitting: isSubmittingSetpoint
      });
      
      if (shouldUpdate) {
        console.log(`[${timestamp}] SETPOINT UPDATE (STABLE): ${setpointInput} -> ${newValue}`);
        setSetpointInput(newValue);
        localStorage.setItem('eggbot_setpoint_input', newValue);
        setCurrentSetpoint(apiValue);
      }
    }
    
    if (typeof debouncedStatus?.damper_percent === "number" && !isEditingDamper && !isSubmittingDamper) {
      const newValue = debouncedStatus.damper_percent.toString();
      const shouldUpdate = damperInput !== newValue && Math.abs(currentDamper - debouncedStatus.damper_percent) > 0.5;
      
      console.log(`[${timestamp}] DAMPER CHECK:`, {
        apiValue: debouncedStatus.damper_percent,
        currentInput: damperInput,
        newValue,
        currentDamper,
        shouldUpdate
      });
      
      if (shouldUpdate) {
        console.log(`[${timestamp}] DAMPER UPDATE: ${damperInput} -> ${newValue}`);
        setDamperInput(newValue);
        localStorage.setItem('eggbot_damper_input', newValue);
        setCurrentDamper(debouncedStatus.damper_percent);
      }
    }
    
    if (debouncedStatus?.meat_setpoint_c && !isEditingMeatSetpoint && !isSubmittingMeatSetpoint) {
      const apiValue = debouncedStatus.meat_setpoint_c;
      const displayValue = getDisplayTemperature(apiValue, temperatureUnit);
      const newValue = Math.round(displayValue).toString();
      const now = Date.now();
      
      // Check stability for meat setpoint
      setApiValueStability(prev => {
        const current = prev.meatSetpoint;
        const isNewValue = Math.abs(current.value - apiValue) > 0.5;
        
        if (isNewValue) {
          return {
            ...prev,
            meatSetpoint: { value: apiValue, count: 1, lastChange: now }
          };
        } else {
          return {
            ...prev,
            meatSetpoint: { ...current, count: current.count + 1 }
          };
        }
      });
      
      const stability = apiValueStability.meatSetpoint;
      const isStable = stability.count >= 3 || (now - stability.lastChange) > 2000;
      const shouldUpdate = meatSetpointInput !== newValue && Math.abs(currentMeatSetpoint - apiValue) > 0.5 && isStable;
      
      console.log(`[${timestamp}] MEAT SETPOINT CHECK:`, {
        apiValue,
        currentInput: meatSetpointInput,
        newValue,
        currentMeatSetpoint,
        stability,
        isStable,
        shouldUpdate
      });
      
      if (shouldUpdate) {
        console.log(`[${timestamp}] MEAT SETPOINT UPDATE (STABLE): ${meatSetpointInput} -> ${newValue}`);
        setMeatSetpointInput(newValue);
        localStorage.setItem('eggbot_meat_setpoint_input', newValue);
        setCurrentMeatSetpoint(apiValue);
      }
    }
  }, [debouncedStatus, isEditingSetpoint, isEditingDamper, isEditingPID, isEditingMeatSetpoint, isSubmittingSetpoint, isSubmittingDamper, isSubmittingPID, isSubmittingMeatSetpoint, setpointInput, damperInput, pidGainsInput, meatSetpointInput, currentSetpoint, currentDamper, currentMeatSetpoint, apiValueStability, temperatureUnit]);

  const onSetpointSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingSetpoint(true);
    
    try {
      const displayValue = Number(setpointInput);
      if (isNaN(displayValue)) {
        alert('Please enter a valid number for setpoint');
        return;
      }
      
      // Convert to Celsius for API
      const apiValue = getApiTemperature(displayValue, temperatureUnit);
      await setSetpoint(apiValue);
      setCurrentSetpoint(apiValue);
      setIsEditingSetpoint(false);
    } catch (error) {
      console.error('Failed to set setpoint:', error);
      alert('Failed to set setpoint. Please try again.');
    } finally {
      setIsSubmittingSetpoint(false);
    }
  };

  const onMeatSetpointSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingMeatSetpoint(true);
    
    try {
      const displayValue = Number(meatSetpointInput);
      if (isNaN(displayValue) || displayValue <= 0) {
        alert('Please enter a valid number for meat setpoint');
        return;
      }
      
      // Convert to Celsius for API
      const apiValue = getApiTemperature(displayValue, temperatureUnit);
      await setMeatSetpoint(apiValue);
      setCurrentMeatSetpoint(apiValue);
      setIsEditingMeatSetpoint(false);
    } catch (error) {
      console.error('Failed to set meat setpoint:', error);
      alert('Failed to set meat setpoint. Please try again.');
    } finally {
      setIsSubmittingMeatSetpoint(false);
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
      await setPIDGains(gains);
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
      const presets = await getPIDPresets();
      setPidPresets(presets);
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

  // Cancel handlers
  const handleSetpointCancel = () => {
    const displayValue = getDisplayTemperature(currentSetpoint, temperatureUnit);
    setSetpointInput(Math.round(displayValue).toString());
    setIsEditingSetpoint(false);
  };

  const handleMeatSetpointCancel = () => {
    const displayValue = getDisplayTemperature(currentMeatSetpoint, temperatureUnit);
    setMeatSetpointInput(Math.round(displayValue).toString());
    setIsEditingMeatSetpoint(false);
  };

  const handleDamperCancel = () => {
    setDamperInput(currentDamper.toString());
    setIsEditingDamper(false);
  };

  const handlePIDCancel = () => {
    setPidGainsInput(currentPIDGains.map(g => g.toString()));
    setIsEditingPID(false);
  };

  const handleUnitChange = (newUnit) => {
    // Convert current input values from old unit to new unit
    if (temperatureUnit !== newUnit) {
      const convertInputValue = (inputValue, fromUnit, toUnit) => {
        if (!inputValue || inputValue === '') return inputValue;
        const numValue = Number(inputValue);
        if (isNaN(numValue)) return inputValue;
        
        const celsiusValue = getApiTemperature(numValue, fromUnit);
        const newValue = getDisplayTemperature(celsiusValue, toUnit);
        return Math.round(newValue).toString();
      };
      
      // Convert setpoint inputs if not currently being edited
      if (!isEditingSetpoint) {
        const convertedSetpoint = convertInputValue(setpointInput, temperatureUnit, newUnit);
        setSetpointInput(convertedSetpoint);
        localStorage.setItem('eggbot_setpoint_input', convertedSetpoint);
      }
      
      if (!isEditingMeatSetpoint) {
        const convertedMeatSetpoint = convertInputValue(meatSetpointInput, temperatureUnit, newUnit);
        setMeatSetpointInput(convertedMeatSetpoint);
        localStorage.setItem('eggbot_meat_setpoint_input', convertedMeatSetpoint);
      }
    }
    
    setTemperatureUnit(newUnit);
    localStorage.setItem('eggbot_temperature_unit', newUnit);
  };

  return (
    <div style={{ 
      fontFamily: "Inter, system-ui, sans-serif", 
      color: "#eaeaea", 
      background: "#0a0a0a", 
      minHeight: "100vh",
      display: "flex"
    }}>
      {/* Controls Sidebar */}
      <div style={{ 
        width: 320,
        background: "#111", 
        padding: 20,
        borderRight: "1px solid #333",
        overflowY: "auto"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: "24px" }}>BGE Controller</h1>
          <TemperatureToggle 
            unit={temperatureUnit} 
            onUnitChange={handleUnitChange} 
          />
        </div>
        
        <StatusDisplay status={last} />
        
        <CookSettings 
          meatType={meatType}
          setMeatType={setMeatType}
          meatWeight={meatWeight}
          setMeatWeight={setMeatWeight}
        />
        
        <TemperatureControls 
          setpointInput={setpointInput}
          setSetpointInput={setSetpointInput}
          meatSetpointInput={meatSetpointInput}
          setMeatSetpointInput={setMeatSetpointInput}
          isEditingSetpoint={isEditingSetpoint}
          setIsEditingSetpoint={setIsEditingSetpoint}
          isEditingMeatSetpoint={isEditingMeatSetpoint}
          setIsEditingMeatSetpoint={setIsEditingMeatSetpoint}
          isSubmittingSetpoint={isSubmittingSetpoint}
          isSubmittingMeatSetpoint={isSubmittingMeatSetpoint}
          onSetpointSubmit={onSetpointSubmit}
          onMeatSetpointSubmit={onMeatSetpointSubmit}
          onSetpointCancel={handleSetpointCancel}
          onMeatSetpointCancel={handleMeatSetpointCancel}
          temperatureUnit={temperatureUnit}
        />
        
        <ManualControls 
          damperInput={damperInput}
          setDamperInput={setDamperInput}
          isEditingDamper={isEditingDamper}
          setIsEditingDamper={setIsEditingDamper}
          isSubmittingDamper={isSubmittingDamper}
          onDamperSubmit={onDamperSubmit}
          onDamperCancel={handleDamperCancel}
        />
        
        <PIDControls 
          pidGainsInput={pidGainsInput}
          setPidGainsInput={setPidGainsInput}
          isEditingPID={isEditingPID}
          setIsEditingPID={setIsEditingPID}
          isSubmittingPID={isSubmittingPID}
          onPIDSubmit={onPIDSubmit}
          onPIDCancel={handlePIDCancel}
          pidPresets={pidPresets}
          selectedPreset={selectedPreset}
          setSelectedPreset={setSelectedPreset}
          isLoadingPreset={isLoadingPreset}
          handleLoadPreset={handleLoadPreset}
          showSaveDialog={showSaveDialog}
          setShowSaveDialog={setShowSaveDialog}
          savePresetName={savePresetName}
          setSavePresetName={setSavePresetName}
          isSavingPreset={isSavingPreset}
          handleSavePreset={handleSavePreset}
        />
        
        <MeaterControls temperatureUnit={temperatureUnit} />
      </div>
      
      {/* Main Chart Area */}
      <div style={{ 
        flex: 1, 
        padding: 20,
        display: "flex",
        flexDirection: "column"
      }}>
        <h2 style={{ margin: "0 0 20px 0", fontSize: "20px" }}>Temperature History</h2>
        <div style={{ flex: 1, minHeight: 0 }}>
          <TemperatureChart 
            points={telemetry} 
            status={last}
            meaterStatus={meaterStatus}
            meaterHistory={meaterHistory}
            temperatureUnit={temperatureUnit}
            width={Math.min(window.innerWidth - 380, 1200)} 
            height={Math.min(window.innerHeight - 120, 600)} 
          />
        </div>
      </div>
    </div>
  );
}
