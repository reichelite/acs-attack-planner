import itertools
import math
from collections import defaultdict
from multiprocessing import Pool
from defines import BLANK_CARD, CONDITIONAL_SKILL_IDS
from skills import SKILL_FUNCTIONS

def build_skill_snapshots(cards):
    """
    返回字典：key = 卡牌名称，value = 5×5 效果矩阵
    若技能为条件技能，矩阵全部置零，不会在快照分支使用
    """
    snapshots = {}
    for card in cards:
        name = card["name"]
        skill_id = card.get("skill_id")
        # 条件技能直接存零矩阵，后续通过原始方式计算
        if skill_id in CONDITIONAL_SKILL_IDS:
            matrix = [[{"fixed_atk": 0, "fixed_def": 0, "pct_atk": 0.0, "pct_def": 0.0}
                       for _ in range(5)] for _ in range(5)]
            snapshots[name] = matrix
            continue

        matrix = []
        for pos in range(5):
            single_perm = [BLANK_CARD] * 5
            single_perm[pos] = card
            board = []
            for idx, c in enumerate(single_perm):
                board.append({
                    "pos": idx + 1, "card": c,
                    "base_attack": c["attack"], "base_defense": c["defense"],
                    "skill_disabled": False
                })
            af = defaultdict(int); df = defaultdict(int)
            ap = defaultdict(float); dp = defaultdict(float)
            if skill_id and skill_id in SKILL_FUNCTIONS:
                ap, af, dp, df = SKILL_FUNCTIONS[skill_id](board, pos, card)
            row = []
            for tgt in range(5):
                row.append({
                    "fixed_atk": af.get(tgt, 0),
                    "fixed_def": df.get(tgt, 0),
                    "pct_atk": ap.get(tgt, 0.0) if tgt in ap else 0.0,
                    "pct_def": dp.get(tgt, 0.0) if tgt in dp else 0.0,
                })
            matrix.append(row)
        snapshots[name] = matrix
    return snapshots

def search_for_m(args):
    """在子进程中搜索指定卡牌数量m的所有排列"""
    (m, valid_cards, allowed_positions, boss_effects, fleet_limit,
     boss_atk_threshold, boss_def_threshold, snapshots) = args

    best_both = None          # (perm, atk, def, fleet, m)
    best_def_only = None      # (perm, atk, def)
    best_lower = None         # (perm, atk, def)
    fallback_best = None      # (perm, atk, def)
    best_fleet = float('inf')
    best_m = float('inf')
    best_atk = float('inf')

    for positions in itertools.combinations(allowed_positions, m):
        for perm_cards in itertools.permutations(valid_cards, m):
            #total_perm_count += 1
            fleet_sum = sum(card["fleet_count"] for card in perm_cards)
            if fleet_sum > fleet_limit:
                continue

            # 剪枝：已找到合法解时，跳过必然更差的组合
            if best_both is not None:
                if fleet_sum > best_fleet:
                    continue
                if fleet_sum == best_fleet and m > best_m:
                    continue

            perm = [BLANK_CARD] * 5
            for pos_idx, card in zip(positions, perm_cards):
                perm[pos_idx] = card
            total_def, total_atk = compute_final_stats(perm, boss_effects, snapshots)

            # 无条件保留防御最高的方案
            if fallback_best is None or total_def > fallback_best[2]:
                fallback_best = (perm, total_atk, total_def)

            # 条件1：不受伤且击败
            if total_def >= boss_atk_threshold and total_atk >= boss_def_threshold:
                if best_both is None:
                    best_both = (perm, total_atk, total_def, fleet_sum, m)
                    best_fleet, best_m, best_atk = fleet_sum, m, total_atk
                else:
                    if (fleet_sum < best_fleet or
                            (fleet_sum == best_fleet and m < best_m) or
                            (fleet_sum == best_fleet and m == best_m and total_atk < best_atk)):
                        best_both = (perm, total_atk, total_def, fleet_sum, m)
                        best_fleet, best_m, best_atk = fleet_sum, m, total_atk

            # 条件2：不受伤（攻击最大化）
            if total_def >= boss_atk_threshold:
                if best_def_only is None or total_atk > best_def_only[1]:
                    best_def_only = (perm, total_atk, total_def)

            # 条件3：防御在90%~100%之间且攻击高
            if boss_atk_threshold * 0.9 <= total_def < boss_atk_threshold:
                if best_lower is None or total_atk > best_lower[1]:
                    best_lower = (perm, total_atk, total_def)
    return (best_both, best_def_only, best_lower, fallback_best)

