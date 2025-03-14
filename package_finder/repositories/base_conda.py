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
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Wrapper for search package helper that tries both the package name and 'bioconductor-' + package name.
        """  
        exact_name_result = self.search_package_helper(package_name)
        bioconductor_result = self.search_package_helper("bioconductor-" + package_name)

        if bioconductor_result != None:
            return bioconductor_result
        else:
            return exact_name_result
    
    def search_package_helper(self, package_name: str) -> Optional[PackageInfo]:
        """
        Search for a package in the repository.
        
        Args:
            package_name (str): Name of the package to search for
            
        Returns:
            Optional[PackageInfo]: Package information if found, None otherwise
        """
        try:
            # Try exact match
            response = requests.get(f"{self.base_url}/{package_name}")
            if response.status_code == 200:
                data = response.json()
            else:
                # If exact match fails, get package list and try case-insensitive match
                list_response = requests.get(f"https://api.anaconda.org/package/{self.channel}/")
                if list_response.status_code == 200:
                    available_packages = [pkg['name'] for pkg in list_response.json()]
                    correct_name = self._find_case_insensitive_match(package_name, available_packages)
                    if correct_name:
                        response = requests.get(f"{self.base_url}/{correct_name}")
                        if response.status_code == 200:
                            data = response.json()
                            package_name = correct_name  # Use the correct case
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            
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
                name=package_name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"https://anaconda.org/{self.channel}/{package_name}",
                description=description,
                latest_version=data.get('latest_version'),
                license=license_info,
                thread_support=has_threading,
                thread_flags=thread_flags
            )
        except requests.RequestException:
            return None