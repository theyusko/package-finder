import requests
from typing import Optional, List
from .base import PackageRepository
from .utils import find_thread_flags
from ..models import PackageInfo

class DockerHubRepository(PackageRepository):
    """Docker Hub repository."""
    
    def __init__(self):
        self.base_url = "https://hub.docker.com/v2"
    
    def get_repository_name(self) -> str:
        return "Docker Hub"
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Search for the package
            search_url = f"{self.base_url}/search/repositories"
            params = {
                'query': package_name,
                'page_size': 25
            }
            response = requests.get(search_url, params=params)
            
            if response.status_code != 200:
                return None
                
            results = response.json().get('results', [])
            if not results:
                return None
            
            # Find best match
            # First try official images
            exact_matches = [r for r in results 
                           if r.get('slug', '').lower() == f"library/{package_name}".lower()]
            
            # Then try any exact matches
            if not exact_matches:
                exact_matches = [r for r in results 
                               if r.get('slug', '').lower().endswith(f"/{package_name}".lower())]
            
            # If no exact matches, take the first result
            best_match = exact_matches[0] if exact_matches else results[0]
            
            # Extract the full repository name
            repo_name = best_match.get('slug', '')
            if not repo_name:
                # Try alternative fields
                repo_name = best_match.get('repo_name', '')
                if not repo_name:
                    namespace = best_match.get('namespace', 'library')
                    name = best_match.get('name', package_name)
                    repo_name = f"{namespace}/{name}"
            
            # Get repository tags
            tags_url = f"{self.base_url}/repositories/{repo_name}/tags"
            tags_response = requests.get(tags_url)
            
            versions = []
            if tags_response.status_code == 200:
                tags_data = tags_response.json()
                versions = [tag['name'] for tag in tags_data.get('results', [])]
                # Filter out 'latest' tag and sort
                versions = sorted([v for v in versions if v != 'latest'])
                if 'latest' in [tag['name'] for tag in tags_data.get('results', [])]:
                    versions.append('latest')
            
            description = best_match.get('description', '')
            short_description = best_match.get('short_description', '')
            if short_description and short_description != description:
                description = f"{short_description}\n{description}"
            
            # Clean up repository name for display
            display_name = repo_name.split('/')[-1]
            
            # Check for threading support
            has_threading, thread_flags = find_thread_flags(description)
            
            return PackageInfo(
                name=display_name,
                versions=versions,
                repository=f"{self.get_repository_name()} ({repo_name})",
                url=f"https://hub.docker.com/r/{repo_name}",
                description=description,
                latest_version='latest' if 'latest' in versions else (versions[-1] if versions else None),
                license=None,
                thread_support=has_threading,
                thread_flags=thread_flags
            )
            
        except requests.RequestException as e:
            print(f"Docker Hub connection error: {e}")
            return None
        except Exception as e:
            print(f"Error processing Docker Hub response: {e}")
            return None