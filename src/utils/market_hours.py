"""
Market hours utility for determining trading status.
"""

from datetime import datetime, time, timedelta
import pytz


def is_us_market_open() -> dict:
    """
    Check if US stock market is currently open.
    
    Returns:
        Dict with:
        - 'is_open': bool - Whether market is open
        - 'status': str - 'open', 'pre_market', 'after_hours', 'closed'
        - 'ny_time': datetime - Current time in New York
        - 'next_opening': datetime - Next market opening time
    """
    # New York timezone
    ny_tz = pytz.timezone('America/New_York')
    ny_time = datetime.now(ny_tz)
    
    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = time(9, 30)
    market_close = time(16, 0)
    
    # Pre-market: 4:00 AM - 9:30 AM ET
    pre_market_open = time(4, 0)
    
    # After-hours: 4:00 PM - 8:00 PM ET
    after_hours_close = time(20, 0)
    
    current_time = ny_time.time()
    weekday = ny_time.weekday()  # 0=Monday, 6=Sunday
    
    # Check if it's a weekday (Monday-Friday)
    is_weekday = weekday < 5
    
    if not is_weekday:
        # Market closed on weekends
        # Calculate next Monday opening
        days_until_monday = (7 - weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_opening = ny_time.replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=days_until_monday)
        
        return {
            'is_open': False,
            'status': 'closed',
            'reason': '周末休市',
            'ny_time': ny_time,
            'next_opening': next_opening,
            'display_status': '🔔 已收盤（周末）'
        }
    
    # Check market status
    if market_open <= current_time < market_close:
        # Regular market hours
        return {
            'is_open': True,
            'status': 'open',
            'reason': '交易時段',
            'ny_time': ny_time,
            'next_opening': None,
            'display_status': '📈 開盤中'
        }
    
    elif pre_market_open <= current_time < market_open:
        # Pre-market
        return {
            'is_open': False,
            'status': 'pre_market',
            'reason': '盤前交易',
            'ny_time': ny_time,
            'next_opening': ny_time.replace(hour=9, minute=30, second=0, microsecond=0),
            'display_status': '🔔 盤前交易'
        }
    
    elif market_close <= current_time < after_hours_close:
        # After-hours
        return {
            'is_open': False,
            'status': 'after_hours',
            'reason': '盤後交易',
            'ny_time': ny_time,
            'next_opening': (ny_time + timedelta(days=1)).replace(hour=9, minute=30, second=0, microsecond=0) if weekday < 4 else (ny_time + timedelta(days=7-weekday)).replace(hour=9, minute=30, second=0, microsecond=0),
            'display_status': '🔔 已收盤'
        }
    
    else:
        # Market closed (after 8 PM or before 4 AM)
        if weekday == 4:  # Friday
            # Next opening is Monday
            next_opening = (ny_time + timedelta(days=3)).replace(hour=9, minute=30, second=0, microsecond=0)
        else:
            # Next opening is tomorrow
            next_opening = (ny_time + timedelta(days=1)).replace(hour=9, minute=30, second=0, microsecond=0)
        
        return {
            'is_open': False,
            'status': 'closed',
            'reason': '非交易時段',
            'ny_time': ny_time,
            'next_opening': next_opening,
            'display_status': '🔔 已收盤'
        }


def get_market_status_emoji() -> str:
    """Get emoji based on current market status"""
    status = is_us_market_open()
    return status['display_status']
