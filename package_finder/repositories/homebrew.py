import requests
from typing import Optional, Dict, Any
import json
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class HomebrewRepository(PackageRepository):
    """Homebrew/Linuxbrew-core repository."""
    
    def __init__(self):
        self.base_url = "https://formulae.brew.sh/api"
        self._formula_cache: Dict[str, Any] = {}
        
    def get_repository_name(self) -> str:
        return "Homebrew"
    
    def _load_formulas(self) -> None:
        """Load and cache formula data."""
        if not self._formula_cache:
            try:
                response = requests.get(f"{self.base_url}/formula.json")
                if response.status_code == 200:
                    formulas = response.json()
                    self._formula_cache = {
                        formula['name'].lower(): formula for formula in formulas
                    }
            except requests.RequestException:
                self._formula_cache = {}
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            self._load_formulas()
            
            # Try exact match first
            formula = self._formula_cache.get(package_name.lower())
            
            if not formula:
                # Try case-insensitive search
                matches = [
                    f for name, f in self._formula_cache.items()
                    if package_name.lower() in name
                ]
                if matches:
                    formula = matches[0]
            
            if not formula:
                return None
            
            name = formula['name']
            
            # Get full formula information
            formula_url = f"{self.base_url}/formula/{name}.json"
            response = requests.get(formula_url)
            if response.status_code == 200:
                formula_data = response.json()
            else:
                formula_data = formula
            
            # Get versions
            versions = []
            if 'versions' in formula_data:
                if 'stable' in formula_data['versions']:
                    versions.append(formula_data['versions']['stable'])
                if 'head' in formula_data['versions']:
                    versions.append('head')
            
            description = formula_data.get('desc', '')
            
            # Try to get more detailed description from the repository
            try:
                repo_url = f"https://raw.githubusercontent.com/Homebrew/homebrew-core/master/Formula/{name}.rb"
                repo_response = requests.get(repo_url)
                if repo_response.status_code == 200:
                    formula_content = repo_response.text
                    # Extract detailed description and comments
                    description_lines = []
                    for line in formula_content.split('\n'):
                        if line.strip().startswith('#'):
                            description_lines.append(line.strip('# '))
                        elif not line.strip():
                            break
                    if description_lines:
                        description = '\n'.join(description_lines)
            except requests.RequestException:
                pass
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description)
            
            return PackageInfo(
                name=name,
                versions=versions,
                repository=self.get_repository_name(),
                url=f"https://formulae.brew.sh/formula/{name}",
                description=description,
                latest_version=versions[0] if versions else None,
                license=formula_data.get('license'),
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException:
            return None