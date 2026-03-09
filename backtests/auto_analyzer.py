import os
import re
import json
import webbrowser
from bs4 import BeautifulSoup

def analyze_folder():
    print("Scanning folder for MT5 HTML reports...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ignore known non-report files to avoid exceptions parsing binaries/scripts
    ignored_exts = {'.py', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.set', '.md', '.DS_Store'}
    html_files = [
        f for f in os.listdir(current_dir)
        if os.path.isfile(os.path.join(current_dir, f)) and not any(f.endswith(ext) for ext in ignored_exts)
    ]
    
    all_reports = []
    total_trades_count = 0
    
    for filename in html_files:
        if filename == 'backtest_analyzer.html':
            continue
            
        print(f"Parsing {filename}...")
        filepath = os.path.join(current_dir, filename)
        file_trades = []
        
        try:
            with open(filepath, 'r', encoding='utf-16') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        for t_idx, t in enumerate(tables):
            rows = t.find_all('tr')
            profit_idx = -1
            comment_idx = -1
            dir_idx = -1
            header_row = -1
            
            for r in range(len(rows)):
                cells = [c.get_text(strip=True).lower() for c in rows[r].find_all(['td', 'th'])]
                if 'profit' in cells: profit_idx = cells.index('profit')
                if 'comment' in cells or 'comments' in cells: 
                    comment_idx = cells.index('comment') if 'comment' in cells else cells.index('comments')
                if 'direction' in cells: dir_idx = cells.index('direction')
                time_idx = cells.index('time') if 'time' in cells else -1
                type_idx = cells.index('type') if 'type' in cells else -1
                
                # Check if we have the headers we need
                if profit_idx != -1 and comment_idx != -1 and 'profit' in cells:
                    header_row = r
                    break
                    
            if header_row != -1:
                pending_speed = None
                pending_prev_speed = None
                pending_time_sec = None
                pending_comment = None
                pending_time = None
                pending_type = None
                
                for i in range(header_row + 1, len(rows)):
                    cells = rows[i].find_all('td')
                    if len(cells) > max(profit_idx, comment_idx):
                        profit_text = cells[profit_idx].get_text(strip=True)
                        comment_text = cells[comment_idx].get_text(strip=True)
                        direction = cells[dir_idx].get_text(strip=True).lower() if dir_idx != -1 and len(cells) > dir_idx else ""
                        trade_time = cells[time_idx].get_text(strip=True) if time_idx != -1 and len(cells) > time_idx else ""
                        trade_type = cells[type_idx].get_text(strip=True).lower() if type_idx != -1 and len(cells) > type_idx else ""
                        
                        # Match new format "B|4.50|2.10|15"
                        speed_4d_match = re.search(r'(?:B|S)\|(-?\d+(?:\.\d+)?)\|(-?\d+(?:\.\d+)?)\|(\d+)', comment_text, re.IGNORECASE)
                        
                        speed_match = re.search(r'\|\s*(-?\d+(?:\.\d+)?)\s*pts/s', comment_text, re.IGNORECASE) or \
                                      re.search(r'speed.*?(-?\d+(?:\.\d+)?)', comment_text, re.IGNORECASE) or \
                                      re.search(r'spd.*?(-?\d+(?:\.\d+)?)', comment_text, re.IGNORECASE)
                        
                        pending_speed_val = None
                        pending_prev_speed_val = None
                        pending_time_sec_val = None
                        
                        if speed_4d_match:
                            pending_speed_val = float(speed_4d_match.group(1))
                            pending_prev_speed_val = float(speed_4d_match.group(2))
                            pending_time_sec_val = int(speed_4d_match.group(3))
                        elif speed_match:
                            pending_speed_val = float(speed_match.group(1))
                                      
                        if direction == 'in':
                            if pending_speed_val is not None:
                                pending_speed = pending_speed_val
                                pending_prev_speed = pending_prev_speed_val
                                pending_time_sec = pending_time_sec_val
                                pending_comment = comment_text
                                pending_time = trade_time
                                pending_type = trade_type
                        elif direction == 'out':
                            if pending_speed is not None:
                                clean_profit = re.sub(r'[^\d.-]', '', profit_text)
                                try:
                                    profit = float(clean_profit)
                                    trade_obj = {
                                        'profit': profit, 
                                        'speed': pending_speed, 
                                        'comment': pending_comment,
                                        'entry_time': pending_time,
                                        'exit_time': trade_time,
                                        'trade_type': pending_type
                                    }
                                    if pending_prev_speed is not None:
                                        trade_obj['prev_speed'] = pending_prev_speed
                                        trade_obj['time_sec'] = pending_time_sec
                                        
                                    file_trades.append(trade_obj)
                                except ValueError:
                                    pass
                                pending_speed = None
                                pending_prev_speed = None
                                pending_time_sec = None
                                pending_comment = None
                        elif direction == "":
                            # Fallback if no direction column (MT4 style)
                            if profit_text and profit_text != "0.00" and pending_speed_val is not None:
                                clean_profit = re.sub(r'[^\d.-]', '', profit_text)
                                try:
                                    profit = float(clean_profit)
                                    if profit != 0:
                                        trade_obj = {'profit': profit, 'speed': pending_speed_val, 'comment': comment_text}
                                        if pending_prev_speed_val is not None:
                                            trade_obj['prev_speed'] = pending_prev_speed_val
                                            trade_obj['time_sec'] = pending_time_sec_val
                                        file_trades.append(trade_obj)
                                except ValueError:
                                    pass

        all_reports.append({
            "filename": filename,
            "trades": file_trades
        })
        total_trades_count += len(file_trades)

    js_content = f"window.autoLoadedReports = {json.dumps(all_reports, indent=4)};"
    js_filepath = os.path.join(current_dir, 'trades_data.js')
    
    with open(js_filepath, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"\nSuccess! Extracted {total_trades_count} trades across {len(all_reports)} reports.")
    print("Generated 'trades_data.js'")
    
    # Open the analyzer in the default browser
    analyzer_path = os.path.join(current_dir, 'backtest_analyzer.html')
    print("Opening Edge Analyzer in your browser...")
    webbrowser.open(f'file://{analyzer_path}')

if __name__ == "__main__":
    analyze_folder()
