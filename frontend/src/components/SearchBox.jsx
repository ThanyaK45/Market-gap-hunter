import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = "http://127.0.0.1:8000"

const COUNTRY_OPTIONS = [
  { code: "", label: "🌍 All World" },
  { code: "th", label: "🇹🇭 Thailand" },
  { code: "us", label: "🇺🇸 USA" },
  { code: "jp", label: "🇯🇵 Japan" },
  { code: "uk", label: "🇬🇧 UK" },
  { code: "cn", label: "🇨🇳 China" },
]

function SearchBox({ onSelectLocation }) {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCountry, setSelectedCountry] = useState("th")
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchQuery.length > 2) {
        try {
          const res = await axios.get(`${API_URL}/autocomplete`, {
            params: { query: searchQuery, country: selectedCountry }
          })
          setSuggestions(res.data)
          setShowSuggestions(true)
        } catch (err) {
          console.error(err)
        }
      } else {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 500)

    return () => clearTimeout(delayDebounceFn)
  }, [searchQuery, selectedCountry])

  const selectSuggestion = (item) => {
    setSearchQuery(item.display_name)
    onSelectLocation({ lat: item.lat, lng: item.lon }, item.display_name)
    setShowSuggestions(false)
  }

  return (
    <>
      <div className="control-group">
        <label>🏳️ Country Filter:</label>
        <select 
          value={selectedCountry} 
          onChange={(e) => setSelectedCountry(e.target.value)}
        >
          {COUNTRY_OPTIONS.map(c => (
            <option key={c.code} value={c.code}>{c.label}</option>
          ))}
        </select>
      </div>

      <div className="control-group search-container" style={{position: 'relative'}}>
        <label>🔍 Search Location:</label>
        <input 
          type="text" 
          placeholder="Type location (e.g. Siam)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => searchQuery.length > 2 && setShowSuggestions(true)}
        />
        
        {showSuggestions && suggestions.length > 0 && (
          <ul className="suggestion-list">
            {suggestions.map((item, idx) => (
              <li key={idx} onClick={() => selectSuggestion(item)}>
                {item.display_name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  )
}

export default SearchBox