# -------------------- 最终属性计算 --------------------
def compute_final_stats(perm, boss_effects, snapshots=None):
    total_def, total_atk, _, _ = compute_per_card_stats(perm, boss_effects, snapshots)
    return total_def, total_atk

def compute_per_card_stats(perm, boss_effects, snapshots=None, debug=False):
    board = []
    for i, card in enumerate(perm):
        pos = i + 1
        board.append({
            "pos": pos, "card": card,
            "base_attack": card["attack"], "base_defense": card["defense"],
            "skill_disabled": False
        })

    # 技能失效位
    disabled_skill_positions = set()
    for effect in boss_effects:
        if effect["effect"]["type"] == "disable_skill_pos":
            disabled_skill_positions.add(effect["effect"]["pos"])
    for slot in board:
        if slot["pos"] in disabled_skill_positions:
            slot["skill_disabled"] = True

    # 收集加成
    fixed_atk = [0] * len(board)
    fixed_def = [0] * len(board)
    pct_atk_lists = [[] for _ in range(len(board))]
    pct_def_lists = [[] for _ in range(len(board))]

    # 玩家技能应用
    for i, slot in enumerate(board):
        if slot["skill_disabled"]:
            continue
        card = slot["card"]
        if card["type"] == "blank":
            continue
        use_snapshot = (snapshots is not None and card.get("skill_id") not in CONDITIONAL_SKILL_IDS)
        if use_snapshot:
            name = card["name"]
            if name in snapshots:
                snap = snapshots[name]
                pos_idx = slot["pos"] - 1
                for tgt in range(5):
                    if board[tgt]["card"]["type"] == "blank":
                        continue
                    contrib = snap[pos_idx][tgt]
                    fixed_atk[tgt] += contrib["fixed_atk"]
                    fixed_def[tgt] += contrib["fixed_def"]
                    if contrib["pct_atk"] != 0.0:
                        pct_atk_lists[tgt].append(contrib["pct_atk"])
                    if contrib["pct_def"] != 0.0:
                        pct_def_lists[tgt].append(contrib["pct_def"])
                continue
        # 原始技能计算
        skill_id = card.get("skill_id")
        if not skill_id or skill_id not in SKILL_FUNCTIONS:
            continue
        ap, af, dp, df = SKILL_FUNCTIONS[skill_id](board, i, card)
        for idx, val in af.items():
            if board[idx]["card"]["type"] != "blank":
                fixed_atk[idx] += val
        for idx, val in df.items():
            if board[idx]["card"]["type"] != "blank":
                fixed_def[idx] += val
        for idx, val in ap.items():
            if board[idx]["card"]["type"] != "blank" and val != 0:
                pct_atk_lists[idx].append(val)
        for idx, val in dp.items():
            if board[idx]["card"]["type"] != "blank" and val != 0:
                pct_def_lists[idx].append(val)

    # 敌军效果：缩放和置零
    set_effects = []
    for effect in boss_effects:
        e = effect["effect"]
        t = e["type"]
        if t == "scale_pos_attr":
            pos = e["pos"]
            attr = e["attr"]
            scale = e["scale"]
            delta = scale - 1.0
            if attr == "attack":
                for idx, slot in enumerate(board):
                    if slot["pos"] == pos:
                        pct_atk_lists[idx].append(delta)
            else:
                for idx, slot in enumerate(board):
                    if slot["pos"] == pos:
                        pct_def_lists[idx].append(delta)
        elif t == "scale_all_attr":
            attr = e["attr"]
            scale = e["scale"]
            delta = scale - 1.0
            if attr == "attack":
                for idx in range(len(board)):
                    pct_atk_lists[idx].append(delta)
            else:
                for idx in range(len(board)):
                    pct_def_lists[idx].append(delta)
        elif t == "scale_type_attr":
            type_name = e["type_name"]
            attr = e["attr"]
            scale = e["scale"]
            delta = scale - 1.0
            if attr == "attack":
                for idx, slot in enumerate(board):
                    if slot["card"]["type"] == type_name:
                        pct_atk_lists[idx].append(delta)
            else:
                for idx, slot in enumerate(board):
                    if slot["card"]["type"] == type_name:
                        pct_def_lists[idx].append(delta)
        elif t == "scale_role_attr":
            role = e["role"]
            attr = e["attr"]
            scale = e["scale"]
            delta = scale - 1.0
            if attr == "attack":
                for idx, slot in enumerate(board):
                    if slot["card"]["role"] == role:
                        pct_atk_lists[idx].append(delta)
            else:
                for idx, slot in enumerate(board):
                    if slot["card"]["role"] == role:
                        pct_def_lists[idx].append(delta)
        elif t == "set_pos_attr_zero":
            set_effects.append(e)

    # 百分比降序排列
    for idx in range(len(board)):
        pct_atk_lists[idx].sort(reverse=True)
        pct_def_lists[idx].sort(reverse=True)

    # 计算（使用浮点数，不取整）
    current_atk = [0.0] * len(board)
    current_def = [0.0] * len(board)
    atk_steps = [""] * len(board) if debug else None
    def_steps = [""] * len(board) if debug else None

    for i, slot in enumerate(board):
        val_atk = float(slot["base_attack"] + fixed_atk[i])
        atk_log = f"{slot['base_attack']}+{fixed_atk[i]}={val_atk}" if fixed_atk[i] != 0 else str(val_atk)
        for pct in pct_atk_lists[i]:
            prev = val_atk
            val_atk *= (1 + pct)
            atk_log += f" × {1+pct:.2f}={prev:.2f}×{1+pct:.2f}={val_atk:.2f}"
        current_atk[i] = val_atk
        if debug: atk_steps[i] = atk_log

        val_def = float(slot["base_defense"] + fixed_def[i])
        def_log = f"{slot['base_defense']}+{fixed_def[i]}={val_def}" if fixed_def[i] != 0 else str(val_def)
        for pct in pct_def_lists[i]:
            prev = val_def
            val_def *= (1 + pct)
            def_log += f" × {1+pct:.2f}={prev:.2f}×{1+pct:.2f}={val_def:.2f}"
        current_def[i] = val_def
        if debug: def_steps[i] = def_log

    # 敌军置零
    for e in set_effects:
        t = e["type"]
        if t == "set_pos_attr_zero":
            pos = e["pos"]
            attr = e["attr"]
            if attr == "attack":
                for i, slot in enumerate(board):
                    if slot["pos"] == pos:
                        current_atk[i] = 0.0
                        if debug: atk_steps[i] += " →置零"
            else:
                for i, slot in enumerate(board):
                    if slot["pos"] == pos:
                        current_def[i] = 0.0
                        if debug: def_steps[i] += " →置零"

    # 最终向上取整
    final_atk_list = [int(math.ceil(v)) if v >= 0 else int(math.floor(v)) for v in current_atk]
    final_def_list = [int(math.ceil(v)) if v >= 0 else int(math.floor(v)) for v in current_def]
    total_atk = sum(final_atk_list)
    total_def = sum(final_def_list)

    if debug:
        # ... 调试返回保持不变
        return total_def, total_atk, final_atk_list, final_def_list, atk_steps, def_steps
    else:
        return total_def, total_atk, final_atk_list, final_def_list

