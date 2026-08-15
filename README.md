# 《航母生存》空袭解算器

基于 Python/Tkinter 的卡牌布局求解工具，用于《航母生存》游戏中的空袭编队优化。支持中/英界面、多套敌军属性配置，利用算法从卡池中搜索满足不受损、击败敌军等条件的最优卡牌排列。

本程序由蓝色大肥鱼编写。

## 功能特点

- **卡牌管理**：内置 18 张默认卡牌，可独立启用/禁用，并调整技能等级。
- **敌军技能**：支持禁用牌位、指定位置技能失效、攻防降低、置零、禁止卡牌种类/机种等 9 种敌军效果。
- **多语言**：内置中/英文界面，可通过菜单切换。
- **多页签**：可创建多个敌军配置页签，独立计算。
- **牌组求解**：搜索卡池中最优组合，支持机队数量限制和使用独立号单独攻击模式。
- **结果展示**：输出每个牌位的最终攻防值及策略说明。
- **配置持久化**：卡牌状态自动保存，启动时恢复。

## 使用说明

### 运行可执行程序
将发行版本的压缩包解压至可写目录，执行exe程序运行即可。

### 源码运行（可选）

1. 克隆或下载本仓库。
2. 进入项目目录，执行：
   ```bash
   python main.py
   ```
3. 首次运行会自动生成 `cards.json`、`boss_skills.json`、`lang_zh.json`、`lang_en.json` 等配置文件，请确保程序所在目录可写。

### 操作步骤

1. **配置卡池**：在上方卡牌列表中勾选/取消卡牌，点击“技能等级”列可调整等级。
2. **设置敌军属性**：在下方敌军页签中输入敌军攻击、防御值，选择机队上限及是否使用独立号攻击（独立号攻击模式将使用3张卡牌堆叠最大攻击值）。
3. **添加敌军技能**：从下拉框选择技能，并设置对应参数（如位置、属性、百分比等）。
4. **求解**：点击“求解最优排列”，等待计算完成，下方显示推荐排列及各牌位最终攻防值。

### 多语言切换

点击菜单栏 `Language`，选择 `中文` 或 `English`。

## 编译
### 环境要求

- Python 3.8 或更高版本
- 标准库 `tkinter`, `multiprocessing`（无需额外第三方依赖）

### 源码运行

1. 克隆或下载本仓库。
2. 进入项目目录，执行：
   ```bash
   python main.py
   ```
3. 首次运行会自动生成 `cards.json`、`boss_skills.json`、`lang_zh.json`、`lang_en.json` 等配置文件，请确保程序所在目录可写。

### 打包
项目使用 PyInstaller 进行打包，已提供 `ACSCardCalc.spec` 配置。

1. **安装打包依赖**：
   ```bash
   pip install -r requirements-dev.txt
   ```
   或手动安装：
   ```bash
   pip install pyinstaller
   ```

2. **执行打包**：
   ```bash
   pyinstaller ACSCardCalc.spec
   ```

3. **输出位置**：
   打包结果位于 `dist/ACSCardCalc/` 文件夹，包含 `ACSCardCalc.exe` 及运行所需的 `_internal` 目录。请将整个文件夹分发给用户。

> 注意：打包使用 `--onedir` 模式（生成文件夹），确保多进程功能正常。程序会在 exe 同级目录自动生成配置文件，请勿将程序放置在只读目录（如 `C:\Program Files`）下。

## 配置与数据文件

程序首次运行时会自动创建以下文件：

- `cards.json`：卡牌数据
- `boss_skills.json`：敌军技能定义
- `lang_zh.json` / `lang_en.json`：多语言文本
- `card_state.json`：用户卡牌状态（启用、等级）
- `lang_pref.json`：语言偏好

## 常见问题

**Q：计算结果显示“无可用组合”怎么办？**  
A：检查是否有卡牌被禁用、敌军技能是否过度限制，或尝试调整机队上限。

**Q：打包后 exe 闪退？**  
A：将程序文件夹移动到可写目录，或右键以管理员身份运行。

