# APR 方法及对应工具

自动程序修复的输入一般是待修程序，加上失败测试或缺陷报告。常见做法是先找可疑代码，再造几个候选补丁，编译、测试。通过已有测试的补丁叫 plausible patch，测试没覆盖到的行为仍可能是错的。

下面按候选补丁从哪来分成四类。实际系统经常混用，比如用模板划定搜索空间，再用测试筛模型给出的补丁。本目录的脚本用 tree-sitter 改 C++ 语法树，或拼一段提示，然后用 `python3 -m cases test` 验证。

## 1. 搜索：GenProg

限定几种编辑（删、插、换语句），在这些改法里找能通过测试的。GenProg 用遗传算法改 C 程序，常假设修复要用的语句已经出现在程序里。

课堂命令：`python3 lab.py ast cutoff` 画出语法树，节点是行号和代码，图片在 `logs/ast-cutoff.svg`。`python3 lab.py search cutoff --loc suspicious.txt`（也可换成 `oob`、`scheme`、`median`）先列出要改的位置，再对每个补丁打印 diff 并测试。日志在 `logs/search-<案例>.log`。

这里的脚本没有遗传算法、种群、交叉，用的也不是 GenProg 的 CIL。它不计算可疑行，但可以用 `--loc` 读入定位结果，只改列出的行。`npd` 需要新的判断，只复用已有语句时经常找不到。

原项目：[squaresLab/genprog-code](https://github.com/squaresLab/genprog-code)（C，还要 OCaml 工具链）。

## 2. 模板：TBar

事先写好修复模式，例如换比较符、换逻辑符、插入 NULL 检查。在可疑语句上匹配，实例化，再测试。

课堂命令：`python3 lab.py template npd`（也可用于 `oob`、`cutoff`）。运行时先列出关系运算、指针使用和缺少 else 的 if 在第几行，再套用并测试。现有模板：在 `p->` / `*p` 前插入空指针检查、给没有 else 的 if 补分支、替换关系运算符。else 和空检查里打印的文字来自该案例的测试期望。

TBar 面向 Java 和 Defects4J，模板和故障定位都更多。

原项目：[TruX-DTF/TBar](https://github.com/TruX-DTF/TBar)。

## 3. 约束 / 综合：Angelix、SemFix

从执行结果、测试期望和代码结构推出表达式该怎么写。Angelix 把符号执行和 SMT 合在一起，环境比较重。

课堂命令：`python3 lab.py synth cutoff`。脚本从语法树抽出洞（缺 else 的 if、比较运算、局部变量），写出每个洞在第几行。能填进去的只有函数内变量、几种比较运算，以及测试期望里的字符串。每次只填一个洞，打印 diff 后再测试。

这是单洞枚举，没有符号执行，也没有 SMT。测试期望里的字符串当作可用的常量，不是某个案例单独写的分支。

原项目：[msv-lab/angelix](https://github.com/msv-lab/angelix)；[SemFix](https://abhikrc.com/projects/Repair/index.html)。

## 4. 模型：Agentless 和编程助手

模型根据缺陷描述、相关代码和测试反馈改代码。Agentless 的流程比较固定：定位，生成多个候选，再验证、挑选。

课堂命令：`python3 lab.py prompt cutoff` 打出修复任务、源码和期望行为，可以交给编程助手。`python3 lab.py llm cutoff` 会真实调用 API，默认 DeepSeek（`DEEPSEEK_API_KEY`，模型默认 `deepseek-chat`）。没有密钥就不发请求。返回的代码不会自动跑。

把单个文件贴进聊天窗口，和跑 Agentless 不是一回事。Agentless 还要做项目级定位、补丁处理和筛选。

原项目：[OpenAutoCoder/Agentless](https://github.com/OpenAutoCoder/Agentless)。

## 对照

| 分类 | 候选从哪来 | 没通过时 | 本目录的命令 |
|---|---|---|---|
| 搜索 | 预定的几种 AST 编辑 | 试下一个候选 | `search <案例>` |
| 模板 | 规则在 AST 上套出来 | 换一条规则 | `template <案例>` |
| 约束/综合 | 能满足约束的表达式 | 换组件或换洞 | `synth <案例>` |
| 模型 | 模型根据上下文生成 | 把测试结果喂回去再生成 | `prompt <案例>` / `llm <案例>` |

故障定位、候选排序和测试验证在完整的 APR 系统里都会出现，上面四类只是补丁从哪来。

看一个补丁时可以问三件事：

1. 能不能编译、能不能跑。
2. 已有测试过了没有。只过少量旧测试，可能是过拟合。
3. 没写进旧测试的行为对不对。例如 `cutoff` 的 60 分要输出 pass，原来对的其它分数也不能改坏。

想看搜索和模型混在一起的做法，可以看 [GiantRepair](https://github.com/Feng-Jay/GiantRepair)。这部分不在新生课里。
