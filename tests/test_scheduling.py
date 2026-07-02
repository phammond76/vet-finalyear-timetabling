from pathlib import Path
import csv
import tempfile

from main import (
    StudentChoice,
    rotation_allowed_in_block,
    get_gap_friendly_block_order,
    assign_rotations_to_student,
)


def test_rotation_allowed_in_block_respects_ordering_constraints():
    student = StudentChoice(
        student_id="S1",
        navle_required=False,
        first_choice_1="Selective Dentistry",
        second_choice_1="Selective Oncology",
        first_choice_2="Selective Surgery",
        second_choice_2="Selective Dermatology",
        navle_preferred_block=None,
    )
    all_blocks = ["Block1", "Block2", "Block3"]
    block_rank = {block: idx for idx, block in enumerate(all_blocks)}
    remaining_capacities = {
        "Core Small Animal": {"Block1": 1, "Block2": 1, "Block3": 1},
        "Core Farm Animal": {"Block1": 1, "Block2": 1, "Block3": 1},
    }
    assigned_blocks = {"Block1": "Core Small Animal"}
    order_rules = [("Core Small Animal", "Core Farm Animal")]

    assert rotation_allowed_in_block(
        student,
        "Core Farm Animal",
        "Block2",
        assigned_blocks,
        all_blocks,
        remaining_capacities,
        order_rules,
        block_rank,
    )
    assert not rotation_allowed_in_block(
        student,
        "Core Farm Animal",
        "Block1",
        assigned_blocks,
        all_blocks,
        remaining_capacities,
        order_rules,
        block_rank,
    )


def test_get_gap_friendly_block_order_returns_correct_count_and_unique_blocks():
    blocks = [f"Block{i}" for i in range(1, 9)]
    ordered = get_gap_friendly_block_order(6, blocks)

    assert len(ordered) == 6
    assert len(set(ordered)) == 6
    assert ordered != blocks[:6]


def test_assign_rotations_to_student_assigns_selectives_and_cores():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "capacities.csv"
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["RotationID", "RotationName", "Block1", "Block2", "Block3", "Block4", "Block5", "Block6", "Block7", "Block8"])
            for idx, name in enumerate([
                "Core Small Animal",
                "Core Farm Animal",
                "Core Equine",
                "Core Diagnostic Imaging",
                "Core Surgery",
                "Core Medicine",
                "Selective Dentistry",
                "Selective Oncology",
            ], start=1):
                writer.writerow([str(idx), name] + ["1"] * 8)

        # Build capacities directly without reading from file to reduce test dependency.
        remaining_capacities = {
            "Core Small Animal": {f"Block{i}": 1 for i in range(1, 9)},
            "Core Farm Animal": {f"Block{i}": 1 for i in range(1, 9)},
            "Core Equine": {f"Block{i}": 1 for i in range(1, 9)},
            "Core Diagnostic Imaging": {f"Block{i}": 1 for i in range(1, 9)},
            "Core Surgery": {f"Block{i}": 1 for i in range(1, 9)},
            "Core Medicine": {f"Block{i}": 1 for i in range(1, 9)},
            "Selective Dentistry": {f"Block{i}": 1 for i in range(1, 9)},
            "Selective Oncology": {f"Block{i}": 1 for i in range(1, 9)},
        }
        student = StudentChoice(
            student_id="S1",
            navle_required=False,
            first_choice_1="Selective Dentistry",
            second_choice_1="Selective Oncology",
            first_choice_2="Selective Dentistry",
            second_choice_2="Selective Oncology",
            navle_preferred_block=None,
        )
        block_names = [f"Block{i}" for i in range(1, 9)]
        core_rotations = [
            "Core Diagnostic Imaging",
            "Core Equine",
            "Core Farm Animal",
            "Core Medicine",
            "Core Small Animal",
            "Core Surgery",
        ]

        assignments, warnings = assign_rotations_to_student(
            student,
            block_names,
            core_rotations,
            remaining_capacities,
            [],
        )

        assert len(assignments) == 8
        assert "Selective Dentistry" in assignments.values() or "Selective Oncology" in assignments.values()
        assert not warnings
