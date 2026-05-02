# Vet Final Year Rotation Timetabling System

An automated system for allocating final year veterinary students to clinical rotation blocks while respecting capacity constraints, sequence restrictions, and student preferences.

## Overview

Each student must complete:
- **6 mandatory core rotations** (one of each type)
- **2 elective selective rotations** (chosen based on preferences)
- **NAVLE students also complete 1 NAVLE rotation**
- Scheduled across **10 or more blocks** (time periods in the academic year)
- **Total: 8 blocks allocated for normal students, 9 rotations for NAVLE students**

## Requirements

- Python 3.13+
- No external dependencies (uses only standard library)

## Input Files

### 1. Rotation Capacities CSV (`rotation_capacities_example.csv`)

Defines available slots for each rotation in each block.

**Columns:**
- `RotationID`: Unique identifier (e.g., "1", "20")
- `RotationName`: Full name (e.g., "Core Small Animal", "Selective NAVLE Review")
- `Block1` through `Block10`: Number of available places in each block

**Example row:**
```
1,Core Small Animal,4,4,4,4,4,4,4,4,4,4
20,Selective NAVLE Review,0,0,0,10,0,0,0,0,10,0
```

**Rotation Types:**
- **Core rotations**: Names start with "Core" (mandatory for all students)
- **Selective rotations**: Names start with "Selective" (students choose 2)

### 2. Student Choices CSV (`student_choices_example.csv`)

Collects student preferences for selective rotations.

**Columns:**
- `StudentID`: Unique identifier (e.g., "S001")
- `NAVLE_required`: "Yes" or "No" - whether student must do NAVLE selective
- `FirstChoice1`: First preference for first selective rotation
- `SecondChoice1`: Fallback preference for first selective rotation
- `FirstChoice2`: First preference for second selective rotation
- `SecondChoice2`: Fallback preference for second selective rotation
- `NAVLE_preferred_block`: Preferred block for NAVLE assignment if required

**Example row:**
```
S001,Yes,Selective Emergency,Selective Anaesthesia,Selective Oncology,Selective Dentistry,Block5
```

### 3. Sequence Restrictions Text File (`sequence_restrictions_example.txt`)

Natural language rules for rotation ordering constraints. One constraint per line.

**Supported formats:**
- "A must be undertaken after B."
- "A must be scheduled before B."

**Examples:**
```
Morocco rotation must be undertaken after the Equine rotation.
Selective Surgery must be scheduled before Selective Rehabilitation.
```

## Output File

### Allocation Output CSV (`allocation_output.csv`)

The timetable showing which rotation each student is allocated to in each block.

**Format:**
- Row 1: Headers (`StudentID`, `Block1`, `Block2`, ..., `Block10`)
- Data rows: Each student's allocation using rotation IDs
- Empty cells indicate unallocated blocks

**Example:**
```
StudentID,Block1,Block2,Block3,Block4,Block5,Block6,Block7,Block8,Block9,Block10
S001,4,3,2,6,1,5,20,12,,
S002,4,3,2,6,1,5,8,33,,
```

## Usage

### Basic Usage (with default example files)

```bash
python main.py
```

This uses:
- `rotation_capacities_example.csv`
- `student_choices_example.csv`
- `sequence_restrictions_example.txt`
- Outputs to `allocation_output.csv`

### Custom File Paths

```bash
python main.py \
  --capacities my_rotations.csv \
  --choices my_students.csv \
  --restrictions my_constraints.txt \
  --output my_timetable.csv
```

### Running Tests

A lightweight regression script is included for future edits.

```bash
python test_dynamic_navle_blocks.py
```

If you use VS Code, run the task:
- `Run Vet Timetabling Tests`

### Command Line Arguments

- `--capacities PATH`: Path to rotation capacity file (default: `rotation_capacities_example.csv`)
- `--choices PATH`: Path to student choices file (default: `student_choices_example.csv`)
- `--restrictions PATH`: Path to sequence restrictions file (default: `sequence_restrictions_example.txt`)
- `--output PATH`: Path to output allocation file (default: `allocation_output.csv`)

## Output Statistics

The program prints allocation success metrics:

