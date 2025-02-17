import requests
from typing import Optional
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class PositRepository(PackageRepository):
    """Posit Package Manager repository."""
    
    def __init__(self, base_url: str = "https://packagemanager.posit.co/client"):
        self.base_url = base_url
    
    def get_repository_name(self) -> str:
        return "Posit Package Manager"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Search for package
            response = requests.get(f"{self.base_url}/packages/{package_name}")
            if response.status_code == 200:
                data = response.json()
            else:
                # Try case-insensitive search
                list_response = requests.get(f"{self.base_url}/packages")
                if list_response.status_code == 200:
                    available_packages = [pkg['Package'] for pkg in list_response.json()]
                    correct_name = self._find_case_insensitive_match(package_name, available_packages)
                    if correct_name:
                        response = requests.get(f"{self.base_url}/packages/{correct_name}")
                        if response.status_code == 200:
                            data = response.json()
                            package_name = correct_name
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            
            # Get package details
            description = data.get('Description', '')
            
            # Get all versions
            versions_response = requests.get(f"{self.base_url}/packages/{package_name}/versions")
            versions = []
            if versions_response.status_code == 200:
                versions_data = versions_response.json()
                versions = [v['Version'] for v in versions_data if v.get('Version')]
            
            # Sort versions properly
            versions = sorted(versions,
                          key=lambda x: [int(y) for y in x.split('.')] 
                          if all(y.isdigit() for y in x.split('.')) 
                          else [0])
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description)
            
            return PackageInfo(
                name=package_name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"{self.base_url}/packages/{package_name}",
                description=description,
                latest_version=data.get('Version'),
                license=data.get('License'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None