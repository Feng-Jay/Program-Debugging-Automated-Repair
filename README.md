# Program Debugging and Automated Repair

> [!NOTE]
> 天津大学 2026 级创新实践启蒙项目，介绍程序调试（Debugging）与自动程序修复（Automated Program Repair, APR）的基本方法。

仓库包含 5 个 C++ 缺陷案例及其修复版本，提供测试、语法树分析和自动修复的实验脚本，涵盖搜索式、模板式、约束式和大语言模型修复方法。

**导航：** [快速开始](#快速开始) · [实验案例](#实验案例) · [自动修复实验](#自动修复实验) · [实践任务](#实践任务) · [环境配置](#环境配置) · [项目结构](#项目结构)

## 快速开始

完成[环境配置](#环境配置)后，可以直接运行：

```bash
# 查看案例
python3 -m cases list

# 复现缺陷
python3 -m cases test cutoff cases/cutoff/cutoff.cpp

# 验证修复版本
python3 -m cases test cutoff cases/cutoff/cutoff.fixed.cpp

# 尝试搜索式修复
python3 lab.py search cutoff
```

以 `cutoff` 为例，程序应当在成绩达到 60 分时输出 `pass`，但缺陷版本使用了 `score > 60`，因此无法正确处理 60 分的边界情况。

## 实验案例

| 案例       | 缺陷描述               | 来源               |
| -------- | ------------------ | ---------------- |
| `median` | 计算中位数时错误地使用第二个数    | IntroClass       |
| `scheme` | 将相邻元素相等误判为递减       | AtCoder ABC308 A |
| `npd`    | 查询失败后解引用空指针        | 自建案例             |
| `oob`    | 数组下标越界访问           | 自建案例             |
| `cutoff` | 比较运算符错误，未正确处理 60 分 | 自建案例             |

每个案例均包含缺陷版本（`.cpp`）、修复版本（`.fixed.cpp`）及对应测试。

`median` 和 `scheme` 的许可信息分别见 `cases/median/INTROCLASS-LICENSE.txt` 和 `cases/scheme/CONDEFECTS-LICENSE.txt`。

<details> <summary>查看其他案例的测试命令</summary>

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

也可以测试自行修改的代码：

```bash
python3 -m cases test cutoff my_cutoff.cpp
```

使用 `--few` 只执行部分测试：

```bash
python3 -m cases test cutoff --few my_cutoff.cpp
```

对于 `cutoff`，该测试集不包含触发缺陷的 60 分输入。`scheme`、`npd` 和 `oob` 同样支持 `--few` 参数。

</details>

## 自动修复实验

`lab.py` 提供几种 APR 方法的简化实现。各方法采用不同的候选补丁生成策略，并通过编译和测试进行验证。

| 方法     | 运行命令                           | 主要功能             |
| ------ | ------------------------------ | ---------------- |
| AST 分析 | `python3 lab.py ast cutoff`    | 解析并可视化语法树        |
| 搜索式修复  | `python3 lab.py search cutoff` | 枚举代码修改并测试候选补丁    |
| 模板式修复  | `python3 lab.py template npd`  | 应用预定义修复模板        |
| 约束式修复  | `python3 lab.py synth cutoff`  | 根据代码约束和测试结果生成补丁  |
| LLM 修复 | `python3 lab.py prompt cutoff` | 生成修复提示词          |
| LLM 修复 | `python3 lab.py llm cutoff`    | 调用 DeepSeek 生成补丁 |

> [!NOTE]
> 这些脚本是教学用途的简化实现，并非 GenProg、TBar、SemFix 等工具的完整复现。方法原理及研究工具见 [METHODS.md](METHODS.md)。

<details> <summary>运行说明、日志与可视化</summary>

- **案例范围**：支持 `median`、`scheme`、`npd`、`oob` 和 `cutoff`，但不同方法不一定能成功修复所有缺陷。
- **搜索空间**：当前搜索策略主要复用程序中已有的运算符、变量和语句，对需要新增分支或字符串的缺陷可能无法生成正确补丁。
- **实验日志**：保存于 `logs/<method>-<case>.log`，例如 `logs/search-cutoff.log`。
- **AST 可视化**：生成 `.dot` 文件；安装 Graphviz 后可额外生成 `.svg` 文件。
- **源码保护**：编译和测试均在临时目录中完成，不修改 `cases/` 下的原始文件。

</details>

<details> <summary>使用 DeepSeek 或其他编程助手</summary>

`prompt` 命令只生成修复提示词，不发送 API 请求，可将结果用于 Copilot、Cursor、TRAE 等工具。

`llm` 命令默认调用 DeepSeek API，需要先配置密钥：

```bash
export DEEPSEEK_API_KEY="your-api-key"
python3 lab.py llm cutoff
```

没有配置 API Key 时不会发起模型请求。

其他编程助手的使用说明见 [TOOLS.md](TOOLS.md)。

</details>

## 实践任务

针对提供的 5 个缺陷案例，阅读题目描述及缺陷代码，完成以下任务：

- [ ] **缺陷复现**：运行测试用例，观察失败结果并分析缺陷原因。
- [ ] **自动修复**：尝试使用不同类型的 APR 方法，记录生成的候选补丁和测试结果。
- [ ] **补丁分析**：对比生成的补丁与参考修复，检查其是否满足预期语义。
- [ ] **方法比较**：分析不同 APR 方法的修复能力、适用场景及局限性。

> [!IMPORTANT]
> 测试通过不代表补丁一定正确。除了现有测试，还应结合题目要求检查程序语义，必要时补充边界测试。

建议记录各案例的修复方法、补丁、测试结果和失败原因，作为实验分析的依据。

运行仓库自检：

```bash
python3 lab.py selftest
```

## 环境配置

本项目需要：

- **Python 3.10+**
- **支持 C++17 的编译器**：Clang (`clang++`) 或 GCC (`g++`)，任选其一

脚本会优先使用 `clang++`，其次使用 `g++`。也可以通过环境变量 `APR_CXX` 指定编译器。

<details>
<summary>macOS</summary>

推荐安装 Xcode Command Line Tools，其中包含 `clang++`：

```bash
xcode-select --install
```

如果需要安装 Python，可以使用 Homebrew：

```bash
brew install python
```

也可以选择通过 Homebrew 安装 GCC 或 LLVM：

```bash
brew install gcc
# 或
brew install llvm
```

Homebrew 安装的 GCC 通常带有版本号（如 `g++-15`），可以通过 `APR_CXX` 指定：

```bash
export APR_CXX=g++-15
```

如果已经安装 Xcode Command Line Tools，无需额外安装编译器。

</details>

<details>
<summary>Linux</summary>

**Ubuntu / Debian**

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip g++
```

也可以将 `g++` 替换为 `clang`。

**Fedora**

```bash
sudo dnf install python3 python3-pip gcc-c++
```

也可以将 `gcc-c++` 替换为 `clang`。

**Arch Linux**

```bash
sudo pacman -S python gcc
```

也可以将 `gcc` 替换为 `clang`。

</details>

<details>
<summary>Windows</summary>

推荐使用 [WSL](https://learn.microsoft.com/windows/wsl/install)，安装后按照 Linux 部分配置环境。

也可以使用原生 Windows 环境，安装 Python 和以下任意一种编译器：

- [LLVM](https://releases.llvm.org/)：提供 `clang++`
- [WinLibs](https://winlibs.com/)：提供 `g++`

例如，使用 winget：

```powershell
winget install Python.Python.3.12
winget install LLVM.LLVM
```

安装完成后重新打开终端，确认编译器已加入 PATH。

> [!NOTE]
> 项目使用 `-fsanitize=undefined` 检查运行时错误。该功能在 Windows 原生工具链上的支持可能有所不同。如果遇到兼容性问题，建议使用 WSL。

</details>

<details>
<summary>Python 依赖安装</summary>

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

**Windows（PowerShell）**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

仅运行案例测试（`python3 -m cases`）不需要额外的 Python 依赖。使用 `lab.py` 中的 AST 分析和自动修复功能时，需要安装 `requirements.txt` 中的依赖。

</details>

安装后，可以检查环境：

```bash
python3 --version
clang++ --version   # 使用 Clang 时
g++ --version       # 使用 GCC 时
```

## 项目结构

<details>
<summary>展开目录结构</summary>

```text
apr-course/
├── lab.py                 # APR 实验入口
├── requirements.txt       # Python 依赖
├── cases/                 # 缺陷案例与测试
├── methods/               # APR 方法实现
├── utils/                 # AST、测试与日志工具
├── tests/                 # 项目自检
├── logs/                  # 实验日志
├── slides/
│   └── apr-intro.pptx     # 课程介绍
├── METHODS.md             # APR 方法及研究工具
└── TOOLS.md               # 编程助手使用说明
```

</details>
