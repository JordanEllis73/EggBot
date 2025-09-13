// Use relative path since Vite proxy handles the routing
const API = "/api";

export async function getStatus() {
  const res = await fetch(`${API}/status`);
  return res.json();
}

export async function getTelemetry() {
  const res = await fetch(`${API}/telemetry`);
  return res.json();
}

export async function setSetpoint(setpoint_c) {
  try {
    console.log('Sending: ', setpoint_c);
    
    const res = await fetch(`${API}/setpoint`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ setpoint_c })
    });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const result = await res.json();
    console.log('Success:', result);
    return result;
  } catch (error) {
    console.error("Error.", error);
    throw error;
  }
}

export async function setMeatSetpoint(meat_setpoint_c) {
  try {
    console.log('Setting meat setpoint: ', meat_setpoint_c);
    
    const res = await fetch(`${API}/meat_setpoint`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ meat_setpoint_c })
    });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const result = await res.json();
    console.log('Meat setpoint success:', result);
    return result;
  } catch (error) {
    console.error("Meat setpoint error:", error);
    throw error;
  }
}

export async function setDamper(damper_percent) {
  const res = await fetch(`${API}/damper`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ damper_percent })
  });
  if (!res.ok) {
    throw new Error(`HTTP error! status: ${res.status}`);
  }
  return res.json();
}

export async function setPIDGains(pid_gains) {
  try {
    console.log('Sending PID gains: ', pid_gains);
    
    const res = await fetch(`${API}/pid_gains`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pid_gains })
    });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const result = await res.json();
    console.log('PID gains success:', result);
    return result;
  } catch (error) {
    console.error("PID gains error:", error);
    throw error;
  }
}

// Get list of available PID presets
export async function getPIDPresets() {
  const response = await fetch(`${API}/pid-presets/`);
  if (!response.ok) throw new Error('Failed to get PID presets');
  return response.json();
}

// Load a specific PID preset
export async function loadPIDPreset(presetName) {
  const response = await fetch(`${API}/pid-presets/${encodeURIComponent(presetName)}`);
  if (!response.ok) throw new Error('Failed to load PID preset');
  const data = await response.json();
  return data.gains; // Assuming the API returns { gains: [p, i, d] }
}

// Save current PID gains as a new preset
export async function savePIDPreset(presetName, gains) {
  const response = await fetch(`${API}/pid-presets/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      name: presetName, 
      gains: gains 
    })
  });
  if (!response.ok) throw new Error('Failed to save PID preset');
  return response.json();
}

// Meater API functions
export async function getMeaterStatus() {
  const response = await fetch(`${API}/meater/status`);
  if (!response.ok) throw new Error('Failed to get Meater status');
  return response.json();
}

export async function connectMeater(address) {
  const response = await fetch(`${API}/meater/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address })
  });
  if (!response.ok) throw new Error('Failed to connect to Meater');
  return response.json();
}

export async function disconnectMeater() {
  const response = await fetch(`${API}/meater/disconnect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Failed to disconnect Meater');
  return response.json();
}

export async function scanForMeaterDevices() {
  const response = await fetch(`${API}/meater/scan`);
  if (!response.ok) throw new Error('Failed to scan for Meater devices');
  return response.json();
}

export async function scanAndConnectMeater() {
  const response = await fetch(`${API}/meater/scan-and-connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) throw new Error('Failed to start scan and connect');
  return response.json();
}

