export default function CookSettings({ meatType, setMeatType, meatWeight, setMeatWeight }) {
  return (
    <div style={{ background: "#1a1a1a", padding: 16, borderRadius: 8, marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Cook Settings</h3>
      
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
          Meat Type
        </label>
        <input 
          type="text" 
          value={meatType}
          onChange={(e) => setMeatType(e.target.value)}
          placeholder="e.g., Pork Shoulder, Brisket"
          style={{ 
            width: "100%",
            padding: 8, 
            borderRadius: 4, 
            border: '1px solid #333',
            background: '#222',
            color: '#eaeaea',
            fontSize: 14
          }}
        />
      </div>
      
      <div>
        <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#aaa" }}>
          Weight (kg)
        </label>
        <input 
          type="number" 
          step="0.1"
          value={meatWeight}
          onChange={(e) => setMeatWeight(e.target.value)}
          placeholder="0.0"
          style={{ 
            width: "100%",
            padding: 8, 
            borderRadius: 4, 
            border: '1px solid #333',
            background: '#222',
            color: '#eaeaea',
            fontSize: 14
          }}
        />
      </div>
    </div>
  );
}
