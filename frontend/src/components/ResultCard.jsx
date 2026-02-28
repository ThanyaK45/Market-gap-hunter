import ReactMarkdown from 'react-markdown'
import { Pie } from 'react-chartjs-2'

function ResultCard({ result, aiResponse, aiLoading, onAskAI }) {
  if (!result) return null

  return (
    <div className="result-card">
      <div className="score-box" style={{borderColor: result.verdict_color}}>
        <span className="score-label">คะแนนโอกาสทางธุรกิจ (Opportunity Score)</span>
        <span className="score-val" style={{color: result.verdict_color}}>
          {result.score}
        </span>
        <span className="verdict">{result.verdict}</span>
      </div>

      <hr style={{margin: '20px 0', border: '0.5px solid #eee'}} />
      
      <div className="action-buttons">
        <button 
          className="ai-btn" 
          onClick={onAskAI}
          disabled={aiLoading}
        >
          {aiLoading ? "🤖 AI is thinking..." : "✨ ขอคำปรึกษาจาก AI"}
        </button>
      </div>

      {aiResponse && (
        <div className="ai-result-box">
          <ReactMarkdown>{aiResponse}</ReactMarkdown>
        </div>
      )}

      <div className="growth-box">
        <span>แนวโน้มในอนาคต: <strong>{result.growth_status}</strong></span>
        <small>(พบเขตก่อสร้าง {result.construction_count} แห่งในบริเวณนี้)</small>
      </div>

      <div className="chart-container">
        <h4>👥 สัดส่วนกลุ่มลูกค้าเป้าหมาย</h4>
        <Pie data={{
          labels: ['พนักงานออฟฟิศ', 'นักเรียน/นักศึกษา', 'ผู้อยู่อาศัย (บ้าน/คอนโด)', 'ผู้คนสัญจร'],
          datasets: [{
            data: [
              result.demand_breakdown.Office,
              result.demand_breakdown.Students,
              result.demand_breakdown.Residential,
              result.demand_breakdown.Transport
            ],
            backgroundColor: ['#e74c3c', '#3498db', '#f1c40f', '#2ecc71'],
            borderWidth: 1
          }]
        }} options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }} />
      </div>

      <div className="stats-grid">
        <div className="stat-item">🔴 จำนวนร้านคู่แข่ง: {result.supply_count}</div>
        <div className="stat-item">🟢 ฐานลูกค้าศักยภาพ: {result.demand_count}</div>
      </div>
    </div>
  )
}

export default ResultCard
