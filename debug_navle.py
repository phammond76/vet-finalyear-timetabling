import csv

# Check the allocation and print detailed info
with open('allocation_output.csv', 'r') as f:
    reader = csv.DictReader(f)
    students = list(reader)

# Check student preferences
with open('student_choices_example.csv', 'r') as f:
    prefs_reader = csv.DictReader(f)
    prefs = {row['StudentID']: row for row in prefs_reader}

# Analyze NAVLE students who prefer Block5
print("NAVLE students who prefer Block5:")
for sid in ['S001', 'S006', 'S012', 'S018']:
    row = [s for s in students if s['StudentID'] == sid][0]
    pref = prefs[sid]
    blocks = []
    for i in range(1, 11):
        if row[f'Block{i}']:
            blocks.append(i)
    print(f"\n{sid}: prefers {pref.get('NAVLE_preferred_block')}")
    print(f"  Assigned to blocks: {blocks}")
    print(f"  Block assignments: {[row[f'Block{i}'] for i in range(1, 11)]}")
