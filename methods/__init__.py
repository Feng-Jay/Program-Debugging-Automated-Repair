"""四种修复方法。语法树和测试在 utils/。建议按这个顺序读：

  utils/astutil.py     语法树：找到能改的节点，并替换源码
  astview.py           画出语法树，节点是行号和代码（lab.py ast）
  utils/snippet.py     拼一段插入用的 C++，template 和 synth 共用
  utils/evaluate.py    调用 cases test，看补丁过不过
  utils/runlog.py      把过程打印出来，并保存到 logs/
  search.py            搜索：枚举比较符、变量和已有语句
  template.py          模板：匹配关系运算、空指针检查、缺 else
  synth.py             综合：先标出洞，再用有限组件填一个洞
  model.py             模型：生成提示，或真实调用；不自动改文件

四种方法都不按案例名写死补丁。lab.py 只调用各文件里的 run()。
"""
