import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class HistoryManager:
    """Manage analysis history for tracking changes over time"""
    
    def __init__(self, history_file: str = "analysis_history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(exist_ok=True)
        
        # Create file if doesn't exist
        if not self.history_file.exists():
            self._save_history([])
    
    def _load_history(self) -> List[Dict[Any, Any]]:
        """Load history from file"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    def _save_history(self, history: List[Dict[Any, Any]]) -> None:
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_analysis(self, 
                    lat: float, 
                    lon: float, 
                    business_type: str,
                    radius: int,
                    result: Dict[Any, Any]) -> None:
        """Add new analysis to history"""
        history = self._load_history()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "location": {
                "lat": round(lat, 6),
                "lon": round(lon, 6)
            },
            "business_type": business_type,
            "radius": radius,
            "result": {
                "score": result.get("score"),
                "verdict": result.get("verdict"),
                "supply_count": result.get("supply_count"),
                "demand_count": result.get("demand_count"),
                "growth_status": result.get("growth_status"),
                "construction_count": result.get("construction_count")
            }
        }
        
        history.append(entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        self._save_history(history)
    
    def get_history(self, 
                   limit: int = 10,
                   business_type: Optional[str] = None) -> List[Dict[Any, Any]]:
        """Get recent analysis history"""
        history = self._load_history()
        
        # Filter by business type if specified
        if business_type:
            history = [h for h in history if h.get("business_type") == business_type]
        
        # Return most recent entries
        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def get_location_history(self, 
                            lat: float, 
                            lon: float, 
                            tolerance: float = 0.01) -> List[Dict[Any, Any]]:
        """Get history for a specific location (with tolerance)"""
        history = self._load_history()
        
        location_history = []
        for entry in history:
            entry_lat = entry["location"]["lat"]
            entry_lon = entry["location"]["lon"]
            
            # Check if within tolerance
            if (abs(entry_lat - lat) <= tolerance and 
                abs(entry_lon - lon) <= tolerance):
                location_history.append(entry)
        
        return sorted(location_history, key=lambda x: x["timestamp"], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        history = self._load_history()
        
        if not history:
            return {
                "total_analyses": 0,
                "business_types": {},
                "average_score": 0,
                "most_analyzed_type": None
            }
        
        business_types = {}
        total_score = 0
        
        for entry in history:
            btype = entry.get("business_type", "Unknown")
            business_types[btype] = business_types.get(btype, 0) + 1
            total_score += entry["result"].get("score", 0)
        
        most_analyzed = max(business_types.items(), key=lambda x: x[1])[0] if business_types else None
        
        return {
            "total_analyses": len(history),
            "business_types": business_types,
            "average_score": round(total_score / len(history), 2),
            "most_analyzed_type": most_analyzed,
            "date_range": {
                "first": history[0]["timestamp"] if history else None,
                "last": history[-1]["timestamp"] if history else None
            }
        }
    
    def clear_history(self) -> int:
        """Clear all history"""
        history = self._load_history()
        count = len(history)
        self._save_history([])
        return count
