import os
import re
import json
import webbrowser
from bs4 import BeautifulSoup

def analyze_folder():
    print("Scanning folder for MT5 HTML reports...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = [f for f in os.listdir(current_dir) if f.endswith('.html') or f.endswith('.htm')]
    
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
                
                # Check if we have the headers we need
                if profit_idx != -1 and comment_idx != -1 and 'profit' in cells:
                    header_row = r
                    break
                    
            if header_row != -1:
                pending_speed = None
                pending_comment = None
                
                for i in range(header_row + 1, len(rows)):
                    cells = rows[i].find_all('td')
                    if len(cells) > max(profit_idx, comment_idx):
                        profit_text = cells[profit_idx].get_text(strip=True)
                        comment_text = cells[comment_idx].get_text(strip=True)
                        direction = cells[dir_idx].get_text(strip=True).lower() if dir_idx != -1 and len(cells) > dir_idx else ""
                        
                        speed_match = re.search(r'\|\s*(-?\d+(?:\.\d+)?)\s*pts/s', comment_text, re.IGNORECASE) or \
                                      re.search(r'speed.*?(-?\d+(?:\.\d+)?)', comment_text, re.IGNORECASE) or \
                                      re.search(r'spd.*?(-?\d+(?:\.\d+)?)', comment_text, re.IGNORECASE)
                                      
                        if direction == 'in':
                            if speed_match:
                                pending_speed = float(speed_match.group(1))
                                pending_comment = comment_text
                        elif direction == 'out':
                            if pending_speed is not None:
                                clean_profit = re.sub(r'[^\d.-]', '', profit_text)
                                try:
                                    profit = float(clean_profit)
                                    file_trades.append({'profit': profit, 'speed': pending_speed, 'comment': pending_comment})
                                except ValueError:
                                    pass
                                pending_speed = None
                                pending_comment = None
                        elif direction == "":
                            # Fallback if no direction column (MT4 style)
                            if profit_text and profit_text != "0.00" and speed_match:
                                clean_profit = re.sub(r'[^\d.-]', '', profit_text)
                                try:
                                    profit = float(clean_profit)
                                    if profit != 0:
                                        file_trades.append({'profit': profit, 'speed': float(speed_match.group(1)), 'comment': comment_text})
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
