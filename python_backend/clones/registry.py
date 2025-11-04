"""
Clone Registry - Auto-discovery and instantiation system.
Automatically finds and registers all expert clones.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Type
import importlib
import inspect
import pkgutil
from pathlib import Path

from .base import ExpertCloneBase


class CloneRegistry:
    """
    Singleton registry for all expert cognitive clones.
    
    Automatically discovers and instantiates clones from python_backend/clones/ directory.
    """
    
    _instance: Optional[CloneRegistry] = None
    _clones: Dict[str, ExpertCloneBase] = {}
    _clone_classes: Dict[str, Type[ExpertCloneBase]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._clones:
            self._discover_clones()
    
    def _discover_clones(self) -> None:
        """
        Auto-discover all clone classes in python_backend/clones/ directory.
        Looks for classes that inherit from ExpertCloneBase.
        """
        # Get path to clones directory
        clones_dir = Path(__file__).parent
        
        # Import all Python modules in clones directory
        for module_info in pkgutil.iter_modules([str(clones_dir)]):
            if module_info.name in ['base', 'registry', '__init__']:
                continue
            
            try:
                # Import module (using relative import from clones package)
                module = importlib.import_module(f'clones.{module_info.name}')
                
                # Find all classes that inherit from ExpertCloneBase
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, ExpertCloneBase) and 
                        obj is not ExpertCloneBase and
                        obj.__module__ == module.__name__):
                        
                        # Instantiate clone
                        try:
                            clone_instance = obj()
                            clone_name = clone_instance.name
                            
                            # Validate clone
                            is_valid, errors = clone_instance.validate()
                            if not is_valid:
                                print(f"[CloneRegistry] Warning: {clone_name} has validation errors:")
                                for error in errors:
                                    print(f"  - {error}")
                            
                            # Register clone
                            self._clones[clone_name] = clone_instance
                            self._clone_classes[clone_name] = obj
                            
                            print(f"[CloneRegistry] Registered clone: {clone_name} ({len(clone_instance.story_banks)} stories)")
                        
                        except Exception as e:
                            print(f"[CloneRegistry] Error instantiating {name}: {e}")
            
            except Exception as e:
                print(f"[CloneRegistry] Error importing {module_info.name}: {e}")
    
    def get_clone(self, name: str) -> Optional[ExpertCloneBase]:
        """
        Get clone instance by name.
        
        Args:
            name: Expert name (e.g., "Seth Godin", "Philip Kotler")
            
        Returns:
            Clone instance or None if not found
        """
        return self._clones.get(name)
    
    def get_all_clones(self) -> Dict[str, ExpertCloneBase]:
        """
        Get all registered clones.
        
        Returns:
            Dict mapping name -> clone instance
        """
        return self._clones.copy()
    
    def list_clone_names(self) -> List[str]:
        """
        Get list of all registered clone names.
        
        Returns:
            List of expert names
        """
        return list(self._clones.keys())
    
    def get_clone_metadata(self, name: str) -> Optional[Dict]:
        """
        Get metadata for specific clone.
        
        Args:
            name: Expert name
            
        Returns:
            Metadata dict or None if not found
        """
        clone = self.get_clone(name)
        if clone:
            return clone.get_metadata()
        return None
    
    def reload_clones(self) -> None:
        """
        Force reload of all clones (useful for development).
        """
        self._clones.clear()
        self._clone_classes.clear()
        self._discover_clones()
    
    def register_clone_manually(self, clone: ExpertCloneBase) -> None:
        """
        Manually register a clone instance (for testing/development).
        
        Args:
            clone: Clone instance to register
        """
        is_valid, errors = clone.validate()
        if not is_valid:
            print(f"[CloneRegistry] Warning: Manually registering invalid clone {clone.name}:")
            for error in errors:
                print(f"  - {error}")
        
        self._clones[clone.name] = clone
        self._clone_classes[clone.name] = clone.__class__
        print(f"[CloneRegistry] Manually registered: {clone.name}")
    
    def __len__(self) -> int:
        return len(self._clones)
    
    def __repr__(self) -> str:
        return f"<CloneRegistry: {len(self._clones)} clones registered>"


# Global singleton instance
clone_registry = CloneRegistry()
