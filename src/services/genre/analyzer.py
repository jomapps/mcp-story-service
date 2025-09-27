"""GenreAnalyzer service with 75% confidence threshold pattern matching.

This service analyzes story content for genre adherence with confidence
scoring and pattern matching per FR-005.

Constitutional Compliance:
- Library-First (I): Focused genre analysis service
- Test-First (II): Tests written before implementation  
- Simplicity (III): Clear pattern matching without complexity
"""

import re
import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ...models.genre_template import GenreTemplate, GenreCategory, ConventionType, AuthenticityLevel
from ...models.content_analysis import ContentAnalysisResult, ContentQuality, ProcessingStatus


class GenreMatch:
    """Represents a genre pattern match with confidence."""
    
    def __init__(self, pattern_name: str, confidence: float, evidence: List[str]):
        self.pattern_name = pattern_name
        self.confidence = confidence
        self.evidence = evidence
        self.weight = 1.0


class GenreAnalyzer:
    """
    Service for analyzing genre patterns and validating genre adherence.
    
    Provides pattern matching, confidence scoring with 75% threshold,
    and recommendations for improving genre authenticity.
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/genres"
        self.genre_templates = {}
        self.confidence_threshold = 0.75
        self._load_genre_templates()
    
    def _load_genre_templates(self):
        """Load genre templates from configuration files."""
        try:
            config_dir = Path(self.config_path)
            if not config_dir.exists():
                # Fallback to relative path
                config_dir = Path(__file__).parent.parent.parent.parent / "config" / "genres"
            
            for yaml_file in config_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        template_data = yaml.safe_load(f)
                    
                    genre_template = GenreTemplate.load_from_yaml_config(template_data)
                    self.genre_templates[genre_template.name.lower()] = genre_template
                    
                except Exception as e:
                    print(f"Warning: Failed to load genre template {yaml_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"Warning: Failed to load genre templates from {self.config_path}: {e}")
            # Initialize with minimal built-in templates
            self._initialize_fallback_templates()
    
    def _initialize_fallback_templates(self):
        """Initialize minimal fallback templates if config loading fails."""
        # Create basic thriller template
        thriller_template = GenreTemplate(
            genre_id="thriller",
            name="thriller",
            category=GenreCategory.THRILLER,
            description="Stories designed to keep audience on edge with suspense"
        )
        self.genre_templates["thriller"] = thriller_template
        
        # Create basic romance template
        romance_template = GenreTemplate(
            genre_id="romance",
            name="romance",
            category=GenreCategory.ROMANCE,
            description="Stories centered on romantic relationships"
        )
        self.genre_templates["romance"] = romance_template

    async def apply_genre_patterns(self, story_content: str, target_genre: str,
                                 custom_patterns: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply genre patterns and validate story adherence.
        
        Args:
            story_content: Story content to analyze
            target_genre: Target genre for validation
            custom_patterns: Optional custom pattern definitions
            
        Returns:
            Genre analysis results with confidence and recommendations
        """
        try:
            # Preprocess content
            processed_content = self._preprocess_content(story_content)
            
            if not processed_content.strip():
                return self._create_empty_content_result(target_genre)
            
            # Get genre template
            genre_template = self._get_genre_template(target_genre)
            if not genre_template:
                return self._create_unsupported_genre_result(target_genre)
            
            # Analyze genre patterns
            pattern_matches = await self._analyze_patterns(processed_content, genre_template)
            
            # Calculate adherence score
            adherence_score = self._calculate_adherence_score(pattern_matches, genre_template)
            
            # Validate authenticity
            authenticity_results = genre_template.validate_authenticity({"content": processed_content})
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                pattern_matches, adherence_score, genre_template, processed_content
            )
            
            # Detect multiple genre influences
            genre_analysis = await self._analyze_genre_influences(processed_content)
            
            return {
                "genre_analysis": {
                    "target_genre": target_genre,
                    "genre_confidence": adherence_score,
                    "authenticity_results": authenticity_results,
                    "pattern_analysis": self._create_pattern_analysis(pattern_matches),
                    "genre_influences": genre_analysis,
                    "template_info": genre_template.get_genre_summary()
                },
                "pattern_matches": [self._match_to_dict(match) for match in pattern_matches],
                "adherence_score": adherence_score,
                "recommendations": recommendations,
                "metadata": {
                    "target_genre": target_genre,
                    "content_length": len(processed_content),
                    "patterns_detected": len(pattern_matches),
                    "meets_threshold": adherence_score >= self.confidence_threshold
                }
            }
            
        except Exception as e:
            return self._create_error_result(str(e), target_genre)

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for genre analysis."""
        if not content:
            return ""
        
        # Clean up formatting
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        content = content.strip()
        
        return content

    def _get_genre_template(self, genre_name: str) -> Optional[GenreTemplate]:
        """Get genre template by name."""
        genre_key = genre_name.lower().replace("-", "_").replace(" ", "_")
        
        # Direct match
        if genre_key in self.genre_templates:
            return self.genre_templates[genre_key]
        
        # Check aliases
        for template in self.genre_templates.values():
            if genre_key in [alias.lower() for alias in template.aliases]:
                return template
        
        return None

    async def _analyze_patterns(self, content: str, genre_template: GenreTemplate) -> List[GenreMatch]:
        """Analyze content for genre-specific patterns."""
        matches = []
        
        # Analyze conventions
        for convention in genre_template.conventions:
            convention_matches = self._analyze_convention(content, convention)
            matches.extend(convention_matches)
        
        # Analyze structural patterns
        for pattern in genre_template.structural_patterns:
            structure_matches = self._analyze_structural_pattern(content, pattern)
            matches.extend(structure_matches)
        
        # Analyze character archetypes
        for archetype in genre_template.character_archetypes:
            archetype_matches = self._analyze_character_archetype(content, archetype)
            matches.extend(archetype_matches)
        
        # Analyze thematic elements
        for theme in genre_template.thematic_elements:
            theme_matches = self._analyze_thematic_element(content, theme)
            matches.extend(theme_matches)
        
        return matches

    def _analyze_convention(self, content: str, convention) -> List[GenreMatch]:
        """Analyze content for specific convention patterns."""
        matches = []
        content_lower = content.lower()
        
        # Check keywords
        keyword_matches = 0
        evidence = []
        
        for keyword in convention.keywords:
            if keyword.lower() in content_lower:
                keyword_matches += 1
                evidence.append(f"Found keyword: '{keyword}'")
        
        # Check patterns
        pattern_matches = 0
        for pattern in convention.patterns:
            try:
                regex_matches = re.findall(pattern, content, re.IGNORECASE)
                if regex_matches:
                    pattern_matches += len(regex_matches)
                    evidence.append(f"Pattern match: '{pattern}' ({len(regex_matches)} occurrences)")
            except re.error:
                continue  # Skip invalid patterns
        
        # Calculate confidence
        total_indicators = len(convention.keywords) + len(convention.patterns)
        if total_indicators > 0:
            match_rate = (keyword_matches + pattern_matches) / total_indicators
            confidence = min(match_rate * convention.importance, 1.0)
            
            if confidence > 0.1:  # Only include meaningful matches
                match = GenreMatch(
                    pattern_name=f"convention_{convention.name}",
                    confidence=confidence,
                    evidence=evidence
                )
                matches.append(match)
        
        return matches

    def _analyze_structural_pattern(self, content: str, pattern) -> List[GenreMatch]:
        """Analyze content for structural patterns."""
        matches = []
        
        # Look for required beats
        beats_found = 0
        evidence = []
        
        for beat in pattern.required_beats:
            if self._find_beat_in_content(content, beat):
                beats_found += 1
                evidence.append(f"Found beat: '{beat}'")
        
        # Calculate confidence
        if pattern.required_beats:
            confidence = beats_found / len(pattern.required_beats)
            
            if confidence > 0.2:
                match = GenreMatch(
                    pattern_name=f"structure_{pattern.pattern_name}",
                    confidence=confidence,
                    evidence=evidence
                )
                matches.append(match)
        
        return matches

    def _find_beat_in_content(self, content: str, beat: str) -> bool:
        """Check if a narrative beat is present in content."""
        beat_keywords = {
            "inciting_incident": ["sudden", "unexpected", "changed", "discovered"],
            "midpoint": ["revelation", "twist", "realized", "understood"],
            "climax": ["final", "confrontation", "battle", "decisive"],
            "resolution": ["ended", "resolved", "conclusion", "victory"],
            "setup": ["introduce", "establish", "beginning", "start"],
            "call_to_adventure": ["quest", "journey", "mission", "called"],
            "mentor": ["guide", "teacher", "mentor", "wise"],
            "ordeal": ["challenge", "trial", "test", "difficult"]
        }
        
        keywords = beat_keywords.get(beat, [beat])
        content_lower = content.lower()
        
        return any(keyword in content_lower for keyword in keywords)

    def _analyze_character_archetype(self, content: str, archetype) -> List[GenreMatch]:
        """Analyze content for character archetypes."""
        matches = []
        content_lower = content.lower()
        
        # Look for archetype indicators
        trait_matches = 0
        evidence = []
        
        for trait in archetype.typical_traits:
            if trait.lower() in content_lower:
                trait_matches += 1
                evidence.append(f"Found trait: '{trait}'")
        
        for role in archetype.typical_roles:
            if role.lower() in content_lower:
                trait_matches += 1
                evidence.append(f"Found role: '{role}'")
        
        # Calculate confidence
        total_traits = len(archetype.typical_traits) + len(archetype.typical_roles)
        if total_traits > 0:
            confidence = trait_matches / total_traits
            
            if confidence > 0.1:
                match = GenreMatch(
                    pattern_name=f"archetype_{archetype.archetype_name}",
                    confidence=confidence,
                    evidence=evidence
                )
                matches.append(match)
        
        return matches

    def _analyze_thematic_element(self, content: str, theme) -> List[GenreMatch]:
        """Analyze content for thematic elements."""
        matches = []
        content_lower = content.lower()
        
        # Look for theme keywords
        keyword_matches = 0
        evidence = []
        
        for keyword in theme.keywords:
            if keyword.lower() in content_lower:
                keyword_matches += 1
                evidence.append(f"Found theme keyword: '{keyword}'")
        
        # Look for situations
        for situation in theme.situations:
            if situation.lower() in content_lower:
                keyword_matches += 1
                evidence.append(f"Found thematic situation: '{situation}'")
        
        # Calculate confidence
        total_indicators = len(theme.keywords) + len(theme.situations)
        if total_indicators > 0:
            confidence = (keyword_matches / total_indicators) * theme.prevalence
            
            if confidence > 0.1:
                match = GenreMatch(
                    pattern_name=f"theme_{theme.theme_name}",
                    confidence=confidence,
                    evidence=evidence
                )
                matches.append(match)
        
        return matches

    def _calculate_adherence_score(self, matches: List[GenreMatch], genre_template: GenreTemplate) -> float:
        """Calculate overall genre adherence score."""
        if not matches:
            return 0.0
        
        # Weight different types of matches
        type_weights = {
            "convention": 0.4,
            "structure": 0.3,
            "archetype": 0.2,
            "theme": 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for match in matches:
            # Determine match type from pattern name
            match_type = "convention"  # default
            for pattern_type in type_weights.keys():
                if pattern_type in match.pattern_name:
                    match_type = pattern_type
                    break
            
            weight = type_weights[match_type] * match.weight
            weighted_score += match.confidence * weight
            total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            adherence_score = weighted_score / total_weight
        else:
            adherence_score = 0.0
        
        return min(adherence_score, 1.0)

    async def _analyze_genre_influences(self, content: str) -> Dict[str, Any]:
        """Analyze content for multiple genre influences."""
        genre_scores = {}
        
        # Test against all available genres
        for genre_name, template in self.genre_templates.items():
            matches = await self._analyze_patterns(content, template)
            score = self._calculate_adherence_score(matches, template)
            genre_scores[genre_name] = score
        
        # Sort by score
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Identify significant influences
        significant_genres = [(genre, score) for genre, score in sorted_genres if score > 0.3]
        
        return {
            "all_genre_scores": genre_scores,
            "top_genres": sorted_genres[:5],
            "significant_influences": significant_genres,
            "is_mixed_genre": len(significant_genres) > 1,
            "dominant_genre": sorted_genres[0][0] if sorted_genres else None
        }

    def _create_pattern_analysis(self, matches: List[GenreMatch]) -> Dict[str, Any]:
        """Create detailed pattern analysis."""
        analysis = {
            "total_patterns": len(matches),
            "average_confidence": sum(m.confidence for m in matches) / max(len(matches), 1),
            "strong_patterns": [m for m in matches if m.confidence >= 0.7],
            "weak_patterns": [m for m in matches if m.confidence < 0.3],
            "pattern_categories": {}
        }
        
        # Group by category
        categories = ["convention", "structure", "archetype", "theme"]
        for category in categories:
            category_matches = [m for m in matches if category in m.pattern_name]
            analysis["pattern_categories"][category] = {
                "count": len(category_matches),
                "average_confidence": sum(m.confidence for m in category_matches) / max(len(category_matches), 1)
            }
        
        return analysis

    def _generate_recommendations(self, matches: List[GenreMatch], adherence_score: float,
                                genre_template: GenreTemplate, content: str) -> List[Dict[str, Any]]:
        """Generate recommendations for improving genre adherence."""
        recommendations = []
        
        if adherence_score >= self.confidence_threshold:
            recommendations.append({
                "priority": "info",
                "description": f"Story strongly adheres to {genre_template.name} genre conventions.",
                "type": "positive_feedback"
            })
        else:
            recommendations.append({
                "priority": "high",
                "description": f"Story adherence to {genre_template.name} genre is below threshold ({adherence_score:.1%} < {self.confidence_threshold:.0%})",
                "type": "improvement_needed"
            })
        
        # Check for missing required conventions
        required_conventions = genre_template.get_required_conventions()
        found_conventions = set(m.pattern_name for m in matches if "convention" in m.pattern_name)
        
        for convention in required_conventions:
            convention_name = f"convention_{convention.name}"
            if convention_name not in found_conventions:
                recommendations.append({
                    "priority": "high",
                    "description": f"Add required {genre_template.name} convention: {convention.description}",
                    "type": "missing_element",
                    "element": convention.name
                })
        
        # Check for weak patterns
        weak_matches = [m for m in matches if m.confidence < 0.5]
        if len(weak_matches) > len(matches) * 0.5:  # More than half are weak
            recommendations.append({
                "priority": "medium", 
                "description": f"Strengthen {genre_template.name} genre elements. Many patterns have low confidence.",
                "type": "strengthen_elements"
            })
        
        # Genre-specific recommendations
        if genre_template.name.lower() == "thriller":
            if not any("tension" in m.pattern_name.lower() for m in matches):
                recommendations.append({
                    "priority": "high",
                    "description": "Add more tension and suspense elements typical of thriller genre.",
                    "type": "genre_specific"
                })
        
        elif genre_template.name.lower() == "romance":
            if not any("relationship" in m.pattern_name.lower() or "romance" in m.pattern_name.lower() for m in matches):
                recommendations.append({
                    "priority": "high",
                    "description": "Strengthen romantic relationship development and emotional connection.",
                    "type": "genre_specific"
                })
        
        return recommendations

    def _match_to_dict(self, match: GenreMatch) -> Dict[str, Any]:
        """Convert GenreMatch to dictionary."""
        return {
            "name": match.pattern_name,
            "confidence": match.confidence,
            "evidence": match.evidence,
            "weight": match.weight,
            "description": f"Pattern '{match.pattern_name}' with {match.confidence:.1%} confidence"
        }

    def _create_empty_content_result(self, target_genre: str) -> Dict[str, Any]:
        """Create result for empty content."""
        return {
            "genre_analysis": {
                "target_genre": target_genre,
                "error": "Empty content provided"
            },
            "pattern_matches": [],
            "adherence_score": 0.0,
            "recommendations": [
                {
                    "priority": "error",
                    "description": "No content provided for genre analysis.",
                    "type": "input_error"
                }
            ]
        }

    def _create_unsupported_genre_result(self, target_genre: str) -> Dict[str, Any]:
        """Create result for unsupported genre."""
        available_genres = list(self.genre_templates.keys())
        
        return {
            "genre_analysis": {
                "target_genre": target_genre,
                "error": f"Unsupported genre: {target_genre}",
                "available_genres": available_genres
            },
            "pattern_matches": [],
            "adherence_score": 0.0,
            "recommendations": [
                {
                    "priority": "error",
                    "description": f"Genre '{target_genre}' is not supported. Available genres: {', '.join(available_genres)}",
                    "type": "unsupported_genre"
                }
            ]
        }

    def _create_error_result(self, error_message: str, target_genre: str) -> Dict[str, Any]:
        """Create result for analysis errors."""
        return {
            "genre_analysis": {
                "target_genre": target_genre,
                "error": error_message
            },
            "pattern_matches": [],
            "adherence_score": 0.0,
            "recommendations": [
                {
                    "priority": "error",
                    "description": f"Analysis error: {error_message}",
                    "type": "processing_error"
                }
            ]
        }

    def get_available_genres(self) -> List[str]:
        """Get list of available genre templates."""
        return list(self.genre_templates.keys())

    def get_genre_template_info(self, genre_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific genre template."""
        template = self._get_genre_template(genre_name)
        if template:
            return template.get_genre_summary()
        return None