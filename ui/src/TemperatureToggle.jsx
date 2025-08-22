export default function TemperatureToggle({ unit, onUnitChange }) {
  const toggleUnit = () => {
    const newUnit = unit === 'C' ? 'F' : 'C';
    onUnitChange(newUnit);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: 12, color: '#aaa' }}>Temperature Unit:</span>
      <button
        onClick={toggleUnit}
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '4px 8px',
          borderRadius: 16,
          border: '1px solid #555',
          background: '#222',
          color: '#eaeaea',
          fontSize: 12,
          cursor: 'pointer',
          minWidth: 60,
          justifyContent: 'center'
        }}
        onMouseOver={(e) => e.target.style.background = '#333'}
        onMouseOut={(e) => e.target.style.background = '#222'}
      >
        <span style={{ 
          color: unit === 'C' ? '#5bd' : '#666',
          fontWeight: unit === 'C' ? 'bold' : 'normal'
        }}>
          °C
        </span>
        <span style={{ margin: '0 6px', color: '#666' }}>/</span>
        <span style={{ 
          color: unit === 'F' ? '#5bd' : '#666',
          fontWeight: unit === 'F' ? 'bold' : 'normal'
        }}>
          °F
        </span>
      </button>
    </div>
  );
}