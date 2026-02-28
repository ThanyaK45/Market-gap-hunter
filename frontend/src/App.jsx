import { useState } from 'react'
import axios from 'axios'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import toast, { Toaster } from 'react-hot-toast'
import HistoryPanel from './HistoryPanel'
import SearchBox from './components/SearchBox'
import MapView from './components/MapView'
import AnalysisControls from './components/AnalysisControls'
import ResultCard from './components/ResultCard'
import 'leaflet/dist/leaflet.css'
import './App.css'

ChartJS.register(ArcElement, Tooltip, Legend)

const API_URL = "https://market-gap-api.onrender.com"

function App() {
  const [selectedPos, setSelectedPos] = useState(null)
  const [businessType, setBusinessType] = useState("Cafe")
  const [radius, setRadius] = useState(1000)
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const [aiResponse, setAiResponse] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)

  const handleLocationSelect = (position) => {
    setSelectedPos(position)
  }

  const analyzeMarket = async () => {
    if (!selectedPos) {
      toast.error("กรุณาเลือกตำแหน่งบนแผนที่ก่อน")
      return
    }
    
    setLoading(true)
    setResult(null)
    setAiResponse(null)

    const loadingToast = toast.loading("กำลังวิเคราะห์ตลาด...")

    try {
      const response = await axios.post(`${API_URL}/analyze`, {
        lat: selectedPos.lat,
        lon: selectedPos.lng,
        business_type: businessType,
        radius: radius
      })
      setResult(response.data)
      toast.success("วิเคราะห์เสร็จสิ้น!", { id: loadingToast })
    } catch (error) {
      console.error("Error:", error)
      const errorMsg = error.response?.data?.detail || "เกิดข้อผิดพลาดในการวิเคราะห์"
      toast.error(errorMsg, { id: loadingToast })
    }
    setLoading(false)
  }

  const handleAskAI = async () => {
    if (!result) return
    setAiLoading(true)
    setAiResponse("") // Clear previous response
    
    const loadingToast = toast.loading("AI กำลังวิเคราะห์...")
    
    try {
      const response = await fetch(`${API_URL}/ask-ai-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          business_type: businessType,
          score: result.score,
          supply_count: result.supply_count,
          demand_count: result.demand_count,
          demand_breakdown: result.demand_breakdown,
          growth_status: result.growth_status
        })
      })

      if (!response.ok) {
        throw new Error('AI request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedText = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        accumulatedText += chunk
        setAiResponse(accumulatedText)
      }

      toast.success("AI วิเคราะห์เสร็จแล้ว!", { id: loadingToast })
    } catch (err) {
      console.error(err)
      toast.error("AI ไม่สามารถวิเคราะห์ได้", { id: loadingToast })
    }
    setAiLoading(false)
  }

  return (
    <div className="container">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#27ae60',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#e74c3c',
              secondary: '#fff',
            },
          },
        }}
      />
      
      <div className="sidebar">
        <h1>🏙️ Market Gap Hunter</h1>
        
        <HistoryPanel onSelectLocation={setSelectedPos} />
        
        <SearchBox onSelectLocation={handleLocationSelect} />
        
        <AnalysisControls
          businessType={businessType}
          onBusinessTypeChange={setBusinessType}
          radius={radius}
          onRadiusChange={setRadius}
          onAnalyze={analyzeMarket}
          loading={loading}
          disabled={!selectedPos}
        />

        <ResultCard
          result={result}
          aiResponse={aiResponse}
          aiLoading={aiLoading}
          onAskAI={handleAskAI}
        />
      </div>

      <MapView
        selectedPos={selectedPos}
        setSelectedPos={setSelectedPos}
        radius={radius}
        result={result}
      />
    </div>
  )
}

export default App
