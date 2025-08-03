import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class URLMapping:
    """Data class to store URL mapping information"""
    original_url: str
    short_code: str
    created_at: datetime
    clicks: int = 0

class URLStore:
    """Thread-safe in-memory storage for URL mappings"""
    
    def __init__(self):
        self._mappings: Dict[str, URLMapping] = {}
        self._lock = threading.Lock()
    
    def create_mapping(self, short_code: str, original_url: str) -> URLMapping:
        """Create a new URL mapping"""
        with self._lock:
            mapping = URLMapping(
                original_url=original_url,
                short_code=short_code,
                created_at=datetime.now()
            )
            self._mappings[short_code] = mapping
            return mapping
    
    def get_mapping(self, short_code: str) -> Optional[URLMapping]:
        """Get URL mapping by short code"""
        with self._lock:
            return self._mappings.get(short_code)
    
    def increment_clicks(self, short_code: str) -> bool:
        """Increment click count for a short code"""
        with self._lock:
            if short_code in self._mappings:
                self._mappings[short_code].clicks += 1
                return True
            return False
    
    def get_all_mappings(self) -> Dict[str, URLMapping]:
        """Get all mappings (for testing purposes)"""
        with self._lock:
            return self._mappings.copy()

# Global instance for the application
url_store = URLStore()