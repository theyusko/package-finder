import requests
from typing import Optional
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class PyPIRepository(PackageRepository):
    """PyPI package repository."""
    
    def __init__(self):
        self.base_url = "https://pypi.org/pypi"
    
    def get_repository_name(self) -> str:
        return "PyPI"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # First try exact match
            response = requests.get(f"{self.base_url}/{package_name}/json")
            if response.status_code == 200:
                data = response.json()
            else:
                # If exact match fails, try simple search
                search_response = requests.get(f"https://pypi.org/simple/")
                if search_response.status_code == 200:
                    # Parse the simple HTML page to get package names
                    available_packages = [
                        line.split('>')[-2].split('<')[0]
                        for line in search_response.text.split('\n')
                        if 'a href' in line
                    ]
                    correct_name = self._find_case_insensitive_match(package_name, available_packages)
                    if correct_name:
                        response = requests.get(f"{self.base_url}/{correct_name}/json")
                        if response.status_code == 200:
                            data = response.json()
                            package_name = correct_name  # Use the correct case
                        else:
                            return None
                    else:
                        return None
                else:
                    return None

            # Get description and readme
            description = data['info'].get('summary', '')
            readme = data['info'].get('description', '')
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description, readme)
            
            # Get all versions including pre-releases
            versions = list(data['releases'].keys())
            # Filter out empty releases and sort
            versions = [v for v in versions if data['releases'][v]]
            versions.sort(key=lambda x: [int(y) for y in x.split('.')] 
                        if all(y.isdigit() for y in x.split('.')) 
                        else [0])
            
            return PackageInfo(
                name=package_name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"https://pypi.org/project/{package_name}",
                description=description,
                latest_version=data['info'].get('version'),
                license=data['info'].get('license'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
        except requests.RequestException:
            return None