def print_debug_info(perm, boss_effects):
    """输出最优排列的详细计算过程，包含玩家技能、Boss效果和分步计算"""
    board = []
    for i, card in enumerate(perm):
        pos = i + 1
        board.append({
            "pos": pos, "card": card,
            "base_attack": card["attack"], "base_defense": card["defense"],
            "skill_disabled": False
        })

    # 技能失效位
    disabled_skill_positions = set()
    for effect in boss_effects:
        if effect["effect"]["type"] == "disable_skill_pos":
            disabled_skill_positions.add(effect["effect"]["pos"])
    for slot in board:
        if slot["pos"] in disabled_skill_positions:
            slot["skill_disabled"] = True

    # 调用 debug 模式计算（包含所有加成）
    total_def, total_atk, atk_list, def_list, atk_steps, def_steps = compute_per_card_stats(
        perm, boss_effects, debug=True
    )

    print("\n===== 当前排列调试 =====")
    print("激活的 Boss 效果：")
    for eff in boss_effects:
        name = eff.get("name", eff["effect"]["type"])
        effect = eff["effect"]
        if effect["type"] == "scale_all_attr":
            print(f"  - {name}: {effect['attr']} {effect['scale']:.0%}")
        elif effect["type"] == "scale_pos_attr":
            print(f"  - {name}: 位置{effect['pos']} {effect['attr']} {effect['scale']:.0%}")
        elif effect["type"] == "scale_type_attr":
            print(f"  - {name}: {effect['type_name']} {effect['attr']} {effect['scale']:.0%}")
        elif effect["type"] == "set_pos_attr_zero":
            print(f"  - {name}: 位置{effect['pos']} {effect['attr']} 置0")
        elif effect["type"] == "disable_skill_pos":
            print(f"  - {name}: 位置{effect['pos']} 技能失效")
        elif effect["type"] == "ban_type":
            print(f"  - {name}: 禁止 {effect['value']} 卡牌")
        elif effect["type"] == "ban_role":
            print(f"  - {name}: 禁止 {effect['value']} 机种")
        elif effect["type"] == "disable_position":
            print(f"  - {name}: 禁用位置 {effect['pos']}")
        else:
            print(f"  - {name}")

    print("\n卡牌详情：")
    for i, slot in enumerate(board):
        pos = i + 1
        card = slot["card"]
        if card["type"] == "blank":
            print(f"第{pos}位: 空白")
            continue
        print(f"第{pos}位: {card['name']} (基础攻{card['attack']}, 防{card['defense']})")
        if slot["skill_disabled"]:
            print(f"  ⚠ 技能已失效")
        print(f"  攻击计算: {atk_steps[i]} = {atk_list[i]}")
        print(f"  防御计算: {def_steps[i]} = {def_list[i]}")
    print(f"总攻击: {total_atk}, 总防御: {total_def}")
    print("========================================\n")