export async function setControlMode(control_mode) {
  const response = await fetch(`${API}/control_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ control_mode })
  });
  if (!response.ok) throw new Error('Failed to set control mode');
  return response.json();
}

export async function getControlMode() {
  const response = await fetch(`${API}/control_mode`);
  if (!response.ok) throw new Error('Failed to get control mode');
  return response.json();
}

// Pi-native enhanced API functions
export async function getSystemStatus() {
  try {
    const response = await fetch(`${API}/pi/system/status`);
    if (!response.ok) {
      // Fallback to legacy API if pi-native not available
      return await getStatus();
    }
    return response.json();
  } catch (error) {
    // Fallback to legacy API
    console.warn('Pi-native API not available, using legacy API');
    return await getStatus();
  }
}

export async function getAllTemperatures() {
  try {
    const response = await fetch(`${API}/pi/temperatures`);
    if (!response.ok) throw new Error('Failed to get temperatures');
    return response.json();
  } catch (error) {
    // Fallback to legacy status
    const status = await getStatus();
    return {
      pit_temp_c: status.pit_temp_c,
      meat_temp_1_c: status.meat_temp_c, // Legacy compatibility
      meat_temp_2_c: null,
      ambient_temp_c: null,
      connected_probes: status.pit_temp_c !== null ? ['pit_probe'] : [],
      timestamp: status.timestamp
    };
  }
}

export async function getProbeStatus() {
  try {
    const response = await fetch(`${API}/pi/probes/status`);
    if (!response.ok) throw new Error('Failed to get probe status');
    return response.json();
  } catch (error) {
    console.warn('Pi-native probe status not available');
    return {};
  }
}

export async function getEnhancedTelemetry() {
  try {
    const response = await fetch(`${API}/pi/telemetry/enhanced`);
    if (!response.ok) {
      // Fallback to legacy telemetry
      return await getTelemetry();
    }
    return response.json();
  } catch (error) {
    // Fallback to legacy telemetry
    return await getTelemetry();
  }
}

export async function clearTelemetry() {
  try {
    const response = await fetch(`${API}/pi/telemetry/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Failed to clear telemetry');
    return response.json();
  } catch (error) {
    console.warn('Clear telemetry not available');
    throw error;
  }
}

export async function getPIDTuningInfo() {
  try {
    const response = await fetch(`${API}/pi/pid/tuning-info`);
    if (!response.ok) throw new Error('Failed to get PID tuning info');
    return response.json();
  } catch (error) {
    console.warn('PID tuning info not available');
    return null;
  }
}

export async function getPiNativePIDPresets() {
  try {
    const response = await fetch(`${API}/pi/pid/presets`);
    if (!response.ok) throw new Error('Failed to get Pi-native PID presets');
    return response.json();
  } catch (error) {
    // Fallback to legacy presets
    return await getPIDPresets();
  }
}

export async function loadPiNativePIDPreset(presetName) {
  try {
    const response = await fetch(`${API}/pi/pid/preset/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preset_name: presetName })
    });
    if (!response.ok) throw new Error('Failed to load Pi-native PID preset');
    return response.json();
  } catch (error) {
    // Fallback to legacy preset loading
    console.warn('Pi-native preset loading not available, using legacy method');
    return await loadPIDPreset(presetName);
  }
}

export async function calibrateProbe(probeName, actualTemperature) {
  try {
    const response = await fetch(`${API}/pi/probes/calibrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        probe_name: probeName, 
        actual_temperature: actualTemperature 
      })
    });
    if (!response.ok) throw new Error('Failed to calibrate probe');
    return response.json();
  } catch (error) {
    console.warn('Probe calibration not available');
    throw error;
  }
}

export async function getPerformanceStats() {
  try {
    const response = await fetch(`${API}/pi/system/performance`);
    if (!response.ok) throw new Error('Failed to get performance stats');
    return response.json();
  } catch (error) {
    console.warn('Performance stats not available');
    return null;
  }
}

export async function getSafetyStatus() {
  try {
    const response = await fetch(`${API}/pi/safety/status`);
    if (!response.ok) throw new Error('Failed to get safety status');
    return response.json();
  } catch (error) {
    console.warn('Safety status not available');
    return null;
  }
}

export async function resetSafetyShutdown() {
  try {
    const response = await fetch(`${API}/pi/safety/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Failed to reset safety shutdown');
    return response.json();
  } catch (error) {
    console.warn('Safety reset not available');
    throw error;
  }
}

// Utility function to check if Pi-native features are available
export async function checkPiNativeAvailability() {
  try {
    const response = await fetch(`${API}/pi/system/status`);
    return response.ok;
  } catch (error) {
    return false;
  }
}
