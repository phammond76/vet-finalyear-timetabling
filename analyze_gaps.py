import csv

with open('allocation_output.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Get assigned blocks
        blocks = []
        for i in range(1, 11):
            block_key = f'Block{i}'
            if row[block_key]:
                blocks.append(i)
        
        # Calculate max run length
        max_run = 1
        current_run = 1
        for i in range(1, len(blocks)):
            if blocks[i] == blocks[i-1] + 1:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        
        num_rotations = len(blocks)
        print(f"{row['StudentID']}: {num_rotations} rotations, blocks {blocks}, max run length: {max_run}")
