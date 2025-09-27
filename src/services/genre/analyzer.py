import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from src.lib.genre_loader import GenreLoader
from src.models.genre_template import ConventionImportance
from src.lib.error_handler import AnalysisError

class GenreAnalyzer:
    def __init__(self, genre_loader: GenreLoader):
        self.genre_loader = genre_loader
        self.logger = logging.getLogger(__name__)
        self.genre_patterns = self._initialize_genre_patterns()

    def _initialize_genre_patterns(self) -> Dict[str, Dict]:
        """Initialize genre-specific pattern recognition rules."""
        return {
            "thriller": {
                "keywords": ["danger", "threat", "chase", "escape", "suspense", "tension", "deadline", "race", "urgent"],
                "character_patterns": ["detective", "agent", "spy", "investigator", "villain", "mastermind"],
                "plot_patterns": ["conspiracy", "betrayal", "twist", "revelation", "pursuit", "countdown"],
                "pacing_indicators": ["fast", "quick", "sudden", "immediate", "urgent", "rapid"],
                "atmosphere": ["dark", "mysterious", "ominous", "foreboding", "sinister"]
            },
            "romance": {
                "keywords": ["love", "heart", "passion", "romance", "relationship", "attraction", "kiss", "wedding"],
                "character_patterns": ["lover", "partner", "beloved", "soulmate", "romantic interest"],
                "plot_patterns": ["meet-cute", "misunderstanding", "separation", "reunion", "proposal"],
                "pacing_indicators": ["gentle", "tender", "slow", "intimate", "emotional"],
                "atmosphere": ["warm", "tender", "passionate", "romantic", "intimate"]
            },
            "horror": {
                "keywords": ["fear", "terror", "scream", "blood", "death", "monster", "nightmare", "haunted"],
                "character_patterns": ["victim", "monster", "ghost", "demon", "survivor", "final girl"],
                "plot_patterns": ["haunting", "possession", "curse", "ritual", "sacrifice", "survival"],
                "pacing_indicators": ["slow", "building", "sudden", "shocking", "terrifying"],
                "atmosphere": ["dark", "eerie", "creepy", "terrifying", "supernatural"]
            },
            "comedy": {
                "keywords": ["funny", "laugh", "joke", "humor", "amusing", "hilarious", "comic", "witty"],
                "character_patterns": ["comedian", "fool", "trickster", "straight man", "comic relief"],
                "plot_patterns": ["misunderstanding", "mistaken identity", "pratfall", "wordplay", "irony"],
                "pacing_indicators": ["light", "quick", "snappy", "bouncy", "energetic"],
                "atmosphere": ["light", "cheerful", "playful", "absurd", "satirical"]
            },
            "drama": {
                "keywords": ["emotion", "conflict", "struggle", "family", "relationship", "growth", "change"],
                "character_patterns": ["protagonist", "family member", "friend", "mentor", "rival"],
                "plot_patterns": ["coming of age", "family drama", "personal growth", "moral dilemma"],
                "pacing_indicators": ["steady", "measured", "thoughtful", "deliberate"],
                "atmosphere": ["realistic", "emotional", "serious", "contemplative"]
            }
        }

    def analyze_genre(self, story_beats: List[Dict[str, Any]], character_types: List[Dict[str, Any]], target_genre: str) -> Dict[str, Any]:
        """
        Analyzes the genre compliance of story elements using sophisticated pattern matching.
        """
        if not target_genre:
            raise AnalysisError("Target genre must be specified")

        try:
            self.logger.info(f"Analyzing genre compliance for: {target_genre}")

            # Load genre template
            genre_template = self.genre_loader.get_genre(target_genre.lower())
            if not genre_template:
                raise AnalysisError(f"Genre '{target_genre}' not found in templates")

            # Analyze story content against genre patterns
            content_analysis = self._analyze_content_patterns(story_beats, character_types, target_genre.lower())

            # Check convention compliance
            convention_compliance = self._check_convention_compliance(
                genre_template, story_beats, character_types, content_analysis
            )

            # Generate authenticity improvements
            authenticity_improvements = self._generate_authenticity_improvements(
                genre_template, convention_compliance, content_analysis
            )

            # Identify genre-specific beats
            genre_specific_beats = self._identify_genre_beats(
                genre_template, story_beats, target_genre.lower()
            )

            self.logger.info(f"Genre analysis complete. Score: {convention_compliance['score']:.2f}")

            return {
                "convention_compliance": convention_compliance,
                "authenticity_improvements": authenticity_improvements,
                "genre_specific_beats": genre_specific_beats
            }

        except Exception as e:
            self.logger.error(f"Error analyzing genre: {e}")
            raise AnalysisError(f"Genre analysis failed: {str(e)}")

    def _analyze_content_patterns(self, story_beats: List[Dict[str, Any]], character_types: List[Dict[str, Any]], genre: str) -> Dict[str, Any]:
        """Analyze story content for genre-specific patterns."""
        if genre not in self.genre_patterns:
            return {"keyword_matches": 0, "character_matches": 0, "plot_matches": 0, "atmosphere_score": 0.0}

        patterns = self.genre_patterns[genre]

        # Combine all text content for analysis
        all_text = ""
        for beat in story_beats:
            all_text += f" {beat.get('description', '')} {beat.get('type', '')}"

        for char in character_types:
            all_text += f" {char.get('name', '')} {char.get('role', '')} {char.get('archetype', '')}"

        all_text = all_text.lower()

        # Count pattern matches
        keyword_matches = sum(1 for keyword in patterns["keywords"] if keyword in all_text)
        character_matches = sum(1 for pattern in patterns["character_patterns"] if pattern in all_text)
        plot_matches = sum(1 for pattern in patterns["plot_patterns"] if pattern in all_text)
        pacing_matches = sum(1 for indicator in patterns["pacing_indicators"] if indicator in all_text)
        atmosphere_matches = sum(1 for mood in patterns["atmosphere"] if mood in all_text)

        # Calculate atmosphere score
        total_atmosphere_patterns = len(patterns["atmosphere"])
        atmosphere_score = atmosphere_matches / total_atmosphere_patterns if total_atmosphere_patterns > 0 else 0.0

        return {
            "keyword_matches": keyword_matches,
            "character_matches": character_matches,
            "plot_matches": plot_matches,
            "pacing_matches": pacing_matches,
            "atmosphere_score": atmosphere_score,
            "total_keywords": len(patterns["keywords"]),
            "total_character_patterns": len(patterns["character_patterns"]),
            "total_plot_patterns": len(patterns["plot_patterns"])
        }

    def _check_convention_compliance(self, genre_template, story_beats: List[Dict], character_types: List[Dict], content_analysis: Dict) -> Dict[str, Any]:
        """Check compliance with genre conventions."""
        met_conventions = []
        missing_conventions = []
        score = 0.0
        total_weight = 0.0

        for convention in genre_template.conventions:
            convention_met = self._evaluate_convention(convention, story_beats, character_types, content_analysis)
            weight = self._get_convention_weight(convention.importance)
            total_weight += weight

            if convention_met:
                met_conventions.append(convention.name)
                score += weight
            else:
                missing_conventions.append(convention.name)

        # Normalize score
        final_score = score / total_weight if total_weight > 0 else 0.0
        meets_threshold = final_score >= 0.75

        # Calculate confidence based on content analysis quality
        confidence_score = self._calculate_genre_confidence(content_analysis, len(story_beats), len(character_types))

        return {
            "score": round(final_score, 2),
            "meets_threshold": meets_threshold,
            "confidence_score": round(confidence_score, 2),
            "met_conventions": met_conventions,
            "missing_conventions": missing_conventions
        }

    def _evaluate_convention(self, convention, story_beats: List[Dict], character_types: List[Dict], content_analysis: Dict) -> bool:
        """Evaluate whether a specific convention is met."""
        convention_name = convention.name.lower()

        # High Stakes (Thriller)
        if "high stakes" in convention_name:
            return self._check_high_stakes(story_beats, content_analysis)

        # Fast-Paced Plot (Thriller)
        elif "fast" in convention_name and "pace" in convention_name:
            return content_analysis.get("pacing_matches", 0) >= 2

        # Race Against Time (Thriller)
        elif "race" in convention_name and "time" in convention_name:
            return self._check_time_pressure(story_beats)

        # Romance conventions
        elif "romantic" in convention_name or "love" in convention_name:
            return self._check_romantic_elements(story_beats, character_types, content_analysis)

        # Horror conventions
        elif "supernatural" in convention_name or "fear" in convention_name:
            return self._check_horror_elements(story_beats, content_analysis)

        # Comedy conventions
        elif "humor" in convention_name or "comic" in convention_name:
            return self._check_comedic_elements(story_beats, content_analysis)

        # Default pattern matching
        else:
            return self._check_general_convention(convention, story_beats, content_analysis)

    def _check_high_stakes(self, story_beats: List[Dict], content_analysis: Dict) -> bool:
        """Check for high stakes elements."""
        high_stakes_indicators = ["death", "life", "world", "destroy", "save", "critical", "urgent", "disaster"]

        for beat in story_beats:
            description = beat.get("description", "").lower()
            if any(indicator in description for indicator in high_stakes_indicators):
                return True

        return content_analysis.get("keyword_matches", 0) >= 3

    def _check_time_pressure(self, story_beats: List[Dict]) -> bool:
        """Check for time pressure elements."""
        time_indicators = ["deadline", "time", "hurry", "quick", "fast", "urgent", "countdown", "before"]

        for beat in story_beats:
            description = beat.get("description", "").lower()
            if any(indicator in description for indicator in time_indicators):
                return True

        return False

    def _check_romantic_elements(self, story_beats: List[Dict], character_types: List[Dict], content_analysis: Dict) -> bool:
        """Check for romantic elements."""
        # Check for romantic character types
        for char in character_types:
            role = char.get("role", "").lower()
            archetype = char.get("archetype", "").lower()
            if any(term in f"{role} {archetype}" for term in ["love", "romantic", "partner", "lover"]):
                return True

        # Check for romantic beats
        romantic_beats = ["meet", "attraction", "kiss", "date", "proposal", "wedding", "relationship"]
        for beat in story_beats:
            description = beat.get("description", "").lower()
            beat_type = beat.get("type", "").lower()
            if any(term in f"{description} {beat_type}" for term in romantic_beats):
                return True

        return content_analysis.get("keyword_matches", 0) >= 2

    def _check_horror_elements(self, story_beats: List[Dict], content_analysis: Dict) -> bool:
        """Check for horror elements."""
        horror_indicators = ["fear", "terror", "monster", "ghost", "haunted", "supernatural", "death", "blood"]

        for beat in story_beats:
            description = beat.get("description", "").lower()
            if any(indicator in description for indicator in horror_indicators):
                return True

        return content_analysis.get("atmosphere_score", 0) >= 0.3

    def _check_comedic_elements(self, story_beats: List[Dict], content_analysis: Dict) -> bool:
        """Check for comedic elements."""
        comedy_indicators = ["funny", "laugh", "joke", "humor", "comic", "amusing", "silly", "ridiculous"]

        for beat in story_beats:
            description = beat.get("description", "").lower()
            beat_type = beat.get("type", "").lower()
            if any(indicator in f"{description} {beat_type}" for indicator in comedy_indicators):
                return True

        return content_analysis.get("keyword_matches", 0) >= 2

    def _check_general_convention(self, convention, story_beats: List[Dict], content_analysis: Dict) -> bool:
        """General convention checking using keyword matching."""
        convention_desc = convention.description.lower()
        convention_name = convention.name.lower()

        # Extract key terms from convention description
        key_terms = re.findall(r'\b\w{4,}\b', convention_desc)

        # Check story beats for these terms
        matches = 0
        for beat in story_beats:
            description = beat.get("description", "").lower()
            beat_type = beat.get("type", "").lower()
            content = f"{description} {beat_type}"

            for term in key_terms:
                if term in content:
                    matches += 1

        # Convention is met if we find at least 2 key terms or have good content analysis
        return matches >= 2 or content_analysis.get("keyword_matches", 0) >= 3

    def _get_convention_weight(self, importance) -> float:
        """Get weight for convention based on importance."""
        if importance == ConventionImportance.ESSENTIAL:
            return 1.0
        elif importance == ConventionImportance.TYPICAL:
            return 0.7
        elif importance == ConventionImportance.OPTIONAL:
            return 0.3
        else:
            return 0.5

    def _calculate_genre_confidence(self, content_analysis: Dict, num_beats: int, num_characters: int) -> float:
        """Calculate confidence in genre analysis."""
        base_confidence = 0.7

        # Bonus for content richness
        if num_beats >= 5:
            base_confidence += 0.1
        if num_characters >= 3:
            base_confidence += 0.1

        # Bonus for pattern matches
        keyword_ratio = content_analysis.get("keyword_matches", 0) / max(1, content_analysis.get("total_keywords", 1))
        if keyword_ratio >= 0.3:
            base_confidence += 0.1

        # Bonus for character pattern matches
        char_ratio = content_analysis.get("character_matches", 0) / max(1, content_analysis.get("total_character_patterns", 1))
        if char_ratio >= 0.5:
            base_confidence += 0.05

        return max(0.1, min(0.95, base_confidence))

    def _generate_authenticity_improvements(self, genre_template, convention_compliance: Dict, content_analysis: Dict) -> List[str]:
        """Generate suggestions for improving genre authenticity."""
        improvements = []

        # Suggestions based on missing conventions
        missing_conventions = convention_compliance.get("missing_conventions", [])
        for convention in missing_conventions:
            if "high stakes" in convention.lower():
                improvements.append("Add higher stakes - consider life-or-death consequences or world-changing events")
            elif "fast" in convention.lower() and "pace" in convention.lower():
                improvements.append("Increase pacing - add more action sequences and reduce exposition")
            elif "race" in convention.lower() and "time" in convention.lower():
                improvements.append("Add time pressure - introduce deadlines or countdown elements")
            elif "romantic" in convention.lower():
                improvements.append("Strengthen romantic elements - develop relationship dynamics and emotional connections")
            elif "humor" in convention.lower():
                improvements.append("Add comedic elements - include witty dialogue, situational comedy, or character quirks")
            elif "supernatural" in convention.lower():
                improvements.append("Enhance supernatural elements - add more mysterious or otherworldly aspects")

        # Suggestions based on content analysis
        if content_analysis.get("keyword_matches", 0) < 3:
            improvements.append("Use more genre-specific vocabulary and terminology")

        if content_analysis.get("character_matches", 0) < 2:
            improvements.append("Develop characters that fit genre archetypes more closely")

        if content_analysis.get("atmosphere_score", 0) < 0.3:
            improvements.append("Strengthen genre atmosphere through setting descriptions and mood")

        # Score-based suggestions
        score = convention_compliance.get("score", 0)
        if score < 0.5:
            improvements.append("Consider major structural changes to better align with genre expectations")
        elif score < 0.75:
            improvements.append("Fine-tune story elements to better match genre conventions")

        return improvements[:5]  # Limit to top 5 suggestions

    def _identify_genre_beats(self, genre_template, story_beats: List[Dict], genre: str) -> List[Dict]:
        """Identify genre-specific story beats."""
        genre_beats = []

        # Get common beats for this genre from template
        common_beats = getattr(genre_template, 'common_beats', [])

        # Map story beats to genre-specific beats
        for beat in story_beats:
            beat_type = beat.get("type", "").upper()
            description = beat.get("description", "")

            # Check if this beat matches genre expectations
            if beat_type in common_beats:
                genre_beats.append({
                    "beat_type": beat_type,
                    "description": description,
                    "genre_relevance": "high",
                    "position": beat.get("position", 0),
                    "suggestions": self._get_beat_suggestions(beat_type, genre, description)
                })
            else:
                # Check if beat could be enhanced for genre
                relevance = self._assess_beat_relevance(beat, genre)
                if relevance != "low":
                    genre_beats.append({
                        "beat_type": beat_type,
                        "description": description,
                        "genre_relevance": relevance,
                        "position": beat.get("position", 0),
                        "suggestions": self._get_beat_suggestions(beat_type, genre, description)
                    })

        return genre_beats

    def _assess_beat_relevance(self, beat: Dict, genre: str) -> str:
        """Assess how relevant a beat is to the genre."""
        if genre not in self.genre_patterns:
            return "medium"

        patterns = self.genre_patterns[genre]
        description = beat.get("description", "").lower()
        beat_type = beat.get("type", "").lower()
        content = f"{description} {beat_type}"

        # Count pattern matches
        matches = 0
        matches += sum(1 for keyword in patterns["keywords"] if keyword in content)
        matches += sum(1 for pattern in patterns["plot_patterns"] if pattern in content)
        matches += sum(1 for mood in patterns["atmosphere"] if mood in content)

        if matches >= 3:
            return "high"
        elif matches >= 1:
            return "medium"
        else:
            return "low"

    def _get_beat_suggestions(self, beat_type: str, genre: str, description: str) -> List[str]:
        """Get suggestions for enhancing a beat for the genre."""
        suggestions = []

        if genre == "thriller":
            if beat_type == "INCITING_INCIDENT":
                suggestions.append("Make the inciting incident more threatening or urgent")
            elif beat_type == "CLIMAX":
                suggestions.append("Increase tension and stakes in the final confrontation")
            elif beat_type == "TWIST":
                suggestions.append("Ensure the twist genuinely surprises and raises stakes")

        elif genre == "romance":
            if beat_type == "INCITING_INCIDENT":
                suggestions.append("Focus on the first meeting or attraction between romantic leads")
            elif beat_type == "CLIMAX":
                suggestions.append("Make the climax about choosing love or overcoming relationship obstacles")

        elif genre == "horror":
            if beat_type == "INCITING_INCIDENT":
                suggestions.append("Introduce the supernatural threat or first sign of danger")
            elif beat_type == "CLIMAX":
                suggestions.append("Create a terrifying final confrontation with the horror element")

        # Generic suggestions if no specific ones
        if not suggestions:
            suggestions.append(f"Enhance this {beat_type.lower()} to better fit {genre} genre expectations")

        return suggestions
