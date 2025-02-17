import requests
from typing import Optional, List
import re
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class GitHubContainerRegistryRepository(PackageRepository):
    """GitHub Container Registry repository."""
    
    def __init__(self, token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def get_repository_name(self) -> str:
        return "GitHub Container Registry"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Search for packages
            search_url = f"{self.base_url}/search/repositories"
            params = {
                'q': f'{package_name} in:name topic:container',
                'per_page': 100
            }
            response = requests.get(search_url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return None
            
            results = response.json().get('items', [])
            if not results:
                return None
            
            # Find best match
            exact_matches = [r for r in results if r['name'].lower() == package_name.lower()]
            best_match = exact_matches[0] if exact_matches else results[0]
            
            # Get package details
            owner = best_match['owner']['login']
            name = best_match['name']
            
            # Get container tags
            packages_url = f"{self.base_url}/users/{owner}/packages/container/{name}/versions"
            versions_response = requests.get(packages_url, headers=self.headers)
            
            versions = []
            if versions_response.status_code == 200:
                versions_data = versions_response.json()
                versions = [v['metadata']['container']['tags'][0] 
                          for v in versions_data 
                          if v.get('metadata', {}).get('container', {}).get('tags')]
            
            # Get readme content
            readme_url = f"{self.base_url}/repos/{owner}/{name}/readme"
            readme = ""
            try:
                readme_response = requests.get(readme_url, headers=self.headers)
                if readme_response.status_code == 200:
                    import base64
                    readme = base64.b64decode(readme_response.json()['content']).decode('utf-8')
            except:
                pass
            
            description = best_match.get('description', '')
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description, readme)
            
            return PackageInfo(
                name=name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"https://github.com/{owner}/{name}/pkgs/container/{name}",
                description=description,
                latest_version=versions[0] if versions else None,
                license=best_match.get('license', {}).get('spdx_id'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None