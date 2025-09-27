import os
import yaml
from typing import Dict, Any
from src.models.genre_template import (
    GenreTemplate,
    Convention,
    GenrePacing,
    CharacterArchetype,
    AuthenticityRule,
    ConventionImportance,
)
from src.models.narrative_beat import BeatType


class GenreLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.genres: Dict[str, GenreTemplate] = self._load_genres()

    def _load_genres(self) -> Dict[str, GenreTemplate]:
        """
        Loads all genre templates from the config directory.
        """
        genres = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), "r") as f:
                    genre_data = yaml.safe_load(f)
                    genre_name = filename.replace(".yaml", "")
                    genres[genre_name] = self._create_genre_template(
                        genre_name, genre_data
                    )
        return genres

    def _create_genre_template(
        self, genre_id: str, data: Dict[str, Any]
    ) -> GenreTemplate:
        """
        Creates a GenreTemplate object from a dictionary.
        """

        def create_convention(conv_data: Dict[str, Any]) -> Convention:
            return Convention(
                name=conv_data.get("name", ""),
                description=conv_data.get("description", ""),
                importance=ConventionImportance(conv_data.get("importance", "typical")),
                examples=conv_data.get("examples", []),
                violations_allowed=conv_data.get("violations_allowed", False),
                confidence_weight=conv_data.get("confidence_weight", 1.0),
            )

        def create_convention_from_alt_format(category: str, items: list) -> Convention:
            # Handle alternative format where conventions are organized by category
            description = (
                f"{category.title()}: {', '.join(items[:3])}"  # Show first 3 items
            )
            return Convention(
                name=category.title(),
                description=description,
                importance=ConventionImportance.TYPICAL,
                examples=items,
                violations_allowed=False,
                confidence_weight=1.0,
            )

        def create_authenticity_rule(rule_data: Dict[str, Any]) -> AuthenticityRule:
            return AuthenticityRule(
                name=rule_data.get("name", ""),
                description=rule_data.get("description", ""),
                validation_logic=rule_data.get("validation_logic", ""),
            )

        # Handle different convention formats
        conventions = []
        conventions_data = data.get("conventions", [])

        if conventions_data:
            if isinstance(conventions_data, list):
                # Standard format: list of convention objects
                for conv in conventions_data:
                    if isinstance(conv, dict):
                        conventions.append(create_convention(conv))
                    elif isinstance(conv, str):
                        # Handle string items (shouldn't happen but just in case)
                        conventions.append(
                            Convention(
                                name=conv,
                                description=conv,
                                importance=ConventionImportance.OPTIONAL,
                                examples=[],
                                violations_allowed=True,
                                confidence_weight=0.5,
                            )
                        )
            elif isinstance(conventions_data, dict):
                # Alternative format: conventions organized by category
                for category, items in conventions_data.items():
                    if isinstance(items, list):
                        conventions.append(
                            create_convention_from_alt_format(category, items)
                        )

        # Handle missing pacing_profile with defaults
        pacing_data = data.get("pacing_profile", {})
        if not pacing_data:
            pacing_data = {"name": "Standard", "curve": [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]}

        return GenreTemplate(
            id=genre_id,
            name=data.get("name"),
            description=data.get("description"),
            conventions=conventions,
            pacing_profile=GenrePacing(**pacing_data),
            character_archetypes=[
                CharacterArchetype(**ca) for ca in data.get("character_archetypes", [])
            ],
            common_beats=[
                BeatType(b.lower()) if not isinstance(b, BeatType) else b
                for b in data.get("common_beats", [])
            ],
            authenticity_rules=[
                create_authenticity_rule(ar)
                for ar in data.get("authenticity_rules", [])
            ],
            subgenres=data.get("subgenres", []),
        )

    def get_genre(self, genre_name: str) -> GenreTemplate:
        """
        Returns a genre template by name.
        """
        return self.genres.get(genre_name)
