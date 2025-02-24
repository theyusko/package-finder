from typing import List, Dict, Optional
import concurrent.futures
import logging
from .models import PackageInfo
from collections import defaultdict
import re

from .repositories import (
    BiocondaRepository,
    AnacondaRepository,
    PyPIRepository,
    BioconductorRepository,
    CondaForgeRepository,
    CRANRepository,
    ROpenSciRepository,
    PositRepository,
    BioLibRepository,
    GalaxyRepository,
    DockerHubRepository,
    GitHubContainerRegistryRepository,
    HomebrewRepository,
    LinuxManpagesRepository,
    BedtoolsRepository
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PackageSearcher:
    """Main class to coordinate package searches across multiple repositories."""
    
    def __init__(self, repositories=None):
        self.repositories = repositories or [
            BiocondaRepository(),
            AnacondaRepository(),
            PyPIRepository(),
            BioconductorRepository(),
            CondaForgeRepository(),
            CRANRepository(),
            ROpenSciRepository(),
            PositRepository(),
            BioLibRepository(),
            GalaxyRepository(),
            DockerHubRepository(),
            GitHubContainerRegistryRepository(),
            HomebrewRepository(),
            LinuxManpagesRepository(),
            BedtoolsRepository()
        ]
    
    def search_package(self, package_name: str) -> List[PackageInfo]:
        """Search for a single package across all repositories."""
        return self.search_packages([package_name])[package_name]
    
    def search_packages(self, package_names: List[str]) -> Dict[str, List[PackageInfo]]:
        """
        Search for multiple packages across all repositories in parallel.
        
        Args:
            package_names: List of package names to search for
            
        Returns:
            Dictionary mapping package names to lists of PackageInfo objects
        """
        # Create results dictionary
        results: Dict[str, List[PackageInfo]] = {name: [] for name in package_names}
        
        # Calculate total searches
        total_searches = len(package_names) * len(self.repositories)
        completed = 0
        
        print(f"\nSearching for {len(package_names)} packages across {len(self.repositories)} repositories...")
        
        # Store exceptions for debugging
        exceptions = []
        
        # Perform search with more detailed debugging
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, total_searches)) as executor:
            # Create futures for all package-repository combinations
            future_to_search = {
                executor.submit(self._safe_search, repo, pkg_name): (pkg_name, repo)
                for pkg_name in package_names
                for repo in self.repositories
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_search):
                pkg_name, repo = future_to_search[future]
                completed += 1
                
                try:
                    result = future.result()
                    if result:
                        # Log each result found
                        logger.debug(f"Found result for {pkg_name} in {repo.get_repository_name()}: {result}")
                        
                        # Avoid exact duplicate results
                        existing_names = {r.name.lower() for r in results[pkg_name]}
                        existing_repos = {r.repository.lower() for r in results[pkg_name]}
                        
                        # Ensure the result is not a duplicate
                        if (result.name.lower() not in existing_names or 
                            result.repository.lower() not in existing_repos):
                            results[pkg_name].append(result)
                        else:
                            logger.debug(f"Skipped duplicate result for {result.name}")
                    else:
                        logger.debug(f"No result found for {pkg_name} in {repo.get_repository_name()}")
                    
                    # Update progress
                    progress = (completed * 100) // total_searches
                    print(f"\rProgress: {progress}% ({completed}/{total_searches} searches completed)", end="")
                    
                except Exception as e:
                    logger.error(f"Error searching {repo.get_repository_name()} for {pkg_name}: {e}")
                    exceptions.append((pkg_name, repo.get_repository_name(), str(e)))
        
        print("\nSearch completed!")
        
        # Print out any exceptions for debugging
        if exceptions:
            print("\nExceptions during search:")
            for pkg, repo, err in exceptions:
                print(f"  - Package: {pkg}, Repository: {repo}, Error: {err}")
        
        # Log final results
        for pkg_name, pkg_results in results.items():
            if pkg_results:
                logger.debug(f"Final results for {pkg_name}: {[f'{r.name} ({r.repository})' for r in pkg_results]}")
            else:
                logger.debug(f"No results found for {pkg_name}")
        
        return results
    
    def _safe_search(self, repo, package_name: str) -> Optional[PackageInfo]:
        """
        Safely search a single repository with detailed error handling.
        
        Args:
            repo: Repository to search
            package_name: Name of the package to search for
        
        Returns:
            PackageInfo object if found, None otherwise
        """
        try:
            # Attempt to search the repository
            result = repo.search_package(package_name)
            
            # Log the search attempt
            if result:
                logger.debug(f"Found result in {repo.get_repository_name()}: {result.name}")
            else:
                logger.debug(f"No result found in {repo.get_repository_name()} for {package_name}")
            
            return result
        except Exception as e:
            # Log any exceptions during the search
            logger.error(f"Exception in {repo.get_repository_name()} for {package_name}: {e}")
            return None

