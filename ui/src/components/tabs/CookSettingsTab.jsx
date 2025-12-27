import CookSettings from '../../CookSettings';

export default function CookSettingsTab({
  meatType,
  setMeatType,
  meatWeight,
  setMeatWeight
}) {
  return (
    <div style={{ maxWidth: 500 }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: 20 }}>Cook Settings</h2>
      <CookSettings
        meatType={meatType}
        setMeatType={setMeatType}
        meatWeight={meatWeight}
        setMeatWeight={setMeatWeight}
      />
    </div>
  );
}
