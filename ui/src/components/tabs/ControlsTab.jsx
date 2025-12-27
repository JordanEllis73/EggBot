import ManualControls from '../../ManualControls';
import PIDControls from '../../PIDControls';
import CSVLoggingControls from '../../CSVLoggingControls';

export default function ControlsTab({
  // Manual controls
  damperInput,
  setDamperInput,
  isEditingDamper,
  setIsEditingDamper,
  isSubmittingDamper,
  onDamperSubmit,
  onDamperCancel,
  controlMode,
  // PID controls
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
    <div style={{ maxWidth: 500 }}>
      <h2 style={{ margin: '0 0 20px 0', fontSize: 20 }}>Controls</h2>

      <ManualControls
        damperInput={damperInput}
        setDamperInput={setDamperInput}
        isEditingDamper={isEditingDamper}
        setIsEditingDamper={setIsEditingDamper}
        isSubmittingDamper={isSubmittingDamper}
        onDamperSubmit={onDamperSubmit}
        onDamperCancel={onDamperCancel}
        disabled={controlMode === 'automatic'}
      />

      <PIDControls
        pidGainsInput={pidGainsInput}
        setPidGainsInput={setPidGainsInput}
        isEditingPID={isEditingPID}
        setIsEditingPID={setIsEditingPID}
        isSubmittingPID={isSubmittingPID}
        onPIDSubmit={onPIDSubmit}
        onPIDCancel={onPIDCancel}
        pidPresets={pidPresets}
        selectedPreset={selectedPreset}
        setSelectedPreset={setSelectedPreset}
        isLoadingPreset={isLoadingPreset}
        handleLoadPreset={handleLoadPreset}
        showSaveDialog={showSaveDialog}
        setShowSaveDialog={setShowSaveDialog}
        savePresetName={savePresetName}
        setSavePresetName={setSavePresetName}
        isSavingPreset={isSavingPreset}
        handleSavePreset={handleSavePreset}
      />

      <CSVLoggingControls />
    </div>
  );
}
