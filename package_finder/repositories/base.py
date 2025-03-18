from abc import ABC, abstractmethod
import re
from typing import Optional, List
import unicodedata
from ..models import PackageInfo

class PackageRepository(ABC):
    """Abstract base class for package repositories."""
    
    @abstractmethod
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """Search for a package in the repository."""
        pass
    
    @abstractmethod
    def get_repository_name(self) -> str:
        """Get the name of the repository."""
        pass

    def _normalize_package_name(self, package_name: str) -> str:
        """
        Normalize package name for case-insensitive comparison.
        Uses a more thorough approach for special characters.
        """
        # Convert to lowercase
        package_name = package_name.lower()
        
        # Replace Turkish characters specifically
        package_name = package_name.replace('ı', 'i')
        package_name = package_name.replace('İ', 'i') 
        package_name = package_name.replace('I', 'i')
        
        # Normalize to decomposed form and remove diacritics
        package_name = unicodedata.normalize('NFD', package_name)
        package_name = ''.join(c for c in package_name if not unicodedata.combining(c))
        
        # Remove any remaining special characters, just keep alphanumeric
        package_name = re.sub(r'[^a-z0-9]', '', package_name)
        
        return package_name
    
    
    def _find_case_insensitive_match(self, package_name: str, available_packages: List[str]) -> Optional[str]:
        """
        Find a case-insensitive match for the package name.
        Returns the correct case if found, None otherwise.
        """
        package_lower = self._normalize_package_name(package_name)

        package_map = {self._normalize_package_name(pkg): pkg for pkg in available_packages}
        return package_map.get(package_lower)
    
    