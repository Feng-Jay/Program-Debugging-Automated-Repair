# 本机副本的变更说明

原始材料未改动，对照位置：

- `/workspace/apr-course-materials/apr-course-original/`
- `/workspace/apr-course-materials/apr-course.zip`
- 本目录 git 仓库的首次提交 `Import original apr-course materials`

工作副本：`/workspace/apr-course-materials/apr-course/`

主要改动：

1. 用 tree-sitter 解析 C++，search / template / synth 在语法树上做真实的语句或表达式替换，而不是按案例名写死补丁文本。
2. synth 改为对所有案例相同的“洞 + 组件”枚举；组件来自局部变量、比较运算和测试期望字符串。
3. `lab.py llm` 默认调用 DeepSeek；无密钥时明确说明未发起真实调用，不用假输出冒充。
4. 新增泛化案例 `cutoff`（60 分边界），并增加 `tests/` 回归，禁止方法源码嵌入已知正确答案。
5. 方法可在任意已注册案例上运行。README / METHODS.md / TOOLS.md 已按实际机制更新。

已知限制见 TOOLS.md 与 METHODS.md：搜索受冗余假设约束；幻灯片尚未同步；没有密钥时无法验证真实 DeepSeek 调用。
