from abc import ABC, abstractmethod
from typing import Optional, List
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
    
    def _find_case_insensitive_match(self, package_name: str, available_packages: List[str]) -> Optional[str]:
        """
        Find a case-insensitive match for the package name.
        Returns the correct case if found, None otherwise.
        """
        package_lower = package_name.lower()
        package_map = {pkg.lower(): pkg for pkg in available_packages}
        return package_map.get(package_lower)