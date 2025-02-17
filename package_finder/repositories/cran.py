import requests
from typing import Optional
import re
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class CRANRepository(PackageRepository):
    """CRAN (Comprehensive R Archive Network) package repository."""
    
    def __init__(self):
        self.base_url = "https://cran.r-project.org/web/packages"
    
    def get_repository_name(self) -> str:
        return "CRAN"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Try to get package details
            response = requests.get(f"{self.base_url}/{package_name}/index.html")
            if response.status_code != 200:
                # Try searching in packages list
                list_response = requests.get(f"{self.base_url}/available_packages_by_name.html")
                if list_response.status_code == 200:
                    available_packages = re.findall(r'href="[^"]+">([^<]+)</a>', list_response.text)
                    correct_name = self._find_case_insensitive_match(package_name, available_packages)
                    if correct_name:
                        response = requests.get(f"{self.base_url}/{correct_name}/index.html")
                        if response.status_code == 200:
                            package_name = correct_name
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            
            # Parse package details
            content = response.text
            
            # Extract version using regex
            version_match = re.search(r'Version:</td>\s*<td>([^<]+)</td>', content)
            latest_version = version_match.group(1) if version_match else None
            
            # Extract description
            desc_match = re.search(r'Description:</td>\s*<td>([^<]+)</td>', content)
            description = desc_match.group(1) if desc_match else None
            
            # Extract license
            license_match = re.search(r'License:</td>\s*<td>([^<]+)</td>', content)
            license_info = license_match.group(1) if license_match else None
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description or '')
            
            # Get available versions from CRAN archive
            archive_url = f"https://cran.r-project.org/src/contrib/Archive/{package_name}/"
            archive_response = requests.get(archive_url)
            versions = set()
            
            if archive_response.status_code == 200:
                # Extract versions from archive links
                archive_versions = re.findall(rf'{package_name}_([0-9.]+)\.tar\.gz', archive_response.text)
                versions.update(archive_versions)
            
            # Add current version if it exists
            if latest_version:
                versions.add(latest_version)
            
            # Convert versions to sorted list
            versions = sorted(list(versions))
            
            return PackageInfo(
                name=package_name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"https://cran.r-project.org/web/packages/{package_name}/index.html",
                description=description,
                latest_version=latest_version,
                license=license_info,
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None