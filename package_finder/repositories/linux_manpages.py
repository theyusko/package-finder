import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class LinuxManpagesRepository(PackageRepository):
    """Linux Manpages repository."""
    
    def __init__(self):
        self.base_url = "https://man7.org/linux/man-pages/man"
        self._cache: Dict[str, Dict] = {}
    
    def get_repository_name(self) -> str:
        return "Linux Manpages"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Try different manual sections (1-8)
            for section in range(1, 9):
                url = f"{self.base_url}{section}/{package_name}.{section}.html"
                response = requests.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract description from the NAME section
                    description = ""
                    name_section = soup.find('div', {'class': 'NAME'})
                    if name_section:
                        description = name_section.get_text(strip=True)
                        if ' - ' in description:
                            description = description.split(' - ')[1]
                    
                    # Extract full content for thread detection
                    content = soup.get_text()
                    
                    # Check for threading support
                    has_threading, thread_flags = find_thread_flags(content)
                    
                    return PackageInfo(
                        name=package_name,
                        versions=[f"Section {section}"],
                        repository=self.get_repository_name(),
                        url=url,
                        description=description,
                        latest_version=f"Section {section}",
                        license="GNU Free Documentation License",
                        thread_support=has_threading,
                        thread_flags=thread_flags
                    )
            
            return None
            
        except requests.RequestException:
            return None