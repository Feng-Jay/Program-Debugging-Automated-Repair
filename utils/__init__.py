"""语法树、补丁片段、测试和日志。修复方法在 methods/ 里调用这里。

  astutil.py    语法树：找到能改的节点，并替换源码
  snippet.py    拼一段插入用的 C++，template 和 synth 共用
  evaluate.py   调用 cases test，看补丁过不过
  runlog.py     把过程打印出来，保存到 logs/，并逐个测试补丁
"""
