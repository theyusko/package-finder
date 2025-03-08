import requests
import re
from typing import Optional, Dict, Any, List, Set
from .base import PackageRepository
from .models import PackageInfo

def find_thread_flags(description: str, readme: Optional[str] = None) -> tuple[bool, List[str]]:
    """
    Analyze package description and readme for threading support.
    Returns (has_threading, thread_flags).
    """
    thread_keywords = {
        '-t', '--threads', '-threads', '--thread', '-thread',
        '--nthreads', '-nthreads', '--num-threads', '-n'
    }
    
    # Common patterns for thread-related flags
    thread_patterns = [
        r'-t\s*\d+',
        r'--threads\s*\d+',
        r'--thread\s*\d+',
        r'-n\s*\d+',
        r'--num-threads\s*\d+'
    ]
    
    text_to_search = (description or '').lower() + ' ' + (readme or '').lower()
    
    # Look for thread-related keywords
    found_flags: Set[str] = set()
    
    # Check for exact matches of thread flags
    for keyword in thread_keywords:
        if keyword in text_to_search:
            found_flags.add(keyword)
    
    # Check for pattern matches
    for pattern in thread_patterns:
        if re.search(pattern, text_to_search):
            matches = re.findall(pattern, text_to_search)
            found_flags.update(matches)
    
    # Also look for general threading indicators
    has_threading = any(word in text_to_search for word in 
                       ['parallel', 'multithread', 'multi-thread', 'multi thread', 
                        'concurrent', 'cpu cores', 'processor cores'])
    
    return has_threading or len(found_flags) > 0, list(found_flags)

class BiocondaRepository(PackageRepository):
    """Bioconda package repository."""
    
    def __init__(self):
        self.base_url = "https://api.anaconda.org/package/bioconda"
    
    def get_repository_name(self) -> str:
        return "Bioconda"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # First try exact match
            response = requests.get(f"{self.base_url}/{package_name}")
            if response.status_code == 200:
                data = response.json()
            else:
                # If exact match fails, get package list and try case-insensitive match
                list_response = requests.get("https://api.anaconda.org/package/bioconda/")
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

            # Get license information
            license_info = data.get('license', None)
            
            # Get description and readme
            description = data.get('summary', '')
            readme = data.get('readme', '')
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description, readme)
            
            return PackageInfo(
                name=package_name,
                versions=data.get('versions', []),
                repository=self.get_repository_name(),
                url=f"https://anaconda.org/bioconda/{package_name}",
                description=description,
                latest_version=data.get('latest_version'),
                license=license_info,
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None
        except requests.RequestException:
            return None

class AnacondaRepository(PackageRepository):
    """Anaconda (defaults) package repository."""
    
    def __init__(self):
        self.base_url = "https://api.anaconda.org/package/anaconda"
    
    def get_repository_name(self) -> str:
        return "Anaconda"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            response = requests.get(f"{self.base_url}/{package_name}")
            if response.status_code == 200:
                data = response.json()
                
                # Get license and description
                license_info = data.get('license', None)
                description = data.get('summary', '')
                readme = data.get('readme', '')
                
                # Check for threading support
                has_threading, thread_flags = find_thread_flags(description, readme)
                
                return PackageInfo(
                    name=package_name,
                    versions=data.get('versions', []),
                    repository=self.get_repository_name(),
                    url=f"https://anaconda.org/anaconda/{package_name}",
                    description=description,
                    latest_version=data.get('latest_version'),
                    license=license_info,
                    thread_support=has_threading,
                    thread_flags=thread_flags
                )
            return None
        except requests.RequestException:
            return None

class PyPIRepository(PackageRepository):
    """PyPI package repository."""
    
    def __init__(self):
        self.base_url = "https://pypi.org/pypi"
    
    def get_repository_name(self) -> str:
        return "PyPI"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            response = requests.get(f"{self.base_url}/{package_name}/json")
            if response.status_code == 200:
                data = response.json()
                
                # Get description and readme
                description = data['info'].get('summary', '')
                readme = data['info'].get('description', '')
                
                # Check for threading support
                has_threading, thread_flags = find_thread_flags(description, readme)
                
                return PackageInfo(
                    name=package_name,
                    versions=list(data['releases'].keys()),
                    repository=self.get_repository_name(),
                    url=f"https://pypi.org/project/{package_name}",
                    description=description,
                    latest_version=data['info'].get('version'),
                    license=data['info'].get('license'),
                    thread_support=has_threading,
                    thread_flags=thread_flags
                )
            return None
        except requests.RequestException:
            return None

class BioconductorRepository(PackageRepository):
    """Bioconductor package repository supporting multiple versions."""
    
    def __init__(self):
        # Calculate all Bioconductor versions from 2005 to 2025
        # Bioconductor releases twice a year: Spring (April) and Fall (October)
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
                # Try both JSON and HTML endpoints as older versions might not have JSON
                urls = [
                    f"https://bioconductor.org/packages/{version}/bioc/packages.json",
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
                        else:
                            # For HTML endpoints, extract package information from the page
                            # This is a fallback for very old versions
                            # Basic parsing of the HTML table
                            packages = {}
                            # Simple HTML parsing - could be improved with BeautifulSoup
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
                print(f"Error loading Bioconductor {version}: {e}")
                self._packages_cache[version] = {}
        
        return self._packages_cache[version]
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """Search for a package across all Bioconductor versions."""
        all_versions = set()
        latest_info = None
        latest_version_number = "0.0"
        
        # Get initial package list to find correct case
        initial_packages = self._load_packages(self.versions[-1])  # Use latest version for initial search
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
                    print(f"Error searching Bioconductor {version}: {e}")
        
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
            
            # Find first and last appearance versions
            available_versions = sorted(all_versions, key=lambda x: [int(p) for p in x.split('.')])
            first_version = available_versions[0]
            last_version = available_versions[-1]
            
            description = f"{description}\nAvailable from Bioconductor {first_version} to {last_version}"
            
            return PackageInfo(
                name=package_name,
                versions=available_versions,
                repository=f"{self.get_repository_name()}",
                url=f"https://bioconductor.org/packages/release/bioc/html/{package_name}.html",
                description=description,
                latest_version=last_version,
                license=latest_info.get('License'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        return None