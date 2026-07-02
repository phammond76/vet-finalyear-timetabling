from pathlib import Path
import csv
import tempfile

from main import read_rotation_capacities, read_student_choices, StudentChoice


def test_read_rotation_capacities_parses_blocks_and_capacities():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "rotations.csv"
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["RotationID", "RotationName", "Block1", "Block2", "Block3"])
            writer.writerow(["R1", "Core Small Animal", "2", "1", "0"])
            writer.writerow(["R2", "Selective Dentistry", "1", "0", "1"])

        blocks, capacities, rotation_ids = read_rotation_capacities(path)

        assert blocks == ["Block1", "Block2", "Block3"]
        assert rotation_ids == {
            "Core Small Animal": "R1",
            "Selective Dentistry": "R2",
        }
        assert capacities["Core Small Animal"] == {"Block1": 2, "Block2": 1, "Block3": 0}
        assert capacities["Selective Dentistry"] == {"Block1": 1, "Block2": 0, "Block3": 1}


def test_read_student_choices_parses_navle_and_optional_block():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "choices.csv"
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
                "S1",
                "Yes",
                "Selective Dentistry",
                "Selective Oncology",
                "Selective Surgery",
                "Selective Dermatology",
                "Block5",
            ])
            writer.writerow([
                "S2",
                "No",
                "Selective Dentistry",
                "Selective Oncology",
                "Selective Surgery",
                "Selective Dermatology",
                "",
            ])

        students = read_student_choices(path)

        assert len(students) == 2
        assert students[0] == StudentChoice(
            student_id="S1",
            navle_required=True,
            first_choice_1="Selective Dentistry",
            second_choice_1="Selective Oncology",
            first_choice_2="Selective Surgery",
            second_choice_2="Selective Dermatology",
            navle_preferred_block="Block5",
        )
        assert students[1].navle_required is False
        assert students[1].navle_preferred_block is None
