import { useState, useEffect } from 'react'
import axios from 'axios'
import './HistoryPanel.css'

const API_URL = "http://127.0.0.1:8000"

function HistoryPanel({ onSelectLocation }) {
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const [historyRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/history?limit=10`),
        axios.get(`${API_URL}/history/stats`)
      ])
      setHistory(historyRes.data)
      setStats(statsRes.data)
    } catch (err) {
      console.error("Error fetching history:", err)
    }
    setLoading(false)
  }

  useEffect(() => {
    if (showHistory) {
      fetchHistory()
    }
  }, [showHistory])

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleSelectHistory = (item) => {
    onSelectLocation({
      lat: item.location.lat,
      lng: item.location.lon
    })
    setShowHistory(false)
  }

  return (
    <div className="history-panel">
      <button 
        className="history-toggle-btn"
        onClick={() => setShowHistory(!showHistory)}
      >
        📊 {showHistory ? 'ซ่อนประวัติ' : 'ดูประวัติการวิเคราะห์'}
      </button>

      {showHistory && (
        <div className="history-content">
          {loading ? (
            <div className="history-loading">กำลังโหลด...</div>
          ) : (
            <>
              {stats && (
                <div className="history-stats">
                  <h4>📈 สถิติการใช้งาน</h4>
                  <div className="stat-row">
                    <span>วิเคราะห์ทั้งหมด:</span>
                    <strong>{stats.total_analyses} ครั้ง</strong>
                  </div>
                  <div className="stat-row">
                    <span>คะแนนเฉลี่ย:</span>
                    <strong>{stats.average_score}</strong>
                  </div>
                  <div className="stat-row">
                    <span>ประเภทยอดนิยม:</span>
                    <strong>{stats.most_analyzed_type || '-'}</strong>
                  </div>
                </div>
              )}

              <div className="history-list">
                <h4>🕐 ประวัติล่าสุด</h4>
                {history.length === 0 ? (
                  <p className="no-history">ยังไม่มีประวัติการวิเคราะห์</p>
                ) : (
                  history.map((item, idx) => (
                    <div 
                      key={idx} 
                      className="history-item"
                      onClick={() => handleSelectHistory(item)}
                    >
                      <div className="history-header">
                        <span className="history-type">{item.business_type}</span>
                        <span className="history-date">{formatDate(item.timestamp)}</span>
                      </div>
                      <div className="history-details">
                        <span className="history-score" style={{color: item.result.verdict === "ศักยภาพสูง (น่าลงทุน)" ? "#27ae60" : "#e67e22"}}>
                          Score: {item.result.score}
                        </span>
                        <span className="history-location">
                          📍 {item.location.lat.toFixed(4)}, {item.location.lon.toFixed(4)}
                        </span>
                      </div>
                      <div className="history-verdict">{item.result.verdict}</div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default HistoryPanel
