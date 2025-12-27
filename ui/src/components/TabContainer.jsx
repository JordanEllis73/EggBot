import useMediaQuery from '../hooks/useMediaQuery';
import useTouchDevice from '../hooks/useTouchDevice';

export default function TabContainer({ activeTab, onTabChange, tabs }) {
  const { isMobile } = useMediaQuery();
  const isTouchDevice = useTouchDevice();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab Bar */}
      <div style={{
        display: 'flex',
        flexWrap: isMobile ? 'nowrap' : 'wrap',
        overflowX: isMobile ? 'auto' : 'visible',
        gap: isMobile ? 2 : 4,
        padding: isMobile ? '8px 4px' : '8px 0',
        borderBottom: '1px solid #333',
        marginBottom: 16,
        WebkitOverflowScrolling: 'touch'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              padding: isMobile ? '10px 12px' : '8px 16px',
              background: activeTab === tab.id ? '#2a2a2a' : 'transparent',
              color: activeTab === tab.id ? '#5bd' : '#888',
              border: activeTab === tab.id ? '1px solid #5bd' : '1px solid #444',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: isMobile ? 13 : 14,
              fontWeight: activeTab === tab.id ? 600 : 400,
              transition: 'all 0.15s ease',
              minHeight: isTouchDevice ? 44 : 'auto',
              whiteSpace: 'nowrap',
              WebkitUserSelect: 'none',
              userSelect: 'none',
              WebkitTapHighlightColor: 'transparent'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        {tabs.find(t => t.id === activeTab)?.content}
      </div>
    </div>
  );
}
