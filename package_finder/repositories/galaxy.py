import requests
from typing import Optional, List, Dict, Tuple
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class GalaxyRepository(PackageRepository):
    """Galaxy Tool Shed repository."""
    
    def __init__(self):
        self.toolshed_url = "https://toolshed.g2.bx.psu.edu/api"
        self.galaxy_url = "https://usegalaxy.org/api"
    
    def get_repository_name(self) -> str:
        return "Galaxy Tool Shed"
    
    def _fetch_tool_shed_tools(self) -> Dict[str, Dict]:
        """Fetch all tools from Tool Shed."""
        try:
            # Fetch list of all repositories
            repositories_url = f"{self.toolshed_url}/repositories"
            response = requests.get(repositories_url)
            
            if response.status_code != 200:
                print("Failed to fetch Tool Shed repositories")
                return {}
            
            repositories = response.json()
            
            # Collect tool information
            tools = {}
            for repo in repositories:
                # Extract key tool information
                tool_name = repo.get('name', '')
                if tool_name:
                    # Construct Tool Shed repository link
                    toolshed_link = f"https://toolshed.g2.bx.psu.edu/view/{repo.get('owner', '')}/{tool_name}"
                    
                    tools[tool_name] = {
                        'name': tool_name,
                        'owner': repo.get('owner', ''),
                        'description': repo.get('description', ''),
                        'homepage_url': repo.get('homepage_url', ''),
                        'toolshed_url': toolshed_link
                    }
            
            return tools
        
        except requests.RequestException as e:
            print(f"Error fetching Tool Shed tools: {e}")
            return {}
    
    def _fetch_galaxy_tools(self) -> Dict[str, Dict]:
        """Fetch all tools from main Galaxy instance."""
        try:
            # Fetch list of tools from Galaxy API
            tools_url = f"{self.galaxy_url}/tools"
            response = requests.get(tools_url)
            
            if response.status_code != 200:
                print("Failed to fetch Galaxy tools")
                return {}
            
            tools_data = response.json()
            
            # Collect tool information
            tools = {}
            for tool in tools_data:
                tool_name = tool.get('name', '')
                if tool_name:
                    tools[tool_name] = {
                        'name': tool_name,
                        'description': tool.get('description', ''),
                        'version': tool.get('version', ''),
                        'id': tool.get('id', '')
                    }
            
            return tools
        
        except requests.RequestException as e:
            print(f"Error fetching Galaxy tools: {e}")
            return {}
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """
        Compare Tool Shed and Galaxy tools.
        
        Returns PackageInfo highlighting tool presence across platforms.
        """
        # Fetch tools from both sources
        tool_shed_tools = self._fetch_tool_shed_tools()
        galaxy_tools = self._fetch_galaxy_tools()
        
        # Check package presence
        in_tool_shed = package_name in tool_shed_tools
        in_galaxy = package_name in galaxy_tools
        
        # If package not found in either
        if not (in_tool_shed or in_galaxy):
            return None
        
        # Collect tool information
        tool_info = tool_shed_tools.get(package_name, {}) or galaxy_tools.get(package_name, {})
        
        # Determine threading support
        description = tool_info.get('description', '')
        has_threading, thread_flags = find_thread_flags(description)
        
        # Construct versions
        versions = []
        if in_galaxy:
            versions.append(galaxy_tools[package_name].get('version', 'unknown'))
        
        # Construct URLs
        homepage_url = tool_info.get('homepage_url', '')
        toolshed_url = tool_shed_tools.get(package_name, {}).get('toolshed_url', '')
        
        # Combine URLs if both exist
        url = homepage_url
        if toolshed_url and homepage_url:
            url = f"{homepage_url}\n{toolshed_url}"
        elif toolshed_url:
            url = toolshed_url
        
        return PackageInfo(
            name=package_name,
            versions=versions,
            repository=f"Galaxy ({', '.join(filter(bool, ['Tool Shed' if in_tool_shed else '', 'Galaxy Tools' if in_galaxy else '']))})",
            url=url,
            description=description,
            latest_version=versions[0] if versions else None,
            license=None,
            thread_support=has_threading,
            thread_flags=thread_flags
        )