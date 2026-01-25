import pandas as pd
import os
import sys
from datetime import datetime

# Force unbuffered output (Windows compatible)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except:
        pass

def read_inputs_from_file(filename, file_ext):
    inside_inputs = False
    data = []
    
    if file_ext == 'chr':
        with open(filename, 'r', encoding='utf-16') as file:
            for line in file:
                # print(line)
                if '<inputs>' in line:
                    inside_inputs = True
                    continue
                elif '</inputs>' in line:
                    inside_inputs = False
                    continue
                if line.startswith('='):
                    blank = True
                else:
                    blank = False
                
                if inside_inputs and not blank:
                    data.append(line.strip())
                    
        if not data:
            raise ValueError(f"No inputs found in {filename}")
            
        df = pd.DataFrame([x.split('=') for x in data]).transpose()
        df.columns = df.iloc[0]
        df = df[1:]
        
    elif file_ext == 'set':
        # Try different encodings - UTF-16 first, then UTF-8, then latin-1
        file_encoding = None
        file_content = None
        
        for encoding in ['utf-16', 'utf-8', 'latin-1']:
            try:
                with open(filename, 'r', encoding=encoding) as file:
                    file_content = file.readlines()
                file_encoding = encoding
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if file_encoding is None or file_content is None:
            raise ValueError(f"Could not determine encoding for {filename}")
        
        # Process the content
        for line in file_content:
            if ';' not in line:
                first_part = line.split('||')[0].strip()
                data.append(first_part.split('='))
        
        if not data:
            raise ValueError(f"No data found in file {filename}")
        
        df = pd.DataFrame(data).transpose()
        if len(df) == 0:
            raise ValueError(f"Empty DataFrame created from {filename}")
        df.columns = df.iloc[0]
        df = df[1:]
    
    return df


    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sets2csv.py <directory_path>")
        sys.exit(1)

    # Directory containing your files
    directory = sys.argv[1]
    
    # Verify directory exists
    if not os.path.exists(directory):
        error_msg = f"Error: Directory does not exist: {directory}"
        print(error_msg, flush=True)
        log_path = os.path.join(directory, 'error_log.txt') if os.path.exists(os.path.dirname(directory)) else 'error_log.txt'
        try:
            with open(log_path, 'w') as f:
                f.write(error_msg + '\n')
        except:
            with open('error_log.txt', 'w') as f:
                f.write(error_msg + '\n')
        sys.exit(1)
    
    if not os.path.isdir(directory):
        error_msg = f"Error: Path is not a directory: {directory}"
        print(error_msg, flush=True)
        with open(os.path.join(directory, 'error_log.txt'), 'w') as f:
            f.write(error_msg + '\n')
        sys.exit(1)

    # Detect file types in root
    files_root = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    has_set_root = any(f.lower().endswith('.set') for f in files_root)
    has_chr_root = any(f.lower().endswith('.chr') for f in files_root)

    process_chr = False
    process_set = False
    set_directory = directory

    if has_set_root and has_chr_root:
        error_msg = "Error: Input directory contains both *.set and *.chr files. Please provide a directory with only one type."
        print(error_msg, flush=True)
        with open(os.path.join(directory, 'error_log.txt'), 'w') as f:
            f.write(error_msg + '\n')
        sys.exit(1)
    
    if has_set_root:
        process_set = True
        set_directory = directory
        file_ext_name = 'set'
    elif has_chr_root:
        process_chr = True
        file_ext_name = 'chr'
        # Check for sets or set subdirectory
        for subdir_name in ['sets', 'set']:
            subdir_path = os.path.join(directory, subdir_name)
            if os.path.isdir(subdir_path):
                subdir_files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.set')]
                if subdir_files:
                    process_set = True
                    set_directory = subdir_path
                    file_ext_name = 'chr_and_set'
                    break
    else:
        error_msg = f"Error: No .set or .chr files found in {directory}"
        print(error_msg, flush=True)
        with open(os.path.join(directory, 'error_log.txt'), 'w') as f:
            f.write(error_msg + '\n')
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f'all_sets_{file_ext_name}_{timestamp}.csv'
    
    chr_dfs = []
    set_dfs = []

    # Process CHR files if found in root
    if process_chr:
        for filename in files_root:
            if filename.lower().endswith('.chr'):
                try:
                    df = read_inputs_from_file(os.path.join(directory, filename), 'chr')
                    df.insert(0, 'Filename', filename)
                    chr_dfs.append(df)
                except Exception as e:
                    print(f"Error reading chr file {filename}: {e}")
                    continue

    # Process SET files if found in root or subdir
    if process_set:
        files_set = [f for f in os.listdir(set_directory) if f.lower().endswith('.set')]
        for filename in files_set:
            try:
                df = read_inputs_from_file(os.path.join(set_directory, filename), 'set')
                df.insert(0, 'Filename', filename)
                set_dfs.append(df)
            except Exception as e:
                print(f"Error reading set file {filename}: {e}")
                continue

    try:
        output_path = os.path.join(directory, out_file)
        
        if chr_dfs and set_dfs:
            # Both types processed
            final_chr_df = pd.concat(chr_dfs, ignore_index=True)
            final_set_df = pd.concat(set_dfs, ignore_index=True)
            
            # Write CHR table
            final_chr_df.to_csv(output_path, index=False)
            
            # Append empty rows and SET table
            with open(output_path, 'a', newline='') as f:
                f.write('\n\n\n') # 3 empty rows
            
            final_set_df.to_csv(output_path, mode='a', index=False)
            success_msg = f"Data (CHR and SET) has been written to {output_path}"
        
        elif chr_dfs:
            final_chr_df = pd.concat(chr_dfs, ignore_index=True)
            final_chr_df.to_csv(output_path, index=False)
            success_msg = f"Data (CHR only) has been written to {output_path}"
            
        elif set_dfs:
            final_set_df = pd.concat(set_dfs, ignore_index=True)
            final_set_df.to_csv(output_path, index=False)
            success_msg = f"Data (SET only) has been written to {output_path}"
        else:
            raise ValueError("No data extracted from any files.")

        print(success_msg, flush=True)

    except Exception as e:
        error_msg = f"Error processing files: {e}"
        print(error_msg, flush=True)
        import traceback
        traceback.print_exc()
        with open(os.path.join(directory, 'error_log.txt'), 'w') as f:
            f.write(error_msg + '\n')
            traceback.print_exc(file=f)
        sys.exit(1)
