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
