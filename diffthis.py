import os
import filecmp

# Define the directories
current_dir = os.getcwd()  # Current working directory
compare_dir = os.path.join(current_dir, 'mestastic-utils')

# Get all .py files in the current directory
current_files = [f for f in os.listdir(current_dir) if f.endswith('.py')]
compare_files = [f for f in os.listdir(compare_dir) if f.endswith('.py')]

# Compare files
for file in current_files:
    if file in compare_files:
        # Compare the files using filecmp
        cmp_result = filecmp.cmp(os.path.join(current_dir, file), os.path.join(compare_dir, file), shallow=False)
        if cmp_result:
            print(f"{file} is the same")
        else:
            print(f"{file} differs")
    else:
        print(f"{file} does not exist in mestastic-utils/")
