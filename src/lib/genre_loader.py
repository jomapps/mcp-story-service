"""Load 15+ genre templates from config files with validation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, ValidationError

from ..models.genre import GenrePattern


class GenreTemplate(BaseModel):
    """Genre template definition."""
    name: str
    description: str
    conventions: Dict[str, Any]
    authenticity_rules: List[Dict[str, Any]]
    pattern_weights: Dict[str, float]
    example_elements: List[str]
    conflicting_genres: List[str] = []
    subgenres: List[str] = []
    confidence_threshold: float = 0.75


class GenreValidationResult(BaseModel):
    """Result of genre template validation."""
    template_name: str
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    missing_fields: List[str] = []
    invalid_patterns: List[str] = []


class GenreLibrary:
    """Library of loaded and validated genre templates."""
    
    def __init__(self):
        """Initialize genre library."""
        self.templates: Dict[str, GenreTemplate] = {}
        self.genre_patterns: Dict[str, GenrePattern] = {}
        self.validation_results: Dict[str, GenreValidationResult] = {}
        self.logger = logging.getLogger(__name__)
        
        # Required fields for valid genre templates
        self.required_fields = {
            "name", "description", "conventions", "authenticity_rules", 
            "pattern_weights", "example_elements"
        }
        
        # Supported genre categories
        self.supported_genres = {
            "thriller", "drama", "comedy", "action", "horror", "romance",
            "sci-fi", "fantasy", "mystery", "western", "war", "historical",
            "biographical", "documentary", "animation", "crime", "adventure"
        }
    
    def get_template(self, genre_name: str) -> Optional[GenreTemplate]:
        """Get genre template by name.
        
        Args:
            genre_name: Name of the genre
            
        Returns:
            Genre template or None if not found
        """
        return self.templates.get(genre_name.lower())
    
    def get_pattern(self, genre_name: str) -> Optional[GenrePattern]:
        """Get genre pattern by name.
        
        Args:
            genre_name: Name of the genre
            
        Returns:
            Genre pattern or None if not found
        """
        return self.genre_patterns.get(genre_name.lower())
    
    def list_available_genres(self) -> List[str]:
        """List all available genre names.
        
        Returns:
            List of genre names
        """
        return list(self.templates.keys())
    
    def get_genre_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded genres.
        
        Returns:
            Genre statistics
        """
        valid_templates = sum(1 for result in self.validation_results.values() if result.is_valid)
        
        return {
            "total_templates": len(self.templates),
            "valid_templates": valid_templates,
            "invalid_templates": len(self.templates) - valid_templates,
            "supported_genres": len(self.supported_genres),
            "loaded_genres": list(self.templates.keys()),
            "validation_summary": {
                name: result.is_valid for name, result in self.validation_results.items()
            }
        }


