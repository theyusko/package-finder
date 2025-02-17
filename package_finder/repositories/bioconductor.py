import requests
import concurrent.futures
from typing import Dict, Any, Optional, List
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
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """Search for a package across all Bioconductor versions."""
        all_versions = set()
        latest_info = None
        latest_version_number = "0.0"
        
        # Get initial package list to find correct case
        initial_packages = self._load_packages(self.versions[-1])
        
        if package_name not in initial_packages:
            correct_name = self._find_case_insensitive_match(package_name, list(initial_packages.keys()))
            if correct_name:
                package_name = correct_name
            else:
                return None
        
        # Search through all versions in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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
            description = latest_info.get('Title', '')
            
            # Try to get more detailed description
            try:
                details_url = f"https://bioconductor.org/packages/release/bioc/vignettes/{package_name}/inst/doc/README"
                readme_response = requests.get(details_url)
                readme = readme_response.text if readme_response.status_code == 200 else ''
            except requests.RequestException:
                readme = ''
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description, readme)
            
            # Sort versions properly
            available_versions = sorted(all_versions, 
                                     key=lambda x: [int(p) for p in x.split('.')] 
                                     if all(p.isdigit() for p in x.split('.')) 
                                     else [0])
            
            if available_versions:
                description = f"{description}\nAvailable from Bioconductor {available_versions[0]} to {available_versions[-1]}"
            
            return PackageInfo(
                name=package_name,
                versions=available_versions,
                repository=self.get_repository_name(),
                url=f"https://bioconductor.org/packages/release/bioc/html/{package_name}.html",
                description=description,
                latest_version=latest_version_number,
                license=latest_info.get('License'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
        
        return None