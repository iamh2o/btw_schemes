import sys
import os
import re

# Set the directory where the files are located
directory = sys.argv[1]

# Regular expression to capture the leading string of integers followed by an underscore
pattern = re.compile(r'^\d+_')

# Process each file in the directory
for filename in os.listdir(directory):
    # Check if the filename matches the pattern
    new_name = pattern.sub('', filename)
    # If the name has changed, rename the file
    if new_name != filename:
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        print(f'Renamed: {old_path} -> {new_path}')
