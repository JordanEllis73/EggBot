export default function ManualControls({
  damperInput,
  setDamperInput,
  isEditingDamper,
  setIsEditingDamper,
  isSubmittingDamper,
  onDamperSubmit,
  onDamperCancel,
  disabled = false
}) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Manual Controls</h3>
      
      {disabled && (
        <div style={{ 
          marginBottom: 12, 
          padding: 8, 
          background: '#2a2a2a', 
          borderRadius: 4,
          fontSize: 11,
          color: '#aaa',
          borderLeft: '3px solid #ff9500'
        }}>
          <strong>Disabled:</strong> Manual controls are disabled in automatic mode. 
          Switch to manual mode to adjust damper directly.
        </div>
      )}
      
      <div>
        <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
          Damper Override
        </label>
        <form onSubmit={onDamperSubmit}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <input 
              type="number" 
              value={damperInput}
              onChange={(e) => {
                if (!disabled) {
                  setIsEditingDamper(true);
                  setDamperInput(e.target.value);
                }
              }}
              disabled={isSubmittingDamper || disabled}
              min="0" 
              max="100"
              style={{ 
                flex: 1,
                padding: 8, 
                borderRadius: 4, 
                border: isEditingDamper ? '2px solid #5bd' : '1px solid #333',
                background: disabled ? '#111' : '#222',
                color: disabled ? '#666' : '#eaeaea',
                fontSize: 14,
                cursor: disabled ? 'not-allowed' : 'default'
              }}
            />
            <span style={{ fontSize: 14 }}>%</span>
          </div>
          
          {isEditingDamper && (
            <div style={{ display: "flex", gap: 8 }}>
              <button 
                type="submit" 
                disabled={isSubmittingDamper}
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
                {isSubmittingDamper ? 'Setting...' : 'Apply'}
              </button>
              <button 
                type="button" 
                onClick={onDamperCancel}
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
