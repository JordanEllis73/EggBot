export default function TabContainer({ activeTab, onTabChange, tabs }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 4,
        padding: '8px 0',
        borderBottom: '1px solid #333',
        marginBottom: 16
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              padding: '8px 16px',
              background: activeTab === tab.id ? '#2a2a2a' : 'transparent',
              color: activeTab === tab.id ? '#5bd' : '#888',
              border: activeTab === tab.id ? '1px solid #5bd' : '1px solid #444',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: activeTab === tab.id ? 600 : 400,
              transition: 'all 0.15s ease'
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