```
Allocation written to allocation_output.csv
Students assigned at least one first choice: 18/20
Students assigned both second choices: 15/20
```

Metrics:
- **First choice satisfaction**: Percentage of students assigned at least one of their first-choice options
- **Second choice satisfaction**: Percentage of students assigned both of their second-choice options

## Algorithm Details

### Approach

The system uses a **maximum flow algorithm (Dinic's algorithm)** to solve the assignment problem:

1. **Build flow network:**
   - Source → each rotation (capacity 1)
   - Each rotation → valid blocks (based on availability and constraints)
   - Each block → sink (capacity 1)

2. **Find maximum flow:** Assigns each student's rotations (8 for normal, 9 for NAVLE) to valid blocks, attempting to spread assignments across blocks to create gaps

3. **Respect constraints:**
   - Capacity: Only assign if rotation has availability in that block
   - Sequence: Enforce ordering rules (A must be before B)
   - Coverage: Ensure NAVLE-required students get NAVLE rotation in eligible blocks
   - Preferences: Prioritize student choices for selectives
   - Gaps: Low-priority attempt to avoid consecutive block assignments by using fixed gap-friendly block patterns

### Selective Rotation Selection

For each student, the system selects rotations using this priority:

1. If `NAVLE_required = Yes`: reserve the NAVLE rotation separately (not from choices)
2. Assign NAVLE to the preferred block when possible
3. Fill the two selective slots prioritizing: FirstChoice1 > FirstChoice2 > SecondChoice1 > SecondChoice2
4. If fewer than 2 unique choices are available, fill with other available selectives

### NAVLE Requirements

- `NAVLE_required = Yes` means the student will complete **9 rotations** total.
- NAVLE students complete **6 cores + 2 selectives + 1 NAVLE rotation**.
- NAVLE rotation is only available in the two NAVLE-eligible blocks.
- `NAVLE_preferred_block` is used to assign the NAVLE rotation before scheduling the rest of the student's rotations.
- When NAVLE is assigned to a preferred block, the algorithm then schedules the remaining rotations using a gap-aware block ordering so the NAVLE block is treated as occupied and not counted as the only gap.

## Algorithm Complexity

- **Time:** O(n·m·V·E·log(V)) where n=students, m=rotations, V/E=flow network nodes/edges
- **Space:** O(n·m·V²) for flow network storage

Scales efficiently to 100+ students with 36 rotations and 10 blocks.

## Troubleshooting

### "Unable to assign all rotations for student S###"
- **Cause:** Insufficient capacity or conflicting constraints
- **Solution:** Review capacity for that student's preference list; increase capacity or relax constraints

### "Unable to allocate all core rotations"
- **Cause:** Insufficient total capacity across blocks for core rotations
- **Solution:** Increase capacity in `rotation_capacities_example.csv`

### Rotation names not recognized in restrictions file
- **Cause:** Typo or format mismatch with exact names in capacity file
- **Solution:** Check that rotation names match exactly; system is case-insensitive but requires full names

## Example Files

Three example files are provided:

- `rotation_capacities_example.csv`: 36 rotations (6 core + 30 selective) with sample capacities
- `student_choices_example.csv`: 20 sample students with preferences
- `sequence_restrictions_example.txt`: 5 sample ordering constraints

Run `python main.py` to generate `allocation_output.csv` using these examples.

## Development

### Code Structure

- `StudentChoice`: Dataclass representing student preferences
- `read_rotation_capacities()`: Parse capacity CSV
- `read_student_choices()`: Parse student preferences CSV
- `parse_restrictions()`: Parse natural language constraints
- `Dinic`: Maximum flow algorithm implementation
- `assign_rotations_to_students()`: Main allocation logic
- `write_allocation_output()`: Output results to CSV

### Key Classes

- **Dinic**: Implements Dinic's maximum flow algorithm with BFS/DFS for efficient bipartite matching

### Adding Custom Constraints

To add constraint types beyond ordering, modify `rotation_allowed_in_block()` function to check additional conditions before allowing an assignment.

## License

Internal use for veterinary program administration.

## Contact

For questions or modifications, see code comments in `main.py` for detailed algorithm explanation.
