import { getDisplayTemperature, formatTemperature } from "./utils/temperature";

export default function StatusDisplay({ status, temperatureUnit }) {
  console.log('StatusDisplay - temperatureUnit:', temperatureUnit, 'status:', status);
  const pitTemp = getDisplayTemperature(status?.pit_temp_c, temperatureUnit);

  // Support multiple meat probes with legacy compatibility
  const meatTemp1 = getDisplayTemperature(status?.meat_temp_1_c || status?.meat_temp_c, temperatureUnit);
  const meatTemp2 = getDisplayTemperature(status?.meat_temp_2_c, temperatureUnit);

  console.log('StatusDisplay - pitTemp:', pitTemp, 'meatTemp1:', meatTemp1, 'meatTemp2:', meatTemp2);

  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 12px 0" }}>Current Status</h3>
      <div style={{ fontSize: 14, lineHeight: 1.6 }}>
        <div>Pit: <strong>{formatTemperature(pitTemp, temperatureUnit)}</strong></div>
        {meatTemp1 !== null && (
          <div>Meat 1: <strong>{formatTemperature(meatTemp1, temperatureUnit)}</strong></div>
        )}
        {meatTemp2 !== null && (
          <div>Meat 2: <strong>{formatTemperature(meatTemp2, temperatureUnit)}</strong></div>
        )}
        <div>Damper: <strong>{status?.damper_percent ?? 0}%</strong></div>
      </div>
    </div>
  );
}
