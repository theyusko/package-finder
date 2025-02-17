import requests
from typing import Optional
import re
from bs4 import BeautifulSoup
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class BioLibRepository(PackageRepository):
    """BioLib package repository."""
    
    def __init__(self):
        self.base_url = "https://biolib.com"
        self.verbose_logging = True
    
    def _log(self, message):
        """Logging method that can be toggled."""
        if self.verbose_logging:
            print(f"[BioLib DEBUG] {message}")
    
    def get_repository_name(self) -> str:
        return "BioLib"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            self._log(f"Searching for package: {package_name}")
            
            # More comprehensive URL variations
            url_variations = [
                f"{self.base_url}/bio-utils/{package_name.lower()}",
                f"{self.base_url}/bio-utils/{package_name}",
                f"{self.base_url}/package/{package_name.lower()}",
                f"{self.base_url}/package/{package_name}",
                f"{self.base_url}/{package_name.lower()}",
                f"{self.base_url}/{package_name}"
            ]
            
            response = None
            working_url = None
            
            # Try direct URLs first
            for url in url_variations:
                try:
                    self._log(f"Trying direct URL: {url}")
                    response = requests.get(url)
                    if response.status_code == 200:
                        working_url = url
                        break
                except requests.RequestException as e:
                    self._log(f"Failed to access {url}: {e}")
            
            # If direct access fails, try search
            if not response or response.status_code != 200:
                self._log("Direct access failed, attempting search")
                search_url = f"{self.base_url}/search"
                params = {'q': package_name}
                
                try:
                    search_response = requests.get(search_url, params=params)
                    
                    if search_response.status_code != 200:
                        self._log(f"Search failed with status {search_response.status_code}")
                        return None
                    
                    # Parse search results
                    soup = BeautifulSoup(search_response.text, 'html.parser')
                    
                    # Enhanced search matching
                    exact_matches = soup.find_all('a', href=re.compile(
                        f'(/bio-utils/|/package/|/).*{re.escape(package_name)}.*', 
                        re.IGNORECASE
                    ))
                    
                    if not exact_matches:
                        self._log("No matching packages found in search")
                        return None
                    
                    # Use first matching result
                    package_link = exact_matches[0]
                    package_url = package_link['href']
                    if not package_url.startswith('http'):
                        package_url = self.base_url + package_url
                    
                    self._log(f"Found package URL through search: {package_url}")
                    
                    response = requests.get(package_url)
                    working_url = package_url
                    
                    if response.status_code != 200:
                        self._log(f"Failed to access search result URL: {package_url}")
                        return None
                
                except requests.RequestException as e:
                    self._log(f"Search request failed: {e}")
                    return None
            
            # Parse package page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract package information
            title_elem = (
                soup.find('h1', class_='package-title') or 
                soup.find('h1') or 
                soup.find('title')
            )
            
            if not title_elem:
                self._log("Could not find package title")
                return None
            
            # Get the actual package name from the page
            actual_name = title_elem.text.strip()
            if ':' in actual_name:
                actual_name = actual_name.split(':')[0].strip()
            
            self._log(f"Extracted package name: {actual_name}")
            
            # Extract description
            description_elem = (
                soup.find('div', class_='package-description') or
                soup.find('meta', {'name': 'description'}) or
                soup.find('div', class_='description')
            )
            
            description = None
            if description_elem:
                if isinstance(description_elem, str):
                    description = description_elem.strip()
                elif description_elem.get('content'):
                    description = description_elem['content'].strip()
                else:
                    description = description_elem.text.strip()
            
            self._log(f"Extracted description: {description}")
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description or '')
            
            return PackageInfo(
                name=actual_name,
                versions=[],  # No version info found
                repository=self.get_repository_name(),
                url=working_url,
                description=description,
                latest_version=None,
                license=None,
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except Exception as e:
            self._log(f"Unexpected error: {e}")
            return None