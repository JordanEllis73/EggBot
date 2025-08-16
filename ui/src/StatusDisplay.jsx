export default function StatusDisplay({ status }) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 12px 0" }}>Current Status</h3>
      <div style={{ fontSize: 14, lineHeight: 1.6 }}>
        <div>Pit: <strong>{status?.pit_temp_c?.toFixed(1) ?? "—"}°C</strong></div>
        <div>Meat: <strong>{status?.meat_temp_c?.toFixed(1) ?? "—"}°C</strong></div>
        <div>Damper: <strong>{status?.damper_percent ?? 0}%</strong></div>
      </div>
    </div>
  );
}
