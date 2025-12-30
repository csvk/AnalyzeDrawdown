import pandas as pd
import os
import shutil
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse
from datetime import datetime
import numpy as np
import math

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Portfolio Analysis')
    parser.add_argument('output_folder', type=str, help='Path to the output folder created in Step 1 (e.g., analysis/output_*).')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--base', type=float, default=100000.0, help='Base capital (default: 100,000)')
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_folder)

    # 1. Locate Trades folder and create Charts folder
    trades_folder = os.path.join(output_dir, "Trades")
    charts_folder = os.path.join(output_dir, "charts")
    
    if os.path.exists(charts_folder):
        print(f"Refreshing charts folder: {charts_folder}")
        shutil.rmtree(charts_folder)
        
    os.makedirs(charts_folder, exist_ok=True)
    
    if not os.path.exists(trades_folder):
        print(f"Error: Trades folder not found in {output_dir}")
        return
    
    os.makedirs(charts_folder, exist_ok=True)
    print(f"Using trades folder: {trades_folder}")
    print(f"Saving charts to: {charts_folder}")

    # 2. Load all deals
    csv_files = glob.glob(os.path.join(trades_folder, "selected_trades_*.csv"))
    all_deals = []
    if csv_files:
        for f in csv_files:
            df = pd.read_csv(f)
            df['Time'] = pd.to_datetime(df['Time'])
            all_deals.append(df)
        df_deals = pd.concat(all_deals).sort_values('Time')
        # Calculate DealPnL on the fly (Profit + Commission + Swap)
        df_deals['DealPnL'] = df_deals['Profit'] + df_deals['Commission'] + df_deals['Swap']
    else:
        df_deals = pd.DataFrame(columns=['Time', 'SourceFile', 'Direction', 'Profit', 'Commission', 'Swap', 'DealPnL'])
        print("Note: No portfolio-wide selected trades found. Proceeding with detailed report analysis only.")

    # 3. Determine Date Range
    if not df_deals.empty:
        data_start = df_deals['Time'].min().normalize()
        data_end = df_deals['Time'].max().normalize() + pd.Timedelta(days=1)
    else:
        # Fallback to current year or some sensible default if everything is empty
        data_start = pd.Timestamp.now().normalize() - pd.Timedelta(days=365)
        data_end = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
    
    calc_start = pd.to_datetime(args.start) if args.start else data_start
    calc_end = pd.to_datetime(args.end) if args.end else data_end

    print(f"Analysis range: {calc_start.date()} to {calc_end.date()}")

    # 4. Filter deals by date range
    if not df_deals.empty:
        df_deals = df_deals[(df_deals['Time'] >= calc_start) & (df_deals['Time'] < calc_end)]

    if df_deals.empty:
        print("No trades found in the specified date range for portfolio aggregation.")
        # Create an empty portfolio dataframe to satisfy later plotting code if necessary
        # Or simply skip the portfolio overview part
        portfolio = pd.DataFrame(columns=['Balance', 'Drawdown%', 'PeakBalance'])
    else:
        # 5. Create Portfolio Timeline
        # We create a 1-minute grid
        full_idx = pd.date_range(start=calc_start, end=calc_end, freq='1min')
        portfolio = pd.DataFrame(index=full_idx)
        portfolio['BalancePnL'] = 0.0

        # Group deals by minute to avoid duplicates on the grid
        deals_grouped = df_deals.copy()
        deals_grouped['Time'] = deals_grouped['Time'].dt.floor('1min')
        
        # Balance changes only at exit ('out' or 'in/out')
        balance_deals = deals_grouped[deals_grouped['Direction'].str.lower().isin(['out', 'in/out'])]
        balance_changes = balance_deals.groupby('Time')['DealPnL'].sum()

        # Map to grid
        portfolio.loc[balance_changes.index, 'BalancePnL'] = balance_changes.values

        # Cumulative Sums
        portfolio['Balance'] = portfolio['BalancePnL'].cumsum() + args.base

        # 6. Drawdown Calculation (Underwater)
        portfolio['PeakBalance'] = portfolio['Balance'].expanding().max()
        portfolio['Drawdown'] = (portfolio['Balance'] / portfolio['PeakBalance']) - 1
        # Note: Using Balance for drawdown as is typical.
        portfolio['Drawdown%'] = portfolio['Drawdown'] * 100

    # 7. Charting
    overview_chart_path = os.path.join(charts_folder, "Portfolio_Overview.png")
    if not portfolio.empty:
        def add_monthly_grids(ax, start, end):
            # Add vertical lines at start of each month
            months = pd.date_range(start=start.replace(day=1), end=end, freq='MS')
            for m in months:
                ax.axvline(m, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)

        # 7. Portfolio Overview Chart (1x2: Balance and Drawdown)
        fig_overview, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Plot 1: Portfolio Balance
        ax1.plot(portfolio.index, portfolio['Balance'], label='Balance', color='blue', linewidth=1.5)
        ax1.set_title('Portfolio Performance (Balance)', fontsize=14)
        ax1.set_ylabel('Amount')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        add_monthly_grids(ax1, calc_start, calc_end)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')

        # Plot 2: Underwater Drawdown
        ax2.fill_between(portfolio.index, portfolio['Drawdown%'], 0, color='red', alpha=0.3)
        ax2.plot(portfolio.index, portfolio['Drawdown%'], color='red', linewidth=0.8)
        ax2.set_title('Underwater Drawdown', fontsize=14)
        ax2.set_ylabel('Drawdown %')
        ax2.grid(True, alpha=0.3)
        add_monthly_grids(ax2, calc_start, calc_end)

        # Add secondary Y-axis for absolute drawdown values
        ax2_abs = ax2.twinx()
        abs_drawdown = portfolio['Balance'] - portfolio['PeakBalance']
        ax2_abs.plot(portfolio.index, abs_drawdown, alpha=0) 
        ax2_abs.set_ylabel('Drawdown Absolute')
        ax2_abs.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')

        plt.tight_layout()
        plt.savefig(overview_chart_path)
        plt.close()
    else:
        # Create a placeholder or just don't save. Later code will check for file existence.
        print("Skipping Portfolio Overview chart as portfolio is empty.")

    # 8. Consolidated Monthly Contributor Table (with Gradient Color Coding)
    table_html = ""
    if not df_deals.empty:
        df_deals['Month'] = df_deals['Time'].dt.to_period('M')
        # Group by File, Symbol, and Month
        file_monthly_pnl = df_deals.groupby(['SourceFile', 'Symbol', 'Month'])['DealPnL'].sum().reset_index()
        
        # Pivot to get months as columns, keep SourceFile and Symbol as indices
        pivot_table = file_monthly_pnl.pivot(index=['Symbol', 'SourceFile'], columns='Month', values='DealPnL').fillna(0)
        
        # Sort by Symbol (which is the first level of the index) then SourceFile
        pivot_table = pivot_table.sort_index(level=['Symbol', 'SourceFile'])

        def get_color(val, min_val, max_val):
            if val == 0: return "#ffffff" # White for zero
            if val > 0:
                # Green gradient
                alpha = min(val / (max_val if max_val > 0 else 1), 1)
                r = int(255 - (255 - 34) * alpha)
                g = int(255 - (255 - 197) * alpha)
                b = int(255 - (255 - 94) * alpha)
                return f"#{r:02x}{g:02x}{b:02x}"
            else:
                # Red gradient
                alpha = min(abs(val) / (abs(min_val) if min_val < 0 else 1), 1)
                r = int(255 - (255 - 239) * alpha)
                g = int(255 - (255 - 68) * alpha)
                b = int(255 - (255 - 68) * alpha)
                return f"#{r:02x}{g:02x}{b:02x}"

        # Calculate global min/max for the gradient scale
        all_values = pivot_table.values.flatten()
        global_min = all_values.min()
        global_max = all_values.max()

        months_headers = [str(m) for m in pivot_table.columns]
        
        table_html = "## Monthly Contributor Breakdown\n\n"
        table_html += "<table>\n<thead>\n<tr>"
        table_html += "<th>S.No</th><th>Symbol</th><th>Report File</th>" + "".join([f"<th>{m}</th>" for m in months_headers]) + "<th>Total</th>"
        table_html += "</tr>\n</thead>\n<tbody>\n"
        
        for i, ((symbol, file_name), row) in enumerate(pivot_table.iterrows(), 1):
            table_html += "<tr>"
            table_html += f"<td>{i}</td>"
            table_html += f"<td>{symbol}</td>"
            table_html += f"<td><code>{file_name}</code></td>"
            for val in row:
                color = get_color(val, global_min, global_max)
                table_html += f'<td style="background-color:{color}; color:black; text-align:right;">{val:.2f}</td>'
            
            total_pnl_val = row.sum()
            total_color = get_color(total_pnl_val, pivot_table.sum(axis=1).min(), pivot_table.sum(axis=1).max())
            table_html += f'<td style="background-color:{total_color}; color:black; text-align:right;"><b>{total_pnl_val:.2f}</b></td>'
            table_html += "</tr>\n"
        
        # Total row
        monthly_totals = pivot_table.sum()
        grand_total = monthly_totals.sum()
        table_html += "<tr>"
        table_html += "<td colspan='3'><b>Total</b></td>"
        for val in monthly_totals:
            color = get_color(val, monthly_totals.min(), monthly_totals.max())
            table_html += f'<td style="background-color:{color}; color:black; text-align:right;"><b>{val:.2f}</b></td>'
        
        gt_color = get_color(grand_total, pivot_table.values.sum(), pivot_table.values.sum())
        table_html += f'<td style="background-color:{gt_color}; color:black; text-align:right;"><b>{grand_total:.2f}</b></td>'
        table_html += "</tr>\n</tbody>\n</table>\n\n"
    else:
        table_html = "No trades included in the aggregate portfolio for the specified period.\n\n"



    # 9. Compile Markdown Report
    num_included = df_deals['SourceFile'].nunique()
    
    # Try to find the total number of files and skipped files from report_list_<timestamp>.csv
    num_total = "Unknown"
    explicitly_skipped = []
    overlapping_skipped = []
    
    report_list_path = os.path.join(output_dir, "report_list.csv")
    if os.path.exists(report_list_path):
        try:
            df_list = pd.read_csv(report_list_path)
            num_total = len(df_list)
            
            # Categorize skipped files
            actually_included = set(df_deals['SourceFile'].unique()) if not df_deals.empty else set()
            
            explicitly_excluded_paths = df_list[df_list['Include'] == 0]['FilePath']
            explicitly_skipped = sorted([os.path.basename(f) for f in explicitly_excluded_paths])
            
            potentially_included_paths = df_list[df_list['Include'] == 1]['FilePath']
            potentially_included = set(os.path.basename(f) for f in potentially_included_paths)
            
            overlapping_skipped = sorted(list(potentially_included - actually_included))
        except:
            pass

    report_path = os.path.join(output_dir, "Full_Analysis.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Portfolio Analysis Report\n\n")
        f.write(f"**Period:** {calc_start.date()} to {calc_end.date()}\n")
        f.write(f"**Included Reports:** {num_included} / {num_total}\n")
        f.write(f"**Base Capital:** {args.base:,.2f}\n")
        
        final_balance = portfolio['Balance'].iloc[-1] if not portfolio.empty and 'Balance' in portfolio.columns else args.base
        f.write(f"**Final Balance:** {final_balance:,.2f}\n")
        f.write(f"**Total Profit:** {(final_balance - args.base):,.2f}\n\n")
        
        f.write("## Performance Charts\n\n")
        overview_path = "charts/Portfolio_Overview.png"
        if os.path.exists(os.path.join(output_dir, overview_path)):
            f.write(f"![Portfolio Overview]({overview_path})\n\n")
        else:
            f.write("Portfolio Overview chart is not available (no portfolio-wide trades found).\n\n")
        
        f.write(table_html)

        if explicitly_skipped:
            f.write("## Explicitly Excluded Reports\n\n")
            f.write("These files were skipped because they were marked with `Include = 0` in the report list:\n\n")
            for sf in explicitly_skipped:
                f.write(f"- `{sf}`\n")
            f.write("\n")

        if overlapping_skipped:
            f.write("## Overlapping Trades (Skipped)\n\n")
            f.write("These files were marked for inclusion but skipped because all their trades overlapped with already accepted sequences:\n\n")
            for sf in overlapping_skipped:
                f.write(f"- `{sf}`\n")
            f.write("\n")

        # 10. Detailed Per-Report Analysis
        f.write("## Detailed Per-Report Analysis\n\n")
        
        all_trades_files = glob.glob(os.path.join(trades_folder, "all_trades_*.csv"))
        
        def load_parquet_data(html_file_path):
            """Tries to find and load corresponding parquet file from sibling CSV folder."""
            try:
                base_dir = os.path.dirname(html_file_path)
                csv_folder = os.path.join(os.path.dirname(base_dir), "CSV")
                if not os.path.exists(csv_folder):
                    return None
                
                filename_no_ext = os.path.splitext(os.path.basename(html_file_path))[0]
                parquet_pattern = os.path.join(csv_folder, f"{filename_no_ext}*.parquet")
                matches = glob.glob(parquet_pattern)
                
                if not matches:
                    return None
                    
                p_df = pd.read_parquet(matches[0])
                if p_df.empty: return None
                
                # Parse tab-separated format
                cols = p_df.columns[0].split('\t')
                data = [row[0].split('\t') for row in p_df.values]
                df_parsed = pd.DataFrame(data, columns=cols)
                
                # Cleanup names and types
                df_parsed.columns = [c.replace('<', '').replace('>', '').strip() for c in df_parsed.columns]
                df_parsed['DATE'] = pd.to_datetime(df_parsed['DATE'], format='%Y.%m.%d %H:%M', errors='coerce')
                df_parsed = df_parsed.dropna(subset=['DATE'])
                
                for c in ['BALANCE', 'EQUITY']:
                    if c in df_parsed.columns:
                        df_parsed[c] = pd.to_numeric(df_parsed[c], errors='coerce').fillna(0)
                        
                return df_parsed.sort_values('DATE')
            except Exception as e:
                print(f"Warning: Could not parse parquet for {html_file_path}: {e}")
                return None

        def parse_set_file(html_file_path):
            """Reads .set file from parent directory above the report directory."""
            params = {
                "LotSize": "N/A",
                "MaxLots": "N/A",
                "LotSizeExponent": "N/A",
                "DelayTradeSequence": "N/A",
                "LiveDelay": "N/A"
            }
            try:
                report_dir = os.path.dirname(html_file_path)
                parent_dir = os.path.dirname(report_dir)
                base_name = os.path.splitext(os.path.basename(html_file_path))[0]
                set_path = os.path.join(parent_dir, f"{base_name}.set")

                if not os.path.exists(set_path):
                    # Try current directory too just in case
                    set_path_alt = os.path.join(report_dir, f"{base_name}.set")
                    if os.path.exists(set_path_alt):
                        set_path = set_path_alt
                    else:
                        return params

                content = None
                for enc in ['utf-16', 'utf-8']:
                    try:
                        with open(set_path, 'r', encoding=enc, errors='ignore') as sf:
                            content = sf.read()
                            if '=' in content:
                                break
                    except:
                        continue
                
                if content:
                    for line in content.splitlines():
                        if '=' in line:
                            key, val = line.split('=', 1)
                            key = key.strip()
                            if key in params:
                                params[key] = val.strip()
                return params
            except Exception as e:
                print(f"Warning: Could not parse .set file for {html_file_path}: {e}")
                return params

        if not all_trades_files:
            f.write("No detailed trade files found.\n")
        else:
            # Sort files for consistent report order
            all_trades_files.sort()
            # Create sets for easy lookup
            included_files = set(df_deals['SourceFile'].unique()) if not df_deals.empty else set()
            
            # Get original HTML paths from report_list.csv for parquet lookup
            html_path_map = {}
            if os.path.exists(report_list_path):
                try:
                    df_list_tmp = pd.read_csv(report_list_path)
                    for _, row in df_list_tmp.iterrows():
                        html_path_map[os.path.basename(row['FilePath'])] = row['FilePath']
                except: pass

            # Iterate through all files specified in report_list.csv to ensure all are shown
            all_reports_to_show = []
            if os.path.exists(report_list_path):
                try:
                    df_list_all = pd.read_csv(report_list_path)
                    for _, row_all in df_list_all.iterrows():
                        fname = os.path.basename(row_all['FilePath'])
                        basename = os.path.splitext(fname)[0]
                        all_reports_to_show.append({
                            'basename': basename,
                            'original_filename': fname,
                            'full_html_path': row_all['FilePath']
                        })
                except:
                    # Fallback to current behavior if list reading fails
                    for atf in all_trades_files:
                        bn = os.path.basename(atf).replace("all_trades_", "").replace(".csv", "")
                        all_reports_to_show.append({'basename': bn, 'original_filename': bn + ".html", 'full_html_path': None})
            
            for idx, r_info in enumerate(all_reports_to_show, 1):
                report_basename = r_info['basename']
                original_filename = r_info['original_filename']
                full_html_path = r_info['full_html_path']
                
                # Initialize per-report metrics
                total_pnl = None
                max_dd_abs = None
                max_dd_pct = None
                df_parquet = None
                set_params = None
                
                atf = os.path.join(trades_folder, f"all_trades_{report_basename}.csv")
                
                if not os.path.exists(atf):
                    f.write(f"### {idx}. Report: {report_basename}\n\n")
                    f.write(f"- **Status**: Skipped (File could not be parsed or has no trades)\n\n")
                    continue

                df_at = pd.read_csv(atf)
                
                # Calculate DealPnL - exclude 'balance' type rows to get profit only
                df_at['Direction_lower'] = df_at['Direction'].astype(str).str.lower()
                df_pnl_only = df_at[df_at['Direction_lower'].isin(['in', 'out', 'in/out'])]
                
                df_at['DealPnL'] = df_at['Profit'] + df_at['Commission'] + df_at['Swap']
                total_pnl = df_pnl_only['Profit'].sum() + df_pnl_only['Commission'].sum() + df_pnl_only['Swap'].sum()
                
                # Determine Status
                status = "Unknown"
                reason = ""
                
                if original_filename in included_files:
                    status = "Included"
                elif original_filename in explicitly_skipped:
                    status = "Skipped"
                    reason = "Manual (Include=0)"
                elif original_filename in overlapping_skipped:
                    status = "Skipped"
                    reason = "Overlapping trades"
                else:
                    # Check if it was filtered out by date range
                    df_at['Time'] = pd.to_datetime(df_at['Time'])
                    df_at_filtered = df_at[(df_at['Time'] >= calc_start) & (df_at['Time'] < calc_end)]
                    if df_at_filtered.empty:
                        status = "Skipped"
                        reason = "Date range"
                    else:
                        status = "Partially Included"

                df_at['Time'] = pd.to_datetime(df_at['Time'])
                
                # Load parquet data if available
                df_parquet = load_parquet_data(full_html_path) if full_html_path else None
                
                # Load .set file data if available
                set_params = parse_set_file(full_html_path) if full_html_path else None
                
                # Balance calculation from HTML trades (for fallback or comparison)
                df_at_sorted = df_at.sort_values('Time')
                exits = df_at_sorted[df_at_sorted['Direction'].str.lower().isin(['out', 'in/out'])].copy()
                
                # Chart 1x3: Balance, Underwater, and Histogram
                fig, (ax_bal, ax_dd, ax_hist) = plt.subplots(1, 3, figsize=(20, 6))
                
                max_dd_pct = 0.0
                max_dd_abs = 0.0

                if df_parquet is not None:
                    # Filter parquet to match analysis date range
                    df_pq_filtered = df_parquet[(df_parquet['DATE'] >= calc_start) & (df_parquet['DATE'] < calc_end)]
                    
                    if not df_pq_filtered.empty:
                        # Plot 1: Balance & Equity Growth
                        ax_bal.plot(df_pq_filtered['DATE'], df_pq_filtered['BALANCE'], color='blue', linewidth=1, label='Balance')
                        ax_bal.plot(df_pq_filtered['DATE'], df_pq_filtered['EQUITY'], color='red', linewidth=0.8, alpha=0.7, label='Equity')
                        ax_bal.set_title(f'Balance and Equity Growth', fontsize=12)
                        ax_bal.legend()
                        
                        # Plot 2: Drawdown from Equity
                        df_pq_filtered = df_pq_filtered.copy()
                        df_pq_filtered['Peak'] = df_pq_filtered['EQUITY'].expanding().max()
                        df_pq_filtered['DD_Pct'] = (df_pq_filtered['EQUITY'] / df_pq_filtered['Peak'] - 1) * 100
                        
                        ax_dd.fill_between(df_pq_filtered['DATE'], df_pq_filtered['DD_Pct'], 0, color='red', alpha=0.3)
                        ax_dd.plot(df_pq_filtered['DATE'], df_pq_filtered['DD_Pct'], color='red', linewidth=0.8)
                        ax_dd.set_title(f'Underwater Drawdown (Equity)', fontsize=12)

                        # Add secondary Y-axis for absolute drawdown
                        ax_dd_abs_plot = ax_dd.twinx()
                        abs_diff = df_pq_filtered['EQUITY'] - df_pq_filtered['Peak']
                        ax_dd_abs_plot.plot(df_pq_filtered['DATE'], abs_diff, alpha=0)
                        ax_dd_abs_plot.set_ylabel('Drawdown Absolute')
                        ax_dd_abs_plot.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

                        max_dd_pct = df_pq_filtered['DD_Pct'].min()
                        max_dd_abs = abs_diff.min()
                    else:
                        df_parquet = None # Revert to fallback if date range filters out everything
                
                if df_parquet is None and not exits.empty:
                    # Fallback to HTML trade data
                    exits['CumPnL'] = exits['DealPnL'].cumsum()
                    exits['Balance'] = exits['CumPnL'] + args.base
                    exits['Peak'] = exits['Balance'].expanding().max()
                    exits['DD_Pct'] = (exits['Balance'] / exits['Peak'] - 1) * 100
                    
                    ax_bal.plot(exits['Time'], exits['Balance'], color='blue', linewidth=1)
                    ax_bal.set_title(f'Balance Growth', fontsize=12)
                    
                    ax_dd.fill_between(exits['Time'], exits['DD_Pct'], 0, color='red', alpha=0.3)
                    ax_dd.plot(exits['Time'], exits['DD_Pct'], color='red', linewidth=0.8)
                    ax_dd.set_title(f'Underwater Drawdown', fontsize=12)

                    # Add secondary Y-axis for absolute drawdown
                    ax_dd_abs_plot = ax_dd.twinx()
                    abs_diff = exits['Balance'] - exits['Peak']
                    ax_dd_abs_plot.plot(exits['Time'], abs_diff, alpha=0)
                    ax_dd_abs_plot.set_ylabel('Drawdown Absolute')
                    ax_dd_abs_plot.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

                    max_dd_pct = exits['DD_Pct'].min()
                    max_dd_abs = abs_diff.min()

                ax_bal.set_ylabel('Amount')
                ax_bal.grid(True, alpha=0.3)
                ax_bal.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
                plt.setp(ax_bal.get_xticklabels(), rotation=30, ha='right')
                
                ax_dd.set_ylabel('Drawdown %')
                ax_dd.grid(True, alpha=0.3)
                plt.setp(ax_dd.get_xticklabels(), rotation=30, ha='right')

                # Plot 3: Sequence Histogram (Dual Axis)
                if 'SequenceNumber' in df_at.columns and 'TradeNumberInSequence' in df_at.columns:
                    seq_groups = df_at[df_at['SequenceNumber'] > 0].groupby('SequenceNumber')
                    seq_data = []
                    for _, group in seq_groups:
                        length = group['TradeNumberInSequence'].max()
                        pnl = group[group['Direction'].str.lower().isin(['out', 'in/out'])]['DealPnL'].sum()
                        seq_data.append({'Length': length, 'PnL': pnl})
                    
                    if seq_data:
                        df_seq_curr = pd.DataFrame(seq_data)
                        dist_agg_curr = df_seq_curr.groupby('Length').agg(
                            Frequency=('PnL', 'count'),
                            TotalPnL=('PnL', 'sum')
                        ).reset_index()
                        
                        # Primary axis: Frequency
                        color_freq = 'tab:blue'
                        width_pnl = 0.8
                        width_freq = 0.4
                        
                        ax_hist_pnl = ax_hist.twinx()
                        ax_hist_pnl.bar(dist_agg_curr['Length'], dist_agg_curr['TotalPnL'], width=width_pnl, color='green', alpha=0.3, label='Total PnL')
                        ax_hist_pnl.set_ylabel('Total PnL', color='green')
                        ax_hist_pnl.tick_params(axis='y', labelcolor='green')
                        
                        ax_hist.bar(dist_agg_curr['Length'], dist_agg_curr['Frequency'], width=width_freq, color=color_freq, label='Frequency', edgecolor='black', linewidth=0.5)
                        ax_hist.set_title("Sequence PnL Distribution", fontsize=12)
                        ax_hist.set_xlabel("Trades in Sequence")
                        ax_hist.set_ylabel("Frequency", color=color_freq)
                        ax_hist.tick_params(axis='y', labelcolor=color_freq)
                        ax_hist.grid(axis='y', alpha=0.3)
                        ax_hist.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
                    else:
                        ax_hist.set_title("No Sequence Data", fontsize=12)
                else:
                    ax_hist.set_title("No Sequence Columns Found", fontsize=12)
                
                plt.tight_layout()
                per_file_chart_path = os.path.join(charts_folder, f"Chart_{report_basename}.png")
                plt.savefig(per_file_chart_path)
                plt.close()

                print(f"Processed: {report_basename} - {status}")
                if total_pnl is not None:
                    print(f"  PnL: {total_pnl:,.2f}")
                    if max_dd_abs is not None:
                        print(f"  Max DD: {max_dd_abs:,.2f} ({max_dd_pct:.2f}%)")
                
                f.write(f"### {idx}. Report: {report_basename}\n\n")

                f.write(f"- **Status**: {status} {'(' + reason + ')' if reason else ''}\n")
                if total_pnl is not None:
                    f.write(f"- **Total PnL**: {total_pnl:,.2f}\n")
                    if max_dd_abs is not None:
                        f.write(f"- **Max Drawdown**: {max_dd_abs:,.2f} ({max_dd_pct:.2f}%)\n")
                    if df_parquet is not None:
                        f.write(f"- **Data Source**: Parquet (Balance & Equity)\n")
                    
                    if set_params:
                        f.write("- **Parameters**:\n")
                        f.write(f"  - Lot Size: `{set_params['LotSize']}`\n")
                        f.write(f"  - Max Lots: `{set_params['MaxLots']}`\n")
                        f.write(f"  - Lot Size Exponent: `{set_params['LotSizeExponent']}`\n")
                        f.write(f"  - Delay Trade Sequence: `{set_params['DelayTradeSequence']}`\n")
                        f.write(f"  - Live Delay: `{set_params['LiveDelay']}`\n")

                    f.write("\n")
                    f.write(f"![{report_basename} Charts](charts/Chart_{report_basename}.png)\n\n")

    print(f"Analysis complete. Report saved to: {report_path}")

if __name__ == "__main__":
    main()
