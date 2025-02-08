# 主界面功能
- 启动代理
- 关闭代理
- 运行状态显示

# 渠道服账号管理

# 设置界面功能

# 代理劫持
1. host劫持
2. clash tun 劫持 + mitmproxy # 不好打包

# 已完成
- 日记功能
- 配置文件读取写入
- 初步实现代理

# 提交信息格式
```
<type>[optional scope]: <description>
<BLANK LINE>
[optional body]
<BLANK LINE>
[optional footer(s)]
```
提交说明包含了下面的结构化元素，以向类库使用者表明其意图
## 提交信息头部（Message Header）
提交信息的头部是一行简洁的变更描述，包含类型（type）、可选范围（scope）和主题（subject）
例如 `feat(parser): adds ability to parse arrays`
### 允许的 `<type>`
描述该提交提供的更改类型：

- feat: 类型 为 feat 的提交表示在代码库中新增了一个功能
- fix: 类型 为 fix 的提交表示在代码库中修复了一个 bug
- docs: 用于修改文档，例如修改 README 文件、API 文档等
- style: 用于修改代码的样式，例如调整缩进、空格、空行等，不涉及逻辑变更
- refactor: 用于重构代码，例如修改代码结构、变量名、函数名等但不修改功能逻辑
- test: 用于修改测试用例，例如添加、删除、修改代码的测试用例等
- chore: 用于对非业务性代码进行修改，例如修改构建流程或者工具配置等
- ci: 用于修改持续集成流程，例如修改 Travis、Jenkins 等工作流配置
- build: 用于修改项目构建系统，例如修改依赖库、外部接口或者升级 Node 版本等
- perf: 用于优化性能，例如提升代码的性能、减少内存占用等
- revert: 用于表明撤销提交，并紧随被撤销提交的标题。在正文中应说明：`This reverts commit <hash>.`，其中 `<hash>` 是被撤销提交的 SHA 值

### 允许的 `<scope>`
范围可以是指定代码变更的模块，例如 `$location`、`$browser`、`$compile`、`$rootScope`、`ngHref`、`ngClick`、`ngView` 等。如果没有合适的范围，可以使用 `*`。

### `<subject>` 主题
- 使用祈使句，时态为现在时（如 "change"，而不是 "changed" 或 "changes"）
- 首字母小写
- 结尾不加句号（.）

## 提交信息正文（Message Body）
和 `<subject>` 一样，使用祈使句和现在时。说明变更的动机，并与先前行为进行对比

## 提交信息页脚（Message Footer）
脚注中除了 BREAKING CHANGE: <description> ，其它条目应该采用类似 git trailer format 这样的惯例
### 重大变更（Breaking Changes）
在脚注中包含 BREAKING CHANGE: 或 <类型>(范围) 后面有一个 ! 的提交，表示引入了破坏性 API 变更（这和语义化版本中的 MAJOR 相对应）。 破坏性变更可以是任意 类型 提交的一部分。
所有重大变更（Breaking Changes）必须在页脚的 `BREAKING CHANGE` 块中描述
```
chore!: drop support for Node 6
BREAKING CHANGE: use JavaScript features not available in Node 6.
```
### 关联问题（Referencing Issues）
关闭的 Bug 应该单独列在页脚，并加上 `Closes` 关键词，例如：`Closes #123`
