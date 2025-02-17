import requests
from typing import Optional, List
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class GalaxyToolShedRepository(PackageRepository):
    """Galaxy Tool Shed repository."""
    
    def __init__(self):
        self.base_url = "https://toolshed.g2.bx.psu.edu/api"
    
    def get_repository_name(self) -> str:
        return "Galaxy Tool Shed"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Search for repositories
            search_url = f"{self.base_url}/repositories/search/{package_name}"
            response = requests.get(search_url)
            
            if response.status_code != 200:
                return None
            
            repositories = response.json()
            if not repositories:
                return None
            
            # Find best match
            exact_matches = [repo for repo in repositories 
                           if repo['name'].lower() == package_name.lower()]
            best_match = exact_matches[0] if exact_matches else repositories[0]
            
            # Get repository details
            owner = best_match['owner']
            name = best_match['name']
            details_url = f"{self.base_url}/repositories/{owner}/{name}"
            details_response = requests.get(details_url)
            
            if details_response.status_code != 200:
                return None
            
            details = details_response.json()
            
            # Get changeset revisions (versions)
            versions = [rev['rev_id'][:7] for rev in details.get('revisions', [])]
            
            # Get readme if available
            readme = ""
            try:
                readme_url = f"https://toolshed.g2.bx.psu.edu/repository/download?repository_id={details['id']}&file=README.md"
                readme_response = requests.get(readme_url)
                if readme_response.status_code == 200:
                    readme = readme_response.text
            except requests.RequestException:
                pass
            
            description = details.get('description', '') or best_match.get('description', '')
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description, readme)
            
            # Create tool URL
            tool_url = f"https://toolshed.g2.bx.psu.edu/view/{owner}/{name}"
            
            return PackageInfo(
                name=name,
                versions=versions,
                repository=self.get_repository_name(),
                url=tool_url,
                description=description,
                latest_version=versions[-1] if versions else None,
                license=None,  # Galaxy Tool Shed doesn't consistently provide license info
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None