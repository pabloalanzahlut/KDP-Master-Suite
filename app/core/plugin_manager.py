# -*- coding: utf-8 -*-
"""
UI Plugin Architecture for KDP Master Suite
Allows extensions to register tabs, menu items, and hooks.
"""

import os
import sys
import importlib
import importlib.util
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("KDP_MASTER")

class BasePlugin:
    """Base class for all UI plugins."""
    name = "Base Plugin"
    version = "1.0"
    min_app_version = "1.0"
    
    def __init__(self, context):
        self.context = context
        self._loaded = False
        
    def on_load(self):
        """Called when plugin is loaded. Use to register UI elements."""
        self._loaded = True
        
    def on_unload(self):
        """Called when plugin is unloaded. Clean up resources here."""
        self._loaded = False

class PluginManager:
    """
    Manages loading, lifecycle, and registry of UI plugins.
    """
    def __init__(self, app_root):
        self.root = app_root
        self.plugins: Dict[str, BasePlugin] = {}
        self._modules: Dict[str, Any] = {}
        self.plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        
        # Ensure plugins dir exists
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
    def discover_plugins(self):
        """Scans plugins/ directory for python files or packages."""
        discovered = []
        if not os.path.exists(self.plugin_dir):
            return discovered
            
        for item in os.listdir(self.plugin_dir):
            full_path = os.path.join(self.plugin_dir, item)
            
            # Simple single file plugin
            if os.path.isfile(full_path) and item.endswith(".py") and not item.startswith("_"):
                discovered.append(full_path)
            # Package plugin (folder with __init__.py)
            elif os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "__init__.py")):
                discovered.append(full_path)
                
        return discovered

    def load_plugins(self, context):
        """Loads all discovered plugins depending on context."""
        plugin_paths = self.discover_plugins()
        for path in plugin_paths:
            try:
                self._load_single_plugin(path, context)
            except Exception as e:
                logger.error(f"Failed to load plugin from {path}: {e}")

    def _load_single_plugin(self, path, context):
        name = os.path.basename(path).replace(".py", "")
        
        # Version check: ensure plugin is compatible
        spec = importlib.util.spec_from_file_location(
            name, path if os.path.isfile(path) else os.path.join(path, "__init__.py")
        )
        if spec is None or spec.loader is None:
            logger.error(f"Cannot load spec for plugin: {name}")
            return
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check for Plugin class
        if not hasattr(module, "Plugin"):
            logger.warning(f"Plugin {name} has no 'Plugin' class, skipping")
            return
        
        plugin_cls = module.Plugin
        if not (isinstance(plugin_cls, type) and issubclass(plugin_cls, BasePlugin)):
            logger.error(f"Plugin {name}: 'Plugin' is not a subclass of BasePlugin")
            return
        
        # Version compatibility check
        instance = plugin_cls.__new__(plugin_cls)
        app_version = getattr(self.root, 'app_version', '1.0')
        min_version = getattr(instance, 'min_app_version', '1.0')
        
        if not self._version_compatible(app_version, min_version):
            logger.warning(
                f"Plugin {name} requires app >= {min_version}, "
                f"current is {app_version}. Skipping."
            )
            return
        
        # Instantiate and load
        plugin_instance = plugin_cls(context)
        try:
            plugin_instance.on_load()
        except Exception as e:
            logger.error(f"Error during on_load for plugin {name}: {e}")
            return
        
        self.plugins[name] = plugin_instance
        self._modules[name] = module
        logger.info(f"Plugin loaded: {plugin_instance.name} v{plugin_instance.version}")

    def unload_plugin(self, name: str) -> bool:
        """Unload a single plugin and clean up its resources."""
        if name not in self.plugins:
            return False
        
        plugin = self.plugins[name]
        try:
            plugin.on_unload()
        except Exception as e:
            logger.error(f"Error during on_unload for plugin {name}: {e}")
        
        # Remove module from sys.modules to allow clean reload
        if name in self._modules:
            module = self._modules[name]
            module_name = getattr(module, '__name__', None)
            if module_name and module_name in sys.modules:
                del sys.modules[module_name]
            del self._modules[name]
        
        del self.plugins[name]
        logger.info(f"Plugin unloaded: {name}")
        return True

    def unload_all_plugins(self):
        """Unload all plugins in reverse order."""
        for name in list(self.plugins.keys()):
            self.unload_plugin(name)

    def _version_compatible(self, app_version: str, min_version: str) -> bool:
        """Simple semantic version comparison."""
        try:
            app_parts = [int(x) for x in app_version.split('.')[:2]]
            min_parts = [int(x) for x in min_version.split('.')[:2]]
            # Pad with zeros if needed
            while len(app_parts) < 2:
                app_parts.append(0)
            while len(min_parts) < 2:
                min_parts.append(0)
            return app_parts >= min_parts
        except (ValueError, AttributeError):
            return True

    def register_tab(self, notebook, title, content_frame):
        """Helper for plugins to add a tab."""
        notebook.add(content_frame, text=f" {title} ")

    def register_menu_action(self, menu, label, command):
        """Helper for plugins to add menu item."""
        menu.add_command(label=label, command=command)
