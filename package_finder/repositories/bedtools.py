import requests
from typing import Optional, Dict, List, Tuple
import re
import logging
import os
from .base import PackageRepository
from ..models import PackageInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedtoolsRepository(PackageRepository):
    """Repository for BedTools core tools and patches."""
    
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com"
        self.github_repo = "arq5x/bedtools2"
        self._versions_cache: Optional[List[str]] = None
        
        # More comprehensive version tracking
        self.common_versions = [
            '2.31.0', '2.30.0', '2.29.0', '2.28.0', '2.27.0', 
            '2.26.0', '2.25.0', '2.24.0', '2.23.0', '2.22.0',
            '2.21.0', '2.20.0', '2.19.1', '2.19.0', '2.18.0'
        ]
        
        # Potential search paths
        self.search_paths = [
            'patches/{tool_name}.patch',
            'patches/{tool_name}_v{version}.patch',
            'patches/{tool_name}/{tool_name}.patch',
            'src/utils/{tool_name}.patch',
            'src/{tool_name}.patch',
            'tools/{tool_name}.patch',
            '{tool_name}.patch',
            'src/utils/{tool_name}.cpp',
            'src/{tool_name}.cpp',
            'src/{tool_name}.h',
            'tools/{tool_name}.cpp',
            'src/utils/{tool_name}.c',
            'src/{tool_name}.c'
        ]
    
    def get_repository_name(self) -> str:
        return "Bedtools"
    
    def _check_raw_url(self, path: str, ref: str = 'master') -> Optional[str]:
        """Check if a raw URL exists and get its content."""
        try:
            url = f"{self.base_url}/{self.github_repo}/{ref}/{path}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            logger.error(f"Error checking URL {path}: {e}")
            return None
    
    def _find_tool_across_versions(self, tool_name: str) -> List[Dict]:
        """Find tool or patch across multiple versions and paths."""
        results = []
        
        # Refs to search
        refs = ['master', 'develop']
        refs.extend([f'v{v}' for v in self.common_versions])
        
        # Try different paths
        for ref in refs:
            for path_template in self.search_paths:
                # Replace placeholders
                path = path_template.format(
                    tool_name=tool_name, 
                    version=ref.lstrip('v') if ref.startswith('v') else ref
                )
                
                content = self._check_raw_url(path, ref)
                if content:
                    results.append({
                        'version': ref.lstrip('v') if ref.startswith('v') else ref,
                        'url': f"https://github.com/{self.github_repo}/blob/{ref}/{path}",
                        'content': content,
                        'path': path
                    })
        
        return results
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Search for a package in BedTools (either core tool or patch).
        
        Args:
            package_name (str): Name of the tool/patch to search for
            
        Returns:
            Optional[PackageInfo]: Package information if found, None otherwise
        """
        try:
            logger.info(f"Searching for {package_name} in Bedtools")
            tool_name = package_name.lower()
            
            # Search for tool/patch
            results = self._find_tool_across_versions(tool_name)
            
            if results:
                # Get unique versions and sort
                versions = sorted(list(set(r['version'] for r in results)))
                urls = [r['url'] for r in results]
                
                # Classify result type
                is_patch = any('patch' in r['path'] for r in results)
                
                description = (
                    f"{'Patch' if is_patch else 'Core tool'} available in "
                    f"Bedtools version{'s' if len(versions) > 1 else ''} "
                    f"{', '.join(versions)}."
                )
                
                if is_patch:
                    description += (
                        "\n\nInstallation:\n"
                        f"1. Download and extract bedtools (e.g., v{versions[0]})\n"
                        "2. Download the patch file\n"
                        "3. Apply the patch: patch -p1 < patch_file.patch\n"
                        "4. Compile bedtools: make"
                    )
                
                return PackageInfo(
                    name=package_name,
                    versions=versions,
                    repository=self.get_repository_name(),
                    url=urls[0] if urls else f"https://github.com/{self.github_repo}",
                    description=description,
                    latest_version=versions[-1] if versions else None,
                    license="MIT",
                    thread_support=False,
                    thread_flags=[]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in BedtoolsRepository: {e}")
            return None