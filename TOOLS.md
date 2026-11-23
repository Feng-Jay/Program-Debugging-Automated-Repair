# 使用编程工具辅助 APR 实验

## 研究原型与课堂演示的区别

| 类型 | 代表工具 | 主要目标语言/项目 | 本仓库中能直接运行的演示 |
|---|---|---|---|
| 搜索式修复 | [GenProg](https://github.com/squaresLab/genprog-code) | C；原版依赖 OCaml 工具链 | `python3 lab.py search cutoff`（AST 搜索，不是 GenProg） |
| 模板修复 | [TBar](https://github.com/TruX-DTF/TBar) | Java；Defects4J / GZoltar | `python3 lab.py template npd`（AST 模板，不是 TBar） |
| 语义约束/综合 | [Angelix](https://github.com/msv-lab/angelix) | C；符号执行 / SMT | `python3 lab.py synth cutoff`（有限洞枚举，不是 Angelix） |
| LLM 修复 | [Agentless](https://github.com/OpenAutoCoder/Agentless) | GitHub issue / SWE-bench 多文件修复 | `python3 lab.py prompt cutoff` / `llm cutoff`（不是 Agentless） |

这四个原项目依赖都比较重，10–15 分钟的课上不建议现装。这里用 C 编译器、Python 和 tree-sitter 把缺陷跑出来，并在语法树上改、测。要复现论文，课后按原项目的 README 单独装。

## 可选：用现成编程助手或 DeepSeek 生成补丁

电脑上已安装下列任意一个工具即可；本课程不要求新生注册、购买订阅或配置 API Key。功能模式和额度可能随版本和地区变化，以下链接以官方说明为准。

| 工具 | 打开方式（以当前产品界面为准） | 官方说明 |
|---|---|---|
| GitHub Copilot | 在 VS Code 中打开 Chat；引用 `cases/cutoff/cutoff.cpp` | [VS Code Copilot](https://code.visualstudio.com/docs/setup/copilot) |
| Cursor | 打开课程目录，在 Ask/Chat 中引用 `cases/cutoff/cutoff.cpp` | [Cursor Quickstart](https://cursor.com/docs/get-started/quickstart) |
| TRAE | 打开课程目录，在 Chat 模式中引用文件 | [TRAE 文档](https://docs.trae.cn/ide_get-started-with-trae) |
| Qoder CN | 打开课程目录，在智能问答中引用文件 | [Qoder CN 文档](https://docs.qoder.cn/user-guide/ask) |

1. 先运行 `python3 -m cases test cutoff cases/cutoff/cutoff.cpp`，确认 60 分失败，其余分数通过。
2. 执行 `python3 lab.py prompt cutoff`，把输出与 `cases/cutoff/cutoff.cpp` 发给工具，让它生成**补丁**而不自动修改仓库。
3. 看懂补丁，自己复制 `cases/cutoff/cutoff.cpp` 为 `my_cutoff.cpp`，再手动修改它；不要修改 `cases/cutoff/cutoff.fixed.cpp`。
4. 运行 `python3 -m cases test cutoff my_cutoff.cpp`，检查 60 分以及原来已经通过的分数。
5. 如果失败，把真实运行输出交给工具，让它修改建议；不要只依据模型声称的“已修复”。

也可以在本机通过 DeepSeek（默认）或其它 OpenAI 兼容接口进行真实模型调用：

```bash
export DEEPSEEK_API_KEY='你的实际密钥'
# 可选：export DEEPSEEK_MODEL='deepseek-chat'
# 可选：export DEEPSEEK_BASE_URL='https://api.deepseek.com/v1'
python3 lab.py llm cutoff
```

换其它兼容接口时设置 `OPENAI_API_KEY`、`OPENAI_MODEL` 和 `OPENAI_BASE_URL`。密钥不要提交，也不要发给学生。脚本不记录密钥，不改示例文件，也不执行模型给出的代码。没设密钥就不会发请求。

## 教师备课说明

- 课前装好 `requirements.txt`，确认有 `g++` 或 `clang++`。可以先跑 `python3 lab.py selftest`。
- 要用 Copilot、Cursor 或 DeepSeek 的话，课前自己登一次、通一次网。现场登不上就改跑 `template`、`search`、`synth`。
- `slides/apr-intro.pptx` 还能讲流程和四类方法。里面的 `lab.py reproduce`、以 `npd` 为主的搜索，以及 `divzero`，和现在的仓库对不上。操作按 README，案例用 `cutoff`、`npd`。
- 学生不用把 sanitizer 讲透。UBSan 只是用来确认程序真的做了非法操作，行为对不对仍看测试。
- 不同机器上的堆栈文字可以不一样。看 `runtime error` 和错误种类就行。
- 讲搜索时先跑 `cutoff` 或 `oob`，能看到比较符被改掉。再跑 `npd`：要用的判断原来没有，搜索就会失败。
