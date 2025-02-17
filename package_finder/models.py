from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class PackageInfo:
    """Standardized package information across different sources."""
    name: str
    versions: List[str]
    repository: str
    url: str
    description: Optional[str] = None
    latest_version: Optional[str] = None
    license: Optional[str] = None
    thread_support: Optional[bool] = None
    thread_flags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        """Convert PackageInfo to dictionary."""
        return {
            'name': self.name,
            'repository': self.repository,
            'url': self.url,
            'description': self.description,
            'latest_version': self.latest_version,
            'license': self.license,
            'thread_support': self.thread_support,
            'thread_flags': self.thread_flags or []
        }