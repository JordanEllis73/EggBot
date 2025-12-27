import TemperatureChart from '../../TemperatureChart';
import ControlModeToggle from '../../ControlModeToggle';

export default function DashboardTab({
  telemetry,
  status,
  meaterStatus,
  meaterHistory,
  temperatureUnit,
  controlMode,
  onControlModeChange
}) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: 16
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>Temperature History</h2>
        <ControlModeToggle
          controlMode={controlMode}
          onControlModeChange={onControlModeChange}
          compact
        />
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <TemperatureChart
          points={telemetry}
          status={status}
          meaterStatus={meaterStatus}
          meaterHistory={meaterHistory}
          temperatureUnit={temperatureUnit}
        />
      </div>
    </div>
  );
}
