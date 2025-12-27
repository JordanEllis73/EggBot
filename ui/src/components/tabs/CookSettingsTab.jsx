import CookSettings from '../../CookSettings';
import useMediaQuery from '../../hooks/useMediaQuery';

export default function CookSettingsTab({
  meatType,
  setMeatType,
  meatWeight,
  setMeatWeight
}) {
  const { isMobile } = useMediaQuery();

  return (
    <div style={{ maxWidth: isMobile ? '100%' : 500, padding: isMobile ? '0 12px' : 0 }}>
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