def get_major_minor(version: str) -> str:
    """Extract major.minor from version string."""
    version = version.lower().replace('v', '')
    match = re.match(r'(\d+\.\d+)', version)
    return match.group(1) if match else version

def format_version_groups(version_groups: dict) -> str:
    """Format version groups in a concise way."""
    formatted_parts = []
    
    for major_minor in sorted(version_groups.keys()):
        versions = sorted(version_groups[major_minor])
        if len(versions) == 1 and versions[0] == major_minor:
            # Single version with no patches
            formatted_parts.append(major_minor)
        else:
            # Multiple versions or has patches
            formatted_parts.append(f"{{{', '.join(versions)}}}")
    
    return ", ".join(formatted_parts)

def print_package_info(package_info: PackageInfo) -> None:
    """Print package information in a formatted way, including concise version groups."""
    print(f"\n✅ Package '{package_info.name}' found in {package_info.repository}!")
    print(f"URL: {package_info.url}")
    
    if package_info.description:
        print(f"Description: {package_info.description}")
    else:
        print("Description: No description available")
    
    # Version information
    if package_info.versions:
        # Remove any 'latest' tag for sorting but keep it for display
        has_latest = 'latest' in package_info.versions
        versions = [v for v in package_info.versions if v != 'latest']
        
        # Sort versions
        try:
            sorted_versions = sorted(versions, 
                                   key=lambda x: [int(y) for y in x.replace('v','').replace('V','').split('.')] 
                                   if all(y.isdigit() for y in x.replace('v','').replace('V','').split('.')) 
                                   else [0])
        except:
            sorted_versions = sorted(versions)
        
        # Get counts and groups
        version_groups = defaultdict(list)
        total_versions = len(versions)
        
        for version in versions:
            major_minor = get_major_minor(version)
            version_groups[major_minor].append(version)
        
        major_minor_count = len(version_groups)
        
        # Print version information
        print(f"Latest version: {sorted_versions[-1] if sorted_versions else 'unknown'}")
        print(f"Version counts: {major_minor_count} major.minor, {total_versions} total")
        
        # Print concise version groups
        versions_display = format_version_groups(version_groups)
        if has_latest:
            versions_display += ", latest"
        print(f"All versions grouped by Major.Minor: {versions_display}")
    else:
        print("Versions: No version information available")
    
    # License information
    if package_info.license:
        print(f"License: {package_info.license}")
    else:
        print("License: Not specified")
    
    # Threading information
    if package_info.thread_support:
        print("Threading: Supported")
        if package_info.thread_flags:
            print("Thread flags:", ', '.join(package_info.thread_flags))
    else:
        print("Threading: No explicit support found")

def print_search_results(results: Dict[str, List[PackageInfo]], show_versions: bool = False) -> None:
    """Print results for multiple package searches."""
    for package_name, package_results in results.items():
        if package_results:
            print(f"\nFound '{package_name}' in {len(package_results)} repositories:")
            for result in package_results:
                print_package_info(result)
        else:
            print(f"\n❌ Package '{package_name}' was not found in any repository.")