# -------------------- 求解器（含机队限制） --------------------
def solve(hand_cards, boss_atk, boss_def, boss_effects, fleet_limit, disabled_positions, independent_mode=False):
    banned_types, banned_roles = set(), set()
    for eff in boss_effects:
        e = eff["effect"]
        if e["type"] == "ban_type":
            banned_types.add(e["value"])
        elif e["type"] == "ban_role": banned_roles.add(e["value"])

    valid_cards = [c for c in hand_cards if c["type"] not in banned_types and c["role"] not in banned_roles]
    if not valid_cards:
        return None, (0, 0, "info_all_cards_banned", {})

    # ★ 按机队数量升序排序，让高性价比卡牌优先尝试
    valid_cards.sort(key=lambda c: c["fleet_count"])

    allowed_positions = [i for i in range(5) if i not in disabled_positions]
    max_slots = len(allowed_positions)

    # 独立号攻击模式（保持原逻辑，不并行）
    if independent_mode:
        best_perm = None
        best_atk = -1
        best_fleet = 9999
        max_cards = min(max_slots, len(valid_cards))
        snapshots = build_skill_snapshots(valid_cards)
        for m in range(1, max_cards + 1):
            for positions in itertools.combinations(allowed_positions, m):
                for perm_cards in itertools.permutations(valid_cards, m):
                    fleet_sum = sum(card["fleet_count"] for card in perm_cards)
                    if fleet_sum > 3:
                        continue
                    perm = [BLANK_CARD] * 5
                    for pos_idx, card in zip(positions, perm_cards):
                        perm[pos_idx] = card
                    total_def, total_atk = compute_final_stats(perm, boss_effects, snapshots)
                    if total_atk > best_atk or (total_atk == best_atk and fleet_sum < best_fleet):
                        best_atk = total_atk
                        best_perm = perm
                        best_fleet = fleet_sum
        if best_perm is None:
            return None, (0, 0, "info_cvl_result_none", {})
        total_def, total_atk, _, _ = compute_per_card_stats(best_perm, boss_effects)
        return list(best_perm), (total_def, total_atk, "info_cvl_result",
                                 {"total_atk":total_atk, "fleet":best_fleet})

    # ---------- 原有模式（并行化） ----------
    max_cards = min(max_slots, len(valid_cards))
    if max_cards == 0:
        return None, (0, 0, "info_result_none", {})

    snapshots = build_skill_snapshots(valid_cards)

    # 构建各 m 的参数
    tasks = []
    for m in range(1, max_cards + 1):
        tasks.append((
            m,
            valid_cards,
            allowed_positions,
            boss_effects,
            fleet_limit,
            boss_atk,
            boss_def,
            snapshots
        ))

    # 使用进程池并行计算
    with Pool(processes=4) as pool:
        results = pool.map(search_for_m, tasks)

    # 合并所有进程的结果
    best_both = None
    best_def_only = None
    best_lower = None
    fallback_best = None

    for res in results:
        b_both, b_def_only, b_lower, fbest = res

        # 合并 best_both：优先机队最小，攻击最小
        if b_both is not None:
            if best_both is None:
                best_both = b_both
            else:
                _, atk1, def1, fleet1, m1 = b_both
                _, atk2, def2, fleet2, m2 = best_both
                if (fleet1 < fleet2 or
                        (fleet1 == fleet2 and m1 < m2) or
                        (fleet1 == fleet2 and m1 == m2 and atk1 < atk2)):
                    best_both = b_both

        # 合并 best_def_only：攻击最大化
        if b_def_only is not None:
            if best_def_only is None or b_def_only[1] > best_def_only[1]:
                best_def_only = b_def_only

        # 合并 best_lower：攻击最大化
        if b_lower is not None:
            if best_lower is None or b_lower[1] > best_lower[1]:
                best_lower = b_lower

        # 合并 fallback_best：防御最高
        if fbest is not None:
            if fallback_best is None or fbest[2] > fallback_best[2]:
                fallback_best = fbest

    # 决策（与原 solve 完全相同）
    if best_both:
        perm, atk, def_, _, m = best_both
        return list(perm), (def_, atk, "info_strategy_best", {"card":m})
    elif best_def_only:
        if best_lower and best_lower[1] > best_def_only[1] * 1.15:
            perm, atk, def_ = best_lower
            return list(perm), (def_, atk, "info_strategy_good", {})
        else:
            perm, atk, def_ = best_def_only
            return list(perm), (def_, atk, "info_strategy_fair", {})
    else:
        if fallback_best:
            perm, atk, def_ = fallback_best
            return list(perm), (def_, atk, "info_strategy_bad", {})
        else:
            return None, (0, 0, "info_strategy_none", {})
