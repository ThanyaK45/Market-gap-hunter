const BUSINESS_OPTIONS = [
  "Cafe", "Restaurant", "Bar/Pub", "Convenience Store", 
  "Pharmacy", "Gym/Fitness", "Coworking Space"
]

function AnalysisControls({ 
  businessType, 
  onBusinessTypeChange, 
  radius, 
  onRadiusChange,
  onAnalyze,
  loading,
  disabled
}) {
  return (
    <>
      <div className="control-group">
        <label>🏢 Business Type:</label>
        <select value={businessType} onChange={(e) => onBusinessTypeChange(e.target.value)}>
          {BUSINESS_OPTIONS.map(b => <option key={b} value={b}>{b}</option>)}
        </select>
      </div>

      <div className="control-group">
        <label>📏 รัศมีการค้นหา: {radius} เมตร ({(radius/1000).toFixed(1)} กม.)</label>
        <input 
          type="range" 
          min="500" 
          max="3000" 
          step="100"
          value={radius}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
          className="radius-slider"
        />
        <div className="radius-labels">
          <span>500m</span>
          <span>1.5km</span>
          <span>3km</span>
        </div>
      </div>

      <button 
        className="analyze-btn" 
        onClick={onAnalyze}
        disabled={loading || disabled}
      >
        {loading ? "Processing..." : "🚀 Analyze Market Gap"}
      </button>
    </>
  )
}

export default AnalysisControls
