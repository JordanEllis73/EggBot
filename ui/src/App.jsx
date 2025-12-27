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
  getMeaterStatus,
  setControlMode
} from "./api";
import { useDebounce } from "./hooks/useDebounce";
import useMediaQuery from "./hooks/useMediaQuery";
import useTouchDevice from "./hooks/useTouchDevice";
import { getApiTemperature, getDisplayTemperature } from "./utils/temperature";
import StatusDisplay from "./StatusDisplay";
import TemperatureToggle from "./TemperatureToggle";
import TabContainer from "./components/TabContainer";
import DashboardTab from "./components/tabs/DashboardTab";
import CookSettingsTab from "./components/tabs/CookSettingsTab";
import TemperatureTargetsTab from "./components/tabs/TemperatureTargetsTab";
import ControlsTab from "./components/tabs/ControlsTab";
import PIDOutputTab from "./components/tabs/PIDOutputTab";
import ProbesTab from "./components/tabs/ProbesTab";

export default function App() {
  // Responsive hooks
  const { isMobile, isTablet, isDesktop } = useMediaQuery();
  const isTouchDevice = useTouchDevice();

  const [status, setStatus] = useState(null);
  const [telemetry, setTelemetry] = useState([]);
  const [meaterStatus, setMeaterStatus] = useState(null);
  const [meaterHistory, setMeaterHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [currentSetpoint, setCurrentSetpoint] = useState(110);
  const [currentMeatSetpoint, setCurrentMeatSetpoint] = useState(100);
  const [currentDamper, setCurrentDamper] = useState(0);
  const [currentPIDGains, setCurrentPIDGains] = useState([1.0, 0.1, 0.05]);
  const [controlMode, setControlModeState] = useState('manual');

  const [apiValueStability, setApiValueStability] = useState({
    setpoint: { value: 110, count: 0, lastChange: Date.now() },
    meatSetpoint: { value: 100, count: 0, lastChange: Date.now() },
    damper: { value: 0, count: 0, lastChange: Date.now() }
  });

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

  const [temperatureUnit, setTemperatureUnit] = useState(() => {
    const saved = localStorage.getItem('eggbot_temperature_unit');
    return saved || 'C';
  });

  const [isEditingSetpoint, setIsEditingSetpoint] = useState(false);
  const [isEditingMeatSetpoint, setIsEditingMeatSetpoint] = useState(false);
  const [isEditingDamper, setIsEditingDamper] = useState(false);
  const [isEditingPID, setIsEditingPID] = useState(false);

  const [isSubmittingSetpoint, setIsSubmittingSetpoint] = useState(false);
  const [isSubmittingMeatSetpoint, setIsSubmittingMeatSetpoint] = useState(false);
  const [isSubmittingDamper, setIsSubmittingDamper] = useState(false);
  const [isSubmittingPID, setIsSubmittingPID] = useState(false);

  const [pidPresets, setPidPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isLoadingPreset, setIsLoadingPreset] = useState(false);
  const [isSavingPreset, setIsSavingPreset] = useState(false);
  const [savePresetName, setSavePresetName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  const last = useMemo(() => status, [status]);
  const debouncedStatus = useDebounce(last, 500);

  useEffect(() => {
    let t1, t2;
    let isMemoryConstrained = false;

    const checkMemory = () => {
      try {
        if (navigator.deviceMemory && navigator.deviceMemory <= 2) {
          isMemoryConstrained = true;
        }
      } catch (e) {}
    };

    checkMemory();

    const pollStatus = async () => {
      try {
        const statusData = await getStatus();
        setStatus(statusData);
      } catch (error) {
        console.error('Failed to get status:', error);
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

    const statusInterval = isMemoryConstrained ? 1000 : 250;
    const telemetryInterval = isMemoryConstrained ? 5000 : 2000;
    const meaterInterval = isMemoryConstrained ? 3000 : 1000;

    t1 = setInterval(pollStatus, statusInterval);
    t2 = setInterval(pollTelemetry, telemetryInterval);
    const t3 = setInterval(pollMeaterStatus, meaterInterval);

    return () => {
      clearInterval(t1);
      clearInterval(t2);
      clearInterval(t3);
    };
  }, []);

  useEffect(() => {
    if (debouncedStatus?.setpoint_c && !isEditingSetpoint && !isSubmittingSetpoint) {
      const apiValue = debouncedStatus.setpoint_c;
      const displayValue = getDisplayTemperature(apiValue, temperatureUnit);
      const newValue = Math.round(displayValue).toString();
      const now = Date.now();

      setApiValueStability(prev => {
        const current = prev.setpoint;
        const isNewValue = Math.abs(current.value - apiValue) > 0.5;
        if (isNewValue) {
          return { ...prev, setpoint: { value: apiValue, count: 1, lastChange: now } };
        }
        return { ...prev, setpoint: { ...current, count: current.count + 1 } };
      });

      const stability = apiValueStability.setpoint;
      const isStable = stability.count >= 3 || (now - stability.lastChange) > 2000;
      const shouldUpdate = setpointInput !== newValue && Math.abs(currentSetpoint - apiValue) > 0.5 && isStable;

      if (shouldUpdate) {
        setSetpointInput(newValue);
        localStorage.setItem('eggbot_setpoint_input', newValue);
        setCurrentSetpoint(apiValue);
      }
    }

    if (typeof debouncedStatus?.damper_percent === "number" && !isEditingDamper && !isSubmittingDamper) {
      const newValue = debouncedStatus.damper_percent.toString();
      const shouldUpdate = damperInput !== newValue && Math.abs(currentDamper - debouncedStatus.damper_percent) > 0.5;

      if (shouldUpdate) {
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

      setApiValueStability(prev => {
        const current = prev.meatSetpoint;
        const isNewValue = Math.abs(current.value - apiValue) > 0.5;
        if (isNewValue) {
          return { ...prev, meatSetpoint: { value: apiValue, count: 1, lastChange: now } };
        }
        return { ...prev, meatSetpoint: { ...current, count: current.count + 1 } };
      });

      const stability = apiValueStability.meatSetpoint;
      const isStable = stability.count >= 3 || (now - stability.lastChange) > 2000;
      const shouldUpdate = meatSetpointInput !== newValue && Math.abs(currentMeatSetpoint - apiValue) > 0.5 && isStable;

      if (shouldUpdate) {
        setMeatSetpointInput(newValue);
        localStorage.setItem('eggbot_meat_setpoint_input', newValue);
        setCurrentMeatSetpoint(apiValue);
      }
    }

    if (debouncedStatus?.control_mode && debouncedStatus.control_mode !== controlMode) {
      setControlModeState(debouncedStatus.control_mode);
    }
  }, [debouncedStatus, isEditingSetpoint, isEditingDamper, isEditingPID, isEditingMeatSetpoint, isSubmittingSetpoint, isSubmittingDamper, isSubmittingPID, isSubmittingMeatSetpoint, setpointInput, damperInput, meatSetpointInput, currentSetpoint, currentDamper, currentMeatSetpoint, apiValueStability, temperatureUnit, controlMode]);

  const onSetpointSubmit = async (e) => {
    e.preventDefault();
    setIsSubmittingSetpoint(true);
    try {
      const displayValue = Number(setpointInput);
      if (isNaN(displayValue)) {
        alert('Please enter a valid number for setpoint');
        return;
      }
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
    if (temperatureUnit !== newUnit) {
      const convertInputValue = (inputValue, fromUnit, toUnit) => {
        if (!inputValue || inputValue === '') return inputValue;
        const numValue = Number(inputValue);
        if (isNaN(numValue)) return inputValue;
        const celsiusValue = getApiTemperature(numValue, fromUnit);
        const newValue = getDisplayTemperature(celsiusValue, toUnit);
        return Math.round(newValue).toString();
      };

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

  const handleControlModeChange = async (newMode) => {
    try {
      await setControlMode(newMode);
      setControlModeState(newMode);
    } catch (error) {
      console.error('Failed to set control mode:', error);
      throw error;
    }
  };

  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      content: (
        <DashboardTab
          telemetry={telemetry}
          status={last}
          meaterStatus={meaterStatus}
          meaterHistory={meaterHistory}
          temperatureUnit={temperatureUnit}
          controlMode={controlMode}
          onControlModeChange={handleControlModeChange}
        />
      )
    },
    {
      id: 'cook',
      label: 'Cook',
      content: (
        <CookSettingsTab
          meatType={meatType}
          setMeatType={setMeatType}
          meatWeight={meatWeight}
          setMeatWeight={setMeatWeight}
        />
      )
    },
    {
      id: 'temps',
      label: 'Temps',
      content: (
        <TemperatureTargetsTab
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
      )
    },
    {
      id: 'controls',
      label: 'Controls',
      content: (
        <ControlsTab
          damperInput={damperInput}
          setDamperInput={setDamperInput}
          isEditingDamper={isEditingDamper}
          setIsEditingDamper={setIsEditingDamper}
          isSubmittingDamper={isSubmittingDamper}
          onDamperSubmit={onDamperSubmit}
          onDamperCancel={handleDamperCancel}
          controlMode={controlMode}
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
      )
    },
    {
      id: 'pid',
      label: 'PID Output',
      content: <PIDOutputTab telemetry={telemetry} />
    },
    {
      id: 'probes',
      label: 'Probes',
      content: <ProbesTab temperatureUnit={temperatureUnit} status={last} />
    }
  ];

  // Determine sidebar width based on screen size
  const sidebarWidth = isMobile ? 280 : (isTablet ? 160 : 180);

  // Auto-close sidebar when tab changes on mobile
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  }, [activeTab, isMobile]);

  return (
    <div style={{
      fontFamily: "Inter, system-ui, sans-serif",
      color: "#eaeaea",
      background: "#0a0a0a",
      minHeight: "100vh",
      display: "flex",
      position: "relative",
      overscrollBehavior: "contain"
    }}>
      {/* Hamburger Menu Button (Mobile Only) */}
      {isMobile && (
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle menu"
          style={{
            position: "fixed",
            top: 12,
            left: 12,
            zIndex: 1000,
            width: 44,
            height: 44,
            background: "#222",
            border: "1px solid #444",
            borderRadius: 8,
            color: "#eaeaea",
            fontSize: 20,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            WebkitUserSelect: "none",
            userSelect: "none",
            WebkitTapHighlightColor: "transparent"
          }}
        >
          ☰
        </button>
      )}

      {/* Backdrop (Mobile Only) */}
      {isMobile && sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.5)",
            zIndex: 998
          }}
        />
      )}

      {/* Status Sidebar */}
      <div style={{
        width: sidebarWidth,
        background: "#111",
        padding: 16,
        borderRight: "1px solid #333",
        display: "flex",
        flexDirection: "column",
        position: isMobile ? "fixed" : "relative",
        left: isMobile ? (sidebarOpen ? 0 : -sidebarWidth) : 0,
        top: isMobile ? 0 : "auto",
        bottom: isMobile ? 0 : "auto",
        zIndex: isMobile ? 999 : "auto",
        transition: "left 0.3s ease",
        overflowY: "auto",
        boxSizing: "border-box"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16
        }}>
          <h1 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>BGE</h1>
          <TemperatureToggle
            unit={temperatureUnit}
            onUnitChange={handleUnitChange}
          />
        </div>

        <StatusDisplay
          status={last}
          meaterStatus={meaterStatus}
          temperatureUnit={temperatureUnit}
          controlMode={controlMode}
        />
      </div>

      {/* Main Tab Area */}
      <div style={{
        flex: 1,
        padding: isMobile ? 12 : 20,
        paddingTop: isMobile ? 64 : 20,
        display: "flex",
        flexDirection: "column",
        minWidth: 0
      }}>
        <TabContainer
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={tabs}
        />
      </div>
    </div>
  );
}
