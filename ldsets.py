import os
import argparse
import re
import math
import shutil
from bs4 import BeautifulSoup

def parse_max_trades(html_path):
    """
    Parses Full_Analysis.html and returns a dictionary mapping report basename to Max Trades.
    """
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return {}

    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    report_max_trades = {}

    # Find all h3 tags which represent report sections
    sections = soup.find_all('h3')
    for h3 in sections:
        h3_text = h3.get_text()
        if 'Report:' not in h3_text:
            continue
        
        # Extract report name (e.g., "1. Report: ADX_BB_AUDJPY_1_5674")
        # The link within h3 usually has the base name
        a_tag = h3.find('a')
        if a_tag:
            report_name = a_tag.get_text(strip=True)
        else:
            report_name = h3_text.split('Report:')[-1].strip()

        # Look for "Max Trades in Sequence" in the metrics list following the h3
        metrics_list = h3.find_next('ul', class_='metrics-list')
        if metrics_list:
            for li in metrics_list.find_all('li'):
                li_text = li.get_text()
                if 'Max Trades in Sequence' in li_text:
                    # Match "Max Trades in Sequence: 6 [2025-01-02]" or "Max Trades in Sequence: 6"
                    match = re.search(r'Max Trades in Sequence[:\s]+(\d+)', li_text)
                    if match:
                        max_trades = int(match.group(1))
                        report_max_trades[report_name] = max_trades
                        break

    return report_max_trades

def update_set_file(src_path, dst_path, live_delay):
    """
    Copies a set file and updates the LiveDelay parameter.
    """
    try:
        # Detect encoding
        content = None
        for enc in ['utf-16', 'utf-16-le', 'utf-8', 'latin-1', 'cp1252']:
            try:
                with open(src_path, 'r', encoding=enc, errors='ignore') as f:
                    content = f.read()
                    if '=' in content:
                        used_enc = enc
                        break
            except:
                continue
        
        if content is None:
            print(f"Warning: Could not read {src_path}")
            return False

        lines = content.splitlines()
        new_lines = []
        found = False
        for line in lines:
            if '=' in line:
                key = line.split('=')[0].strip()
                if key.lower() == 'livedelay':
                    # MT5 set files might have || after value for comments
                    parts = line.split('||', 1)
                    if len(parts) > 1:
                        new_lines.append(f"LiveDelay={live_delay}||{parts[1]}")
                    else:
                        new_lines.append(f"LiveDelay={live_delay}")
                    found = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if not found:
            # If LiveDelay was not in the file, we can optionally add it at the end
            # But usually it should be there.
            new_lines.append(f"LiveDelay={live_delay}")

        with open(dst_path, 'w', encoding=used_enc) as f:
            f.write('\n'.join(new_lines) + '\n')
        return True
    except Exception as e:
        print(f"Error updating {src_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create LiveDelay variations of set files based on Max Trades.')
    parser.add_argument('output_dir', type=str, help='Path to the analysis output directory (e.g., analysis/output_*)')
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    html_path = os.path.join(output_dir, "Full_Analysis.html")
    sets_dir = os.path.join(output_dir, "sets")
    ldsets_dir = os.path.join(output_dir, "ldsets")

    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return

    if not os.path.exists(sets_dir):
        print(f"Error: Sets directory not found at {sets_dir}")
        return

    # 1. Create ldsets folder
    os.makedirs(ldsets_dir, exist_ok=True)
    print(f"Created directory: {ldsets_dir}")

    # 2. Extract Max Trades from report
    report_max_trades = parse_max_trades(html_path)
    print(f"Extracted Max Trades for {len(report_max_trades)} reports.")

    # 3. Process each report
    created_count = 0
    for report_name, max_trades in report_max_trades.items():
        if max_trades > 4:
            max_ld = math.floor(max_trades / 2)
            print(f"Processing {report_name}: Max Trades = {max_trades}, Creating {max_ld} variations...")

            # Locate original set file
            src_set_path = os.path.join(sets_dir, f"{report_name}.set")
            if not os.path.exists(src_set_path):
                # Try case-insensitive or partial match if needed, but Step 1 (list.py) copies it as {basename}.set
                print(f"  Warning: Original set file not found at {src_set_path}")
                continue

            # 4. Create max_ld variations
            for ld in range(1, max_ld + 1):
                dst_set_name = f"{report_name}_ld{ld}.set"
                dst_set_path = os.path.join(ldsets_dir, dst_set_name)
                
                if update_set_file(src_set_path, dst_set_path, ld):
                    created_count += 1
        else:
            # print(f"Skipping {report_name}: Max Trades = {max_trades} (<= 4)")
            pass

    print(f"\nDone. Created {created_count} new set files in {ldsets_dir}.")

if __name__ == "__main__":
    main()