class GenreLoader:
    """Loads and validates genre templates from configuration files."""
    
    def __init__(self, config_dir: str = "config/genres"):
        """Initialize genre loader.
        
        Args:
            config_dir: Directory containing genre template files
        """
        self.config_dir = Path(config_dir)
        self.library = GenreLibrary()
        self.logger = logging.getLogger(__name__)
    
    async def load_all_genres(self) -> GenreLibrary:
        """Load all genre templates from config directory.
        
        Returns:
            Loaded genre library
        """
        self.logger.info(f"Loading genre templates from {self.config_dir}")
        
        if not self.config_dir.exists():
            self.logger.warning(f"Genre config directory {self.config_dir} does not exist")
            await self._create_default_templates()
        
        # Load all YAML files in the config directory
        template_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        
        if not template_files:
            self.logger.warning("No genre template files found, creating defaults")
            await self._create_default_templates()
            template_files = list(self.config_dir.glob("*.yaml"))
        
        # Load templates in parallel
        load_tasks = [self._load_template_file(file_path) for file_path in template_files]
        results = await asyncio.gather(*load_tasks, return_exceptions=True)
        
        # Process results
        loaded_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error loading {template_files[i]}: {result}")
            elif result:
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count} genre templates successfully")
        
        # Validate cross-references
        await self._validate_cross_references()
        
        return self.library
    
    async def load_specific_genres(self, genre_names: List[str]) -> GenreLibrary:
        """Load specific genre templates.
        
        Args:
            genre_names: List of genre names to load
            
        Returns:
            Genre library with requested genres
        """
        self.logger.info(f"Loading specific genres: {genre_names}")
        
        load_tasks = []
        for genre_name in genre_names:
            file_path = self.config_dir / f"{genre_name.lower()}.yaml"
            if file_path.exists():
                load_tasks.append(self._load_template_file(file_path))
            else:
                self.logger.warning(f"Genre template file not found: {file_path}")
        
        if load_tasks:
            await asyncio.gather(*load_tasks, return_exceptions=True)
        
        return self.library
    
    async def validate_genre_template(self, template_data: Dict[str, Any]) -> GenreValidationResult:
        """Validate a genre template.
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Validation result
        """
        template_name = template_data.get("name", "unknown")
        result = GenreValidationResult(
            template_name=template_name,
            is_valid=True
        )
        
        try:
            # Check required fields
            missing_fields = []
            for field in self.library.required_fields:
                if field not in template_data:
                    missing_fields.append(field)
            
            result.missing_fields = missing_fields
            
            if missing_fields:
                result.errors.append(f"Missing required fields: {', '.join(missing_fields)}")
                result.is_valid = False
            
            # Validate template structure
            try:
                template = GenreTemplate(**template_data)
                
                # Additional validations
                await self._validate_template_content(template, result)
                
            except ValidationError as e:
                result.errors.append(f"Template validation error: {str(e)}")
                result.is_valid = False
            
        except Exception as e:
            result.errors.append(f"Unexpected validation error: {str(e)}")
            result.is_valid = False
        
        return result
    
    async def _load_template_file(self, file_path: Path) -> bool:
        """Load a single template file.
        
        Args:
            file_path: Path to template file
            
        Returns:
            True if loaded successfully
        """
        try:
            self.logger.debug(f"Loading template file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            if not template_data:
                self.logger.warning(f"Empty template file: {file_path}")
                return False
            
            # Validate template
            validation_result = await self.validate_genre_template(template_data)
            
            # Store validation result
            template_name = template_data.get("name", file_path.stem).lower()
            self.library.validation_results[template_name] = validation_result
            
            if validation_result.is_valid:
                # Create and store template
                template = GenreTemplate(**template_data)
                self.library.templates[template_name] = template
                
                # Create genre pattern
                genre_pattern = await self._create_genre_pattern(template)
                self.library.genre_patterns[template_name] = genre_pattern
                
                self.logger.debug(f"Successfully loaded genre template: {template_name}")
                return True
            else:
                self.logger.error(f"Invalid template {template_name}: {validation_result.errors}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading template file {file_path}: {e}")
            return False
    
    async def _validate_template_content(
        self,
        template: GenreTemplate,
        result: GenreValidationResult
    ):
        """Validate template content for consistency and completeness.
        
        Args:
            template: Template to validate
            result: Validation result to update
        """
        # Validate conventions structure
        if not isinstance(template.conventions, dict):
            result.errors.append("Conventions must be a dictionary")
            result.is_valid = False
        
        # Validate authenticity rules
        for i, rule in enumerate(template.authenticity_rules):
            if not isinstance(rule, dict):
                result.errors.append(f"Authenticity rule {i} must be a dictionary")
                result.is_valid = False
                continue
            
            if "pattern" not in rule:
                result.warnings.append(f"Authenticity rule {i} missing 'pattern' field")
            
            if "weight" not in rule:
                rule["weight"] = 1.0  # Default weight
                result.warnings.append(f"Authenticity rule {i} missing 'weight', using default 1.0")
        
        # Validate pattern weights
        if not isinstance(template.pattern_weights, dict):
            result.errors.append("Pattern weights must be a dictionary")
            result.is_valid = False
        else:
            for pattern, weight in template.pattern_weights.items():
                if not isinstance(weight, (int, float)) or weight < 0:
                    result.errors.append(f"Invalid weight for pattern '{pattern}': {weight}")
                    result.is_valid = False
        
        # Validate confidence threshold
        if not (0.0 <= template.confidence_threshold <= 1.0):
            result.errors.append(f"Confidence threshold must be between 0.0 and 1.0, got {template.confidence_threshold}")
            result.is_valid = False
        
        # Check if genre is in supported list
        if template.name.lower() not in self.library.supported_genres:
            result.warnings.append(f"Genre '{template.name}' is not in supported genres list")
    
    async def _create_genre_pattern(self, template: GenreTemplate) -> GenrePattern:
        """Create genre pattern from template.
        
        Args:
            template: Genre template
            
        Returns:
            Genre pattern
        """
        # Extract patterns from template
        patterns = {}
        
        # Structure patterns
        if "structure" in template.conventions:
            patterns["structure"] = template.conventions["structure"]
        
        # Character patterns
        if "characters" in template.conventions:
            patterns["characters"] = template.conventions["characters"]
        
        # Theme patterns
        if "themes" in template.conventions:
            patterns["themes"] = template.conventions["themes"]
        
        # Setting patterns
        if "settings" in template.conventions:
            patterns["settings"] = template.conventions["settings"]
        
        return GenrePattern(
            genre=template.name,
            patterns=patterns,
            authenticity_rules=template.authenticity_rules,
            confidence_threshold=template.confidence_threshold,
            metadata={
                "template_source": "config_file",
                "pattern_weights": template.pattern_weights,
                "example_elements": template.example_elements,
                "conflicting_genres": template.conflicting_genres,
                "subgenres": template.subgenres
            }
        )
    
    async def _validate_cross_references(self):
        """Validate cross-references between genre templates."""
        self.logger.debug("Validating genre template cross-references")
        
        for template_name, template in self.library.templates.items():
            validation_result = self.library.validation_results[template_name]
            
            # Check conflicting genres
            for conflicting_genre in template.conflicting_genres:
                if conflicting_genre.lower() not in self.library.templates:
                    validation_result.warnings.append(
                        f"Conflicting genre '{conflicting_genre}' not found in loaded templates"
                    )
            
            # Check subgenres
            for subgenre in template.subgenres:
                if subgenre.lower() not in self.library.templates:
                    validation_result.warnings.append(
                        f"Subgenre '{subgenre}' not found in loaded templates"
                    )
    
    async def _create_default_templates(self):
        """Create default genre templates if none exist."""
        self.logger.info("Creating default genre templates")
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        default_templates = {
            "thriller": {
                "name": "Thriller",
                "description": "High-tension narratives with suspense and danger",
                "conventions": {
                    "structure": {
                        "inciting_incident": "Early threat or danger",
                        "rising_action": "Escalating tension and obstacles",
                        "climax": "Confrontation with primary threat",
                        "resolution": "Threat resolved or overcome"
                    },
                    "characters": {
                        "protagonist": "Ordinary person in extraordinary circumstances",
                        "antagonist": "Threatening force or villain",
                        "allies": "Limited support network"
                    },
                    "themes": ["survival", "justice", "paranoia", "trust"],
                    "settings": ["urban_environments", "isolated_locations", "time_pressure"]
                },
                "authenticity_rules": [
                    {"pattern": "constant_tension", "weight": 0.8, "description": "Maintain high tension throughout"},
                    {"pattern": "ticking_clock", "weight": 0.6, "description": "Time pressure element"},
                    {"pattern": "cat_and_mouse", "weight": 0.7, "description": "Pursuit dynamic"}
                ],
                "pattern_weights": {
                    "tension_escalation": 0.9,
                    "suspense_elements": 0.8,
                    "danger_indicators": 0.7,
                    "time_pressure": 0.6
                },
                "example_elements": [
                    "Chase scenes", "Hidden threats", "Deadline pressure", 
                    "Paranoid atmosphere", "Limited escape options"
                ],
                "conflicting_genres": ["comedy", "romance"],
                "subgenres": ["psychological_thriller", "action_thriller", "techno_thriller"],
                "confidence_threshold": 0.75
            },
            "drama": {
                "name": "Drama",
                "description": "Character-driven narratives focusing on emotional conflict",
                "conventions": {
                    "structure": {
                        "setup": "Character introduction and normal world",
                        "inciting_incident": "Emotional or personal crisis",
                        "development": "Character growth through conflict",
                        "climax": "Emotional confrontation or realization",
                        "resolution": "Character transformation or acceptance"
                    },
                    "characters": {
                        "protagonist": "Flawed character seeking growth",
                        "supporting_characters": "Complex relationships",
                        "antagonist": "Often internal conflict or circumstances"
                    },
                    "themes": ["family", "love", "loss", "identity", "redemption"],
                    "settings": ["realistic_contemporary", "family_homes", "workplace"]
                },
                "authenticity_rules": [
                    {"pattern": "emotional_depth", "weight": 0.9, "description": "Deep emotional exploration"},
                    {"pattern": "character_development", "weight": 0.8, "description": "Significant character growth"},
                    {"pattern": "realistic_dialogue", "weight": 0.7, "description": "Natural conversation"}
                ],
                "pattern_weights": {
                    "emotional_moments": 0.9,
                    "character_relationships": 0.8,
                    "internal_conflict": 0.7,
                    "realistic_situations": 0.6
                },
                "example_elements": [
                    "Family conflicts", "Personal growth", "Emotional revelations",
                    "Relationship dynamics", "Life transitions"
                ],
                "conflicting_genres": ["action", "horror"],
                "subgenres": ["family_drama", "romantic_drama", "medical_drama"],
                "confidence_threshold": 0.75
            },
            "comedy": {
                "name": "Comedy",
                "description": "Humorous narratives designed to entertain and amuse",
                "conventions": {
                    "structure": {
                        "setup": "Establish comedic premise",
                        "complications": "Escalating misunderstandings",
                        "climax": "Peak of comedic chaos",
                        "resolution": "Humorous resolution"
                    },
                    "characters": {
                        "protagonist": "Likeable but flawed comic hero",
                        "supporting_cast": "Ensemble of quirky characters",
                        "straight_man": "Character who reacts to absurdity"
                    },
                    "themes": ["absurdity", "misunderstanding", "irony", "timing"],
                    "settings": ["everyday_situations", "workplace", "social_gatherings"]
                },
                "authenticity_rules": [
                    {"pattern": "humor_timing", "weight": 0.8, "description": "Well-timed comedic moments"},
                    {"pattern": "comedic_characters", "weight": 0.7, "description": "Funny character interactions"},
                    {"pattern": "situational_comedy", "weight": 0.6, "description": "Amusing situations"}
                ],
                "pattern_weights": {
                    "humor_elements": 0.9,
                    "comedic_timing": 0.8,
                    "character_quirks": 0.7,
                    "amusing_situations": 0.6
                },
                "example_elements": [
                    "Witty dialogue", "Physical comedy", "Misunderstandings",
                    "Character quirks", "Ironic situations"
                ],
                "conflicting_genres": ["horror", "thriller"],
                "subgenres": ["romantic_comedy", "dark_comedy", "slapstick"],
                "confidence_threshold": 0.75
            }
        }
        
        # Create template files
        for genre_name, template_data in default_templates.items():
            file_path = self.config_dir / f"{genre_name}.yaml"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, indent=2)
            
            self.logger.debug(f"Created default template: {file_path}")


# Global genre loader instance
genre_loader = GenreLoader()


async def load_genre_library(config_dir: Optional[str] = None) -> GenreLibrary:
    """Load genre library from configuration directory.
    
    Args:
        config_dir: Optional config directory path
        
    Returns:
        Loaded genre library
    """
    if config_dir:
        loader = GenreLoader(config_dir)
    else:
        loader = genre_loader
    
    return await loader.load_all_genres()


async def get_genre_template(genre_name: str) -> Optional[GenreTemplate]:
    """Get a specific genre template.
    
    Args:
        genre_name: Name of the genre
        
    Returns:
        Genre template or None if not found
    """
    if not genre_loader.library.templates:
        await genre_loader.load_all_genres()
    
    return genre_loader.library.get_template(genre_name)


async def validate_genre_config_directory(config_dir: str) -> Dict[str, Any]:
    """Validate a genre configuration directory.
    
    Args:
        config_dir: Directory to validate
        
    Returns:
        Validation summary
    """
    loader = GenreLoader(config_dir)
    library = await loader.load_all_genres()
    
    return {
        "config_directory": config_dir,
        "validation_summary": library.get_genre_stats(),
        "detailed_results": {
            name: result.dict() for name, result in library.validation_results.items()
        }
    }