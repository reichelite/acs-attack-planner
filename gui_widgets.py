import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner_frame = ttk.Frame(self.canvas)

        self.window_id = self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack_forget()  # 初始隐藏

        self.inner_frame.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 鼠标滚轮支持
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._toggle_scrollbar()

    def _on_canvas_configure(self, event):
        # 使内部框架宽度与画布一致，避免水平滚动条
        self.canvas.itemconfig(self.window_id, width=event.width)
        self._toggle_scrollbar()

    def _toggle_scrollbar(self):
        inner_height = self.inner_frame.winfo_reqheight()
        canvas_height = self.canvas.winfo_height()
        if inner_height > canvas_height:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.scrollbar.pack_forget()

# -------------------- BossTabData 与 GUI --------------------
class BossTabData:
    # __init__ 增加 trans 引用
    def __init__(self, name, app, tab_num):
        self.name = name
        self.app = app
        self.tab_num = tab_num
        self.boss_attack_var = tk.StringVar(value="0")
        self.boss_defense_var = tk.StringVar(value="0")
        self.fleet_limit_var = tk.StringVar(value="6")
        self.independent_var = tk.BooleanVar(value=False)
        self.boss_effect_vars = []
        self.result_labels = []
        self.solution_info_label = None
        self.frame = None
        self.boss_effects_container = None
        self.bottom_frame = None
        self.last_result = None  # (perm, final_def, final_atk, desc_key, kwargs, atk_list, def_list)

    def build_ui(self, parent, boss_skills_data, add_boss_effect_row_callback):
        t = self.app.t
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 排列结果区域（固定在底部）
        bottom_frame = ttk.LabelFrame(self.frame, text=t("result"), padding=10)
        bottom_frame.trans_key = "result"
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.bottom_frame = bottom_frame

        # 机队数量上限
        fleet_frame = ttk.Frame(bottom_frame)
        fleet_frame.pack(fill=tk.X, pady=5)
        lbl_squad = ttk.Label(fleet_frame, text=t("squad_limit"))
        lbl_squad.trans_key = "squad_limit"
        lbl_squad.pack(side=tk.LEFT)
        ttk.Combobox(fleet_frame, textvariable=self.fleet_limit_var,
                     values=["6", "7", "8"], state="readonly", width=6).pack(side=tk.LEFT, padx=5)

        # 独立号攻击复选框
        self.independent_var = tk.BooleanVar(value=False)
        cb_cvl = ttk.Checkbutton(fleet_frame, text=t("cvl_attack"), variable=self.independent_var)
        cb_cvl.trans_key = "cvl_attack"
        cb_cvl.pack(side=tk.RIGHT, padx=20)

        # 结果标签（5个空位，初始显示默认占位文本）
        self.result_labels = []
        for i in range(5):
            lbl = ttk.Label(bottom_frame, text=t("slot_empty", pos=i+1),
                            relief=tk.SUNKEN, width=40, anchor=tk.W)
            lbl.trans_key = "slot_empty"
            lbl.trans_params = {"pos": i+1}
            lbl.pack(pady=2)
            self.result_labels.append(lbl)

        # 信息标签（初始为空）
        self.solution_info_label = ttk.Label(bottom_frame, text="", foreground="blue")
        self.solution_info_label.pack(pady=5)

        # 求解按钮
        solve_btn = ttk.Button(bottom_frame, text=t("solve_btn"),
                               command=lambda: self.app.on_solve(self))
        solve_btn.trans_key = "solve_btn"
        solve_btn.pack(pady=10)

        # 可滚动的 敌军 属性区域（填充剩余空间）
        scroll_frame = ScrollableFrame(self.frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # 敌军属性区域
        boss_frame = ttk.LabelFrame(scroll_frame.inner_frame, text=t("boss_attr"), padding=10)
        boss_frame.trans_key = "boss_attr"
        boss_frame.pack(fill=tk.BOTH, expand=False)

        # 敌军攻击/防御输入行
        boss_top = ttk.Frame(boss_frame)
        boss_top.pack(fill=tk.X)

        lbl_atk = ttk.Label(boss_top, text=t("boss_atk"))
        lbl_atk.trans_key = "boss_atk"
        lbl_atk.pack(side=tk.LEFT)
        ttk.Entry(boss_top, textvariable=self.boss_attack_var, width=8).pack(side=tk.LEFT, padx=5)

        lbl_def = ttk.Label(boss_top, text=t("boss_def"))
        lbl_def.trans_key = "boss_def"
        lbl_def.pack(side=tk.LEFT, padx=(20,0))
        ttk.Entry(boss_top, textvariable=self.boss_defense_var, width=8).pack(side=tk.LEFT, padx=5)

        # 关闭按钮（放在同一行右侧）
        close_btn = tk.Button(boss_top, text=t("close_btn"), font=("TkDefaultFont", 10),
                              relief="flat", bd=0, padx=5, pady=0,
                              command=lambda: self.app.remove_tab(self))
        close_btn.trans_key = "close_btn"
        close_btn.pack(side=tk.RIGHT)

        # 敌军技能特性标签
        lbl_skills = ttk.Label(boss_frame, text=t("boss_skills"))
        lbl_skills.trans_key = "boss_skills"
        lbl_skills.pack(anchor=tk.W, pady=(10,0))

        # 敌军效果容器（动态内容）
        self.boss_effects_container = ttk.Frame(boss_frame)
        self.boss_effects_container.pack(fill=tk.X, pady=5)

        # 添加第一行效果选择
        add_boss_effect_row_callback(self)

