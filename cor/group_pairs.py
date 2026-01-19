import csv
import random
import os

def load_correlation_data(filepath):
    correlations = {}
    pairs = set()
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        header_found = False
        for row in reader:
            if not row or len(row) < 7:
                continue
            if row[0] == 'pair1' and row[1] == 'pair2':
                header_found = True
                continue
            if not header_found:
                continue
            
            p1, p2, daily_cor = row[0], row[1], row[6]
            try:
                val = float(daily_cor)
                correlations[(p1, p2)] = val
                pairs.add(p1)
                pairs.add(p2)
            except ValueError:
                continue
    return sorted(list(pairs)), correlations

def calculate_score(buckets, correlations):
    score = 0
    high_cor_count = 0
    bucket_high_cor_counts = []
    
    for bucket in buckets:
        curr_bucket_high_cor = 0
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                p1, p2 = bucket[i], bucket[j]
                val = correlations.get((p1, p2))
                if val is None:
                    val = correlations.get((p2, p1), 100.0)
                
                abs_val = abs(val)
                score += abs_val
                if abs_val >= 65:
                    high_cor_count += 1
                    curr_bucket_high_cor += 1
        bucket_high_cor_counts.append(curr_bucket_high_cor)
    
    # Penalize the total count of high correlations heavily
    # Penalize the "max" high correlation count in any single bucket even more heavily to distribute them
    max_high_cor = max(bucket_high_cor_counts) if bucket_high_cor_counts else 0
    return high_cor_count * 10000 + max_high_cor * 100000 + score

def group_pairs(pairs, correlations, num_buckets=5):
    best_buckets = None
    best_score = float('inf')
    
    # Try more random restarts for a deeper search
    for _ in range(100):
        current_buckets = [[] for _ in range(num_buckets)]
        pair_list = list(pairs)
        random.shuffle(pair_list)
        for i, p in enumerate(pair_list):
            current_buckets[i % num_buckets].append(p)
        
        current_score = calculate_score(current_buckets, correlations)
        
        improved = True
        while improved:
            improved = False
            # Randomly shuffle buckets to browse
            b_indices = list(range(num_buckets))
            random.shuffle(b_indices)
            
            for b_idx in b_indices:
                if not current_buckets[b_idx]: continue
                
                # Randomly shuffle pairs within bucket
                p_indices = list(range(len(current_buckets[b_idx])))
                random.shuffle(p_indices)
                
                for p_idx in p_indices:
                    p = current_buckets[b_idx][p_idx]
                    
                    target_b_indices = list(range(num_buckets))
                    random.shuffle(target_b_indices)
                    
                    for target_b_idx in target_b_indices:
                        if b_idx == target_b_idx: continue
                        
                        # Move
                        item = current_buckets[b_idx].pop(p_idx)
                        current_buckets[target_b_idx].append(item)
                        new_score = calculate_score(current_buckets, correlations)
                        
                        if new_score < current_score:
                            current_score = new_score
                            improved = True
                            break # Found improvement, restart bucket loops
                        else:
                            # Move back
                            current_buckets[target_b_idx].pop()
                            current_buckets[b_idx].insert(p_idx, item)
                    if improved: break
                if improved: break
        
        if current_score < best_score:
            best_score = current_score
            best_buckets = [list(b) for b in current_buckets]
            
    return best_buckets

def generate_md_report(buckets, correlations, output_path):
    with open(output_path, 'w') as f:
        f.write("# FX Pair Correlation Buckets\n\n")
        f.write("Pairs grouped into 5 buckets to minimize intra-bucket absolute correlation (Daily).\n\n")
        
        for idx, bucket in enumerate(buckets):
            f.write(f"## Bucket {idx + 1}\n\n")
            f.write("| | " + " | ".join(bucket) + " |\n")
            f.write("|---" + "|---" * len(bucket) + "|\n")
            for p1 in bucket:
                row = [p1]
                for p2 in bucket:
                    if p1 == p2:
                        row.append("100")
                    else:
                        val = correlations.get((p1, p2))
                        if val is None:
                            val = correlations.get((p2, p1))
                        
                        if val is not None:
                            # Highlight if abs(val) >= 65
                            if abs(val) >= 65:
                                # Red for positive high, Orange/Red for negative high? 
                                # Let's stick to red for any high absolute correlation
                                row.append(f'<span style="color:red">**{val}**</span>')
                            else:
                                row.append(str(val))
                        else:
                            row.append("N/A")
                f.write("| " + " | ".join(row) + " |\n")


            f.write("\n")

if __name__ == "__main__":
    csv_path = r'd:\Trading\MT5Enhance\cor\correlation.csv'
    report_path = r'd:\Trading\MT5Enhance\cor\buckets_report.md'
    pairs, correlations = load_correlation_data(csv_path)
    final_buckets = group_pairs(pairs, correlations)
    generate_md_report(final_buckets, correlations, report_path)
    print(f"Report generated at {report_path}")
