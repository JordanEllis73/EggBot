const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
      throw new Error("HTTP error! status: ${response.status}");
    }

    const result = await res.json();
    console.log('Success:', result);

    return result;
  } catch (error) {
    console.error("Error.", error);
  }
}

export async function setDamper(damper_percent) {
  const res = await fetch(`${API}/damper`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ damper_percent })
  });
  return res.json();
}
