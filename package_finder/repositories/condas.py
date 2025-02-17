from .base_conda import BaseAnacondaRepository

class AnacondaRepository(BaseAnacondaRepository):
    """Anaconda package repository."""
    
    def __init__(self):
        super().__init__(channel="anaconda")
    
    def get_repository_name(self) -> str:
        return "Anaconda"

class BiocondaRepository(BaseAnacondaRepository):
    """Bioconda package repository."""
    
    def __init__(self):
        super().__init__(channel="bioconda")
    
    def get_repository_name(self) -> str:
        return "Bioconda"
    
class CondaForgeRepository(BaseAnacondaRepository):
    """Bioconda package repository."""
    
    def __init__(self):
        super().__init__(channel="conda-forge")
    
    def get_repository_name(self) -> str:
        return "Conda-forge"