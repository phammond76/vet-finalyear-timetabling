from typing import Dict

from main import (
    StudentChoice,
    assign_rotations_to_students,
)


def test_assign_rotations_to_students_assigns_all_students():
    students = [
        StudentChoice(
            student_id="S1",
            navle_required=False,
            first_choice_1="Selective Dentistry",
            second_choice_1="Selective Oncology",
            first_choice_2="Selective Dentistry",
            second_choice_2="Selective Oncology",
            navle_preferred_block=None,
        )
    ]
    block_names = [f"Block{i}" for i in range(1, 9)]
    core_rotations = [
        "Core Diagnostic Imaging",
        "Core Equine",
        "Core Farm Animal",
        "Core Medicine",
        "Core Small Animal",
        "Core Surgery",
    ]
    remaining_capacities = {
        rotation: {block: 1 for block in block_names}
        for rotation in core_rotations + ["Selective Dentistry", "Selective Oncology"]
    }

    assignments, warnings = assign_rotations_to_students(
        students,
        core_rotations,
        block_names,
        remaining_capacities,
        [],
    )

    assert "S1" in assignments
    assert len(assignments["S1"]) == 8
    assert warnings == []


def test_assign_rotations_to_students_raises_when_impossible():
    students = [
        StudentChoice(
            student_id="S1",
            navle_required=False,
            first_choice_1="Selective Dentistry",
            second_choice_1="Selective Oncology",
            first_choice_2="Selective Dentistry",
            second_choice_2="Selective Oncology",
            navle_preferred_block=None,
        )
    ]
    block_names = ["Block1"]
    core_rotations = [
        "Core Diagnostic Imaging",
        "Core Equine",
        "Core Farm Animal",
        "Core Medicine",
        "Core Small Animal",
        "Core Surgery",
    ]
    remaining_capacities = {rotation: {"Block1": 0} for rotation in core_rotations + ["Selective Dentistry", "Selective Oncology"]}

    try:
        assign_rotations_to_students(students, core_rotations, block_names, remaining_capacities, [])
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "Assignment failed" in str(exc)
