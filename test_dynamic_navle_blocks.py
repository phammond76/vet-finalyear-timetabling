from pathlib import Path
import csv
import tempfile

from main import (
    assign_rotations_to_student,
    get_gap_friendly_block_order,
    read_rotation_capacities,
    read_student_choices,
)


def write_test_capacity_csv(path: Path) -> None:
    blocks = [f"Block{i}" for i in range(1, 12)]
    rows = [
        {
            "RotationID": "1",
            "RotationName": "Core Small Animal",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "2",
            "RotationName": "Core Farm Animal",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "3",
            "RotationName": "Core Equine",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "4",
            "RotationName": "Core Diagnostic Imaging",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "5",
            "RotationName": "Core Surgery",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "6",
            "RotationName": "Core Medicine",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "7",
            "RotationName": "Selective Dentistry",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "8",
            "RotationName": "Selective Oncology",
            **{block: "1" for block in blocks},
        },
        {
            "RotationID": "9",
            "RotationName": "Selective NAVLE Review",
            **{block: "0" for block in blocks},
        },
    ]
    rows[-1]["Block6"] = "2"
    rows[-1]["Block11"] = "2"

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["RotationID", "RotationName"] + blocks)
        writer.writeheader()
        writer.writerows(rows)


def write_test_choices_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "StudentID",
            "NAVLE_required",
            "FirstChoice1",
            "SecondChoice1",
            "FirstChoice2",
            "SecondChoice2",
            "NAVLE_preferred_block",
        ])
        writer.writerow([
            "S_TEST",
            "Yes",
            "Selective Dentistry",
            "Selective Oncology",
            "Selective Dentistry",
            "Selective Oncology",
            "Block11",
        ])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        capacity_path = tmp_path / "rotation_capacities_test.csv"
        choices_path = tmp_path / "student_choices_test.csv"

        write_test_capacity_csv(capacity_path)
        write_test_choices_csv(choices_path)

        block_names, capacities, rotation_ids = read_rotation_capacities(capacity_path)
        assert len(block_names) == 11, f"Expected 11 blocks, got {len(block_names)}"

        navle_blocks = [
            block for block, cap in capacities["Selective NAVLE Review"].items() if cap > 0
        ]
        assert navle_blocks == ["Block6", "Block11"], f"NAVLE blocks mismatch: {navle_blocks}"

        gap_blocks = get_gap_friendly_block_order(8, block_names)
        assert len(gap_blocks) == 8, f"Expected 8 gap-friendly blocks, got {len(gap_blocks)}"
        assert gap_blocks != block_names[:8], "Gap ordering should not be purely sequential for 11 blocks"

        students = read_student_choices(choices_path)
        core_rotations = [
            rotation for rotation in capacities if rotation.lower().startswith("core")
        ]
        core_rotations.sort()
        remaining_capacities = {rotation: dict(values) for rotation, values in capacities.items()}

        assignments, warnings = assign_rotations_to_student(
            students[0], block_names, core_rotations, remaining_capacities, []
        )

        assert assignments.get("Block11") == "Selective NAVLE Review", (
            f"Expected NAVLE at preferred block Block11, got {assignments.get('Block11')}"
        )
        assert len(assignments) == 9, f"Expected 9 assignments, got {len(assignments)}"
        assert not warnings, f"Unexpected warnings: {warnings}"

        print("All dynamic block and NAVLE tests passed.")


if __name__ == "__main__":
    main()
