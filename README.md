# Program Debugging and Automated Repair

[!INFO]
本项目面向天津大学 2026 级创新实践启蒙课程，介绍程序调试（Debugging）与自动程序修复（Automated Program Repair, APR）的基本方法。

仓库包含若干简单C++ 缺陷程序及其修复版本，并提供测试、语法树分析和自动修复的实验脚本。通过这些示例，可以了解程序缺陷的复现与验证过程，以及搜索式、模板式、约束式和大语言模型修复方法的基本流程。

## 1. 实验案例

目前包含 5 个案例，涉及比较运算、空指针解引用和数组越界等问题。

| 案例 | 缺陷描述 | 来源 |
|---|---|---|
| `median` | 计算中位数时错误地使用了第二个数 | IntroClass |
| `scheme` | 将相邻元素相等的情况错误判定为递减 | AtCoder ABC308 A |
| `npd` | 查询失败后解引用空指针 | 自建案例 |
| `oob` | 数组下标越界访问 | 自建案例 |
| `cutoff` | 比较运算符错误，未正确处理 60 分的边界情况 | 自建案例 |

每个案例均提供缺陷版本（`.cpp`）、修复版本（`.fixed.cpp`）及对应测试。源文件开头包含题目说明，可直接阅读代码或运行测试。

其中，`median` 来自 IntroClass，许可信息保存在 `cases/median/INTROCLASS-LICENSE.txt`；`scheme` 的许可信息见 `cases/scheme/CONDEFECTS-LICENSE.txt`。

## 2. 环境配置

需要以下环境：

- Python 3.10 及以上
- 支持 C++17 的 Clang 或 GCC。脚本依次查找 `clang++`、`g++`、`clang`，也可以用环境变量 `APR_CXX` 指定编译器

### macOS

安装 Xcode 命令行工具，即可得到 `clang++`：

```bash
xcode-select --install
```

也可以用 Homebrew 安装 Python 和编译器：

```bash
brew install python llvm
```

Homebrew 的 `clang++` 不在默认 PATH 里。当前终端要用它时执行：

```bash
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

若改用 Homebrew 的 GCC，包里的命令名带版本号，例如 `g++-15`。先用 `brew list gcc` 确认名字，再执行 `export APR_CXX=g++-15`。已经装过命令行工具的话，直接用系统的 `clang++` 即可。

### Linux

Debian、Ubuntu：

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip g++
```

Fedora：

```bash
sudo dnf install python3 python3-pip gcc-c++
```

Arch Linux：

```bash
sudo pacman -S python gcc
```

要装 Clang 时，把上面的 `g++`、`gcc-c++` 或 `gcc` 换成该发行版的 `clang` 包。

### Windows

