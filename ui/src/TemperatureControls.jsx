export default function TemperatureControls({ 
  setpointInput, 
  setSetpointInput,
  meatSetpointInput,
  setMeatSetpointInput,
  isEditingSetpoint,
  setIsEditingSetpoint,
  isEditingMeatSetpoint,
  setIsEditingMeatSetpoint,
  isSubmittingSetpoint,
  isSubmittingMeatSetpoint,
  onSetpointSubmit,
  onMeatSetpointSubmit,
  onSetpointCancel,
  onMeatSetpointCancel,
  temperatureUnit = 'C'
}) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Temperature Targets</h3>
      
      {/* Pit Temperature */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
          Pit Temperature
        </label>
        <form onSubmit={onSetpointSubmit}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input 
              type="number" 
              value={setpointInput}
              onChange={(e) => {
                setIsEditingSetpoint(true);
                setSetpointInput(e.target.value);
                localStorage.setItem('eggbot_setpoint_input', e.target.value);
              }}
              disabled={isSubmittingSetpoint}
              min="0" 
              max={temperatureUnit === 'F' ? "750" : "400"}
              style={{ 
                flex: 1,
                padding: 8, 
                borderRadius: 4, 
                border: isEditingSetpoint ? '2px solid #5bd' : '1px solid #333',
                background: '#222',
                color: '#eaeaea',
                fontSize: 14
              }}
            />
            <span style={{ fontSize: 14 }}>°{temperatureUnit}</span>
          </div>
          
          {isEditingSetpoint && (
            <div style={{ display: "flex", gap: 8 }}>
              <button 
                type="submit" 
                disabled={isSubmittingSetpoint}
                style={{ 
                  flex: 1,
                  padding: '6px 12px', 
                  borderRadius: 4, 
                  border: 'none',
                  background: '#5bd',
                  color: '#000',
                  fontSize: 12
                }}
              >
                {isSubmittingSetpoint ? 'Setting...' : 'Apply'}
              </button>
              <button 
                type="button" 
                onClick={onSetpointCancel}
                style={{ 
                  flex: 1,
                  padding: '6px 12px', 
                  borderRadius: 4, 
                  border: '1px solid #666',
                  background: 'transparent',
                  color: '#eaeaea',
                  fontSize: 12
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Meat Temperature */}
      <div>
        <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
          Meat Target Temperature
        </label>
        <form onSubmit={onMeatSetpointSubmit}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input 
              type="number" 
              value={meatSetpointInput}
              onChange={(e) => {
                setIsEditingMeatSetpoint(true);
                setMeatSetpointInput(e.target.value);
                localStorage.setItem('eggbot_meat_setpoint_input', e.target.value);
              }}
              disabled={isSubmittingMeatSetpoint}
              min="0" 
              max={temperatureUnit === 'F' ? "400" : "200"}
              placeholder="Optional"
              style={{ 
                flex: 1,
                padding: 8, 
                borderRadius: 4, 
                border: isEditingMeatSetpoint ? '2px solid #4ecdc4' : '1px solid #333',
                background: '#222',
                color: '#eaeaea',
                fontSize: 14
              }}
            />
            <span style={{ fontSize: 14 }}>°{temperatureUnit}</span>
          </div>
          
          {isEditingMeatSetpoint && (
            <div style={{ display: "flex", gap: 8 }}>
              <button 
                type="submit" 
                disabled={isSubmittingMeatSetpoint}
                style={{ 
                  flex: 1,
                  padding: '6px 12px', 
                  borderRadius: 4, 
                  border: 'none',
                  background: '#4ecdc4',
                  color: '#000',
                  fontSize: 12
                }}
              >
                {isSubmittingMeatSetpoint ? 'Setting...' : 'Apply'}
              </button>
              <button 
                type="button" 
                onClick={onMeatSetpointCancel}
                style={{ 
                  flex: 1,
                  padding: '6px 12px', 
                  borderRadius: 4, 
                  border: '1px solid #666',
                  background: 'transparent',
                  color: '#eaeaea',
                  fontSize: 12
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
