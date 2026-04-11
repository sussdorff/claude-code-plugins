"""Tests for retro skill — validates SKILL.md frontmatter and retro-methods.yml structure."""
import yaml
import re
from pathlib import Path

SKILL_DIR = Path(__file__).parent
SKILL_MD = SKILL_DIR / "SKILL.md"
METHODS_YML = Path(__file__).parent.parent.parent / "standards" / "retro-methods.yml"


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from markdown."""
    match = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError("No frontmatter found")
    return yaml.safe_load(match.group(1))


# === SKILL.md Tests ===

def test_skill_md_exists():
    assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}"


def test_skill_md_has_frontmatter():
    text = SKILL_MD.read_text()
    fm = parse_frontmatter(text)
    assert "name" in fm, "Frontmatter missing 'name'"
    assert "description" in fm, "Frontmatter missing 'description'"
    assert fm["name"] == "retro", f"Name should be 'retro', got '{fm['name']}'"


def test_skill_md_description_length():
    text = SKILL_MD.read_text()
    fm = parse_frontmatter(text)
    desc = fm["description"]
    assert 150 <= len(desc) <= 300, f"Description length {len(desc)} not in 150-300 range: {desc}"


def test_skill_md_under_500_lines():
    lines = SKILL_MD.read_text().splitlines()
    assert len(lines) <= 500, f"SKILL.md has {len(lines)} lines, max 500"


# === retro-methods.yml Tests ===

def test_methods_yml_exists():
    assert METHODS_YML.exists(), f"retro-methods.yml not found at {METHODS_YML}"


def test_methods_yml_valid_yaml():
    data = yaml.safe_load(METHODS_YML.read_text())
    assert isinstance(data, dict), "Root should be a dict"
    assert "methods" in data, "Missing 'methods' key"


def test_methods_yml_has_required_methods():
    data = yaml.safe_load(METHODS_YML.read_text())
    names = [m["name"] for m in data["methods"]]
    for required in ["4Ls", "5 Whys", "Energy Radar", "Data Deep-Dive"]:
        assert required in names, f"Missing required method: {required}"


def test_methods_yml_method_structure():
    data = yaml.safe_load(METHODS_YML.read_text())
    required_fields = {"name", "signal_match", "description", "round_prompts"}
    for method in data["methods"]:
        missing = required_fields - set(method.keys())
        assert not missing, f"Method '{method.get('name', '?')}' missing fields: {missing}"
        assert isinstance(method["signal_match"], list), f"signal_match must be list in '{method['name']}'"
        assert len(method["round_prompts"]) == 4, f"round_prompts must have exactly 4 entries in '{method['name']}', got {len(method['round_prompts'])}"


def test_methods_yml_signal_coverage():
    """Each required signal must be matched by at least one method."""
    data = yaml.safe_load(METHODS_YML.read_text())
    all_signals = set()
    for m in data["methods"]:
        all_signals.update(m["signal_match"])
    for signal in ["recurring_problems", "low_energy", "data_heavy", "high_churn"]:
        assert signal in all_signals, f"Signal '{signal}' not covered by any method"


# === Content Tests (AK1-AK6) ===

def test_skill_md_has_researcher_subagent():
    text = SKILL_MD.read_text()
    assert "researcher" in text.lower() or "subagent" in text.lower(), "SKILL.md must reference researcher subagent (AK1)"


def test_skill_md_has_signal_detection():
    text = SKILL_MD.read_text()
    for signal in ["recurring_problems", "low_energy", "data_heavy", "high_churn"]:
        assert signal in text, f"SKILL.md must reference signal '{signal}' (AK2)"


def test_skill_md_has_reflection_rounds():
    text = SKILL_MD.read_text()
    assert "round_prompts" in text or "reflection" in text.lower(), "SKILL.md must describe reflection rounds (AK3)"


def test_skill_md_has_action_creation():
    text = SKILL_MD.read_text()
    assert "bd create" in text, "SKILL.md must show bd create for action beads (AK4/AK5)"
    assert "retro-action" in text, "SKILL.md must use retro-action label (AK5)"


def test_skill_md_has_followup_check():
    text = SKILL_MD.read_text()
    assert "bd list" in text and "retro-action" in text, "SKILL.md must check previous retro actions (AK6)"


def test_skill_md_has_max_3_actions():
    text = SKILL_MD.read_text()
    assert "3" in text and "action" in text.lower(), "SKILL.md must enforce max 3 actions (AK4)"


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
    sys.exit(1 if failed else 0)
