import requests
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple
from bs4 import BeautifulSoup
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class BioconductorRepository(PackageRepository):
    """Bioconductor package repository supporting multiple versions."""
    
    def __init__(self):
        # Calculate all Bioconductor versions from 2005 to 2025
        self.versions = self._calculate_bioc_versions()
        self._packages_cache: Dict[str, Dict[str, Any]] = {}
    
    def _calculate_bioc_versions(self) -> List[str]:
        """Calculate all Bioconductor versions from 2005 to present."""
        versions = []
        
        # Starting with Bioconductor 1.6 (Spring 2005)
        major_version = 1
        minor_version = 6
        
        # Generate versions up to present
        for year in range(2005, 2026):
            # Spring release (April)
            versions.append(f"{major_version}.{minor_version}")
            minor_version += 1
            
            # Fall release (October)
            versions.append(f"{major_version}.{minor_version}")
            minor_version += 1
            
            # Increment major version if needed
            if minor_version > 9:
                major_version += 1
                minor_version = 0
        
        return versions
    
    def get_repository_name(self) -> str:
        return "Bioconductor"
    
    def _load_packages(self, version: str) -> Dict[str, Any]:
        """Load and cache package information for a specific version."""
        if version not in self._packages_cache:
            try:
                urls = [
                    f"https://bioconductor.org/packages/release/bioc/VIEWS",  # Try current release first
                    f"https://bioconductor.org/packages/{version}/bioc/src/contrib/PACKAGES",  # Then version-specific
                    f"https://bioconductor.org/packages/json/{version}/bioc/packages.json",
                    f"https://bioconductor.org/packages/{version}/bioc/"
                ]
                
                for url in urls:
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                        if url.endswith('.json'):
                            self._packages_cache[version] = response.json()
                            break
                        elif url.endswith('VIEWS') or url.endswith('PACKAGES'):
                            packages = {}
                            current_package = {}
                            for line in response.text.split('\n'):
                                if line.startswith('Package:'):
                                    if current_package and 'Package' in current_package:
                                        packages[current_package['Package']] = current_package
                                    current_package = {'Package': line.split(': ')[1].strip()}
                                elif ': ' in line:
                                    key, value = line.split(': ', 1)
                                    current_package[key.strip()] = value.strip()
                            if current_package and 'Package' in current_package:
                                packages[current_package['Package']] = current_package
                            self._packages_cache[version] = packages
                            break
                        else:
                            packages = {}
                            for line in response.text.split('\n'):
                                if '<td><a href="html/' in line and 'package=' in line:
                                    pkg_name = line.split('package=')[1].split('"')[0]
                                    packages[pkg_name] = {'Package': pkg_name}
                            self._packages_cache[version] = packages
                            break
                    except requests.RequestException:
                        continue
                
                if version not in self._packages_cache:
                    self._packages_cache[version] = {}
                    
            except Exception as e:
                self._packages_cache[version] = {}
        
        return self._packages_cache[version]
    
    def _extract_package_info_from_html(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract package information directly from the HTML page.
        
        Args:
            url: URL of the package HTML page
            
        Returns:
            Dictionary with package information or None if not found
        """
        try:
            print(f"Attempting to extract package info from {url}")
            response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to access {url} (Status: {response.status_code})")
                return None
                
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get the package title/description
            title_element = soup.find('h1')
            description = title_element.text.strip() if title_element else ""
            
            # Get the version
            version_info = soup.find(string=lambda text: text and 'Version:' in text)
            version = ""
            if version_info:
                version_text = version_info.strip()
                version = version_text.split('Version:')[1].strip().split()[0]
            
            # Get the license
            license_info = soup.find(string=lambda text: text and 'License:' in text)
            license_text = ""
            if license_info:
                license_text = license_info.strip().split('License:')[1].strip()
            
            # Get the readme/description
            readme = ""
            details_div = soup.find('div', {'id': 'detailsPage'})
            if details_div:
                readme = details_div.get_text(strip=True)
            
            package_info = {
                'Title': description,
                'Version': version,
                'License': license_text,
                'README': readme
            }
            
            print(f"Successfully extracted info for package: {package_info}")
            return package_info
            
        except Exception as e:
            print(f"Error extracting package info from HTML: {str(e)}")
            return None
    
    def _extract_package_name_from_url(self, url: str) -> str:
        """Extract the package name from a package URL."""
        # Extract the last part of the URL after the last slash
        parts = url.rstrip('/').split('/')
        filename = parts[-1]
        
        # Remove .html extension if present
        if filename.endswith('.html'):
            filename = filename[:-5]
            
        return filename
    
    def _find_package_by_direct_url(self, package_name: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Try to find a package by directly accessing its HTML page URL.
        
        Args:
            package_name: Name of the package to search for
            
        Returns:
            Tuple of (package_info, correct_name) or (None, original_name) if not found
        """
        # Try different capitalizations
        variants = [
            package_name,
            package_name.upper(),
            package_name.lower(),
            package_name.capitalize()
        ]
        
        # Try different URL patterns
        url_patterns = [
            "https://www.bioconductor.org/packages/release/bioc/html/{}.html",
            "https://bioconductor.org/packages/release/bioc/html/{}.html",
            "https://www.bioconductor.org/packages/release/data/experiment/html/{}.html",
            "https://bioconductor.org/packages/release/data/experiment/html/{}.html",
            "https://www.bioconductor.org/packages/devel/bioc/html/{}.html"
        ]
        
        # Try each combination
        for variant in variants:
            for pattern in url_patterns:
                url = pattern.format(variant)
                
                try:
                    # Make a HEAD request first to check if the page exists
                    head_response = requests.head(url, timeout=10)
                    
                    if head_response.status_code == 200:
                        print(f"Found package page at {url}")
                        
                        # Extract information from the HTML page
                        package_info = self._extract_package_info_from_html(url)
                        
                        if package_info:
                            correct_name = self._extract_package_name_from_url(url)
                            return package_info, correct_name
                            
                except Exception as e:
                    print(f"Error checking {url}: {str(e)}")
        
        return None, package_name
    
    def _find_package_via_api(self, package_name: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Try to find a package using the Bioconductor JSON API.
        
        Args:
            package_name: Name of the package to search for
            
        Returns:
            Tuple of (package_info, correct_name) or (None, original_name) if not found
        """
        try:
            api_urls = [
                "https://bioconductor.org/packages/json/release/bioc/packages.json",
                "https://www.bioconductor.org/packages/json/release/bioc/packages.json"
            ]
            
            for api_url in api_urls:
                print(f"Trying API URL: {api_url}")
                response = requests.get(api_url, timeout=15)
                
                if response.status_code == 200:
                    packages = response.json()
                    
                    # Look for case-insensitive match
                    for pkg_name, pkg_info in packages.items():
                        if pkg_name.lower() == package_name.lower():
                            print(f"Found package {pkg_name} via API")
                            return pkg_info, pkg_name
        except Exception as e:
            print(f"Error accessing API: {str(e)}")
            
        return None, package_name
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Enhanced search for a package with improved reliability.
        Tries multiple approaches to find the package information.
        """
        print(f"Searching for Bioconductor package: {package_name}")
        
        # First try to find the package by direct URL access
        package_info, correct_name = self._find_package_by_direct_url(package_name)
        
        # If that fails, try the API
        if not package_info:
            package_info, correct_name = self._find_package_via_api(package_name)
            
        # If all approaches fail, fall back to the original search method
        if not package_info:
            try:
                # Get initial package list to find correct case
                initial_packages = self._load_packages(self.versions[-1])
                
                if package_name not in initial_packages:
                    correct_name = self._find_case_insensitive_match(package_name, list(initial_packages.keys()))
                    if correct_name:
                        package_name = correct_name
                
                # Original search logic using versions
                all_versions = set()
                latest_info = None
                latest_version_number = "0.0"
                
                # Search through all versions in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                    future_to_version = {
                        executor.submit(self._load_packages, version): version
                        for version in self.versions
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_version):
                        version = future_to_version[future]
                        try:
                            packages = future.result()
                            if package_name in packages:
                                pkg_info = packages[package_name]
                                pkg_version = pkg_info.get('Version', '0.0')
                                all_versions.add(pkg_version)
                                
                                # Keep track of the latest version information
                                if pkg_version > latest_version_number:
                                    latest_version_number = pkg_version
                                    latest_info = pkg_info
                        except Exception as e:
                            pass
                
                if latest_info:
                    package_info = latest_info
                    correct_name = package_name
            except Exception as e:
                print(f"Error in fallback search: {str(e)}")
        
        # If we still couldn't find the package
        if not package_info:
            print(f"Package {package_name} not found in Bioconductor")
            return None
            
        # Process the package information
        description = package_info.get('Title', '')
        version = package_info.get('Version', '1.0.0')
        license_info = package_info.get('License', '')
        readme = package_info.get('README', '')
        
        # Try to get more detailed description if needed
        if not readme:
            try:
                details_url = f"https://bioconductor.org/packages/release/bioc/vignettes/{correct_name}/inst/doc/README"
                readme_response = requests.get(details_url)
                readme = readme_response.text if readme_response.status_code == 200 else ''
            except requests.RequestException:
                pass
        
        # Check for threading support
        has_threading, thread_flags = find_thread_flags(description, readme)
        
        # For packages found via direct URL or API, we might only have one version
        # So create a versions list with at least the current version
        versions = [version]
        
        return PackageInfo(
            name=correct_name,
            versions=versions,
            repository=self.get_repository_name(),
            url=f"https://www.bioconductor.org/packages/release/bioc/html/{correct_name}.html",
            description=description,
            latest_version=version,
            license=license_info,
            thread_support=has_threading,
            thread_flags=thread_flags
        )