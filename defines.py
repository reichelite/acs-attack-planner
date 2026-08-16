import sys
import os
import json

# -------------------- 配置 --------------------
if getattr(sys, 'frozen', False):
    # 打包后：exe 所在目录（可读写）
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境：脚本所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_FILE = os.path.join(BASE_DIR, "card_state.json")
CARDS_FILE = os.path.join(BASE_DIR, "cards.json")
BOSS_SKILLS_FILE = os.path.join(BASE_DIR, "boss_skills.json")
DEBUG = False

# ---------- 条件技能集合 ----------
CONDITIONAL_SKILL_IDS = {
    "atk_if_support_3",
    "def_prev_battle_fixed",
    "atk_fixed_after_def5",
    "def_adjacent_attack",
    "atk_adjacent_defense",
    "atk_dual_torpedo",
    "atk_prev_bomb",
    "atk_def_other_fighter",
}

# -------------------- 多语言文件 --------------------
LANG_FILES = {
    "zh": {
        "app_title": "《航母生存》空袭解算器",
        "card_pool": "卡池",
        "atk_bonus": "攻击增益:",
        "def_bonus": "防御增益:",
        "fighter_lv": "战斗等级:",
        "bomber_lv": "轰炸等级:",
        "torpedo_lv": "鱼雷等级:",
        "type_attack": "进攻",
        "type_defense": "防御",
        "type_support": "支援",
        "enable": "启用",
        "name": "名称",
        "role": "机种",
        "atk_score": "攻击",
        "def_score": "防御",
        "attack": "攻击",
        "defense": "防御",
        "skill_desc": "技能约束",
        "skill_lvl": "技能等级",
        "squadron": "机队",
        "boss_attr": "敌军属性",
        "boss_atk": "敌军攻击值:",
        "boss_def": "敌军防御值:",
        "boss_skills": "敌军技能 (可多选):",
        "result": "排列结果",
        "squad_limit": "机队数量上限:",
        "cvl_attack": "独立号攻击",
        "solve_btn": "求解最优排列",
        "slot_empty": "第{pos}位: 空白",
        "result_info": "总攻击: {atk} | 总防御: {def} | 策略: {desc}",
        "info_calculating": "正在计算中，请稍后...",
        "animated_calculating": "计算中，请稍后... {char}",
        "warn_input_error": "输入错误",
        "warn_boss_stat_invalid": "敌军攻击/防御值必须为整数",
        "warn_squad_limit_invalid": "机队数量上限必须为整数",
        "warn_no_cards": "无可用卡牌",
        "warn_no_enabled_cards": "没有启用的卡牌，请至少启用一张卡牌。",
        "warn_unable_solve": "无法求解",
        "warn_no_valid_combo": "无可用组合",
        "info_combo_result": "第{pos}位: {name}  [攻击: {atk}, 防御: {defs}]",
        "info_combo_empty": "第{pos}位: 空白",
        "info_combo_summery": "总攻击: {final_atk} | 总防御: {final_def} | 策略: {desc}",
        "info_cvl_result_none": "无满足机队限制的组合（总机队≤3）",
        "info_cvl_result": "独立号攻击：最大攻击 {total_atk} (机队 {fleet})",
        "info_strategy_best": "满足不受伤并击败敌军 (机队最小, 上阵{card}张)",
        "info_strategy_good": "略微降低防御换取大幅攻击提升(≥15%)",
        "info_strategy_fair": "保证不受伤，攻击最大化",
        "info_strategy_bad": "无法不受伤，防御最高方案",
        "info_strategy_none": "所有组合均超出机队限制",
        "info_result_none": "无可用位置或可用卡牌",
        "info_all_cards_banned": "所有卡牌被禁用",
        "info": "提示",
        "tip_rename": "重命名",
        "tip_enter_name": "输入新名称：",
        "warn_keep_one_tab": "至少需要保留一个敌军页签。",
        "warn_keep_one_skill": "至少需要保留一个敌军技能。",
        "delete": "删除",
        "add_btn": "+",
        "close_btn": "✕",
        "ban_type": "禁止指定行动卡牌",
        "disable_skill_pos": "指定位置技能失效",
        "scale_pos_attr": "指定位置攻防下降",
        "scale_all_attr": "全体攻防减少",
        "scale_type_attr": "指定行动卡牌攻防下降",
        "disable_position": "禁用牌位",
        "set_pos_attr_zero": "指定位置攻防置0",
        "ban_role": "禁止使用机种卡牌",
        "scale_role_attr": "指定机种卡牌攻防降低",
        "fighter": "战斗",
        "bomber": "轰炸",
        "torpedo": "鱼雷",
        "role_fighter": "战斗",
        "role_bomber": "轰炸",
        "role_torpedo": "鱼雷",
        "position": "位置",
        "fleet_tab": "舰队{num}",
        "card_blank": "空白",
        # 卡牌名称
        "skill_anvil_attack": "铁砧攻击",
        "skill_fixed_target": "目标定影",
        "skill_torpedo_run": "巡弋潜艇",
        "skill_precision_bombing": "精准炸弹",
        "skill_defensive_bombing": "防御性轰炸",
        "skill_bulwark": "铁墙",
        "skill_jinking": "快速闪避",
        "skill_combat_box": "箱型战斗队形",
        "skill_strike_from_the_sun": "耀式攻击",
        "skill_feint": "假装进攻",
        "skill_lone_wolf": "独狼",
        "skill_barrel_roll": "进攻型桶滚",
        "skill_wingmen": "僚机",
        "skill_leap_of_faith": "信仰飞跃",
        "skill_finger_four": "四指队形",
        "skill_tin_fish": "双鱼雷",
        "skill_thach_weave": "萨奇剪",
        "skill_lufbery_circle": "卢氏圆圈",
        # 卡牌描述
        "desc_anvil_attack": "5号位攻防增加（比例）",
        "desc_fixed_target": "若3号位为支援类，自身攻击增加（定值）",
        "desc_torpedo_run": "前加防，后加攻（比例）",
        "desc_precision_bombing": "前一位为战斗则加防（定值）",
        "desc_defensive_bombing": "前一位加防（比例）",
        "desc_bulwark": "相邻位加攻防（比例）",
        "desc_jinking": "1、5号位加攻（比例）",
        "desc_combat_box": "所有战斗机加防（比例）",
        "desc_strike_from_the_sun": "1、2号位加攻（定值）",
        "desc_feint": "后两位加防（比例）",
        "desc_lone_wolf": "进攻类加防（比例）",
        "desc_barrel_roll": "先前所有轰炸机加攻（比例）",
        "desc_wingmen": "其余战斗机加攻防（比例）",
        "desc_leap_of_faith": "相邻行动加防御（比例）",
        "desc_finger_four": "5为防御则后续行动加攻击（定值）",
        "desc_tin_fish": "其余鱼雷机加攻击（定值）",
        "desc_thach_weave": "前后为进攻，防御增加（比例）",
        "desc_lufbery_circle": "前后为防御，攻击增加（定值）",
    },
    "en": {
        "app_title": "Aircraft Carrier: Survival Attack Planner",
        "card_pool": "Card Pool",
        "atk_bonus": "ATK Bonus:",
        "def_bonus": "DEF Bonus:",
        "fighter_lv": "Fighter Lv:",
        "bomber_lv": "Bomber Lv:",
        "torpedo_lv": "Torpedo Lv:",
        "type_attack": "Offensive",
        "type_defense": "Defensive",
        "type_support": "Supportive",
        "enable": "Enable",
        "name": "Name",
        "role": "Role",
        "atk_score": "ATK",
        "def_score": "DEF",
        "attack": "ATK",
        "defense": "DEF",
        "skill_desc": "Modifier",
        "skill_lvl": "Level",
        "squadron": "Squadron",
        "boss_attr": "Enemy Attributes",
        "boss_atk": "Enemy ATK:",
        "boss_def": "Enemy DEF:",
        "boss_skills": "Enemy Debuffs (multiple):",
        "result": "Result",
        "squad_limit": "Squadron Limit:",
        "cvl_attack": "USS Independence Attack",
        "solve_btn": "Solve",
        "slot_empty": "Slot {pos}: Empty",
        "result_info": "ATK: {atk} | DEF: {def} | Strategy: {desc}",
        "warn_input_error": "Input Error",
        "warn_boss_stat_invalid": "Enemy ATK/DEF must be integers",
        "warn_squad_limit_invalid": "Squadron limit must be an integer",
        "warn_no_cards": "No Cards",
        "warn_no_enabled_cards": "No cards enabled. Enable at least one.",
        "warn_unable_solve": "Unable to solve",
        "warn_no_valid_combo": "No valid combinations",
        "info_combo_result": "#{pos}: {name}  [ATK: {atk}, DEF: {defs}]",
        "info_combo_empty": "#{pos}: Empty",
        "info_combo_summery": "Total DEF: {final_atk} | Total ATK: {final_def} | Strategy: {desc}",
        "info_cvl_result_none": "No combination meeting squadron limit (≤3)",
        "info_cvl_result": "CVL attack：Total ATK {total_atk} (Squadrons {fleet})",
        "info_strategy_best": "No loss, enemy eliminated (fewest squadrons, {card} cards)",
        "info_strategy_good": "Trade DEF slightly for ATK boost (≥15%)",
        "info_strategy_fair": "No loss, max ATK",
        "info_strategy_bad": "Loss unavoidable，max DEF",
        "info_strategy_none": "All combinations beyond squadron limits",
        "info_result_none": "No available slots or cards",
        "info_all_cards_banned": "All cards banned",
        "info": "Info",
        "info_calculating": "Calculating, please wait...",
        "animated_calculating": "Calculating, please wait... {char}",
        "tip_rename": "Rename",
        "tip_enter_name": "Enter new name:",
        "warn_keep_one_tab": "At least one enemy tab must remain.",
        "warn_keep_one_skill": "At least one enemy debuff must remain.",
        "delete": "Delete",
        "add_btn": "+",
        "close_btn": "✕",
        "ban_type": "Disable Ops Type",
        "disable_skill_pos": "Disable Modifier at #",
        "scale_pos_attr": "ATK/DEF Decrease at #",
        "scale_all_attr": "Overall ATK/DEF Decrease",
        "scale_type_attr": "Ops ATK/DEF Decrease",
        "disable_position": "Disable Slot",
        "set_pos_attr_zero": "Nullify ATK/DEF at #",
        "ban_role": "Disable Plane Type",
        "scale_role_attr": "Plane Type ATK/DEF Decrease",
        "fighter": "Fighter",
        "bomber": "Bomber",
        "torpedo": "Torpedo",
        "role_fighter": "Fighter",
        "role_bomber": "Bomber",
        "role_torpedo": "Torpedo",
        "position": "Position",
        "fleet_tab": "Fleet {num}",
        "card_blank": "Empty",
        "skill_anvil_attack": "Anvil Attack",
        "skill_fixed_target": "Fixed Target",
        "skill_torpedo_run": "Torpedo Run",
        "skill_precision_bombing": "Precision Bombing",
        "skill_defensive_bombing": "Defensive Bombing",
        "skill_bulwark": "Bulwark",
        "skill_jinking": "Jinking",
        "skill_combat_box": "Combat Box",
        "skill_strike_from_the_sun": "Strike from the Sun",
        "skill_feint": "Feint",
        "skill_lone_wolf": "Lone Wolf",
        "skill_barrel_roll": "Barrel Roll",
        "skill_wingmen": "Wingman",
        "skill_leap_of_faith": "Leap of Faith",
        "skill_finger_four": "Finger-Four",
        "skill_tin_fish": "Tin Fish",
        "skill_thach_weave": "Thach Weave",
        "skill_lufbery_circle": "Lufbery Circle",
        "desc_anvil_attack": "#5 ATK/DEF+",
        "desc_fixed_target": "If #3 is Support, self ATK+",
        "desc_torpedo_run": "Prev slots DEF+, following slots ATK+",
        "desc_precision_bombing": "If prev is fighter, DEF+",
        "desc_defensive_bombing": "Prev slot DEF+",
        "desc_bulwark": "Adjacent slots ATK/DEF+",
        "desc_jinking": "#1,5 ATK+",
        "desc_combat_box": "All fighters DEF+",
        "desc_strike_from_the_sun": "#1,2 ATK+",
        "desc_feint": "Next two slots DEF+",
        "desc_lone_wolf": "Offensive ops DEF+",
        "desc_barrel_roll": "Prev bombers ATK+",
        "desc_wingmen": "Other fighters ATK/DEF+",
        "desc_leap_of_faith": "Adjacent slots DEF+",
        "desc_finger_four": "If #5 is Defensive, following slots ATK+",
        "desc_tin_fish": "Other Torpedoes ATK+",
        "desc_thach_weave": "If adjacent slots are Offensive, DEF+",
        "desc_lufbery_circle": "If adjacent slots are Defensive, ATK+",
    }
}

