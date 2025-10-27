"""Configuration management for GitHub Assistant."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.debug("PyYAML not installed, config file support disabled")


class Config:
    """Configuration manager for GitHub Assistant."""

    DEFAULT_CONFIG = {
        "ai": {
            "model": "claude-3-5-sonnet-20241022",
            "max_diff_size": 50000,
            "max_pr_diff_size": 100000,
        },
        "git": {
            "default_branch": "main",
            "auto_stage": False,
        },
        "github": {
            "default_private": False,
            "auto_init": True,
        },
        "cli": {
            "debug": False,
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager.

        Args:
            config_path: Path to config file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path or self._find_config_file()

        if self.config_path and os.path.exists(self.config_path):
            self._load_config()

        # Override with environment variables
        self._load_from_env()

    def _find_config_file(self) -> Optional[str]:
        """Find config file in common locations."""
        possible_paths = [
            Path.cwd() / ".gh-assistant.yml",
            Path.cwd() / ".gh-assistant.yaml",
            Path.home() / ".config" / "gh-assistant" / "config.yml",
            Path.home() / ".gh-assistant.yml",
        ]

        for path in possible_paths:
            if path.exists():
                logger.debug(f"Found config file: {path}")
                return str(path)

        logger.debug("No config file found, using defaults")
        return None

    def _load_config(self):
        """Load configuration from YAML file."""
        if not HAS_YAML:
            logger.warning("PyYAML not installed, cannot load config file")
            return

        try:
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}

            # Deep merge with defaults
            self._merge_config(self.config, user_config)
            logger.info(f"Loaded configuration from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load config file: {e}")

    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            "ANTHROPIC_MODEL": ("ai", "model"),
            "GH_ASSIST_DEBUG": ("cli", "debug"),
            "GH_ASSIST_DEFAULT_BRANCH": ("git", "default_branch"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert boolean strings
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                # Convert numeric strings
                elif value.isdigit():
                    value = int(value)

                self.config[section][key] = value
                logger.debug(f"Loaded {env_var} from environment")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Config section
            key: Config key
            default: Default value if not found

        Returns:
            Configuration value
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.config.get(section, {})

    def set(self, section: str, key: str, value: Any):
        """Set configuration value (runtime only, not persisted)."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self, path: Optional[str] = None):
        """
        Save current configuration to file.

        Args:
            path: Path to save to (defaults to current config path)
        """
        if not HAS_YAML:
            logger.error("PyYAML not installed, cannot save config")
            return

        save_path = path or self.config_path
        if not save_path:
            save_path = Path.cwd() / ".gh-assistant.yml"

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")


# Global config instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None or reload:
        _config = Config()
    return _config
