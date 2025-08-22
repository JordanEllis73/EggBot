import { useState, useEffect } from 'react';
import { getMeaterStatus, connectMeater, disconnectMeater, scanForMeaterDevices, scanAndConnectMeater } from './api';
import { formatTemperature } from './utils/temperature';

export default function MeaterControls({ temperatureUnit = 'C' }) {
  const [status, setStatus] = useState(null);
  const [address, setAddress] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [availableDevices, setAvailableDevices] = useState([]);
  const [showDeviceList, setShowDeviceList] = useState(false);

  // Poll Meater status
  useEffect(() => {
    let interval;
    
    const pollStatus = async () => {
      try {
        const meaterStatus = await getMeaterStatus();
        // Only update status if we're not in the middle of connection operations
        if (!isConnecting && !isDisconnecting && !isScanning) {
          setStatus(meaterStatus);
        }
      } catch (error) {
        console.error('Failed to get Meater status:', error);
      }
    };
    
    pollStatus();
    interval = setInterval(pollStatus, 2000); // Poll every 2 seconds
    
    return () => clearInterval(interval);
  }, [isConnecting, isDisconnecting, isScanning]);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (!address.trim()) {
      alert('Please enter a Bluetooth address');
      return;
    }
    
    setIsConnecting(true);
    try {
      await connectMeater(address.trim());
      setAddress(''); // Clear input on successful connection start
    } catch (error) {
      console.error('Failed to connect to Meater:', error);
      alert('Failed to connect to Meater. Please check the address and try again.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setIsDisconnecting(true);
    try {
      await disconnectMeater();
    } catch (error) {
      console.error('Failed to disconnect Meater:', error);
      alert('Failed to disconnect Meater.');
    } finally {
      setIsDisconnecting(false);
    }
  };

  const handleScan = async () => {
    setIsScanning(true);
    try {
      const result = await scanForMeaterDevices();
      setAvailableDevices(result.devices || []);
      setShowDeviceList(true);
      
      if (result.devices && result.devices.length === 0) {
        alert('No Meater devices found. Make sure your device is nearby and discoverable.');
      }
    } catch (error) {
      console.error('Failed to scan for devices:', error);
      alert('Failed to scan for devices. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleScanAndConnect = async () => {
    try {
      await scanAndConnectMeater();
    } catch (error) {
      console.error('Failed to start scan and connect:', error);
      alert('Failed to start scan and connect. Please try again.');
    }
  };

  const handleConnectToDevice = async (deviceAddress) => {
    setAddress(deviceAddress);
    setShowDeviceList(false);
    await handleConnect({ preventDefault: () => {} });
  };

  const getTemperatureValue = (data, tempType) => {
    if (!data) return null;
    const fieldName = `${tempType}_temp_${temperatureUnit.toLowerCase()}`;
    return data[fieldName];
  };

  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Meater Probe</h3>
      
      {/* Connection Status */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 12, color: "#aaa", marginBottom: 4 }}>Status</div>
        <div style={{ fontSize: 14 }}>
          {status?.is_scanning && <span style={{ color: '#ff9500' }}>Scanning...</span>}
          {status?.is_connecting && <span style={{ color: '#ff9500' }}>Connecting...</span>}
          {status?.is_connected && <span style={{ color: '#00ff00' }}>Connected</span>}
          {!status?.is_connected && !status?.is_connecting && !status?.is_scanning && <span style={{ color: '#666' }}>Disconnected</span>}
        </div>
        {status?.address && (
          <div style={{ fontSize: 12, color: "#aaa", marginTop: 4 }}>
            Address: {status.address}
          </div>
        )}
      </div>

      {/* Auto-Connect Button */}
      {!status?.is_connected && !status?.is_connecting && !status?.is_scanning && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={handleScanAndConnect}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: 4,
              border: '1px solid #00aa00',
              background: '#00aa00',
              color: 'white',
              fontSize: 14,
              cursor: 'pointer',
              marginBottom: 8
            }}
          >
            Auto-Find & Connect
          </button>
          <div style={{ fontSize: 11, color: "#666", textAlign: 'center' }}>
            Automatically finds and connects to nearby Meater devices
          </div>
        </div>
      )}

      {/* Manual Connection Controls */}
      {!status?.is_connected && !status?.is_connecting && !status?.is_scanning && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#aaa", marginBottom: 8, textAlign: 'center' }}>
            — or connect manually —
          </div>
          
          {/* Scan Button */}
          <button
            onClick={handleScan}
            disabled={isScanning}
            style={{
              width: '100%',
              padding: '8px 16px',
              borderRadius: 4,
              border: '1px solid #666',
              background: '#333',
              color: 'white',
              fontSize: 14,
              cursor: isScanning ? 'not-allowed' : 'pointer',
              opacity: isScanning ? 0.6 : 1,
              marginBottom: 8
            }}
          >
            {isScanning ? 'Scanning...' : 'Scan for Devices'}
          </button>
          
          {/* Device List */}
          {showDeviceList && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: "#aaa", marginBottom: 4 }}>
                Found Devices ({availableDevices.length})
              </div>
              {availableDevices.length > 0 ? (
                <div style={{ maxHeight: 100, overflowY: 'auto' }}>
                  {availableDevices.map((device, index) => (
                    <button
                      key={index}
                      onClick={() => handleConnectToDevice(device)}
                      style={{
                        width: '100%',
                        padding: '6px 8px',
                        borderRadius: 4,
                        border: '1px solid #555',
                        background: '#2a2a2a',
                        color: '#eaeaea',
                        fontSize: 12,
                        cursor: 'pointer',
                        marginBottom: 2,
                        textAlign: 'left'
                      }}
                    >
                      {device}
                    </button>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "#666", fontStyle: 'italic' }}>
                  No devices found
                </div>
              )}
            </div>
          )}
          
          {/* Manual Address Input */}
          <form onSubmit={handleConnect}>
            <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
              Or enter address manually
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input 
                type="text" 
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="XX:XX:XX:XX:XX:XX"
                style={{ 
                  flex: 1,
                  padding: 8, 
                  borderRadius: 4, 
                  border: '1px solid #333',
                  background: '#222',
                  color: '#eaeaea',
                  fontSize: 14
                }}
              />
              <button
                type="submit"
                disabled={isConnecting}
                style={{
                  padding: '8px 16px',
                  borderRadius: 4,
                  border: '1px solid #0070f3',
                  background: '#0070f3',
                  color: 'white',
                  fontSize: 14,
                  cursor: isConnecting ? 'not-allowed' : 'pointer',
                  opacity: isConnecting ? 0.6 : 1
                }}
              >
                {isConnecting ? 'Connecting...' : 'Connect'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Disconnect Button */}
      {(status?.is_connected || status?.is_connecting) && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={handleDisconnect}
            disabled={isDisconnecting}
            style={{
              padding: '8px 16px',
              borderRadius: 4,
              border: '1px solid #ff4444',
              background: '#ff4444',
              color: 'white',
              fontSize: 14,
              cursor: isDisconnecting ? 'not-allowed' : 'pointer',
              opacity: isDisconnecting ? 0.6 : 1
            }}
          >
            {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
          </button>
        </div>
      )}

      {/* Temperature Readings */}
      {status?.is_connected && status?.data && (
        <div>
          <div style={{ fontSize: 12, color: "#aaa", marginBottom: 8 }}>Readings</div>
          <div style={{ fontSize: 14, lineHeight: 1.6 }}>
            <div>Probe: <strong>{formatTemperature(getTemperatureValue(status.data, 'probe'), temperatureUnit)}</strong></div>
            <div>Ambient: <strong>{formatTemperature(getTemperatureValue(status.data, 'ambient'), temperatureUnit)}</strong></div>
            <div>Battery: <strong>{status.data.battery_percent}%</strong></div>
          </div>
          {status.last_update && (
            <div style={{ fontSize: 11, color: "#666", marginTop: 8 }}>
              Last update: {new Date(status.last_update).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}