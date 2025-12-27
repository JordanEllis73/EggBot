import { useState, useEffect } from 'react';

/**
 * Custom hook for responsive breakpoints
 *
 * Breakpoints:
 * - Mobile: < 768px
 * - Tablet: 768px - 1023px
 * - Desktop: >= 1024px
 *
 * @returns {Object} { isMobile, isTablet, isDesktop }
 */
export default function useMediaQuery() {
  const [breakpoint, setBreakpoint] = useState({
    isMobile: false,
    isTablet: false,
    isDesktop: true
  });

  useEffect(() => {
    // Define media queries
    const mobileQuery = window.matchMedia('(max-width: 767px)');
    const tabletQuery = window.matchMedia('(min-width: 768px) and (max-width: 1023px)');
    const desktopQuery = window.matchMedia('(min-width: 1024px)');

    // Update state based on current matches
    const updateBreakpoint = () => {
      setBreakpoint({
        isMobile: mobileQuery.matches,
        isTablet: tabletQuery.matches,
        isDesktop: desktopQuery.matches
      });
    };

    // Set initial values
    updateBreakpoint();

    // Add listeners
    mobileQuery.addEventListener('change', updateBreakpoint);
    tabletQuery.addEventListener('change', updateBreakpoint);
    desktopQuery.addEventListener('change', updateBreakpoint);

    // Cleanup listeners on unmount
    return () => {
      mobileQuery.removeEventListener('change', updateBreakpoint);
      tabletQuery.removeEventListener('change', updateBreakpoint);
      desktopQuery.removeEventListener('change', updateBreakpoint);
    };
  }, []);

  return breakpoint;
}
