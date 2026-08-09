# 开发规范 — sb-two-tops

## 命名

- 类名：CamelCase（如 `HomePage`）
- 函数：snake_case（如 `make_lparam`）
- 变量：snake_case（如 `post_click_wait_ms`）
- 常量：snake_case（如 `wm_left_button_down`）
- 受保护成员：`_leading_underscore`（如 `_handle_battle`）
- 注释、commit message 用中文
- **禁止使用 `# noinspection` 注释跳过拼写检查**

## 代码风格（PyCharm 零警告规则）

**必须保证 PyCharm 打开后没有任何红线、黄线、波浪线。**

### 红线（Error）

| 问题         | 规则                                                             |
|--------------|------------------------------------------------------------------|
| 语法错误     | 提交前 `python3 -c "import ast; ast.parse(open(f).read())"` 验证 |
| 未解析的引用 | import 路径必须正确                                              |
| 未定义的变量 | 变量必须先赋值再使用                                             |

### 黄线（Warning）

| 检查项               | 规避方法                                                                |
|----------------------|-------------------------------------------------------------------------|
| 方法不用 self        | 不用 self → `@staticmethod`；签名必须保留但暂未用 → `_ = self.xxx` 占位 |
| 未使用的 import      | 只 import 实际用到的                                                    |
| 未使用的变量         | 删掉，或 `_ = var` 标记为"有意不用"                                     |
| 变量遮蔽内置名       | 不用 `list`、`dict`、`id`、`type` 等做变量名                            |
| 冗余括号             | `if (x):` → `if x:`                                                     |
| 比较 None/True/False | `if x == True:` → `if x:`，`if x is None:` 正确                         |

### 代码风格（PEP 8）

- 缩进：4 空格，不用 tab
- 行宽：120 字符，不超
- 空行：类定义前 2 空行，方法前 1 空行
- import 分组：标准库 → 第三方 → 本地，每组内字母序

### Markdown 表格

- 表头行与分隔行宽度对齐：表头用空格填充到与分隔符一致

```
| 问题         | 规则                                                             |
|--------------|------------------------------------------------------------------|
```
- 分隔符用 `-` 填充，不用多余空格
- 表格内文字居左（默认），不需要对齐标记

### 验证命令

```bash
# 语法检查
python3 -c "import ast; ast.parse(open('src/main.py').read()); print('OK')"

# 行宽检查
awk 'length>120 {print NR": "length" chars"}' src/**/*.py

# self 未使用检查
python3 -c "
import ast, os
for root, dirs, files in os.walk('src'):
    for f in files:
        if not f.endswith('.py'): continue
        tree = ast.parse(open(os.path.join(root, f)).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.args.args and item.args.args[0].arg == 'self':
                        if not any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self' for n in ast.walk(item)):
                            print(f'{os.path.join(root, f)}:{item.lineno} {item.name}() self 未使用')
"
```

## 架构

- **单一职责**：每个文件只做一件事，避免大文件
- 核心模块放 `core/`，页面识别放 `pages/`，入口在 `main.py`
- 截图、识别、点击三者严格分离

## 安全

- 仓库公开，不写任何敏感信息
- 截图文件默认在 `.gitignore` 中排除

## 工作流

- 代码修改后先展示给用户确认，再 push
- 开发环境只做 `ast.parse` 语法验证，不装依赖