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