# ---------- 常量 ----------
PCT_VALUES = ["+20%","+15%","+10%","-10%","-15%","-20%","-25%","-30%","-35%","-40%","-100%"]
POS_VALUES = ["1","2","3","4","5"]
AIRCRAFT_TYPES = ["role_fighter", "role_bomber", "role_torpedo"]
OPS_VALUES = ["type_attack", "type_defense", "type_support"]
ATTR_VALUES = ["attack", "defense"]
AIRCRAFT_LVLS = ["1","2","3"]

# ---------- 空白卡 ----------
BLANK_CARD = {
    "name": "card_blank", "type": "blank", "role": "blank",
    "attack": 0, "defense": 0,
    "skill_id": None, "skill_value": 0, "skill_type": "percent", "skill_desc": "",
    "fleet_count": 0, "trans_key": "card_blank"
}

def create_default_lang_files():
    for lang, data in LANG_FILES.items():
        path = os.path.join(BASE_DIR, f"lang_{lang}.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


def create_default_cards(filepath):
    """创建默认卡牌数据"""
    cards = [
        {"name": "铁砧攻击", "type": "type_attack", "role": "role_torpedo", "attack": 11, "defense": 3,
         "skill_id": "atk_def_pos5", "skill_levels": [125, 150, 175], "skill_type": "percent",
         "skill_desc": "desc_anvil_attack", "fleet_count": 2,
         "trans_key": "skill_anvil_attack"},
        {"name": "目标定影", "type": "type_attack", "role": "role_bomber", "attack": 7, "defense": 5,
         "skill_id": "atk_if_support_3", "skill_levels": [5, 6, 7], "skill_type": "fixed",
         "skill_desc": "desc_fixed_target", "fleet_count": 1,
         "trans_key": "skill_fixed_target"},
        {"name": "巡弋潜艇", "type": "type_attack", "role": "role_torpedo", "attack": 7, "defense": 6,
         "skill_id": "front_def_back_atk", "skill_levels": [25, 50, 75], "skill_type": "percent",
         "skill_desc": "desc_torpedo_run", "fleet_count": 1,
         "trans_key": "skill_torpedo_run"},
        {"name": "精准炸弹", "type": "type_attack", "role": "role_bomber", "attack": 8, "defense": 4,
         "skill_id": "def_prev_battle_fixed", "skill_levels": [3, 6, 8], "skill_type": "fixed",
         "skill_desc": "desc_precision_bombing", "fleet_count": 1,
         "trans_key": "skill_precision_bombing"},
        {"name": "防御性轰炸", "type": "type_defense", "role": "role_bomber", "attack": 3, "defense": 5,
         "skill_id": "def_prev", "skill_levels": [125, 150, 175], "skill_type": "percent",
         "skill_desc": "desc_defensive_bombing", "fleet_count": 1,
         "trans_key": "skill_defensive_bombing"},
        {"name": "铁墙", "type": "type_defense", "role": "role_fighter", "attack": 5, "defense": 8,
         "skill_id": "atk_def_adjacent", "skill_levels": [50, 75, 100], "skill_type": "percent",
         "skill_desc": "desc_bulwark", "fleet_count": 2,
         "trans_key": "skill_bulwark"},
        {"name": "快速闪避", "type": "type_defense", "role": "role_fighter", "attack": 4, "defense": 7,
         "skill_id": "atk_pos1_and_5", "skill_levels": [75, 100, 125], "skill_type": "percent",
         "skill_desc": "desc_jinking", "fleet_count": 1,
         "trans_key": "skill_jinking"},
        {"name": "箱型战斗队形", "type": "type_defense", "role": "role_bomber", "attack": 6, "defense": 11,
         "skill_id": "def_all_fighter", "skill_levels": [100, 125, 150], "skill_type": "percent",
         "skill_desc": "desc_combat_box", "fleet_count": 2,
         "trans_key": "skill_combat_box"},
        {"name": "耀式攻击", "type": "type_support", "role": "role_bomber", "attack": 5, "defense": 6,
         "skill_id": "atk_pos1_and_2", "skill_levels": [4, 6, 8], "skill_type": "fixed",
         "skill_desc": "desc_strike_from_the_sun", "fleet_count": 1,
         "trans_key": "skill_strike_from_the_sun"},
        {"name": "假装进攻", "type": "type_support", "role": "role_bomber", "attack": 6, "defense": 6,
         "skill_id": "def_next_two", "skill_levels": [75, 100, 125], "skill_type": "percent",
         "skill_desc": "desc_feint", "fleet_count": 1,
         "trans_key": "skill_feint"},
        {"name": "独狼", "type": "type_support", "role": "role_bomber", "attack": 10, "defense": 1,
         "skill_id": "def_all_atk", "skill_levels": [50, 75, 100], "skill_type": "percent",
         "skill_desc": "desc_lone_wolf", "fleet_count": 1,
         "trans_key": "skill_lone_wolf"},
        {"name": "进攻型桶滚", "type": "type_support", "role": "role_torpedo", "attack": 4, "defense": 2,
         "skill_id": "atk_prev_bomb", "skill_levels": [3, 5, 7], "skill_type": "fixed",
         "skill_desc": "desc_barrel_roll", "fleet_count": 1,
         "trans_key": "skill_barrel_roll"},
        {"name": "僚机", "type": "type_support", "role": "role_fighter", "attack": 3, "defense": 4,
         "skill_id": "atk_def_other_fighter", "skill_levels": [125, 150, 175], "skill_type": "percent",
         "skill_desc": "desc_wingmen", "fleet_count": 1,
         "trans_key": "skill_wingmen"},
        {"name": "信仰飞跃", "type": "type_defense", "role": "role_fighter", "attack": 5, "defense": 6,
         "skill_id": "def_adjacent", "skill_levels": [150, 200, 250], "skill_type": "percent",
         "skill_desc": "desc_leap_of_faith", "fleet_count": 2,
         "trans_key": "skill_leap_of_faith"},
        {"name": "四指队形", "type": "type_attack", "role": "role_torpedo", "attack": 4, "defense": 4,
         "skill_id": "atk_fixed_after_def5", "skill_levels": [4, 5, 6], "skill_type": "fixed",
         "skill_desc": "desc_finger_four", "fleet_count": 1,
         "trans_key": "skill_finger_four"},
        {"name": "双鱼雷", "type": "type_attack", "role": "role_torpedo", "attack": 8, "defense": 3,
         "skill_id": "atk_dual_torpedo", "skill_levels": [4, 6, 8], "skill_type": "fixed",
         "skill_desc": "desc_tin_fish", "fleet_count": 2,
         "trans_key": "skill_tin_fish"},
        {"name": "萨奇剪", "type": "type_defense", "role": "role_fighter", "attack": 5, "defense": 6,
         "skill_id": "def_adjacent_attack", "skill_levels": [125, 150, 175], "skill_type": "percent",
         "skill_desc": "desc_thach_weave", "fleet_count": 1,
         "trans_key": "skill_thach_weave"},
        {"name": "卢氏圆圈", "type": "type_support", "role": "role_torpedo", "attack": 0, "defense": 6,
         "skill_id": "atk_adjacent_defense", "skill_levels": [10, 12, 14], "skill_type": "fixed",
         "skill_desc": "desc_lufbery_circle", "fleet_count": 1,
         "trans_key": "skill_lufbery_circle"}
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)


def create_default_boss_skills(filepath):
    skills = [
        {"name": "禁止指定行动卡牌", "effect": {"type": "ban_type"}, "trans_key": "ban_type"},
        {"name": "指定位置技能失效", "effect": {"type": "disable_skill_pos", "pos": 3}, "trans_key": "disable_skill_pos"},
        {"name": "指定位置攻防下降", "effect":{"type": "scale_pos_attr"}, "trans_key": "scale_pos_attr"},
        {"name": "全体攻防减少", "effect": {"type": "scale_all_attr", "scale": 0.85}, "trans_key": "scale_all_attr"},
        {"name": "指定行动卡牌攻防下降", "effect":{"type": "scale_type_attr"}, "trans_key": "scale_type_attr"},
        {"name": "禁用牌位", "effect": {"type": "disable_position", "pos": 1}, "trans_key": "disable_position"},
        {"name": "指定位置攻防置0", "effect":{"type": "set_pos_attr_zero", "value": 0}, "trans_key": "set_pos_attr_zero"},
        {"name": "禁止使用机种卡牌", "effect":{"type": "ban_role"}, "trans_key": "ban_role"},
        {"name": "指定机种卡牌攻防降低", "effect":{"type": "scale_role_attr"}, "trans_key": "scale_role_attr"}
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


def load_json(filename, default_creator):
    if not os.path.exists(filename):
        default_creator(filename)
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            if all(isinstance(item, dict) and "name" in item for item in data):
                return data
        print(f"警告：{filename} 数据损坏，正在重新生成...")
        default_creator(filename)
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"警告：{filename} 读取失败，正在重新生成...")
        default_creator(filename)
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
