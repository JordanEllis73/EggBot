export default function ManualControls({
  damperInput,
  setDamperInput,
  isEditingDamper,
  setIsEditingDamper,
  isSubmittingDamper,
  onDamperSubmit,
  onDamperCancel
}) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Manual Controls</h3>
      
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
                setIsEditingDamper(true);
                setDamperInput(e.target.value);
              }}
              disabled={isSubmittingDamper}
              min="0" 
              max="100"
              style={{ 
                flex: 1,
                padding: 8, 
                borderRadius: 4, 
                border: isEditingDamper ? '2px solid #5bd' : '1px solid #333',
                background: '#222',
                color: '#eaeaea',
                fontSize: 14
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
