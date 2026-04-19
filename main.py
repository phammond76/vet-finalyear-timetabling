"""
Vet Final Year Rotation Timetabling System

Automates the allocation of final year veterinary students to clinical rotations.
Each student must complete 6 mandatory core rotations and 2 elective selective rotations
across 10 blocks (time periods). The system respects capacity constraints and
sequence restrictions while attempting to satisfy student preferences.
"""

import argparse
import csv
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class StudentChoice:
    """Represents a student's rotation preferences and requirements."""
    student_id: str
    navle_required: bool  # Whether this student must do the NAVLE selective
    first_choice_1: str   # First choice for first selective rotation
    second_choice_1: str  # Second choice for first selective rotation
    first_choice_2: str   # First choice for second selective rotation
    second_choice_2: str  # Second choice for second selective rotation


def read_rotation_capacities(path: Path) -> Tuple[List[str], Dict[str, Dict[str, int]], Dict[str, str]]:
    """
    Reads rotation capacity data from CSV file.
    
    Args:
        path: Path to CSV file with columns: RotationID, RotationName, Block1...Block10
        
    Returns:
        Tuple of:
        - block_columns: List of block names (e.g., ['Block1', 'Block2', ...])
        - capacities: Dict mapping rotation names to dict of block->capacity
        - rotation_ids: Dict mapping rotation names to rotation IDs
    """
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        block_columns = [name for name in reader.fieldnames if name and name.startswith("Block")]
        capacities: Dict[str, Dict[str, int]] = {}
        rotation_ids: Dict[str, str] = {}

        for row in reader:
            name = row["RotationName"].strip()
            rotation_ids[name] = row["RotationID"].strip()
            capacities[name] = {
                block: int(row[block]) if row[block] else 0 for block in block_columns
            }

    return block_columns, capacities, rotation_ids


def read_student_choices(path: Path) -> List[StudentChoice]:
    """
    Reads student choice preferences from CSV file.
    
    Args:
        path: Path to CSV file with columns: StudentID, NAVLE_required,
              FirstChoice1, SecondChoice1, FirstChoice2, SecondChoice2
              
    Returns:
        List of StudentChoice objects
    """
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        students: List[StudentChoice] = []
        for row in reader:
            students.append(
                StudentChoice(
                    student_id=row["StudentID"].strip(),
                    navle_required=row.get("NAVLE_required", "No").strip().lower() == "yes",
                    first_choice_1=row["FirstChoice1"].strip(),
                    second_choice_1=row["SecondChoice1"].strip(),
                    first_choice_2=row["FirstChoice2"].strip(),
                    second_choice_2=row["SecondChoice2"].strip(),
                )
            )
    return students


def parse_restrictions(path: Path, known_rotations: Sequence[str]) -> List[Tuple[str, str]]:
    """
    Parses natural language restriction rules from text file.
    
    Supports formats like:
    - "A must be undertaken after B"
    - "A must be scheduled before B"
    
    Args:
        path: Path to text file with one restriction per line
        known_rotations: List of valid rotation names for validation
        
    Returns:
        List of (before_rotation, after_rotation) tuples representing ordering constraints
    """
    rules: List[Tuple[str, str]] = []
    known = {name.lower(): name for name in known_rotations}

    def normalize(text: str) -> str:
        """Normalizes text for comparison by removing common words."""
        t = text.lower().strip()
        t = re.sub(r"\brotation\b", "", t)
        t = re.sub(r"\bthe\b", "", t)
        return t.strip()

    def find_rotation(fragment: str) -> Optional[str]:
        """Finds matching rotation name from user input fragment."""
        fragment_norm = normalize(fragment)
        for candidate_lower, canonical in known.items():
            if candidate_lower == fragment_norm:
                return canonical
        return None

    with path.open("r", encoding="utf-8") as infile:
        for line in infile:
            raw = line.strip()
            if not raw:
                continue

            # Try to match "X must be undertaken after Y" pattern
            after_match = re.search(
                r"^(.+?)\s+must\s+be\s+undertaken\s+after\s+(.+?)\.?$",
                raw,
                flags=re.IGNORECASE,
            )
            # Try to match "X must be scheduled before Y" or "X must before Y" pattern
            before_match = re.search(
                r"^(.+?)\s+must\s+(?:be\s+scheduled\s+)?before\s+(.+?)\.?$",
                raw,
                flags=re.IGNORECASE,
            )

            if after_match:
                first, second = after_match.group(1), after_match.group(2)
                rot_after = find_rotation(first)
                rot_before = find_rotation(second)
                if rot_after and rot_before:
                    rules.append((rot_before, rot_after))
                continue

            if before_match:
                first, second = before_match.group(1), before_match.group(2)
                rot_before = find_rotation(first)
                rot_after = find_rotation(second)
                if rot_before and rot_after:
                    rules.append((rot_before, rot_after))
                continue

    return rules


