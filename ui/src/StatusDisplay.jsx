import { getDisplayTemperature, formatTemperature } from "./utils/temperature";
import useMediaQuery from "./hooks/useMediaQuery";

export default function StatusDisplay({ status, meaterStatus, temperatureUnit, controlMode }) {
  const { isMobile } = useMediaQuery();

  const pitTemp = getDisplayTemperature(status?.pit_temp_c, temperatureUnit);
  const meatTemp1 = getDisplayTemperature(status?.meat_temp_1_c || status?.meat_temp_c, temperatureUnit);
  const meatTemp2 = getDisplayTemperature(status?.meat_temp_2_c, temperatureUnit);
  const meaterTemp = meaterStatus?.is_connected && meaterStatus?.data
    ? getDisplayTemperature(meaterStatus.data.probe_temp_c, temperatureUnit)
    : null;

  const ProbeRow = ({ label, temp, color, connected = true }) => (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: isMobile ? '5px 0' : '6px 0',
      borderBottom: '1px solid #2a2a2a'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{
          width: isMobile ? 10 : 8,
          height: isMobile ? 10 : 8,
          borderRadius: '50%',
          background: connected && temp !== null ? color : '#444'
        }} />
        <span style={{ fontSize: isMobile ? 11 : 12, color: '#999' }}>{label}</span>
      </div>
      <span style={{
        fontSize: isMobile ? 13 : 14,
        fontWeight: 600,
        color: connected && temp !== null ? '#eee' : '#555'
      }}>
        {connected && temp !== null ? formatTemperature(temp, temperatureUnit) : '—'}
      </span>
    </div>
  );

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 8px 0', fontSize: 13, color: '#888', textTransform: 'uppercase', letterSpacing: 1 }}>
        Live Readings
      </h3>

      <div style={{ background: '#1a1a1a', borderRadius: 6, padding: '4px 10px' }}>
        <ProbeRow label="Pit" temp={pitTemp} color="#ff6b35" />
        <ProbeRow label="Meat 1" temp={meatTemp1} color="#4ecdc4" />
        {meatTemp2 !== null && (
          <ProbeRow label="Meat 2" temp={meatTemp2} color="#4ecdc4" />
        )}
        {meaterStatus && (
          <ProbeRow
            label="Meater"
            temp={meaterTemp}
            color="#c44ecb"
            connected={meaterStatus.is_connected}
          />
        )}

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: isMobile ? '5px 0' : '6px 0',
          borderBottom: '1px solid #2a2a2a'
        }}>
          <span style={{ fontSize: isMobile ? 11 : 12, color: '#999' }}>Damper</span>
          <span style={{ fontSize: isMobile ? 13 : 14, fontWeight: 600, color: '#eee' }}>
            {status?.damper_percent ?? 0}%
          </span>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: isMobile ? '5px 0' : '6px 0'
        }}>
          <span style={{ fontSize: isMobile ? 11 : 12, color: '#999' }}>Mode</span>
          <span style={{
            fontSize: isMobile ? 11 : 12,
            fontWeight: 600,
            color: controlMode === 'automatic' ? '#00aa00' : '#888',
            display: 'flex',
            alignItems: 'center',
            gap: 4
          }}>
            <span>{controlMode === 'automatic' ? '🤖' : '👤'}</span>
            {controlMode === 'automatic' ? 'Auto' : 'Manual'}
          </span>
        </div>
      </div>

      {status?.setpoint_c && (
        <div style={{ marginTop: 12 }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: 13, color: '#888', textTransform: 'uppercase', letterSpacing: 1 }}>
            Targets
          </h3>
          <div style={{ background: '#1a1a1a', borderRadius: 6, padding: '4px 10px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: isMobile ? '5px 0' : '6px 0',
              borderBottom: status?.meat_setpoint_c ? '1px solid #2a2a2a' : 'none'
            }}>
              <span style={{ fontSize: isMobile ? 11 : 12, color: '#999' }}>Pit Target</span>
              <span style={{ fontSize: isMobile ? 13 : 14, fontWeight: 600, color: '#ff6b35' }}>
                {formatTemperature(getDisplayTemperature(status.setpoint_c, temperatureUnit), temperatureUnit)}
              </span>
            </div>
            {status?.meat_setpoint_c && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: isMobile ? '5px 0' : '6px 0'
              }}>
                <span style={{ fontSize: isMobile ? 11 : 12, color: '#999' }}>Meat Target</span>
                <span style={{ fontSize: isMobile ? 13 : 14, fontWeight: 600, color: '#4ecdc4' }}>
                  {formatTemperature(getDisplayTemperature(status.meat_setpoint_c, temperatureUnit), temperatureUnit)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
