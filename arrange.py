"""
arrange.py - File Organizer for MT5 Reports

This script organizes files in a /Hunted subdirectory into a structured format.
The resulting 'Hunted/arranged' folder is designed to be the parent directory 
for subsequent analysis scripts like 'list.py'.

Usage:
    python arrange.py <root_directory>
"""

import os
import shutil
import glob
import argparse

def arrange_files():
    parser = argparse.ArgumentParser(description='Arrange files in /Hunted folder into a structured hierarchy.')
    parser.add_argument('root_dir', type=str, help='Root directory containing the Hunted folder.')
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root_dir)
    hunted_path = os.path.join(root_dir, "Hunted")

    if not os.path.isdir(hunted_path):
        print(f"Error: Hunted folder not found in {root_dir}")
        return

    # 2. Create the following folder structure:
    # a. /Hunted/arranged
    # b. /Hunted/arranged/HTML Reports
    # c. /Hunted/arranged/CSV
    # d. /Hunted/arranged/Graphs
    arranged_path = os.path.join(hunted_path, "arranged")
    html_reports_path = os.path.join(arranged_path, "HTML Reports")
    csv_path = os.path.join(arranged_path, "CSV")
    graphs_path = os.path.join(arranged_path, "Graphs")

    folders_to_create = [arranged_path, html_reports_path, csv_path, graphs_path]
    for folder in folders_to_create:
        os.makedirs(folder, exist_ok=True)
        print(f"Ensured directory: {folder}")

    # 3. All *.set files from /Hunted should be copied to /Hunted/arranged
    set_files = glob.glob(os.path.join(hunted_path, "*.set"))
    for f in set_files:
        shutil.copy2(f, arranged_path)
    print(f"Copied {len(set_files)} .set files to {arranged_path}")

    # 4. All *.parquet files from /Hunted should be copied to /Hunted/arranged/CSV
    parquet_files = glob.glob(os.path.join(hunted_path, "*.parquet"))
    for f in parquet_files:
        shutil.copy2(f, csv_path)
    print(f"Copied {len(parquet_files)} .parquet files to {csv_path}")

    # 5. Copy all *.htm and ALL *.png files to /Hunted/arranged/HTML Reports
    #    Additionally, copy "remaining" *.png files (not matching standard report patterns) to /Hunted/arranged/Graphs
    html_patterns = [
        "*_overview.png",
        "*_holding.png",
        "*holding.png",
        "*-hst.png",
        "*-mfemae.png"
    ]
    
    all_pngs = set(glob.glob(os.path.join(hunted_path, "*.png")))
    specific_pngs = set()
    for pattern in html_patterns:
        specific_pngs.update(glob.glob(os.path.join(hunted_path, pattern)))
    
    # All .htm and all .png to HTML Reports
    html_files = glob.glob(os.path.join(hunted_path, "*.htm")) + list(all_pngs)
    for f in html_files:
        shutil.copy2(f, html_reports_path)
    print(f"Copied {len(html_files)} files (.htm and all .png) to {html_reports_path}")

    # 6. Copy remaining *.png files to Graphs
    remaining_pngs = all_pngs - specific_pngs
    for f in remaining_pngs:
        shutil.copy2(f, graphs_path)
    print(f"Copied {len(remaining_pngs)} remaining .png files to {graphs_path}")

    print("\nFile arrangement complete.")
    print(f"The directory '{arranged_path}' is now ready for list.py.")

if __name__ == "__main__":
    arrange_files()