class Dinic:
    """
    Maximum flow algorithm implementation using Dinic's algorithm.
    Used to solve the bipartite matching problem of assigning rotations to blocks.
    """
    
    @dataclass
    class Edge:
        """Represents a directed edge in the flow network."""
        to: int      # Target node
        rev: int     # Index of reverse edge in target node's adjacency list
        cap: int     # Remaining capacity

    def __init__(self, n: int) -> None:
        """Initialize flow network with n nodes."""
        self.n = n
        self.graph: List[List[Dinic.Edge]] = [[] for _ in range(n)]
        self.level: List[int] = [-1] * n  # BFS levels for nodes
        self.iter: List[int] = [0] * n    # DFS iteration counters

    def add_edge(self, fr: int, to: int, cap: int) -> None:
        """
        Add a directed edge with capacity cap from fr to to.
        Also adds reverse edge with 0 capacity for flow cancellation.
        """
        self.graph[fr].append(Dinic.Edge(to=to, rev=len(self.graph[to]), cap=cap))
        self.graph[to].append(Dinic.Edge(to=fr, rev=len(self.graph[fr]) - 1, cap=0))

    def bfs(self, s: int) -> None:
        """Build level graph from source using BFS."""
        self.level = [-1] * self.n
        queue = deque([s])
        self.level[s] = 0
        while queue:
            v = queue.popleft()
            for edge in self.graph[v]:
                if edge.cap > 0 and self.level[edge.to] < 0:
                    self.level[edge.to] = self.level[v] + 1
                    queue.append(edge.to)

    def dfs(self, v: int, t: int, f: int) -> int:
        """Find augmenting path from v to t using DFS, pushing up to f flow."""
        if v == t:
            return f
        for i in range(self.iter[v], len(self.graph[v])):
            edge = self.graph[v][i]
            if edge.cap > 0 and self.level[v] < self.level[edge.to]:
                d = self.dfs(edge.to, t, min(f, edge.cap))
                if d > 0:
                    edge.cap -= d
                    self.graph[edge.to][edge.rev].cap += d
                    return d
            self.iter[v] += 1
        return 0

    def max_flow(self, s: int, t: int) -> int:
        """Compute maximum flow from source s to sink t."""
        flow = 0
        INF = 10**9
        while True:
            self.bfs(s)
            if self.level[t] < 0:
                return flow
            self.iter = [0] * self.n
            f = self.dfs(s, t, INF)
            while f > 0:
                flow += f
                f = self.dfs(s, t, INF)


def rotation_allowed_in_block(
    student: StudentChoice,
    rotation: str,
    block: str,
    assigned_blocks: Dict[str, str],
    all_blocks: Sequence[str],
    remaining_capacities: Dict[str, Dict[str, int]],
    order_rules: Sequence[Tuple[str, str]],
    block_rank: Dict[str, int],
) -> bool:
    """
    Check if a rotation can be assigned to a block for a student.
    Validates: sequence ordering constraints and availability of future blocks.
    
    Args:
        student: The student
        rotation: Rotation name to check
        block: Block to assign to
        assigned_blocks: Already-assigned rotations for this student
        all_blocks: All available blocks
        remaining_capacities: Available capacity for each rotation/block
        order_rules: List of (before, after) ordering constraints
        block_rank: Mapping of block names to their time order
        
    Returns:
        True if assignment is valid, False otherwise
    """
    current_index = block_rank[block]
    for before, after in order_rules:
        # If this rotation must come before another, check that other rotation
        # is scheduled later (or not yet)
        if rotation == before:
            if after in assigned_blocks:
                if current_index >= block_rank[assigned_blocks[after]]:
                    return False
        # If this rotation must come after another, check that other rotation
        # is scheduled earlier or will have capacity in future blocks
        if rotation == after:
            if before in assigned_blocks:
                if current_index <= block_rank[assigned_blocks[before]]:
                    return False
            else:
                remaining_blocks = [
                    b for b in all_blocks if block_rank[b] > current_index
                ]
                if not any(remaining_capacities[before][b] > 0 for b in remaining_blocks):
                    return False
    return True


