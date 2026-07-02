from pathlib import Path
import csv
import tempfile

from main import write_allocation_output, StudentChoice


def test_write_allocation_output_writes_header_and_ids():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "allocation.csv"
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
        block_names = ["Block1", "Block2"]
        assignments = {"S1": {"Block1": "Core Small Animal", "Block2": "Selective Dentistry"}}
        rotation_ids = {"Core Small Animal": "R1", "Selective Dentistry": "R2"}

        write_allocation_output(path, students, block_names, assignments, rotation_ids)

        with path.open("r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

        assert rows[0] == ["StudentID", "Block1", "Block2"]
        assert rows[1] == ["S1", "R1", "R2"]