## 许可证

MIT License

====================================================

# Aircraft Carrier: Survival Attack Planner

A Python/Tkinter-based card layout solver for optimizing air raid formations in the game *Aircraft Carrier: Survival*. It supports both Chinese and English interfaces, multiple enemy attribute configurations, and uses algorithms to search the card pool for optimal arrangements that satisfy conditions such as taking no damage and defeating the enemy.

This program is wrote by DeepSeek.

## Features

- **Card Management**: Includes 18 default cards that can be individually enabled/disabled, with adjustable skill levels.
- **Enemy Skills**: Supports 9 enemy effects: disabling slots, disabling skills at specific positions, reducing attack/defense, zeroing stats, banning card types, and banning aircraft types.
- **Multilingual**: Built-in Chinese and English interfaces, switchable via the menu.
- **Multiple Tabs**: Create multiple enemy configuration tabs for independent calculations.
- **Deck Solving**: Searches the card pool for the optimal combination, supports squadron size limits, and an independent-attack mode for USS Independence.
- **Result Display**: Shows final attack/defense values for each slot and a strategy description.
- **Persistent Configuration**: Card states are saved automatically and restored on startup.

## Usage

### Running Executable
Extract the distribution archive to a writable directory and run the executable.

### Running from Source (Optional)

1. Clone or download the repository.
2. Navigate to the project directory and run:
   ```bash
   python main.py
   ```
3. On first run, configuration files such as `cards.json`, `boss_skills.json`, `lang_zh.json`, and `lang_en.json` will be generated automatically. Ensure the program directory is writable.

### Operation Steps

1. **Configure Card Pool**: Check/uncheck cards in the card list at the top. Click the "Skill Level" column to adjust levels.
2. **Set Enemy Attributes**: In the enemy tab below, enter enemy attack and defense values, select the fleet limit, and choose whether to use USS Independence attack (this mode uses 3 cards to maximize ATK).
3. **Add Enemy Skills**: Select a skill from the dropdown and set corresponding parameters (position, attribute, percentage, etc.).
4. **Solve**: Click "Solve", wait for the calculation to finish, and the recommended layout along with final ATK / DEF values for each slot will be displayed below.

### Switching Languages

Click the `Language` menu and select `中文` or `English`.

## Building

### Requirements

- Python 3.8 or higher
- Standard libraries `tkinter`, `multiprocessing` (no third-party dependencies required)

### Running from Source

1. Clone or download the repository.
2. Navigate to the project directory and run:
   ```bash
   python main.py
   ```
3. On first run, configuration files such as `cards.json`, `boss_skills.json`, `lang_zh.json`, and `lang_en.json` will be generated automatically. Ensure the program directory is writable.

### Packaging

The project uses PyInstaller for packaging, and an `ACSCardCalc.spec` configuration is provided.

1. **Install packaging dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```
   or manually:
   ```bash
   pip install pyinstaller
   ```

2. **Run packaging**:
   ```bash
   pyinstaller ACSCardCalc.spec
   ```

3. **Output location**:
   The packaged result is in the `dist/ACSCardCalc/` folder, containing `ACSCardCalc.exe` and the required `_internal` directory. Distribute the entire folder to users.

> Note: Packaging uses `--onedir` mode (generates a folder) to ensure multiprocessing works properly. The program will automatically generate configuration files in the same directory as the executable. Do not place the program in a read-only directory (such as `C:\Program Files`).

## Configuration and Data Files

The following files are automatically created on first run:

- `cards.json`: Card data
- `boss_skills.json`: Enemy skill definitions
- `lang_zh.json` / `lang_en.json`: Multilingual texts
- `card_state.json`: User card state (enabled, level)
- `lang_pref.json`: Language preference

## FAQ

**Q: The result shows "No valid combinations". What should I do?**  
A: Check whether any cards are disabled, whether enemy skills are too restrictive, or try adjusting the fleet limit.

**Q: The packaged exe crashes on startup.**  
A: Move the program folder to a writable directory, or right-click and run as administrator.

## License

MIT License