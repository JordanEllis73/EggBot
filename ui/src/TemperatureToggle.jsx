import useMediaQuery from './hooks/useMediaQuery';
import useTouchDevice from './hooks/useTouchDevice';

export default function TemperatureToggle({ unit, onUnitChange }) {
  const { isMobile } = useMediaQuery();
  const isTouchDevice = useTouchDevice();

  const toggleUnit = () => {
    const newUnit = unit === 'C' ? 'F' : 'C';
    onUnitChange(newUnit);
  };

  const buttonSize = isTouchDevice ? 44 : 36;

  return (
    <button
      onClick={toggleUnit}
      aria-label="Toggle temperature unit"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isTouchDevice ? '8px 10px' : '4px 8px',
        borderRadius: 16,
        border: '1px solid #555',
        background: '#222',
        color: '#eaeaea',
        fontSize: isMobile ? 11 : 12,
        cursor: 'pointer',
        minWidth: buttonSize,
        minHeight: buttonSize,
        WebkitUserSelect: 'none',
        userSelect: 'none',
        WebkitTapHighlightColor: 'transparent'
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
  );
}