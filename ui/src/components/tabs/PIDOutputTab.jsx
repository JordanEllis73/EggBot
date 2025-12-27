import PIDChart from '../../PIDChart';

export default function PIDOutputTab({ telemetry }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: 20 }}>PID Controller Output</h2>

      <div style={{ flex: 1, minHeight: 0 }}>
        <PIDChart points={telemetry} />
      </div>
    </div>
  );
}