def assign_rotations_to_students(
    students: Sequence[StudentChoice],
    core_rotations: Sequence[str],
    block_names: Sequence[str],
    remaining_capacities: Dict[str, Dict[str, int]],
    order_rules: Sequence[Tuple[str, str]],
) -> Dict[str, Dict[str, str]]:
    """
    Assign all rotations to all students.
    
    Args:
        students: List of students
        core_rotations: List of mandatory core rotation names
        block_names: List of block names
        remaining_capacities: Available capacity for each rotation/block
        order_rules: Ordering constraints
        
    Returns:
        Dict mapping student_id -> dict of block -> rotation_name assignments
        
    Raises:
        RuntimeError if any student cannot be assigned all rotations
    """
    student_assignments: Dict[str, Dict[str, str]] = {}
    block_rank = {block: idx for idx, block in enumerate(block_names)}

    for student in students:
        assignments, problems = assign_rotations_to_student(
            student, block_names, core_rotations, remaining_capacities, order_rules
        )
        if problems:
            raise RuntimeError(f"Assignment failed for {student.student_id}: {problems}")
        student_assignments[student.student_id] = assignments

    return student_assignments


def assign_rotations_to_student(
    student: StudentChoice,
    all_blocks: Sequence[str],
    core_rotations: Sequence[str],
    remaining_capacities: Dict[str, Dict[str, int]],
    order_rules: Sequence[Tuple[str, str]],
) -> Tuple[Dict[str, str], List[str]]:
    """
    Assign rotations to a single student.
    Each student gets: 6 core rotations + 2 selective rotations = 8 blocks total.
    
    Uses maximum flow algorithm to find optimal assignment respecting constraints.
    
    Args:
        student: The student to assign
        all_blocks: All available blocks
        core_rotations: List of mandatory core rotation names
        remaining_capacities: Available capacity for each rotation/block
        order_rules: Ordering constraints
        
    Returns:
        Tuple of (assignment_dict, error_list) where assignment_dict maps
        block -> rotation_name and error_list contains any warning messages
    """
    
    # Step 1: Select 2 selective rotations for this student
    # Priority: first choices, then second choices
    priorities = [
        student.first_choice_1,
        student.first_choice_2,
        student.second_choice_1,
        student.second_choice_2,
    ]
    selected_selectives: List[str] = []
    for rotation in priorities:
        if rotation and rotation not in selected_selectives and not rotation.lower().startswith("core"):
            selected_selectives.append(rotation)
        if len(selected_selectives) >= 2:
            break

    # If NAVLE is required and not already selected, add it
    if student.navle_required and "Selective NAVLE Review" not in selected_selectives:
        selected_selectives.insert(0, "Selective NAVLE Review")
        selected_selectives = selected_selectives[:2]

    # Final list: 6 cores + 2 selectives
    student_rotations = core_rotations + selected_selectives
    block_rank = {block: idx for idx, block in enumerate(all_blocks)}

    # Step 2: Use maximum flow to assign rotations to blocks
    # Build flow network:
    # source -> rotations -> blocks -> sink
    # Each rotation has capacity 1 (must be assigned once)
    # Each block has capacity 1 (can receive one rotation)
    # Edges between rotations and blocks added only if assignment is valid
    
    source = 0
    rotation_nodes = {rotation: idx + 1 for idx, rotation in enumerate(student_rotations)}
    block_nodes = {block: len(student_rotations) + 1 + idx for idx, block in enumerate(all_blocks)}
    sink = len(student_rotations) + 1 + len(all_blocks)
    graph = Dinic(sink + 1)

    # Source to rotations: each rotation must be assigned once
    for rotation, node in rotation_nodes.items():
        graph.add_edge(source, node, 1)

    # Blocks to sink: each block can receive at most one rotation
    for block, node in block_nodes.items():
        graph.add_edge(node, sink, 1)

    # Rotations to blocks: add edge if assignment is valid
    for rotation, rot_node in rotation_nodes.items():
        for block, block_node in block_nodes.items():
            # Skip if no capacity available
            if remaining_capacities[rotation][block] <= 0:
                continue
            # Skip if ordering constraints violated
            if not rotation_allowed_in_block(
                student,
                rotation,
                block,
                {},  # No prior assignments within this student's assignment
                all_blocks,
                remaining_capacities,
                order_rules,
                block_rank,
            ):
                continue
            graph.add_edge(rot_node, block_node, 1)

    # Run max flow algorithm
    flow = graph.max_flow(source, sink)
    if flow != len(student_rotations):
        return {}, [f"Unable to assign all {len(student_rotations)} rotations for {student.student_id}"]

    # Step 3: Extract assignments from flow graph
    assignments: Dict[str, str] = {}
    for block, block_node in block_nodes.items():
        for edge in graph.graph[block_node]:
            if edge.to == sink and edge.cap == 0:
                # Edge has 0 remaining capacity, so flow went through it
                # Find which rotation was assigned to this block
                for rev_edge in graph.graph[block_node]:
                    if rev_edge.to in rotation_nodes.values() and rev_edge.cap > 0:
                        rotation = next(name for name, node in rotation_nodes.items() if node == rev_edge.to)
                        assignments[block] = rotation
                        remaining_capacities[rotation][block] -= 1
                        break
                break

    return assignments, []


