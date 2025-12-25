import pandas as pd
import json

def process_data(data):
    if not isinstance(data, dict):
        data = json.load(open(data, "r", encoding='utf-8'))
    # Filter and transform data
    all_data = [{
        'txdate': pd.to_datetime(row['txdate']),
        'txamt': round(row['txamt']*0.01, 2),
        'meraddr': row['meraddr'],
        'mername': row['mername'],
        'username': row['username']
    } for row in data['resultData']['rows'] 
        if 'mername' in row and row['summary'] in ['持卡人消费', '实体卡', '离线码在线消费', 'nfc卡消费']]
    # Convert to DataFrame and save raw data
    df = pd.DataFrame(all_data)
    
    # Sort by date
    df = df.sort_values('txdate')

    # Merge nearby records
    merged_records = []
    current_group = None

    for _, row in df.iterrows():
        if current_group is None:
            current_group = {
                'txdate': row['txdate'],
                'txamt': row['txamt'],
                'meraddr': row['meraddr'],
                'mername': [row['mername']],
                'username': row['username']
            }
        else:
            time_diff = (row['txdate'] - current_group['txdate']).total_seconds() / 60
            
            if time_diff <= 120 and row['meraddr'] == current_group['meraddr']:
                current_group['txamt'] = round(current_group['txamt'] + row['txamt'], 2)
                current_group['mername'].append(row['mername'])
            else:
                merged_records.append(current_group)
                current_group = {
                    'txdate': row['txdate'],
                    'txamt': round(row['txamt'], 2),
                    'meraddr': row['meraddr'],
                    'mername': [row['mername']],
                    'username': row['username']
                }

    if current_group is not None:
        merged_records.append(current_group)
    merged_df = pd.DataFrame(merged_records)
    merged_df['time_only'] = merged_df['txdate'].dt.time
    
    return df, merged_df

if __name__ == "__main__":
    df, merged_df = process_data("consumption_data.json")