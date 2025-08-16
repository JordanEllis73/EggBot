export default function PIDControls({
  pidGainsInput,
  setPidGainsInput,
  isEditingPID,
  setIsEditingPID,
  isSubmittingPID,
  onPIDSubmit,
  onPIDCancel,
  pidPresets,
  selectedPreset,
  setSelectedPreset,
  isLoadingPreset,
  handleLoadPreset,
  showSaveDialog,
  setShowSaveDialog,
  savePresetName,
  setSavePresetName,
  isSavingPreset,
  handleSavePreset
}) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>PID Controls</h3>
      
      <form onSubmit={onPIDSubmit}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 12 }}>
          {['P', 'I', 'D'].map((label, index) => (
            <div key={label} style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <label style={{ minWidth: 16, fontSize: 12, color: "#aaa" }}>{label}:</label>
              <input 
                type="number" 
                step="0.001"
                value={pidGainsInput[index]}
                onChange={(e) => {
                  setIsEditingPID(true);
                  const newGains = [...pidGainsInput];
                  newGains[index] = e.target.value;
                  setPidGainsInput(newGains);
                }}
                disabled={isSubmittingPID}
                style={{ 
                  flex: 1,
                  padding: 6, 
                  borderRadius: 4, 
                  border: isEditingPID ? '2px solid #5bd' : '1px solid #333',
                  background: '#222',
                  color: '#eaeaea',
                  fontSize: 12
                }}
              />
            </div>
          ))}
        </div>
        
        {isEditingPID && (
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button 
              type="submit" 
              disabled={isSubmittingPID}
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
              {isSubmittingPID ? 'Setting...' : 'Apply'}
            </button>
            <button 
              type="button" 
              onClick={onPIDCancel}
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

      {/* PID Presets */}
      <div style={{ paddingTop: 16, borderTop: '1px solid #333' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '12px', color: '#aaa' }}>Presets</h4>
        
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <select 
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            disabled={isLoadingPreset}
            style={{ 
              flex: 1,
              padding: 6, 
              borderRadius: 4, 
              border: '1px solid #333',
              background: '#222',
              color: '#eaeaea',
              fontSize: 12
            }}
          >
            <option value="">Select preset...</option>
            {pidPresets.map(preset => (
              <option key={preset.name} value={preset.name}>
                {preset.name}
              </option>
            ))}
          </select>
          
          <button 
            onClick={handleLoadPreset}
            disabled={!selectedPreset || isLoadingPreset}
            style={{ 
              padding: '6px 12px', 
              borderRadius: 4, 
              border: 'none',
              background: selectedPreset ? '#5bd' : '#555',
              color: selectedPreset ? '#000' : '#aaa',
              cursor: selectedPreset ? 'pointer' : 'not-allowed',
              fontSize: 12
            }}
          >
            {isLoadingPreset ? 'Load...' : 'Load'}
          </button>
        </div>

        <button 
          onClick={() => setShowSaveDialog(true)}
          style={{ 
            width: '100%',
            padding: '6px 12px', 
            borderRadius: 4, 
            border: '1px solid #666',
            background: 'transparent',
            color: '#eaeaea',
            fontSize: 12
          }}
        >
          Save Current
        </button>

        {showSaveDialog && (
          <div style={{ 
            marginTop: 12, 
            padding: 12, 
            background: '#222', 
            borderRadius: 6,
            border: '1px solid #444'
          }}>
            <input 
              type="text" 
              placeholder="Preset name..."
              value={savePresetName}
              onChange={(e) => setSavePresetName(e.target.value)}
              disabled={isSavingPreset}
              style={{ 
                width: '100%',
                padding: 6, 
                borderRadius: 4, 
                border: '1px solid #333',
                background: '#111',
                color: '#eaeaea',
                fontSize: 12,
                marginBottom: 8
              }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button 
                onClick={handleSavePreset}
                disabled={isSavingPreset || !savePresetName.trim()}
                style={{ 
                  flex: 1,
                  padding: '4px 8px', 
                  borderRadius: 4, 
                  border: 'none',
                  background: savePresetName.trim() ? '#5bd' : '#555',
                  color: savePresetName.trim() ? '#000' : '#aaa',
                  fontSize: 11
                }}
              >
                {isSavingPreset ? 'Saving...' : 'Save'}
              </button>
              <button 
                onClick={() => {
                  setShowSaveDialog(false);
                  setSavePresetName('');
                }}
                style={{ 
                  flex: 1,
                  padding: '4px 8px', 
                  borderRadius: 4, 
                  border: '1px solid #666',
                  background: 'transparent',
                  color: '#eaeaea',
                  fontSize: 11
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
