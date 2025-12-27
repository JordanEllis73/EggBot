import { useState } from 'react';
import { calibrateProbe } from '../api';
import { getDisplayTemperature, getApiTemperature, formatTemperature } from '../utils/temperature';
import useMediaQuery from '../hooks/useMediaQuery';
import useTouchDevice from '../hooks/useTouchDevice';

export default function ThermistorCalibration({ status, temperatureUnit }) {
  const { isMobile } = useMediaQuery();
  const isTouchDevice = useTouchDevice();

  const [calibrationInputs, setCalibrationInputs] = useState({
    pit_probe: '',
    meat_probe_1: '',
    meat_probe_2: ''
  });
  const [calibrating, setCalibrating] = useState({
    pit_probe: false,
    meat_probe_1: false,
    meat_probe_2: false
  });

  const probeConfigs = [
    {
      name: 'pit_probe',
      label: 'Pit Probe',
      tempKey: 'pit_temp_c',
      connected: status?.pit_temp_c != null
    },
    {
      name: 'meat_probe_1',
      label: 'Meat Probe 1',
      tempKey: 'meat_temp_1_c',
      connected: (status?.meat_temp_1_c || status?.meat_temp_c) != null
    },
    {
      name: 'meat_probe_2',
      label: 'Meat Probe 2',
      tempKey: 'meat_temp_2_c',
      connected: status?.meat_temp_2_c != null
    }
  ];

  const handleCalibrate = async (probeName) => {
    const inputValue = calibrationInputs[probeName];
    if (!inputValue || inputValue === '') {
      alert('Please enter the actual temperature first');
      return;
    }

    const actualTempDisplay = parseFloat(inputValue);
    if (isNaN(actualTempDisplay)) {
      alert('Please enter a valid temperature');
      return;
    }

    // Convert to Celsius for API
    const actualTempC = getApiTemperature(actualTempDisplay, temperatureUnit);

    setCalibrating(prev => ({ ...prev, [probeName]: true }));

    try {
      await calibrateProbe(probeName, actualTempC);
      alert(`${probeName.replace('_', ' ')} calibrated successfully!`);
      // Clear input after successful calibration
      setCalibrationInputs(prev => ({ ...prev, [probeName]: '' }));
    } catch (error) {
      console.error('Calibration error:', error);
      alert(`Failed to calibrate ${probeName}: ${error.message}`);
    } finally {
      setCalibrating(prev => ({ ...prev, [probeName]: false }));
    }
  };

  const handleInputChange = (probeName, value) => {
    setCalibrationInputs(prev => ({ ...prev, [probeName]: value }));
  };

  return (
    <div style={{
      background: '#1a1a1a',
      padding: 16,
      borderRadius: 8,
      marginBottom: 20
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16 }}>Thermistor Calibration</h3>
      <p style={{ fontSize: 13, color: '#999', margin: '0 0 16px 0' }}>
        Calibrate probe offsets using a known temperature reference (e.g., ice water at 0°C or boiling water).
      </p>

      {probeConfigs.map(probe => {
        if (!probe.connected) return null;

        const currentTemp = probe.tempKey === 'meat_temp_1_c'
          ? getDisplayTemperature(status?.meat_temp_1_c || status?.meat_temp_c, temperatureUnit)
          : getDisplayTemperature(status?.[probe.tempKey], temperatureUnit);

        return (
          <div
            key={probe.name}
            style={{
              background: '#2a2a2a',
              padding: 12,
              borderRadius: 6,
              marginBottom: 12,
              border: '1px solid #333'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#eee', marginBottom: 4 }}>
                  {probe.label}
                </div>
                <div style={{ fontSize: 13, color: '#aaa' }}>
                  Current reading: <strong style={{ color: '#ff6b35' }}>
                    {currentTemp !== null ? formatTemperature(currentTemp, temperatureUnit) : '—'}
                  </strong>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, color: '#999', display: 'block', marginBottom: 4 }}>
                  Actual Temperature (°{temperatureUnit})
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={calibrationInputs[probe.name]}
                  onChange={(e) => handleInputChange(probe.name, e.target.value)}
                  disabled={calibrating[probe.name]}
                  placeholder={`e.g., 0 (ice water)`}
                  style={{
                    width: '100%',
                    padding: isTouchDevice ? 12 : '8px 12px',
                    background: '#111',
                    border: '1px solid #444',
                    borderRadius: 4,
                    color: '#eee',
                    fontSize: isMobile ? 16 : 14,
                    minHeight: isTouchDevice ? 44 : 'auto',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                onClick={() => handleCalibrate(probe.name)}
                disabled={calibrating[probe.name] || !calibrationInputs[probe.name]}
                style={{
                  padding: isTouchDevice ? '12px 16px' : '8px 16px',
                  background: calibrating[probe.name] || !calibrationInputs[probe.name] ? '#444' : '#00aa00',
                  color: calibrating[probe.name] || !calibrationInputs[probe.name] ? '#888' : 'white',
                  border: 'none',
                  borderRadius: 4,
                  cursor: calibrating[probe.name] || !calibrationInputs[probe.name] ? 'not-allowed' : 'pointer',
                  fontSize: isMobile ? 15 : 14,
                  fontWeight: 600,
                  minHeight: 44,
                  whiteSpace: 'nowrap'
                }}
              >
                {calibrating[probe.name] ? 'Calibrating...' : 'Calibrate'}
              </button>
            </div>
          </div>
        );
      })}

      {probeConfigs.every(probe => !probe.connected) && (
        <div style={{
          padding: 12,
          background: '#2a2a2a',
          borderRadius: 6,
          color: '#999',
          fontSize: 13,
          textAlign: 'center'
        }}>
          No thermistor probes connected
        </div>
      )}

      <div style={{
        marginTop: 16,
        padding: 10,
        background: '#222',
        borderRadius: 4,
        borderLeft: '3px solid #5bd',
        fontSize: 12,
        color: '#aaa'
      }}>
        <strong style={{ color: '#5bd' }}>Calibration Tips:</strong>
        <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
          <li>Ice water: 0°C / 32°F (most accurate)</li>
          <li>Boiling water: 100°C / 212°F (at sea level)</li>
          <li>Wait 2-3 minutes for probe to stabilize before calibrating</li>
          <li>Calibration is saved and persists across reboots</li>
        </ul>
      </div>
    </div>
  );
}
