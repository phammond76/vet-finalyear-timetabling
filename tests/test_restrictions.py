from pathlib import Path
import tempfile

from main import parse_restrictions


def test_parse_restrictions_after_and_before_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "restrictions.txt"
        path.write_text(
            "Core Small Animal must be undertaken after Core Farm Animal\n"
            "Selective Dentistry must be scheduled before Selective Oncology.\n"
            "Unknown Rotation must be undertaken after Core Medicine\n"
            "\n",
            encoding="utf-8",
        )

        rules = parse_restrictions(path, [
            "Core Small Animal",
            "Core Farm Animal",
            "Core Medicine",
            "Selective Dentistry",
            "Selective Oncology",
        ])

        assert ("Core Farm Animal", "Core Small Animal") in rules
        assert ("Selective Dentistry", "Selective Oncology") in rules
        assert all(rotation in [
            "Core Small Animal",
            "Core Farm Animal",
            "Core Medicine",
            "Selective Dentistry",
            "Selective Oncology",
        ] for pair in rules for rotation in pair)
