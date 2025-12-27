import { useState, useEffect } from 'react';

/**
 * Custom hook to detect if the device supports touch input
 * Used to increase hit areas and adjust UI for touch interaction
 *
 * @returns {boolean} isTouchDevice - true if device supports touch
 */
export default function useTouchDevice() {
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  useEffect(() => {
    // Check if device supports touch
    const hasTouchSupport =
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0;

    setIsTouchDevice(hasTouchSupport);
  }, []);

  return isTouchDevice;
}