从 [python.org](https://www.python.org/downloads/) 安装 Python 3.10 及以上，安装时勾选 **Add python.exe to PATH**。

测试编译用了 `-fsanitize=undefined`，请安装 LLVM 以获得 `clang++`。Visual Studio 自带的 `cl` 不能用来跑这些测试。

```powershell
winget install Python.Python.3.12
winget install LLVM.LLVM
```

装完后新开一个终端。若仍找不到 `clang++`，把 `C:\Program Files\LLVM\bin` 加入 PATH。

后面的命令写的是 `python3`。Windows 上如果只有 `py`，把 `python3` 换成 `py -3`。虚拟环境在 PowerShell 里这样建：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

也可以先安装 [WSL](https://learn.microsoft.com/windows/wsl/install)，再按上一节的 Linux 步骤安装。装好之后，下面的 bash 命令可以直接用。

### Python 依赖

macOS 和 Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

仅运行案例测试（`python3 -m cases`）无需安装额外 Python 依赖；使用 `lab.py` 中的语法树分析、补丁生成和自动修复功能，需要先安装上述依赖。

测试程序采用 C++17 编译，并启用 `-fsanitize=undefined`。编译和执行均在临时目录中完成，不会修改原始案例文件。

## 3. 运行测试

以 `cutoff` 为例，程序读入一个分数，60 分及以上输出 pass，否则输出 fail。原始版本写成了 `score > 60`，正好 60 分会输出 fail。

首先查看案例：

```bash
python3 -m cases list
python3 -m cases info cutoff
```

运行缺陷版本及修复版本：

```bash
# 缺陷版本：前 4 条通过，60 分失败
python3 -m cases test cutoff cases/cutoff/cutoff.cpp

# 修复版本：5 条测试全部通过
python3 -m cases test cutoff cases/cutoff/cutoff.fixed.cpp
```

也可以测试自行修改的代码：

```bash
python3 -m cases test cutoff my_cutoff.cpp
```

使用 `--few` 仅运行指定的少量测试：

```bash
python3 -m cases test cutoff --few my_cutoff.cpp
```

对于 `cutoff`，这组测试不包含触发缺陷的 60 分输入。可以利用这一设置观察不同测试集对补丁验证结果的影响。

测试命令退出码为 0 表示全部测试通过。

## 4. 自动程序修复实验

`lab.py` 提供不同 APR 方法的简化实现，用于演示候选补丁的生成、筛选和验证过程。

| 方法 | 命令 | 实验内容 |
|---|---|---|
| AST 分析 | `python3 lab.py ast cutoff` | 解析程序语法树并生成可视化文件 |
| 搜索式修复 | `python3 lab.py search cutoff` | 修改比较运算符、局部变量或已有语句，逐一验证候选补丁 |
| 模板式修复 | `python3 lab.py template npd` | 应用空指针检查、条件分支和关系运算符等修复模板 |
| 约束式修复 | `python3 lab.py synth cutoff` | 构造待填充的代码位置，根据候选表达式及测试结果生成补丁 |
| LLM 修复 | `python3 lab.py prompt cutoff` | 生成包含缺陷代码和测试信息的修复提示词 |
| LLM 修复 | `python3 lab.py llm cutoff` | 调用 DeepSeek 生成修复补丁 |

上述方法使用同一套案例和测试接口，但采用不同的候选补丁生成策略。

这些脚本是用于教学的简化实现，并非 GenProg、TBar、SemFix 等研究工具的完整复现。相关方法及原始工具介绍见 [METHODS.md](METHODS.md)。

### 测试与日志

实验支持的案例包括 `median`、`scheme`、`npd`、`oob` 和 `cutoff`，但不同方法的修复能力有所区别。

例如，当前搜索策略主要复用程序中已有的运算符、变量和语句，因此对于需要引入新字符串或新分支的缺陷，不一定能够生成正确补丁。

实验日志保存至 `logs/`，文件命名格式为：

```text
logs/<method>-<case>.log
```

例如 `logs/search-cutoff.log`。

AST 分析生成 `.dot` 文件；如果本地安装了 Graphviz，还会生成相应的 `.svg` 可视化结果。

### 使用大语言模型

`prompt` 命令仅生成修复提示词，不会发送 API 请求。生成的提示词可以用于 Copilot、Cursor、TRAE 等编程工具。

`llm` 命令默认使用 DeepSeek API，需要提前设置环境变量：

```bash
export DEEPSEEK_API_KEY="your-api-key"
python3 lab.py llm cutoff
```

未配置 API Key 时不会发起模型请求。

其他编程助手的使用方式见 [TOOLS.md](TOOLS.md)。

## 5. 其他案例

各案例使用相同的测试接口。

```bash
# Median
python3 -m cases test median cases/median/median.cpp
python3 -m cases test median cases/median/median.fixed.cpp

# Scheme
python3 -m cases test scheme cases/scheme/abc308a.cpp
python3 -m cases test scheme cases/scheme/abc308a.fixed.cpp

# Null Pointer Dereference
python3 -m cases test npd cases/npd/npd.cpp
python3 -m cases test npd cases/npd/npd.fixed.cpp

# Out-of-Bounds
python3 -m cases test oob cases/oob/oob.cpp
python3 -m cases test oob cases/oob/oob.fixed.cpp
```

`scheme`、`npd` 和 `oob` 也可以使用 `--few` 参数运行部分测试，对比不同测试范围下的结果。

## 6. 实践任务

对提供的5个案例，阅读题目和缺陷代码，完成以下操作：

1. 缺陷复现：运行原始程序的测试用例，观察失败结果，分析缺陷产生的原因。

2. 自动修复：尝试使用不同类型的 APR 方法修复各个缺陷，记录生成的候选补丁及其测试结果。

3. 补丁分析：对比生成的补丁与参考修复代码，分析其语义是否正确，能否满足题目要求。

4. 方法比较：结合实验结果，比较不同 APR 方法在修复能力、适用场景及局限性等方面的差异。

[!IMPORTANT]
通过测试不等于正确修复。 除了检查现有测试结果，还应结合题目要求分析补丁的正确性，必要时补充边界测试。

建议记录每个案例所使用的修复方法、生成的补丁、测试结果及失败原因，作为最终实验分析的依据。

运行仓库自检：

```bash
python3 lab.py selftest
```

## 7. 项目结构

```text
apr-course/
├── lab.py                 # APR 实验入口
├── requirements.txt       # Python 依赖
├── cases/                 # 缺陷案例、修复版本及测试
├── methods/               # 不同 APR 方法的实现
├── utils/                 # AST、测试与日志等公共功能
├── tests/                 # 项目自检
├── logs/                  # 实验日志
├── slides/
│   └── apr-intro.pptx     # 课程介绍
├── METHODS.md             # APR 方法及研究工具
└── TOOLS.md               # 编程助手使用说明
```