def write_allocation_output(
    path: Path,
    student_order: List[StudentChoice],
    block_names: List[str],
    assignments: Dict[str, Dict[str, str]],
    rotation_ids: Dict[str, str],
) -> None:
    """
    Write allocation results to CSV file.
    
    Args:
        path: Output CSV file path
        student_order: Ordered list of students
        block_names: List of block names for column headers
        assignments: Dict mapping student_id -> dict of block -> rotation_name
        rotation_ids: Dict mapping rotation_name -> rotation_id
    """
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Header: StudentID plus all blocks
        writer.writerow(["StudentID"] + block_names)
        # Data rows: student ID plus rotation ID for each block
        for student in student_order:
            row = [student.student_id]
            assignment = assignments[student.student_id]
            for block in block_names:
                rotation_name = assignment.get(block, "")
                rotation_id = rotation_ids.get(rotation_name, "")
                row.append(rotation_id if rotation_id else rotation_name)
            writer.writerow(row)


def main() -> None:
    """Main entry point. Parses arguments and runs the timetabling algorithm."""
    parser = argparse.ArgumentParser(description="Vet final-year rotation timetabling")
    parser.add_argument(
        "--capacities",
        type=Path,
        default=Path("rotation_capacities_example.csv"),
        help="Rotation capacity CSV file",
    )
    parser.add_argument(
        "--choices",
        type=Path,
        default=Path("student_choices_example.csv"),
        help="Student choice CSV file",
    )
    parser.add_argument(
        "--restrictions",
        type=Path,
        default=Path("sequence_restrictions_example.txt"),
        help="Natural-language restriction file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("allocation_output.csv"),
        help="Output allocation CSV file",
    )
    args = parser.parse_args()

    # Read input files
    block_names, capacities, rotation_ids = read_rotation_capacities(args.capacities)
    students = read_student_choices(args.choices)
    order_rules = parse_restrictions(args.restrictions, list(capacities.keys()))

    # Extract core rotations (those starting with "Core")
    student_count = len(students)
    core_rotations = [name for name in capacities if name.lower().startswith("core")]
    core_rotations.sort()

    # Create mutable capacity tracking (we'll decrement as students are assigned)
    remaining_capacities = {
        rotation: dict(values) for rotation, values in capacities.items()
    }

    # Perform assignment
    allocation_by_student = assign_rotations_to_students(
        students,
        core_rotations,
        block_names,
        remaining_capacities,
        order_rules,
    )

    # Calculate statistics
    first_choice_counts = 0
    second_choice_full_counts = 0

    for student in students:
        assigned_rotations = set(allocation_by_student[student.student_id].values())
        
        # Check if at least one first choice was satisfied
        has_first = (
            student.first_choice_1 in assigned_rotations
            or student.first_choice_2 in assigned_rotations
        )
        
        # Check if both second choices were satisfied
        has_second_both = (
            student.second_choice_1 in assigned_rotations
            and student.second_choice_2 in assigned_rotations
        )

        if has_first:
            first_choice_counts += 1
        if has_second_both:
            second_choice_full_counts += 1

    # Write output and print summary
    write_allocation_output(args.output, students, block_names, allocation_by_student, rotation_ids)

    print(f"Allocation written to {args.output}")
    print(f"Students assigned at least one first choice: {first_choice_counts}/{student_count}")
    print(f"Students assigned both second choices: {second_choice_full_counts}/{student_count}")


if __name__ == "__main__":
    main()
