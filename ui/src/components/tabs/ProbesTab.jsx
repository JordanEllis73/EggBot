import MeaterControls from '../../MeaterControls';

export default function ProbesTab({ temperatureUnit }) {
  return (
    <div style={{ maxWidth: 500 }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: 20 }}>Probe Management</h2>

      <div style={{
        background: '#1a1a1a',
        padding: 16,
        borderRadius: 8,
        marginBottom: 20
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: 16 }}>Meater Wireless Probe</h3>
        <MeaterControls temperatureUnit={temperatureUnit} />
      </div>
    </div>
  );
}
