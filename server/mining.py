from datetime import datetime, timedelta

BASE_RATE = 1.0
HALVING_INTERVAL = 1000
TEAM_BONUS_PERCENT = 0.25


def get_current_rate(total_checkins: int) -> float:
    halvings = total_checkins // HALVING_INTERVAL
    return BASE_RATE / (2 ** halvings)


def can_checkin(last_checkin):
    if last_checkin is None:
        return True, None
    elapsed = datetime.utcnow() - last_checkin
    cooldown = timedelta(hours=24)
    if elapsed >= cooldown:
        return True, None
    remaining = cooldown - elapsed
    return False, remaining


def calculate_reward(team_size: int, total_checkins: int) -> float:
    base = get_current_rate(total_checkins)
    team_bonus = base * TEAM_BONUS_PERCENT * min(team_size, 10)
    return round(base + team_bonus, 4)