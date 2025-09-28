import { getDisplayTemperature, formatTemperature } from "./utils/temperature";

export default function StatusDisplay({ status, temperatureUnit }) {
  console.log('StatusDisplay - temperatureUnit:', temperatureUnit, 'status:', status);
  const pitTemp = getDisplayTemperature(status?.pit_temp_c, temperatureUnit);
  const meatTemp = getDisplayTemperature(status?.meat_temp_c, temperatureUnit);
  console.log('StatusDisplay - pitTemp:', pitTemp, 'meatTemp:', meatTemp);

  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 12px 0" }}>Current Status</h3>
      <div style={{ fontSize: 14, lineHeight: 1.6 }}>
        <div>Pit: <strong>{formatTemperature(pitTemp, temperatureUnit)}</strong></div>
        <div>Meat: <strong>{formatTemperature(meatTemp, temperatureUnit)}</strong></div>
        <div>Damper: <strong>{status?.damper_percent ?? 0}%</strong></div>
      </div>
    </div>
  );
}
