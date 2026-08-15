from collections import defaultdict

# -------------------- 技能系统 --------------------
def skill_atk_def_pos5(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["pos"] == 5:
            if is_pct:
                ap[i] += val / 100.0
                dp[i] += val / 100.0
            else:
                af[i] += val
                df[i] += val
    return ap, af, dp, df

def skill_atk_def_adjacent(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["pos"] in (my_pos - 1, my_pos + 1):
            if is_pct:
                dp[i] += val / 100.0
                ap[i] += val / 100.0
            else:
                df[i] += val
                af[i] += val
    return ap, af, dp, df

def skill_atk_if_support_3(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    for slot in board:
        if slot["pos"] == 3 and slot["card"]["type"] == "type_support":
            val = card["skill_value"]
            if card.get("skill_type", "percent") == "percent":
                ap[card_index] += val / 100.0
            else:
                af[card_index] += val
            break
    return ap, af, dp, df

def skill_def_all_fighter(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["card"]["role"] == "role_fighter":
            if is_pct:
                dp[i] += val / 100.0
            else:
                df[i] += val
    return ap, af, dp, df

def skill_def_all_atk(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["card"]["type"] == "type_attack":
            if is_pct:
                dp[i] += val / 100.0
            else:
                df[i] += val
    return ap, af, dp, df

def skill_atk_pos1_and_5(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["pos"] == 1 or slot["pos"] == 5:
            if is_pct:
                ap[i] += val / 100.0
            else:
                af[i] += val
    return ap, af, dp, df

def skill_atk_pos1_and_2(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["pos"] == 1 or slot["pos"] == 2:
            if is_pct:
                ap[i] += val / 100.0
            else:
                af[i] += val
    return ap, af, dp, df

def skill_front_def_back_atk(board, card_index, card):
    """前防后攻：给之前位置加防御，之后位置加攻击，自身不受影响"""
    ap = defaultdict(float); af = defaultdict(int); dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    my_pos = board[card_index]["pos"]
    for i, slot in enumerate(board):
        if slot["pos"] < my_pos:          # 之前的位置：加防御
            if is_pct:
                dp[i] += val / 100.0
            else:
                df[i] += val
        elif slot["pos"] > my_pos:        # 之后的位置：加攻击
            if is_pct:
                ap[i] += val / 100.0
            else:
                af[i] += val
    return ap, af, dp, df

def skill_def_prev_battle_fixed(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]   # 直接取整数值
    for slot in board:
        if slot["pos"] == my_pos - 1 and slot["card"]["role"] == "role_fighter":
            df[card_index] += val
            break
    return ap, af, dp, df

def skill_def_prev(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    # 寻找位置为 my_pos - 1 的卡牌
    for i, slot in enumerate(board):
        if slot["pos"] == my_pos - 1:
            if is_pct:
                dp[i] += val / 100.0
            else:
                df[i] += val
            break
    return ap, af, dp, df

def skill_def_next_two(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if my_pos < slot["pos"] <= my_pos + 2:   # 之后1~2位
            if is_pct:
                dp[i] += val / 100.0
            else:
                df[i] += val
    return ap, af, dp, df

def skill_atk_prev_bomb(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if slot["pos"] < my_pos and slot["card"]["role"] == "role_bomber":
            if is_pct:
                ap[i] += val / 100.0
            else:
                af[i] += val
    return ap, af, dp, df

def skill_atk_def_other_fighter(board, card_index, card):
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    is_pct = card.get("skill_type", "percent") == "percent"
    for i, slot in enumerate(board):
        if i == card_index:          # 跳过自己
            continue
        if slot["card"]["role"] == "role_fighter":
            if is_pct:
                ap[i] += val / 100.0
                dp[i] += val / 100.0
            else:
                af[i] += val
                df[i] += val
    return ap, af, dp, df

def skill_def_adjacent(board, card_index, card):
    """
    信仰之跃：相邻位置防御增加150%（百分比固定为150%，不受等级影响）
    边界处理：在1号位只影响2号位，在5号位只影响4号位
    """
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    val = card["skill_value"]
    # 遍历所有位置
    for i, slot in enumerate(board):
        if slot["pos"] == my_pos - 1 or slot["pos"] == my_pos + 1:
            dp[i] += val / 100.0
    return ap, af, dp, df


def skill_atk_fixed_after_def5(board, card_index, card):
    """
    四指编队：如果5号位放置了防御类卡牌，则自身之后的所有位置攻击增加固定值4
    边界处理：自身在5号位时无后续位置，不触发
    """
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    # 检查5号位是否存在防御类卡牌
    has_def5 = False
    for slot in board:
        if slot["pos"] == 5 and slot["card"]["type"] == "type_defense":
            has_def5 = True
            break
    if not has_def5:
        return ap, af, dp, df

    my_pos = board[card_index]["pos"]
    # 给之后的位置增加固定攻击值
    for i, slot in enumerate(board):
        if slot["pos"] > my_pos:
            af[i] += val
    return ap, af, dp, df

def skill_atk_dual_torpedo(board, card_index, card):
    """铁鱼：除自身外所有鱼雷机种卡攻击增加固定值"""
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    val = card["skill_value"]
    for i, slot in enumerate(board):
        if i == card_index:
            continue
        if slot["card"]["role"] == "role_torpedo":
            af[i] += val
    return ap, af, dp, df

def skill_def_adjacent_attack(board, card_index, card):
    """萨奇剪：前后均为进攻类卡牌时，自身防御增加百分比"""
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    # 边界：1号位没有前位，5号位没有后位，直接返回
    if my_pos == 1 or my_pos == 5:
        return ap, af, dp, df
    prev_type = None
    next_type = None
    for slot in board:
        if slot["pos"] == my_pos - 1:
            prev_type = slot["card"]["type"]
        if slot["pos"] == my_pos + 1:
            next_type = slot["card"]["type"]
    if prev_type == "type_attack" and next_type == "type_attack":
        val = card["skill_value"]
        if card.get("skill_type", "percent") == "percent":
            dp[card_index] += val / 100.0
        else:
            df[card_index] += val
    return ap, af, dp, df

def skill_atk_adjacent_defense(board, card_index, card):
    """卢氏圈：前后均为防御类卡牌时，自身攻击增加固定值"""
    ap = defaultdict(float); af = defaultdict(int)
    dp = defaultdict(float); df = defaultdict(int)
    my_pos = board[card_index]["pos"]
    if my_pos == 1 or my_pos == 5:
        return ap, af, dp, df
    prev_type = None
    next_type = None
    for slot in board:
        if slot["pos"] == my_pos - 1:
            prev_type = slot["card"]["type"]
        if slot["pos"] == my_pos + 1:
            next_type = slot["card"]["type"]
    if prev_type == "type_defense" and next_type == "type_defense":
        val = card["skill_value"]
        if card.get("skill_type", "percent") == "percent":
            ap[card_index] += val / 100.0
        else:
            af[card_index] += val
    return ap, af, dp, df

SKILL_FUNCTIONS = {
    "atk_def_pos5": skill_atk_def_pos5,
    "atk_def_adjacent": skill_atk_def_adjacent,
    "atk_if_support_3": skill_atk_if_support_3,
    "def_all_fighter": skill_def_all_fighter,
    "front_def_back_atk": skill_front_def_back_atk,
    "def_prev_battle_fixed": skill_def_prev_battle_fixed,
    "def_prev": skill_def_prev,
    "atk_pos1_and_5": skill_atk_pos1_and_5,
    "atk_pos1_and_2": skill_atk_pos1_and_2,
    "def_next_two": skill_def_next_two,
    "def_all_atk": skill_def_all_atk,
    "atk_prev_bomb": skill_atk_prev_bomb,
    "atk_def_other_fighter": skill_atk_def_other_fighter,
    "def_adjacent": skill_def_adjacent,
    "atk_fixed_after_def5": skill_atk_fixed_after_def5,
    "atk_dual_torpedo": skill_atk_dual_torpedo,
    "def_adjacent_attack": skill_def_adjacent_attack,
    "atk_adjacent_defense": skill_atk_adjacent_defense,
}