import TemperatureControls from '../../TemperatureControls';

export default function TemperatureTargetsTab({
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
  temperatureUnit
}) {
  return (
    <div style={{ maxWidth: 500 }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: 20 }}>Temperature Targets</h2>
      <TemperatureControls
        setpointInput={setpointInput}
        setSetpointInput={setSetpointInput}
        meatSetpointInput={meatSetpointInput}
        setMeatSetpointInput={setMeatSetpointInput}
        isEditingSetpoint={isEditingSetpoint}
        setIsEditingSetpoint={setIsEditingSetpoint}
        isEditingMeatSetpoint={isEditingMeatSetpoint}
        setIsEditingMeatSetpoint={setIsEditingMeatSetpoint}
        isSubmittingSetpoint={isSubmittingSetpoint}
        isSubmittingMeatSetpoint={isSubmittingMeatSetpoint}
        onSetpointSubmit={onSetpointSubmit}
        onMeatSetpointSubmit={onMeatSetpointSubmit}
        onSetpointCancel={onSetpointCancel}
        onMeatSetpointCancel={onMeatSetpointCancel}
        temperatureUnit={temperatureUnit}
      />
    </div>
  );
}
