import { useState } from 'react';
import { setControlMode } from './api';

export default function ControlModeToggle({ 
  controlMode = 'manual', 
  onControlModeChange,
  disabled = false 
}) {
  const [isChanging, setIsChanging] = useState(false);

  const handleToggle = async () => {
    if (isChanging || disabled) return;
    
    const newMode = controlMode === 'manual' ? 'automatic' : 'manual';
    setIsChanging(true);
    
    try {
      await setControlMode(newMode);
      onControlModeChange(newMode);
    } catch (error) {
      console.error('Failed to change control mode:', error);
      alert('Failed to change control mode. Please try again.');
    } finally {
      setIsChanging(false);
    }
  };

  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Control Mode</h3>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={handleToggle}
          disabled={isChanging || disabled}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 16px',
            borderRadius: 20,
            border: `2px solid ${controlMode === 'automatic' ? '#00aa00' : '#666'}`,
            background: controlMode === 'automatic' ? '#00aa00' : '#333',
            color: controlMode === 'automatic' ? 'white' : '#eaeaea',
            fontSize: 14,
            cursor: (isChanging || disabled) ? 'not-allowed' : 'pointer',
            opacity: (isChanging || disabled) ? 0.6 : 1,
            minWidth: 120,
            justifyContent: 'center',
            fontWeight: 'bold',
            transition: 'all 0.2s ease'
          }}
          onMouseOver={(e) => {
            if (!isChanging && !disabled) {
              e.target.style.opacity = '0.8';
            }
          }}
          onMouseOut={(e) => {
            if (!isChanging && !disabled) {
              e.target.style.opacity = '1';
            }
          }}
        >
          {isChanging ? (
            'Switching...'
          ) : (
            <>
              <span style={{ 
                marginRight: 8,
                fontSize: 16 
              }}>
                {controlMode === 'automatic' ? '🤖' : '👤'}
              </span>
              {controlMode === 'automatic' ? 'Automatic' : 'Manual'}
            </>
          )}
        </button>
        
        <div style={{ fontSize: 12, color: "#aaa", lineHeight: 1.4 }}>
          {controlMode === 'manual' ? (
            <span>
              <strong>Manual Control:</strong><br />
              Set damper position directly
            </span>
          ) : (
            <span>
              <strong>Automatic Control:</strong><br />
              PID controls damper to maintain temperature
            </span>
          )}
        </div>
      </div>
      
      {controlMode === 'automatic' && (
        <div style={{ 
          marginTop: 12, 
          padding: 8, 
          background: '#2a2a2a', 
          borderRadius: 4,
          fontSize: 11,
          color: '#aaa',
          borderLeft: '3px solid #00aa00'
        }}>
          <strong>Note:</strong> In automatic mode, the system uses PID control to adjust the damper 
          based on the temperature setpoint. Manual damper adjustments will be overridden.
        </div>
      )}
    </div>
  );
}