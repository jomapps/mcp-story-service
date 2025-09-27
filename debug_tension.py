import sys

sys.path.append(".")
from src.services.pacing.calculator import PacingCalculator

pc = PacingCalculator()

# Test medium tension content
content = "argue conflict problem worry"
print(f"Analyzing content: {content}")

tension_score = 0.5  # Base tension

print("High tension indicators:")
for category, words in pc.tension_indicators["high"].items():
    matches = sum(1 for word in words if word in content)
    print(f"  {category}: {matches} matches - {words}")
    tension_score += matches * 0.15

print("Medium tension indicators:")
for category, words in pc.tension_indicators["medium"].items():
    matches = sum(1 for word in words if word in content)
    print(f"  {category}: {matches} matches - {words}")
    tension_score += matches * 0.08

print("Low tension indicators:")
for category, words in pc.tension_indicators["low"].items():
    matches = sum(1 for word in words if word in content)
    print(f"  {category}: {matches} matches - {words}")
    tension_score -= matches * 0.05

print(f"Final tension score: {tension_score}")
print(f"Clamped score: {max(0.1, min(1.0, tension_score))}")

# Test actual method
actual_result = pc._analyze_content_tension(content)
print(f"Actual method result: {actual_result}")
