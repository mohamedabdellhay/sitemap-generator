from datetime import datetime

def format_creation_date(timestamp):
    if not timestamp:
        return 'Unknown'
    try:
        creation_dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
        today_date = datetime.now().date()
        creation_date_only = creation_dt.date()
        days_diff = (today_date - creation_date_only).days

        if days_diff == 0:
            return 'Today at ' + creation_dt.strftime('%H:%M')
        elif days_diff == 1:
            return 'Yesterday'
        elif days_diff < 7:
            return f'{days_diff} days ago'
        else:
            return creation_dt.strftime('%Y-%m-%d')
    except Exception:
        return 'Unknown'