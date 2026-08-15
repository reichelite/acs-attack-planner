import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, font
import json
import os
import copy
from multiprocessing import freeze_support
import threading

from defines import (
    BASE_DIR, STATE_FILE, CARDS_FILE, BOSS_SKILLS_FILE, DEBUG,
    #CONDITIONAL_SKILL_IDS, LANG_FILES,
    PCT_VALUES, POS_VALUES, AIRCRAFT_TYPES, OPS_VALUES, ATTR_VALUES,
    #AIRCRAFT_LVLS, BLANK_CARD,
    create_default_lang_files, create_default_cards, create_default_boss_skills, load_json
)

from solver import solve, compute_per_card_stats, print_debug_info
from gui_widgets import BossTabData

class CardGameApp:
    def __init__(self, root):
        self.root = root
        create_default_lang_files()
        # 多语言支持
        self.trans = {}
        self.current_lang = "zh"
        self.lang_pref_file = os.path.join(BASE_DIR, "lang_pref.json")
        pref_lang = "zh"
        if os.path.exists(self.lang_pref_file):
            try:
                with open(self.lang_pref_file, "r", encoding="utf-8") as f:
                    pref_lang = json.load(f).get("lang", "zh")
            except:
                pass
        self.load_language(pref_lang)

        self.root.title(self.t("app_title"))
        self.cards_data = load_json(CARDS_FILE, create_default_cards)
        self.boss_skills_data = load_json(BOSS_SKILLS_FILE, create_default_boss_skills)

        self.card_level_vars = []
        self.card_enable_vars = []
        for card in self.cards_data:
            levels = card.get("skill_levels", [100])
            if card.get("skill_type", "percent") == "percent":
                var = tk.StringVar(value=f"{levels[0]}%")
            else:
                var = tk.StringVar(value=str(levels[0]))
            self.card_level_vars.append(var)
            self.card_enable_vars.append(tk.BooleanVar(value=True))

        self.attack_gain_var = None
        self.defense_gain_var = None
        self.battle_level_var = tk.StringVar(value="1")
        self.bomb_level_var = tk.StringVar(value="1")
        self.torpedo_level_var = tk.StringVar(value="1")

        self.notebook = None
        self.tab_data_list = []
        self.next_tab_number = 1
        self.add_btn = None

        self.load_card_state()
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.solving = False
        self.solve_result = None
        self.solve_thread = None
        self.progress_chars = ["\\", "/", "-"]
        self.progress_index = 0
        self.after_id = None
        self._pending_boss_effects = None
        self._pending_tab_data = None
        self._reverse_trans = {} #反向映射（当前语言）

    # ---------- 语言核心 ----------
    def load_language(self, lang):
        filename = os.path.join(BASE_DIR, f"lang_{lang}.json")
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.trans = json.load(f)
            # 构建反向映射：翻译文本 -> 键
            self._reverse_trans = {v: k for k, v in self.trans.items()}
        except Exception as e:
            print(f"Load language file failed: {e}")
            self.trans = {}
            self._reverse_trans = {}
        self.current_lang = lang

    def t(self, key, **kwargs):
        text = self.trans.get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

    #def _reverse_lookup(self, translated_text):
    #    """根据当前语言的翻译文本获取内部键，若找不到则返回原文本（可能已经是键或中文）"""
    #    return self._reverse_trans.get(translated_text, translated_text)

    def switch_language(self, lang):
        if lang == self.current_lang:
            return
        self.load_language(lang)

        # 1. 保存每个敌军页签的效果状态（基于trans_key）
        for tab_data in self.tab_data_list:
            saved = []
            for item in tab_data.boss_effect_vars:
                disp = item["combo"].get()
                skill_key = None
                # 通过翻译文本找技能键
                for skill in self.boss_skills_data:
                    if self.t(skill["trans_key"]) == disp:
                        skill_key = skill["trans_key"]
                        break
                # === 新增：回退逻辑 ===
                if not skill_key and disp:
                    # 尝试直接匹配 trans_key（如果用户还没切换过语言）
                    for skill in self.boss_skills_data:
                        if skill["trans_key"] == disp:
                            skill_key = skill["trans_key"]
                            break

                saved.append({
                    "skill_key": skill_key,
                    "pos": item["pos_var"].get(),
                    "role": item["role_var"].get(),
                    "type": item["type_var"].get(),
                    "value": item["value_var"].get(),
                    "role_scale": item["role_scale_var"].get(),
                    "attr_scale": item["role_attr_scale_var"].get(),
                    "pct_scale": item["role_percent_scale_var"].get(),
                    "type_scale": item["type_scale_var"].get(),
                    "type_attr_scale": item["type_attr_scale_var"].get(),
                    "type_pct_scale": item["type_percent_scale_var"].get(),
                    "pos_scale": item["pos_scale_var"].get(),
                    "pos_attr_scale": item["pos_attr_scale_var"].get(),
                    "pos_pct_scale": item["pos_pct_scale_var"].get(),
                    "attr_all": item["attr_all_var"].get(),
                })
            tab_data.saved_effects = saved

        # 2. 重建卡牌列表
        self.populate_card_lists()

        # 3. 刷新主界面静态控件
        self._refresh_language(self.root)

        # 4. 处理每个敌军标签页
        for tab_data in self.tab_data_list:
            for widget in tab_data.boss_effects_container.winfo_children():
                widget.destroy()
            tab_data.boss_effect_vars.clear()

            for saved in tab_data.saved_effects:
                self.add_boss_effect_row_to_tab(tab_data)
                last = tab_data.boss_effect_vars[-1]
                if saved["skill_key"]:
                    last["combo"].set(self.t(saved["skill_key"]))
                last["pos_var"].set(saved["pos"])
                last["role_var"].set(saved["role"])
                last["type_var"].set(saved["type"])
                last["value_var"].set(saved["value"])
                last["role_scale_var"].set(saved["role_scale"])
                last["role_attr_scale_var"].set(saved["attr_scale"])
                last["role_percent_scale_var"].set(saved["pct_scale"])
                last["type_scale_var"].set(saved["type_scale"])
                last["type_attr_scale_var"].set(saved["type_attr_scale"])
                last["type_percent_scale_var"].set(saved["type_pct_scale"])
                last["pos_scale_var"].set(saved["pos_scale"])
                last["pos_attr_scale_var"].set(saved["pos_attr_scale"])
                last["pos_pct_scale_var"].set(saved["pos_pct_scale"])
                last["attr_all_var"].set(saved["attr_all"])

            self._refresh_language(tab_data.frame)
            self._refresh_tab_results(tab_data)

        for i, tab_data in enumerate(self.tab_data_list):
            self.notebook.tab(i, text=self.t("fleet_tab", num=tab_data.tab_num))

    def _refresh_language(self, widget):
        for child in widget.winfo_children():
            if isinstance(child, (tk.Label, ttk.Label, tk.Button, ttk.Button,
                                  ttk.LabelFrame, ttk.Checkbutton)):
                if hasattr(child, 'trans_key'):
                    params = getattr(child, 'trans_params', {})
                    child.config(text=self.t(child.trans_key, **params))
            elif isinstance(child, ttk.Notebook):
                for i in range(child.index("end")):
                    frame = child.nametowidget(child.tabs()[i])
                    if hasattr(frame, 'trans_key'):
                        params = getattr(frame, 'trans_params', {})
                        child.tab(i, text=self.t(frame.trans_key, **params))
            self._refresh_language(child)

    def _refresh_tab_results(self, tab_data):
        for i in range(5):
            if tab_data.last_result:
                perm, _, _, _, _, atk_list, def_list = tab_data.last_result
                if i < len(perm):
                    #card_key = perm[i]["trans_key"]   # 卡牌数据应包含此字段
                    card = perm[i]
                    #name = self.t(card_key) if card_key else perm[i]["name"]
                    name = self.t(card.get("trans_key", ""))
                    lbl = self.t("info_combo_result", pos=i+1, name=name,
                                 atk=atk_list[i], defs=def_list[i])
                else:
                    lbl = self.t("info_combo_empty", pos=i+1)
            else:
                lbl = self.t("slot_empty", pos=i+1)
            tab_data.result_labels[i].config(text=lbl)

        if tab_data.last_result:
            _, final_def, final_atk, desc, kwargs, _, _ = tab_data.last_result
            strategy_text = self.t(desc, **kwargs)
            tab_data.solution_info_label.config(
                text=self.t("info_combo_summery", final_def=final_def, final_atk=final_atk, desc=strategy_text))
        else:
            tab_data.solution_info_label.config(text="")

    # ---------- 界面构建 ----------
    def setup_ui(self):
        t = self.t
        # 菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        lang_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Language", menu=lang_menu)
        lang_menu.add_command(label="中文", command=lambda: self.switch_language("zh"))
        lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))

        # 卡池区域
        top_frame = ttk.LabelFrame(self.root, text=t("card_pool"), padding=10)
        top_frame.trans_key = "card_pool"
        top_frame.pack(fill=tk.X, expand=False, padx=10, pady=5)

        gain_frame = ttk.Frame(top_frame)
        gain_frame.pack(fill=tk.X, pady=(0,5))

        lbl = ttk.Label(gain_frame, text=t("atk_bonus"))
        lbl.trans_key = "atk_bonus"; lbl.pack(side=tk.LEFT, padx=(0,5))
        self.attack_gain_var = tk.StringVar(value="0")
        ttk.Entry(gain_frame, textvariable=self.attack_gain_var, width=3).pack(side=tk.LEFT, padx=5)

        lbl = ttk.Label(gain_frame, text=t("def_bonus"))
        lbl.trans_key = "def_bonus"; lbl.pack(side=tk.LEFT, padx=(10,5))
        self.defense_gain_var = tk.StringVar(value="0")
        ttk.Entry(gain_frame, textvariable=self.defense_gain_var, width=3).pack(side=tk.LEFT, padx=5)

        lbl = ttk.Label(gain_frame, text=t("fighter_lv"))
        lbl.trans_key = "fighter_lv"; lbl.pack(side=tk.LEFT, padx=(10,5))
        ttk.Combobox(gain_frame, textvariable=self.battle_level_var, values=["1","2","3"], state="readonly", width=3).pack(side=tk.LEFT, padx=5)

        lbl = ttk.Label(gain_frame, text=t("bomber_lv"))
        lbl.trans_key = "bomber_lv"; lbl.pack(side=tk.LEFT, padx=(10,5))
        ttk.Combobox(gain_frame, textvariable=self.bomb_level_var, values=["1","2","3"], state="readonly", width=3).pack(side=tk.LEFT, padx=5)

        lbl = ttk.Label(gain_frame, text=t("torpedo_lv"))
        lbl.trans_key = "torpedo_lv"; lbl.pack(side=tk.LEFT, padx=(10,5))
        ttk.Combobox(gain_frame, textvariable=self.torpedo_level_var, values=["1","2","3"], state="readonly", width=3).pack(side=tk.LEFT, padx=5)

        notebook_cards = ttk.Notebook(top_frame)
        notebook_cards.pack(fill=tk.BOTH, expand=True)
        type_keys = ["type_attack", "type_defense", "type_support"]
        self.card_frames = {}
        for key in type_keys:
            frame = ttk.Frame(notebook_cards)
            frame.trans_key = key
            notebook_cards.add(frame, text=t(key))
            self.card_frames[key] = frame
        self.populate_card_lists()

        # 敌军 标签页区域
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tab_bar = ttk.Frame(bottom_frame)
        tab_bar.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Boss.TNotebook", tabposition="nw")
        style.configure("Boss.TNotebook.Tab", width=0)

        self.notebook = ttk.Notebook(tab_bar, style="Boss.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Double-1>", self.on_tab_double_click)

        self.add_btn = tk.Button(tab_bar, text=t("add_btn"), font=("TkDefaultFont", 10), width=2,
                                 relief="raised", bd=1, command=self.add_tab)
        self.add_btn.trans_key = "add_btn"
        self.add_btn.place(relx=1.0, y=2, anchor=tk.NE)

        def reposition_btn(event=None):
            self.add_btn.place_configure(relx=1.0, y=2, anchor=tk.NE)
        tab_bar.bind("<Configure>", reposition_btn)

        self.add_tab()
        self.root.update_idletasks()

        top_height = top_frame.winfo_reqheight()
        top_frame.pack_propagate(False)
        top_frame.configure(height=top_height)

        result_height = 0
        if self.tab_data_list and self.tab_data_list[0].bottom_frame:
            result_height = self.tab_data_list[0].bottom_frame.winfo_reqheight()

        total_height = top_height + 30 + result_height + 150 + 80
        screen_height = self.root.winfo_screenheight()
        final_height = min(max(600, total_height), int(screen_height * 0.9))
        self.root.geometry(f"640x{final_height}")

    def populate_card_lists(self):
        t = self.t
        for tkey, frame in self.card_frames.items():
            for widget in frame.winfo_children():
                widget.destroy()

            columns = ("enable", "name", "role", "atk", "def", "skill_lvl", "squadron", "skill_desc")
            tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')

            # 仅保留水平滚动条，按需显示
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(xscrollcommand=hsb.set)

            tree.grid(row=0, column=0, sticky='nsew')
            # 水平滚动条放在 row=1，初始隐藏（通过后续检查决定是否显示）
            hsb.grid(row=1, column=0, sticky='ew')
            hsb.grid_remove()  # 默认隐藏

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            headings = {
                "enable": t("enable"), "name": t("name"), "role": t("role"),
                "atk": t("atk_score"), "def": t("def_score"), "skill_lvl": t("skill_lvl"),
                "squadron": t("squadron"), "skill_desc": t("skill_desc")
            }
            for col in columns:
                tree.heading(col, text=headings[col], anchor=tk.CENTER)
                tree.column(col, anchor=tk.CENTER, width=50, minwidth=30, stretch=False)

            row_count = 0
            for idx, card in enumerate(self.cards_data):
                if card["type"] != tkey:
                    continue
                enabled = self.card_enable_vars[idx].get()
                enable_text = "☑" if enabled else "☐"
                level_text = self.card_level_vars[idx].get() + " ▼"
                values = (
                    enable_text,
                    t(card["trans_key"]),
                    t(card["role"]),
                    str(card["attack"]),
                    str(card["defense"]),
                    level_text,
                    str(card.get("fleet_count", 0)),
                    t(card["skill_desc"])
                )
                iid = tree.insert("", tk.END, values=values)
                tree.item(iid, tags=(str(idx),))
                row_count += 1

            if row_count > 0:
                tree.configure(height=row_count)

            self._autosize_tree_columns(tree, columns)
            tree.column("name", anchor=tk.W)
            tree.column("skill_desc", anchor=tk.W)

            style = ttk.Style()
            style.configure("Treeview", rowheight=22)

            # 水平滚动条显示/隐藏逻辑
            def update_hscroll():
                # 检查是否需要水平滚动
                if tree.xview() == (0.0, 1.0):
                    hsb.grid_remove()
                else:
                    hsb.grid()

            # 在 tree 尺寸变化或列宽调整后调用
            tree.bind('<Configure>', lambda e: update_hscroll())
            # 也可以在修改列宽后手动调用一次
            update_hscroll()

            tree.bind('<ButtonRelease-1>', lambda e, tr=tree: self._on_tree_click(e, tr))
            tree.bind('<Double-1>', lambda e, tr=tree: self._on_tree_double_click(e, tr))

    def _autosize_tree_columns(self, tree, columns):
        """自动调整列宽，使用动态字体测量"""
        font_obj = tk.font.Font()
        # 获取实际的字体对象（Treeview 可能使用不同字体）
        try:
            style = ttk.Style()
            tree_font = style.lookup('Treeview', 'font')
            if tree_font:
                font_obj = tk.font.Font(name=tree_font, exists=True) or font_obj
        except:
            pass

        PADDING = 8          # 左右各留 8 像素，原为 20
        MIN_WIDTH = 30       # 最小列宽（原为 50）
        '''
        # 列名映射（用于最小宽度保证）
        min_widths = {
            "enable": 50,
            "name": 100,
            "role": 60,
            "atk": 50,
            "def": 50,
            "skill_lvl": 70,
            "squadron": 60,
            "skill_desc": 120,
        }
        '''

        for col in columns:
            # 测量标题宽度
            header_text = tree.heading(col, 'text')
            max_width = font_obj.measure(header_text) + PADDING * 2  # 额外 padding

            # 测量内容宽度
            for item in tree.get_children():
                text = tree.set(item, col)
                # 去掉下拉箭头标记，避免多余宽度
                clean_text = text.replace(" ▼", "")
                width = font_obj.measure(clean_text) + PADDING * 2
                if width > max_width:
                    max_width = width

            # 确保不低于最小宽度
            if max_width < MIN_WIDTH:
                max_width = MIN_WIDTH
            tree.column(col, width=max_width)

    def _on_tree_click(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            # 点击空白区域，关闭已存在的下拉框
            for child in tree.place_slaves():
                if isinstance(child, ttk.Combobox):
                    child.destroy()
            return
        col = tree.identify_column(event.x)
        iid = tree.identify_row(event.y)
        if not iid:
            return

        # 如果点击的不是技能等级列，销毁旧 Combobox
        if col != "#6":
            for child in tree.place_slaves():
                if isinstance(child, ttk.Combobox):
                    child.destroy()

        tags = tree.item(iid, 'tags')
        if not tags:
            return
        idx = int(tags[0])

        if col == "#1":  # 启用列
            current = self.card_enable_vars[idx].get()
            new_state = not current
            self.card_enable_vars[idx].set(new_state)
            tree.set(iid, "enable", "☑" if new_state else "☐")
        elif col == "#6":  # 技能等级列
            # 检查是否已有 Combobox 覆盖在该单元格上
            existing = None
            for child in tree.place_slaves():
                if isinstance(child, ttk.Combobox):
                    existing = child
                    break
            if existing:
                # 已有下拉框，直接展开下拉列表
                existing.focus_set()
                existing.after(30, lambda: existing.event_generate('<Down>'))
            else:
                self._show_level_combo(tree, iid, col, idx)

    def _on_tree_double_click(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region == "nothing":
            tree.selection_remove(tree.selection())

    def _show_level_combo(self, tree, iid, col, idx):
        """显示等级选择下拉框，并增强交互体验"""
        # 移除旧 Combobox（如果有）
        for child in tree.place_slaves():
            if isinstance(child, ttk.Combobox):
                child.destroy()

        card = self.cards_data[idx]
        levels = card.get("skill_levels", [100])
        if card.get("skill_type", "percent") == "percent":
            level_options = [f"{l}%" for l in levels]
        else:
            level_options = [str(l) for l in levels]

        # 创建下拉框
        combo = ttk.Combobox(tree, values=level_options, state="readonly")
        current_display = tree.set(iid, "skill_lvl")
        current_val = current_display.replace(" ▼", "")
        combo.set(current_val)

        # 定位下拉框
        x, y, w, h = tree.bbox(iid, col)
        if not (x and y and w and h):  # 如果列不可见，使用估算位置
            x, y, w, h = 200, 20 * int(iid[1:]) if iid[1:].isdigit() else 20, 60, 22
        combo.place(x=x, y=y, width=w, height=h)

        def on_select(event):
            new_val = combo.get()
            tree.set(iid, "skill_lvl", new_val + " ▼")
            self.card_level_vars[idx].set(new_val)
            combo.destroy()
            self.save_card_state()

        def on_key(event):
            """键盘导航"""
            if event.keysym == 'Escape':
                combo.destroy()
                tree.focus_set()
            elif event.keysym == 'Return':
                on_select(None)
            elif event.keysym == 'Up':
                current_idx = -1
                try:
                    current_idx = level_options.index(combo.get())
                except ValueError:
                    pass
                if current_idx > 0:
                    combo.set(level_options[current_idx - 1])
                    combo.selection_range(0, tk.END)
            elif event.keysym == 'Down':
                current_idx = -1
                try:
                    current_idx = level_options.index(combo.get())
                except ValueError:
                    pass
                if current_idx < len(level_options) - 1:
                    combo.set(level_options[current_idx + 1])
                    combo.selection_range(0, tk.END)

        combo.bind("<<ComboboxSelected>>", on_select)
        combo.bind("<Key>", on_key)

        combo.focus_set()
        combo.after(100, lambda: combo.event_generate('<Down>'))

    # ---------- 敌军标签页管理 ----------
    def add_tab(self):
        tab_num = self.next_tab_number
        name = self.t("fleet_tab", num=tab_num)
        self.next_tab_number += 1
        tab_data = BossTabData(name, self, tab_num)
        tab_data.build_ui(self.notebook, self.boss_skills_data, self.add_boss_effect_row_to_tab)
        self.notebook.add(tab_data.frame, text=name)
        tab_data.frame.trans_key = "fleet_tab"
        tab_data.frame.trans_params = {"num": tab_num}
        self.tab_data_list.append(tab_data)
        self.notebook.select(tab_data.frame)
        self.resize_tabs()

    def remove_tab(self, tab_data):
        if len(self.tab_data_list) <= 1:
            messagebox.showwarning(self.t("info"), self.t("warn_keep_one_tab"))
            return
        idx = self.tab_data_list.index(tab_data)
        self.notebook.forget(tab_data.frame)
        self.tab_data_list.remove(tab_data)
        self.resize_tabs()

    def resize_tabs(self):
        if not self.tab_data_list:
            return
        self.root.update_idletasks()
        nb_width = self.notebook.winfo_width()
        if nb_width < 50:
            self.root.after(50, self.resize_tabs)
            return
        font_obj = font.Font(family="TkDefaultFont")
        tab_text_widths = [font_obj.measure(td.name) + 25 for td in self.tab_data_list]
        total_needed = sum(tab_text_widths)
        style = ttk.Style()
        if total_needed > nb_width - 5:
            per_tab = max(30, int((nb_width - 5) / len(self.tab_data_list)))
            style.configure("Boss.TNotebook.Tab", width=per_tab)
        else:
            style.configure("Boss.TNotebook.Tab", width=0)

    def on_tab_double_click(self, event):
        try:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
            if index >= 0:
                old_name = self.tab_data_list[index].name
                new_name = simpledialog.askstring(self.t("tip_rename"), self.t("tip_enter_name"),
                                                  initialvalue=old_name)
                if new_name:
                    self.tab_data_list[index].name = new_name
                    self.notebook.tab(index, text=new_name)
                    self.resize_tabs()
        except:
            pass

    def add_boss_effect_row_to_tab(self, tab_data):
        t = self.t
        row_frame = ttk.Frame(tab_data.boss_effects_container)
        row_frame.pack(fill=tk.X, pady=2)

        var = tk.StringVar()
        options = [""] + [t(skill["trans_key"]) for skill in self.boss_skills_data]
        combo = ttk.Combobox(row_frame, textvariable=var, values=options, state="readonly", width=30)
        combo.pack(side=tk.LEFT, padx=5)

        pos_var = tk.StringVar(value="1")
        pos_combo = ttk.Combobox(row_frame, textvariable=pos_var, values=POS_VALUES, state="readonly", width=3)
        pos_combo.pack_forget()

        role_var = tk.StringVar(value=t("role_fighter"))
        role_combo = ttk.Combobox(row_frame, textvariable=role_var,
                                  values=[t(r) for r in AIRCRAFT_TYPES], state="readonly", width=6)
        role_combo.pack_forget()

        type_var = tk.StringVar(value=t("type_attack"))
        type_combo = ttk.Combobox(row_frame, textvariable=type_var,
                                  values=[t(r) for r in OPS_VALUES], state="readonly", width=6)
        type_combo.pack_forget()

        value_var = tk.StringVar(value="-15%")
        value_combo = ttk.Combobox(row_frame, textvariable=value_var, values=PCT_VALUES, state="readonly", width=6)
        value_combo.pack_forget()

        # 三级下拉框：机种、属性、百分比
        role_scale_var = tk.StringVar(value=t(AIRCRAFT_TYPES[0]))
        role_scale_combo = ttk.Combobox(row_frame, textvariable=role_scale_var,
                                        values=[t(r) for r in AIRCRAFT_TYPES], state="readonly", width=6)
        role_scale_combo.pack_forget()

        role_attr_scale_var = tk.StringVar(value=t(ATTR_VALUES[0]))
        role_attr_scale_combo = ttk.Combobox(row_frame, textvariable=role_attr_scale_var,
                                             values=[t(a) for a in ATTR_VALUES], state="readonly", width=6)
        role_attr_scale_combo.pack_forget()

        role_percent_scale_var = tk.StringVar(value=PCT_VALUES[3])
        role_percent_scale_combo = ttk.Combobox(row_frame, textvariable=role_percent_scale_var,
                                                values=PCT_VALUES, state="readonly", width=6)
        role_percent_scale_combo.pack_forget()

        attr_all_var = tk.StringVar(value=t(ATTR_VALUES[0]))
        attr_all_combo = ttk.Combobox(row_frame, textvariable=attr_all_var,
                                      values=[t(a) for a in ATTR_VALUES], state="readonly", width=6)
        attr_all_combo.pack_forget()

        type_scale_var = tk.StringVar(value=t(OPS_VALUES[0]))
        type_scale_combo = ttk.Combobox(row_frame, textvariable=type_scale_var,
                                        values=[t(ty) for ty in OPS_VALUES], state="readonly", width=6)
        type_scale_combo.pack_forget()

        type_attr_scale_var = tk.StringVar(value=t(ATTR_VALUES[0]))
        type_attr_scale_combo = ttk.Combobox(row_frame, textvariable=type_attr_scale_var,
                                             values=[t(a) for a in ATTR_VALUES], state="readonly", width=6)
        type_attr_scale_combo.pack_forget()

        type_percent_scale_var = tk.StringVar(value=PCT_VALUES[3])
        type_percent_scale_combo = ttk.Combobox(row_frame, textvariable=type_percent_scale_var,
                                                values=PCT_VALUES, state="readonly", width=6)
        type_percent_scale_combo.pack_forget()

        pos_scale_var = tk.StringVar(value=POS_VALUES[0])
        pos_scale_combo = ttk.Combobox(row_frame, textvariable=pos_scale_var, values=POS_VALUES, state="readonly", width=3)
        pos_scale_combo.pack_forget()

        pos_attr_scale_var = tk.StringVar(value=t(ATTR_VALUES[0]))
        pos_attr_scale_combo = ttk.Combobox(row_frame, textvariable=pos_attr_scale_var,
                                            values=[t(a) for a in ATTR_VALUES], state="readonly", width=6)
        pos_attr_scale_combo.pack_forget()

        pos_pct_scale_var = tk.StringVar(value=PCT_VALUES[3])
        pos_pct_scale_combo = ttk.Combobox(row_frame, textvariable=pos_pct_scale_var,
                                           values=PCT_VALUES, state="readonly", width=6)
        pos_pct_scale_combo.pack_forget()

        # 删除按钮
        def remove_row():
            if len(tab_data.boss_effect_vars) <= 1:
                messagebox.showwarning(self.t("info"), self.t("warn_keep_one_skill"))
                return
            row_frame.destroy()
            # 从tab_data的boss_effect_vars列表中移除对应条目
            for i, item in enumerate(tab_data.boss_effect_vars):
                if item["row"] == row_frame:
                    del tab_data.boss_effect_vars[i]
                    break

        del_btn = ttk.Button(row_frame, text=t("delete"), command=remove_row, width=6)
        del_btn.trans_key = "delete"
        del_btn.pack(side=tk.RIGHT, padx=2)

        def on_select(event, v=var):
            selected_translated = v.get()
            skill = None
            for sk in self.boss_skills_data:
                if t(sk["trans_key"]) == selected_translated:
                    skill = sk
                    break
            pos_combo.pack_forget(); value_combo.pack_forget(); role_combo.pack_forget(); type_combo.pack_forget()
            role_scale_combo.pack_forget(); role_attr_scale_combo.pack_forget(); role_percent_scale_combo.pack_forget()
            type_scale_combo.pack_forget(); type_attr_scale_combo.pack_forget(); type_percent_scale_combo.pack_forget()
            pos_scale_combo.pack_forget(); pos_attr_scale_combo.pack_forget(); pos_pct_scale_combo.pack_forget()
            attr_all_combo.pack_forget()

            if skill:
                etype = skill["effect"]["type"]
                if etype in ("disable_position", "disable_skill_pos"):
                    pos_combo.pack(side=tk.LEFT, padx=5)
                elif etype == "ban_role":
                    role_combo.pack(side=tk.LEFT, padx=5)
                elif etype == "ban_type":
                    type_combo.pack(side=tk.LEFT, padx=5)
                elif etype == "scale_role_attr":
                    role_scale_combo.pack(side=tk.LEFT, padx=2)
                    role_attr_scale_combo.pack(side=tk.LEFT, padx=2)
                    role_percent_scale_combo.pack(side=tk.LEFT, padx=2)
                elif etype == "scale_type_attr":
                    type_scale_combo.pack(side=tk.LEFT, padx=2)
                    type_attr_scale_combo.pack(side=tk.LEFT, padx=2)
                    type_percent_scale_combo.pack(side=tk.LEFT, padx=2)
                elif etype == "scale_pos_attr":
                    pos_scale_combo.pack(side=tk.LEFT, padx=2)
                    pos_attr_scale_combo.pack(side=tk.LEFT, padx=2)
                    pos_pct_scale_combo.pack(side=tk.LEFT, padx=2)
                elif etype == "scale_all_attr":
                    attr_all_combo.pack(side=tk.LEFT, padx=2)
                    value_combo.pack(side=tk.LEFT, padx=2)
                elif etype == "set_pos_attr_zero":
                    pos_combo.pack(side=tk.LEFT, padx=2)
                    attr_all_combo.pack(side=tk.LEFT, padx=2)
            rows = tab_data.boss_effects_container.winfo_children()
            if rows and rows[-1] == row_frame and selected_translated:
                self.add_boss_effect_row_to_tab(tab_data)

        combo.bind("<<ComboboxSelected>>", on_select)

        tab_data.boss_effect_vars.append({
            "var": var, "combo": combo,
            "pos_var": pos_var, "pos_combo": pos_combo,
            "value_var": value_var, "value_combo": value_combo,
            "role_var": role_var, "role_combo": role_combo,
            "type_var": type_var, "type_combo": type_combo,
            "row": row_frame,
            "role_scale_var": role_scale_var, "role_scale_combo": role_scale_combo,
            "role_attr_scale_var": role_attr_scale_var, "role_attr_scale_combo": role_attr_scale_combo,
            "role_percent_scale_var": role_percent_scale_var, "role_percent_scale_combo": role_percent_scale_combo,
            "type_scale_var": type_scale_var, "type_scale_combo": type_scale_combo,
            "type_attr_scale_var": type_attr_scale_var, "type_attr_scale_combo": type_attr_scale_combo,
            "type_percent_scale_var": type_percent_scale_var, "type_percent_scale_combo": type_percent_scale_combo,
            "pos_scale_var": pos_scale_var, "pos_scale_combo": pos_scale_combo,
            "pos_attr_scale_var": pos_attr_scale_var, "pos_attr_scale_combo": pos_attr_scale_combo,
            "pos_pct_scale_var": pos_pct_scale_var, "pos_pct_scale_combo": pos_pct_scale_combo,
            "attr_all_var": attr_all_var, "attr_all_combo": attr_all_combo,
            # 新增内部键列表，用于准确获取值
            "type_keys": OPS_VALUES,           # ["type_attack", "type_defense", "type_support"]
            "role_keys": AIRCRAFT_TYPES,       # ["role_fighter", "role_bomber", "role_torpedo"]
            "attr_keys": ATTR_VALUES,          # ["attack", "defense"]
        })

    def get_active_boss_effects(self, tab_data):
        selected = []
        for item in tab_data.boss_effect_vars:
            translated_name = item["var"].get()
            if not translated_name:
                continue
            # 通过翻译文本找到技能对象（trans_key）
            skill = None
            for sk in self.boss_skills_data:
                if self.t(sk["trans_key"]) == translated_name:
                    skill = sk
                    break
            if not skill:
                continue
            effect = copy.deepcopy(skill["effect"])
            etype = effect["type"]

            if etype in ("disable_position", "disable_skill_pos"):
                effect["pos"] = int(item["pos_var"].get())
            elif etype == "ban_role":
                role_combo = item["role_combo"]
                idx = role_combo.current()
                if idx >= 0:
                    effect["value"] = item["role_keys"][idx]
                else:
                    continue   # 未选择有效项，跳过该效果
            elif etype == "ban_type":
                type_combo = item["type_combo"]
                idx = type_combo.current()
                if idx >= 0:
                    effect["value"] = item["type_keys"][idx]
                else:
                    continue
            elif etype == "scale_pos_attr":
                effect["pos"] = int(item["pos_scale_var"].get())
                #effect["attr"] = self._reverse_lookup(item["pos_attr_scale_var"].get())
                idx = item["pos_attr_scale_combo"].current()
                effect["attr"] = item["attr_keys"][idx] if idx >= 0 else "attack"
                pct_str = item["pos_pct_scale_var"].get().replace("%", "").replace("+", "")
                try: effect["scale"] = 1 + float(pct_str) / 100.0
                except: effect["scale"] = 1.0
            elif etype == "scale_all_attr":
                idx = item["attr_all_combo"].current()
                effect["attr"] = item["attr_keys"][idx] if idx >= 0 else "attack"
                pct_str = item["value_var"].get().replace("%", "").replace("+", "")
                try: effect["scale"] = 1 + float(pct_str) / 100.0
                except: effect["scale"] = 1.0
            elif etype == "scale_type_attr":
                idx_type = item["type_scale_combo"].current()
                effect["type_name"] = item["type_keys"][idx_type] if idx_type >= 0 else "type_attack"
                idx_attr = item["type_attr_scale_combo"].current()
                effect["attr"] = item["attr_keys"][idx_attr] if idx_attr >= 0 else "attack"
                pct_str = item["type_percent_scale_var"].get().replace("%", "").replace("+", "")
                try: effect["scale"] = 1 + float(pct_str) / 100.0
                except: effect["scale"] = 1.0
            elif etype == "scale_role_attr":
                idx_role = item["role_scale_combo"].current()
                effect["role"] = item["role_keys"][idx_role] if idx_role >= 0 else "role_fighter"
                idx_attr = item["role_attr_scale_combo"].current()
                effect["attr"] = item["attr_keys"][idx_attr] if idx_attr >= 0 else "attack"
                pct_str = item["role_percent_scale_var"].get().replace("%", "").replace("+", "")
                try: effect["scale"] = 1 + float(pct_str) / 100.0
                except: effect["scale"] = 1.0
            elif etype == "set_pos_attr_zero":
                effect["pos"] = int(item["pos_var"].get())
                idx = item["attr_all_combo"].current()
                if idx >= 0:
                    effect["attr"] = item["attr_keys"][idx]
                else:
                    continue
            selected.append({"name": skill["name"], "effect": effect})
        return selected

    def on_solve(self, tab_data):
        if self.solving:
            messagebox.showinfo(self.t("info"), self.t("info_calculating"))
            return
        try:
            boss_atk = int(tab_data.boss_attack_var.get())
            boss_def = int(tab_data.boss_defense_var.get())
        except ValueError:
            messagebox.showerror(self.t("warn_input_error"), self.t("warn_boss_stat_invalid"))
            return
        try:
            fleet_limit = int(tab_data.fleet_limit_var.get())
        except ValueError:
            messagebox.showerror(self.t("warn_input_error"), self.t("warn_squad_limit_invalid"))
            return

        try: atk_gain = int(self.attack_gain_var.get())
        except: atk_gain = 0
        try: def_gain = int(self.defense_gain_var.get())
        except: def_gain = 0
        try: battle_lv = int(self.battle_level_var.get())
        except: battle_lv = 1
        try: bomb_lv = int(self.bomb_level_var.get())
        except: bomb_lv = 1
        try: torpedo_lv = int(self.torpedo_level_var.get())
        except: torpedo_lv = 1

        hand_cards = []
        for idx, card in enumerate(self.cards_data):
            if not self.card_enable_vars[idx].get():
                continue
            card_copy = card.copy()
            level_str = self.card_level_vars[idx].get().replace("%", "")
            try: skill_value = int(level_str)
            except: skill_value = card.get("skill_levels", [100])[0]
            card_copy["skill_value"] = skill_value
            card_copy["attack"] = card["attack"] + atk_gain
            card_copy["defense"] = card["defense"] + def_gain
            # 应用机种等级加成（使用原始中文比较）
            role = card["role"]
            if role == "role_fighter":
                if battle_lv >= 2: card_copy["defense"] += 1
                if battle_lv >= 3: card_copy["attack"] += 1
            elif role == "role_bomber":
                if bomb_lv >= 2: card_copy["defense"] += 1
                if bomb_lv >= 3: card_copy["attack"] += 1
            elif role == "role_torpedo":
                if torpedo_lv >= 2: card_copy["defense"] += 1
                if torpedo_lv >= 3: card_copy["attack"] += 1
            hand_cards.append(card_copy)

        if not hand_cards:
            messagebox.showwarning(self.t("warn_no_cards"), self.t("warn_no_enabled_cards"))
            return

        boss_effects = self.get_active_boss_effects(tab_data)
        disabled_positions = set()
        for eff in boss_effects:
            if eff["effect"]["type"] == "disable_position":
                disabled_positions.add(eff["effect"]["pos"] - 1)

        independent_mode = tab_data.independent_var.get()
        self._pending_boss_effects = boss_effects
        self._pending_tab_data = tab_data

        tab_data.solution_info_label.config(text=self.t("animated_calculating", char=" \\"))
        self.solving = True
        self.solve_result = None

        def solve_task():
            result = solve(hand_cards, boss_atk, boss_def, boss_effects,
                           fleet_limit, disabled_positions, independent_mode)
            self.solve_result = result

        self.solve_thread = threading.Thread(target=solve_task, daemon=True)
        self.solve_thread.start()
        self._animate_progress()

    def _animate_progress(self):
        if not self.solving:
            if self.after_id: self.root.after_cancel(self.after_id)
            return
        char = self.progress_chars[self.progress_index % 3]
        self.progress_index += 1
        tab_data = self._pending_tab_data
        tab_data.solution_info_label.config(text=self.t("animated_calculating", char=char))

        if self.solve_result is not None:
            self.solving = False
            result = self.solve_result
            if result is None:
                messagebox.showwarning(self.t("warn_unable_solve"), self.t("warn_no_valid_combo"))
                tab_data.solution_info_label.config(text="")
                return
            result_perm, stats = result
            if result_perm is None:
                _, _, desc, _ = stats
                messagebox.showwarning(self.t("warn_unable_solve"), self.t(desc))
                tab_data.solution_info_label.config(text="")
                return
            final_def, final_atk, desc, kwargs = stats
            if DEBUG:
                print_debug_info(result_perm, self._pending_boss_effects)
            _, _, atk_list, def_list = compute_per_card_stats(result_perm, self._pending_boss_effects)

            # 保存结果时使用 trans_key
            saved_perm = []
            for card in result_perm:
                saved_perm.append(card.copy())   # 保留原始数据，其中应包含 trans_key
            tab_data.last_result = (saved_perm, final_def, final_atk, desc, kwargs, atk_list, def_list)

            for i in range(5):
                if i < len(result_perm):
                    card = result_perm[i]
                    name = self.t(card["trans_key"]) if card["trans_key"] else card["name"]
                    lbl = self.t("info_combo_result", pos=i+1, name=name, atk=atk_list[i], defs=def_list[i])
                else:
                    lbl = self.t("info_combo_empty", pos=i+1)
                tab_data.result_labels[i].config(text=lbl)

            strategy_text = self.t(desc, **kwargs)
            tab_data.solution_info_label.config(
                text=self.t("info_combo_summery", final_def=final_def, final_atk=final_atk, desc=strategy_text))
            return
        self.after_id = self.root.after(200, self._animate_progress)

    def load_card_state(self):
        """从 STATE_FILE 加载卡牌的启用状态和等级选择"""
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved_states = json.load(f)
            # 建立卡牌名称到索引的映射
            name_to_idx = {card["name"]: idx for idx, card in enumerate(self.cards_data)}
            for item in saved_states:
                name = item.get("name")
                if name and name in name_to_idx:
                    idx = name_to_idx[name]
                    # 恢复启用状态
                    self.card_enable_vars[idx].set(item.get("enabled", True))
                    # 恢复等级（如果该等级在选项中存在，否则保留默认值）
                    level = item.get("level", self.card_level_vars[idx].get())
                    self.card_level_vars[idx].set(level)
        except Exception as e:
            print(f"加载卡牌状态失败: {e}")

    def save_card_state(self):
        """保存所有卡牌的启用状态和等级到 STATE_FILE"""
        states = []
        for idx, card in enumerate(self.cards_data):
            states.append({
                "name": card["name"],
                "enabled": self.card_enable_vars[idx].get(),
                "level": self.card_level_vars[idx].get()
            })
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存卡牌状态失败: {e}")

    # 注意在 on_closing 中添加语言偏好保存：
    def on_closing(self):
        self.save_card_state()
        try:
            with open(self.lang_pref_file, "w", encoding="utf-8") as f:
                json.dump({"lang": self.current_lang}, f)
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    freeze_support()
    root = tk.Tk()
    app = CardGameApp(root)
    root.mainloop()