import random
import re

def safe_eval(expr: str) -> int:
    """安全的四則運算器"""
    expr = re.sub(r'[^0-9+\-*/()]', '', expr)
    try:
        return int(eval(expr))
    except:
        return 0

def roll_d100_with_modifiers(dice_count: int, is_bonus: bool = True) -> tuple[int, list[int]]:
    """計算雙 D10 骰子點數，並根據獎懲骰個數決定最終點數。"""
    ones = random.randint(0, 9)
    base_tens = random.randint(0, 9) * 10
    
    extra_tens = [random.randint(0, 9) * 10 for _ in range(dice_count)]
    all_tens = [base_tens] + extra_tens

    detail_rolls = []
    for t in all_tens:
        val = t + ones
        detail_rolls.append(100 if val == 0 else val)

    if dice_count > 0:
        if is_bonus:
            rolled_val = min(detail_rolls)  
        else:
            rolled_val = max(detail_rolls)  
    else:
        rolled_val = detail_rolls[0]

    return rolled_val, detail_rolls

def judge_success_level(rolled_val: int, target: int) -> str:
    """根據最終點數與目標值，判定 COC 7th 的成功等級。"""
    crit_success_high = 5 if target >= 50 else 1
    fumble_low = 100 if target >= 50 else 96

    extreme_success = target // 5
    hard_success = target // 2

    if rolled_val >= fumble_low or rolled_val == 100:
        return "大失敗"
    elif rolled_val <= crit_success_high:
        return "大成功"
    elif rolled_val <= extreme_success:
        return "極限成功"
    elif rolled_val <= hard_success:
        return "困難成功"
    elif rolled_val <= target:
        return "成功"
    else:
        return "失敗"
