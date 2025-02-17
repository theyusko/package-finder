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
    
    def get_repository_name(self) -> str:
        return "BioLib"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
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
                    response = requests.get(url)
                    if response.status_code == 200:
                        working_url = url
                        break
                except requests.RequestException:
                    continue
            
            # If direct access fails, try search
            if not response or response.status_code != 200:
                search_url = f"{self.base_url}/search"
                params = {'q': package_name}
                
                try:
                    search_response = requests.get(search_url, params=params)
                    
                    if search_response.status_code != 200:
                        return None
                    
                    # Parse search results
                    soup = BeautifulSoup(search_response.text, 'html.parser')
                    
                    # Enhanced search matching
                    exact_matches = soup.find_all('a', href=re.compile(
                        f'(/bio-utils/|/package/|/).*{re.escape(package_name)}.*', 
                        re.IGNORECASE
                    ))
                    
                    if not exact_matches:
                        return None
                    
                    # Use first matching result
                    package_link = exact_matches[0]
                    package_url = package_link['href']
                    if not package_url.startswith('http'):
                        package_url = self.base_url + package_url
                    
                    response = requests.get(package_url)
                    working_url = package_url
                    
                    if response.status_code != 200:
                        return None
                
                except requests.RequestException:
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
                return None
            
            # Get the actual package name from the page
            actual_name = title_elem.text.strip()
            if ':' in actual_name:
                actual_name = actual_name.split(':')[0].strip()
            
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
            
        except Exception:
            return None