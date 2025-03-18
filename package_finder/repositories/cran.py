import requests
from typing import Optional, List, Dict, Tuple
import re
import time
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class CRANRepository(PackageRepository):
    """CRAN (Comprehensive R Archive Network) package repository."""
    
    def __init__(self, debug=False):
        self.base_url = "https://cran.r-project.org/web/packages"
        self._available_packages = None
        self.debug = debug
    
    def get_repository_name(self) -> str:
        return "CRAN"
    
    def _print_debug(self, *args, **kwargs):
        """Print debug information if debug mode is enabled."""
        if self.debug:
            print("[CRAN Debug]", *args, **kwargs)
    
    def _load_available_packages(self) -> List[str]:
        """Load and cache the list of available packages from CRAN."""
        if self._available_packages is None:
            try:
                self._print_debug("Loading package list from CRAN...")
                start_time = time.time()
                
                # First try the direct packages page
                list_response = requests.get(f"{self.base_url}/available_packages_by_name.html", timeout=10)
                
                if list_response.status_code == 200:
                    packages = re.findall(r'<a href="[^"]+/([^/]+)/index\.html"', list_response.text)
                    if not packages:
                        # Try alternative pattern
                        packages = re.findall(r'href="./([^/]+)/index\.html"', list_response.text)
                    
                    self._available_packages = packages
                    self._print_debug(f"Loaded {len(packages)} packages in {time.time() - start_time:.2f}s")
                else:
                    self._print_debug(f"Failed to load package list, status code: {list_response.status_code}")
                    self._available_packages = []
            except Exception as e:
                self._print_debug(f"Error loading packages: {e}")
                self._available_packages = []
        
        return self._available_packages
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Search for a package in CRAN.
        Uses case-insensitive matching with special handling for accented and Turkish characters.
        """

        try:
            self._print_debug(f"Searching for package: {package_name}")
            
            # First try direct access with the original name
            response = requests.get(f"{self.base_url}/{package_name}/index.html", timeout=10)
            found_direct = response.status_code == 200
            
            self._print_debug(f"Direct access result: {'Found' if found_direct else 'Not found'}")
            
            # If direct access failed, try with fuzzy matching
            if not found_direct:
                available_packages = self._load_available_packages()
                
                if not available_packages:
                    self._print_debug("No available packages list, cannot perform matching")
                    return None
                
                # Create a mapping of normalized names to original names
                normalized_package_name = self._normalize_package_name(package_name)
                self._print_debug(f"Normalized search term: '{package_name}' -> '{normalized_package_name}'")
                
                package_map = {}
                for pkg in available_packages:
                    norm_pkg = self._normalize_package_name(pkg)
                    package_map[norm_pkg] = pkg
                
                # Try to find a match in the normalized map
                matched_package = package_map.get(normalized_package_name)
                
                if matched_package:
                    self._print_debug(f"Found case-insensitive match: '{matched_package}'")
                    package_name = matched_package
                    
                    # Try to access the package page with the corrected name
                    response = requests.get(f"{self.base_url}/{matched_package}/index.html", timeout=10)
                    found_direct = response.status_code == 200
                    
                    if not found_direct:
                        self._print_debug(f"Failed to access matched package page, status: {response.status_code}")
                        return None
                else:
                    self._print_debug(f"No case-insensitive match found for '{package_name}'")
                    
                    # Debugging: show some near matches if any
                    near_matches = []
                    for norm_pkg, orig_pkg in package_map.items():
                        if normalized_package_name in norm_pkg or norm_pkg in normalized_package_name:
                            near_matches.append((orig_pkg, norm_pkg))
                    
                    if near_matches:
                        self._print_debug("Possible near matches:")
                        for orig, norm in near_matches[:5]:  # Show up to 5 near matches
                            self._print_debug(f"  {orig} (normalized: {norm})")
                    
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
            archive_response = requests.get(archive_url, timeout=10)
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
            
            result = PackageInfo(
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
            
            self._print_debug(f"Successfully found package: {package_name}")
            return result
            
        except Exception as e:
            self._print_debug(f"Error during search: {e}")
            return None