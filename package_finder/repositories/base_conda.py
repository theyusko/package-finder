import requests
from typing import Optional
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class BaseAnacondaRepository(PackageRepository):
    """Base class for Anaconda-based repositories (Anaconda, Bioconda, Conda-forge)."""
    
    def __init__(self, channel: str):
        """
        Initialize the repository with a specific channel.
        
        Args:
            channel (str): The Anaconda channel name (e.g., 'anaconda', 'bioconda', 'conda-forge')
        """
        self.channel = channel
        self.base_url = f"https://api.anaconda.org/package/{channel}"
        
        # Additional package name variations to try
        self.package_name_variations = [
            '{name}',  # Original name
            'bioconductor-{name}',  # Bioconductor prefix
            'r-{name}',  # R package prefix
        ]
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Search for a package in the repository.
        
        Args:
            package_name (str): Name of the package to search for
            
        Returns:
            Optional[PackageInfo]: Package information if found, None otherwise
        """
        # Try different package name variations
        for name_template in self.package_name_variations:
            search_name = name_template.format(name=package_name)
            
            try:
                # First try exact match
                response = requests.get(f"{self.base_url}/{search_name}")
                if response.status_code == 200:
                    data = response.json()
                else:
                    # If exact match fails, get package list and try case-insensitive match
                    list_response = requests.get(f"https://api.anaconda.org/package/{self.channel}/")
                    if list_response.status_code == 200:
                        available_packages = [pkg['name'] for pkg in list_response.json()]
                        correct_name = self._find_case_insensitive_match(search_name, available_packages)
                        if correct_name:
                            response = requests.get(f"{self.base_url}/{correct_name}")
                            if response.status_code == 200:
                                data = response.json()
                                search_name = correct_name  # Use the correct case
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                
                # Get license and description
                license_info = data.get('license', None)
                description = data.get('summary', '')
                readme = data.get('readme', '')
                
                # Check for threading support
                has_threading, thread_flags = find_thread_flags(description, readme)
                
                # Sort versions properly
                versions = sorted(data.get('versions', []),
                              key=lambda x: [int(y) for y in x.split('.')] 
                              if all(y.isdigit() for y in x.split('.')) 
                              else [0])
                
                return PackageInfo(
                    name=search_name,
                    versions=versions,
                    repository=self.get_repository_name(),
                    url=f"https://anaconda.org/{self.channel}/{search_name}",
                    description=description,
                    latest_version=data.get('latest_version'),
                    license=license_info,
                    thread_support=has_threading,
                    thread_flags=thread_flags
                )
            except requests.RequestException:
                continue
        
        return None