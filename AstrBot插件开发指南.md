# AstrBot

## 插件开发指南

欢迎来到 AstrBot 插件开发指南！本章节将引导您如何开发 AstrBot 插件。在我们开始之前，希望你能具备以下基础知识：

1.  有一定的 Python 编程经验。
2.  有一定的 Git、GitHub 使用经验。

欢迎加入我们的开发者专用 QQ 群: `975206796`。

环境准备 [​](#环境准备)
---------------

### 获取插件模板 [​](#获取插件模板)

1.  打开 AstrBot 插件模板: [helloworld](https://github.com/Soulter/helloworld)
2.  点击右上角的 `Use this template`
3.  然后点击 `Create new repository`。
4.  在 `Repository name` 处填写您的插件名。插件名格式:
    *   推荐以 `astrbot_plugin_` 开头；
    *   不能包含空格；
    *   保持全部字母小写；
    *   尽量简短。
5.  点击右下角的 `Create repository`。

### 克隆项目到本地 [​](#克隆项目到本地)

克隆 AstrBot 项目本体和刚刚创建的插件仓库到本地。

bash

```
git clone https://github.com/AstrBotDevs/AstrBot
mkdir -p AstrBot/data/plugins
cd AstrBot/data/plugins
git clone 插件仓库地址
```

然后，使用 `VSCode` 打开 `AstrBot` 项目。找到 `data/plugins/<你的插件名字>` 目录。

更新 `metadata.yaml` 文件，填写插件的元数据信息。

WARNING

请务必修改此文件，AstrBot 识别插件元数据依赖于 `metadata.yaml` 文件。

### 设置插件 Logo（可选） [​](#设置插件-logo-可选)

可以在插件目录下添加 `logo.png` 文件作为插件的 Logo。请保持长宽比为 1:1，推荐尺寸为 256x256。

![](https://docs.astrbot.app/assets/plugin_logo.CQMxkx7t.png)

### 插件展示名（可选） [​](#插件展示名-可选)

可以修改 (或添加) `metadata.yaml` 文件中的 `display_name` 字段，作为插件在插件市场等场景中的展示名，以方便用户阅读。

### 调试插件 [​](#调试插件)

AstrBot 采用在运行时注入插件的机制。因此，在调试插件时，需要启动 AstrBot 本体。

您可以使用 AstrBot 的热重载功能简化开发流程。

插件的代码修改后，可以在 AstrBot WebUI 的插件管理处找到自己的插件，点击右上角 `...` 按钮，选择 `重载插件`。

### 插件依赖管理 [​](#插件依赖管理)

目前 AstrBot 对插件的依赖管理使用 `pip` 自带的 `requirements.txt` 文件。如果你的插件需要依赖第三方库，请务必在插件目录下创建 `requirements.txt` 文件并写入所使用的依赖库，以防止用户在安装你的插件时出现依赖未找到 (Module Not Found) 的问题。

> `requirements.txt` 的完整格式可以参考 [pip 官方文档](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

开发原则 [​](#开发原则)
---------------

感谢您为 AstrBot 生态做出贡献，开发插件请遵守以下原则，这也是良好的编程习惯。

*   功能需经过测试。
*   需包含良好的注释。
*   持久化数据请存储于 `data` 目录下，而非插件自身目录，防止更新 / 重装插件时数据被覆盖。
*   良好的错误处理机制，不要让插件因一个错误而崩溃。
*   在进行提交前，请使用 [ruff](https://docs.astral.sh/ruff/) 工具格式化您的代码。
*   不要使用 `requests` 库来进行网络请求，可以使用 `aiohttp`, `httpx` 等异步网络请求库。
*   如果是对某个插件进行功能扩增，请优先给那个插件提交 PR 而不是单独再写一个插件（除非原插件作者已经停止维护）。


## 最小实例

插件模版中的 `main.py` 是一个最小的插件实例。

python

```
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger # 使用 astrbot 提供的 logger 接口

@register("helloworld", "author", "一个简单的 Hello World 插件", "1.0.0", "repo url")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令''' # 这是 handler 的描述，将会被解析方便用户了解插件内容。非常建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!") # 发送一条纯文本消息

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
```

解释如下：

*   插件需要继承 `Star` 类。
*   `Context` 类用于插件与 AstrBot Core 交互，可以由此调用 AstrBot Core 提供的各种 API。
*   具体的处理函数 `Handler` 在插件类中定义，如这里的 `helloworld` 函数。
*   `AstrMessageEvent` 是 AstrBot 的消息事件对象，存储了消息发送者、消息内容等信息。
*   `AstrBotMessage` 是 AstrBot 的消息对象，存储了消息平台下发的消息的具体内容。可以通过 `event.message_obj` 获取。

TIP

`Handler` 一定需要在插件类中注册，前两个参数必须为 `self` 和 `event`。如果文件行数过长，可以将服务写在外部，然后在 `Handler` 中调用。

插件类所在的文件名需要命名为 `main.py`。

所有的处理函数都需写在插件类中。为了精简内容，在之后的章节中，我们可能会忽略插件类的定义。


## 处理消息事件

事件监听器可以收到平台下发的消息内容，可以实现指令、指令组、事件监听等功能。

事件监听器的注册器在 `astrbot.api.event.filter` 下，需要先导入。请务必导入，否则会和 python 的高阶函数 filter 冲突。

py

```
from astrbot.api.event import filter, AstrMessageEvent
```

消息与事件 [​](#消息与事件)
-----------------

AstrBot 接收消息平台下发的消息，并将其封装为 `AstrMessageEvent` 对象，传递给插件进行处理。

![](https://docs.astrbot.app/assets/message-event.BZZOyJtN.svg)

### 消息事件 [​](#消息事件)

`AstrMessageEvent` 是 AstrBot 的消息事件对象，其中存储了消息发送者、消息内容等信息。

### 消息对象 [​](#消息对象)

`AstrBotMessage` 是 AstrBot 的消息对象，其中存储了消息平台下发的消息具体内容，`AstrMessageEvent` 对象中包含一个 `message_obj` 属性用于获取该消息对象。

py

```
class AstrBotMessage:
    '''AstrBot 的消息对象'''
    type: MessageType  # 消息类型
    self_id: str  # 机器人的识别id
    session_id: str  # 会话id。取决于 unique_session 的设置。
    message_id: str  # 消息id
    group_id: str = "" # 群组id，如果为私聊，则为空
    sender: MessageMember  # 发送者
    message: List[BaseMessageComponent]  # 消息链。比如 [Plain("Hello"), At(qq=123456)]
    message_str: str  # 最直观的纯文本消息字符串，将消息链中的 Plain 消息（文本消息）连接起来
    raw_message: object
    timestamp: int  # 消息时间戳
```

其中，`raw_message` 是消息平台适配器的**原始消息对象**。

### 消息链 [​](#消息链)

![](https://docs.astrbot.app/assets/message-chain.DWhyf4H9.svg)

`消息链`描述一个消息的结构，是一个有序列表，列表中每一个元素称为`消息段`。

常见的消息段类型有：

*   `Plain`：文本消息段
*   `At`：提及消息段
*   `Image`：图片消息段
*   `Record`：语音消息段
*   `Video`：视频消息段
*   `File`：文件消息段

大多数消息平台都支持上面的消息段类型。

此外，OneBot v11 平台（QQ 个人号等）还支持以下较为常见的消息段类型：

*   `Face`：表情消息段
*   `Node`：合并转发消息中的一个节点
*   `Nodes`：合并转发消息中的多个节点
*   `Poke`：戳一戳消息段

TIP

在 aiocqhttp 消息适配器中，对于 `plain` 类型的消息，在发送中会自动使用 `strip()` 方法去除空格及换行符，可以使用零宽空格 `\u200b` 解决限制。

在 AstrBot 中，消息链表示为 `List[BaseMessageComponent]` 类型的列表。

指令 [​](#指令)
-----------

![](https://docs.astrbot.app/assets/message-event-simple-command.BnTOAE4E.svg)

python

```
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("helloworld", "Soulter", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld") # from astrbot.api.event.filter import command
    async def helloworld(self, event: AstrMessageEvent):
        '''这是 hello world 指令'''
        user_name = event.get_sender_name()
        message_str = event.message_str # 获取消息的纯文本内容
        yield event.plain_result(f"Hello, {user_name}!")
```

TIP

指令不能带空格，否则 AstrBot 会将其解析到第二个参数。可以使用下面的指令组功能，或者也使用监听器自己解析消息内容。

带参指令 [​](#带参指令)
---------------

![](https://docs.astrbot.app/assets/command-with-param.BhVvlON8.svg)

AstrBot 会自动帮你解析指令的参数。

python

```
@filter.command("add")
def add(self, event: AstrMessageEvent, a: int, b: int):
    # /add 1 2 -> 结果是: 3
    yield event.plain_result(f"Wow! The anwser is {a + b}!")
```

指令组 [​](#指令组)
-------------

指令组可以帮助你组织指令。

python

```
@filter.command_group("math")
def math(self):
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    # /math add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    # /math sub 1 2 -> 结果是: -1
    yield event.plain_result(f"结果是: {a - b}")
```

指令组函数内不需要实现任何函数，请直接 `pass` 或者添加函数内注释。指令组的子指令使用 `指令组名.command` 来注册。

当用户没有输入子指令时，会报错并，并渲染出该指令组的树形结构。

![](https://docs.astrbot.app/assets/image-1.Dqwv6KEi.png)

![](https://docs.astrbot.app/assets/898a169ae7ed0478f41c0a7d14cb4d64.BNSH8Mmt.png)

![](https://docs.astrbot.app/assets/image-2.Dc6zUa2q.png)

理论上，指令组可以无限嵌套！

py

```
'''
math
├── calc
│   ├── add (a(int),b(int),)
│   ├── sub (a(int),b(int),)
│   ├── help (无参数指令)
'''

@filter.command_group("math")
def math():
    pass

@math.group("calc") # 请注意，这里是 group，而不是 command_group
def calc():
    pass

@calc.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@calc.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")

@calc.command("help")
def calc_help(self, event: AstrMessageEvent):
    # /math calc help
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

指令别名 [​](#指令别名)
---------------

> v3.4.28 后

可以为指令或指令组添加不同的别名：

python

```
@filter.command("help", alias={'帮助', 'helpme'})
def help(self, event: AstrMessageEvent):
    yield event.plain_result("这是一个计算器插件，拥有 add, sub 指令。")
```

### 事件类型过滤 [​](#事件类型过滤)

#### 接收所有 [​](#接收所有)

这将接收所有的事件。

python

```
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条消息。")
```

#### 群聊和私聊 [​](#群聊和私聊)

python

```
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    message_str = event.message_str # 获取消息的纯文本内容
    yield event.plain_result("收到了一条私聊消息。")
```

`EventMessageType` 是一个 `Enum` 类型，包含了所有的事件类型。当前的事件类型有 `PRIVATE_MESSAGE` 和 `GROUP_MESSAGE`。

#### 消息平台 [​](#消息平台)

python

```
@filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP | filter.PlatformAdapterType.QQOFFICIAL)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    '''只接收 AIOCQHTTP 和 QQOFFICIAL 的消息'''
    yield event.plain_result("收到了一条信息")
```

当前版本下，`PlatformAdapterType` 有 `AIOCQHTTP`, `QQOFFICIAL`, `GEWECHAT`, `ALL`。

#### 管理员指令 [​](#管理员指令)

python

```
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    pass
```

仅管理员才能使用 `test` 指令。

### 多个过滤器 [​](#多个过滤器)

支持同时使用多个过滤器，只需要在函数上添加多个装饰器即可。过滤器使用 `AND` 逻辑。也就是说，只有所有的过滤器都通过了，才会执行函数。

python

```
@filter.command("helloworld")
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("你好！")
```

### 事件钩子 [​](#事件钩子)

TIP

事件钩子不支持与上面的 @filter.command, @filter.command_group, @filter.event_message_type, @filter.platform_adapter_type, @filter.permission_type 一起使用。

#### Bot 初始化完成时 [​](#bot-初始化完成时)

> v3.4.34 后

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    print("AstrBot 初始化完成")
```

#### LLM 请求时 [​](#llm-请求时)

在 AstrBot 默认的执行流程中，在调用 LLM 前，会触发 `on_llm_request` 钩子。

可以获取到 `ProviderRequest` 对象，可以对其进行修改。

ProviderRequest 对象包含了 LLM 请求的所有信息，包括请求的文本、系统提示等。

python

```
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import ProviderRequest

@filter.on_llm_request()
async def my_custom_hook_1(self, event: AstrMessageEvent, req: ProviderRequest): # 请注意有三个参数
    print(req) # 打印请求的文本
    req.system_prompt += "自定义 system_prompt"
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### LLM 请求完成时 [​](#llm-请求完成时)

在 LLM 请求完成后，会触发 `on_llm_response` 钩子。

可以获取到 `ProviderResponse` 对象，可以对其进行修改。

python

```
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse

@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse): # 请注意有三个参数
    print(resp)
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

#### 发送消息前 [​](#发送消息前)

在发送消息前，会触发 `on_decorating_result` 钩子。

可以在这里实现一些消息的装饰，比如转语音、转图片、加前缀等等

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    result = event.get_result()
    chain = result.chain
    print(chain) # 打印消息链
    chain.append(Plain("!")) # 在消息链的最后添加一个感叹号
```

> 这里不能使用 yield 来发送消息。这个钩子只是用来装饰 event.get_result().chain 的。如需发送，请直接使用 `event.send()` 方法。

#### 发送消息后 [​](#发送消息后)

在发送消息给消息平台后，会触发 `after_message_sent` 钩子。

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```

> 这里不能使用 yield 来发送消息。如需发送，请直接使用 `event.send()` 方法。

### 优先级 [​](#优先级)

指令、事件监听器、事件钩子可以设置优先级，先于其他指令、监听器、钩子执行。默认优先级是 `0`。

python

```
@filter.command("helloworld", priority=1)
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
```

控制事件传播 [​](#控制事件传播)
-------------------

python

```
@filter.command("check_ok")
async def check_ok(self, event: AstrMessageEvent):
    ok = self.check() # 自己的逻辑
    if not ok:
        yield event.plain_result("检查失败")
        event.stop_event() # 停止事件传播
```

当事件停止传播，后续所有步骤将不会被执行。

假设有一个插件 A，A 终止事件传播之后所有后续操作都不会执行，比如执行其它插件的 handler、请求 LLM。


## 消息的发送

被动消息 [​](#被动消息)
---------------

被动消息指的是机器人被动回复消息。

python

```
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
    yield event.plain_result("你好！")

    yield event.image_result("path/to/image.jpg") # 发送图片
    yield event.image_result("https://example.com/image.jpg") # 发送 URL 图片，务必以 http 或 https 开头
```

主动消息 [​](#主动消息)
---------------

主动消息指的是机器人主动推送消息。某些平台可能不支持主动消息发送。

如果是一些定时任务或者不想立即发送消息，可以使用 `event.unified_msg_origin` 得到一个字符串并将其存储，然后在想发送消息的时候使用 `self.context.send_message(unified_msg_origin, chains)` 来发送消息。

python

```
from astrbot.api.event import MessageChain

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    await self.context.send_message(event.unified_msg_origin, message_chain)
```

通过这个特性，你可以将 unified_msg_origin 存储起来，然后在需要的时候发送消息。

TIP

关于 unified_msg_origin。 unified_msg_origin 是一个字符串，记录了一个会话的唯一 ID，AstrBot 能够据此找到属于哪个消息平台的哪个会话。这样就能够实现在 `send_message` 的时候，发送消息到正确的会话。有关 MessageChain，请参见接下来的一节。

富媒体消息 [​](#富媒体消息)
-----------------

AstrBot 支持发送富媒体消息，比如图片、语音、视频等。使用 `MessageChain` 来构建消息。

python

```
import astrbot.api.message_components as Comp

@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    chain = [
        Comp.At(qq=event.get_sender_id()), # At 消息发送者
        Comp.Plain("来看这个图："),
        Comp.Image.fromURL("https://example.com/image.jpg"), # 从 URL 发送图片
        Comp.Image.fromFileSystem("path/to/image.jpg"), # 从本地文件目录发送图片
        Comp.Plain("这是一个图片。")
    ]
    yield event.chain_result(chain)
```

上面构建了一个 `message chain`，也就是消息链，最终会发送一条包含了图片和文字的消息，并且保留顺序。

类似地，

**文件 File**

py

```
Comp.File(file="path/to/file.txt", ) # 部分平台不支持
```

**语音 Record**

py

```
path = "path/to/record.wav" # 暂时只接受 wav 格式，其他格式请自行转换
Comp.Record(file=path, url=path)
```

**视频 Video**

py

```
path = "path/to/video.mp4"
Comp.Video.fromFileSystem(path=path)
Comp.Video.fromURL(url="https://example.com/video.mp4")
```

发送视频消息 [​](#发送视频消息)
-------------------

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Video
    # fromFileSystem 需要用户的协议端和机器人端处于一个系统中。
    music = Video.fromFileSystem(
        path="test.mp4"
    )
    # 更通用
    music = Video.fromURL(
        url="https://example.com/video.mp4"
    )
    yield event.chain_result([music])
```

![](https://docs.astrbot.app/assets/db93a2bb-671c-4332-b8ba-9a91c35623c2.Bmr_E62o.png)

发送群合并转发消息 [​](#发送群合并转发消息)
-------------------------

> 大多数平台都不支持此种消息类型，当前适配情况：OneBot v11

可以按照如下方式发送群合并转发消息。

py

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    from astrbot.api.message_components import Node, Plain, Image
    node = Node(
        uin=905617992,
        ,
        content=[
            Plain("hi"),
            Image.fromFileSystem("test.jpg")
        ]
    )
    yield event.chain_result([node])
```

![](https://docs.astrbot.app/assets/image-4.hxjQYKnj.png)


## 插件配置

随着插件功能的增加，可能需要定义一些配置以让用户自定义插件的行为。

AstrBot 提供了” 强大 “的配置解析和可视化功能。能够让用户在管理面板上直接配置插件，而不需要修改代码。

配置定义 [​](#配置定义)
---------------

要注册配置，首先需要在您的插件目录下添加一个 `_conf_schema.json` 的 json 文件。

文件内容是一个 `Schema`（模式），用于表示配置。Schema 是 json 格式的，例如上图的 Schema 是：

json

```
{
  "token": {
    "description": "Bot Token",
    "type": "string",
  },
  "sub_config": {
    "description": "测试嵌套配置",
    "type": "object",
    "hint": "xxxx",
    "items": {
      "name": {
        "description": "testsub",
        "type": "string",
        "hint": "xxxx"
      },
      "id": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx"
      },
      "time": {
        "description": "testsub",
        "type": "int",
        "hint": "xxxx",
        "default": 123
      }
    }
  }
}
```

*   `type`: **此项必填**。配置的类型。支持 `string`, `text`, `int`, `float`, `bool`, `object`, `list`。当类型为 `text` 时，将会可视化为一个更大的可拖拽宽高的 textarea 组件，以适应大文本。
*   `description`: 可选。配置的描述。建议一句话描述配置的行为。
*   `hint`: 可选。配置的提示信息，表现在上图中右边的问号按钮，当鼠标悬浮在问号按钮上时显示。
*   `obvious_hint`: 可选。配置的 hint 是否醒目显示。如上图的 `token`。
*   `default`: 可选。配置的默认值。如果用户没有配置，将使用默认值。int 是 0，float 是 0.0，bool 是 False，string 是 ""，object 是 {}，list 是 []。
*   `items`: 可选。如果配置的类型是 `object`，需要添加 `items` 字段。`items` 的内容是这个配置项的子 Schema。理论上可以无限嵌套，但是不建议过多嵌套。
*   `invisible`: 可选。配置是否隐藏。默认是 `false`。如果设置为 `true`，则不会在管理面板上显示。
*   `options`: 可选。一个列表，如 `"options": ["chat", "agent", "workflow"]`。提供下拉列表可选项。
*   `editor_mode`: 可选。是否启用代码编辑器模式。需要 AstrBot >= `v3.5.10`, 低于这个版本不会报错，但不会生效。默认是 false。
*   `editor_language`: 可选。代码编辑器的代码语言，默认为 `json`。
*   `editor_theme`: 可选。代码编辑器的主题，可选值有 `vs-light`（默认）， `vs-dark`。
*   `_special`: 可选。用于调用 AstrBot 提供的可视化提供商选取、人格选取、知识库选取等功能，详见下文。

其中，如果启用了代码编辑器，效果如下图所示:

![](https://docs.astrbot.app/assets/image-6.JmgDWyvk.png)

![](https://docs.astrbot.app/assets/image-7.wpQ2mMo1.png)

**_special** 字段仅 v4.0.0 之后可用。目前支持填写 `select_provider`, `select_provider_tts`, `select_provider_stt`, `select_persona`，用于让用户快速选择用户在 WebUI 上已经配置好的模型提供商、人设等数据。结果均为字符串。以 select_provider 为例，将呈现以下效果:

![](https://docs.astrbot.app/assets/image.9bwMD2Uc.png)

在插件中使用配置 [​](#在插件中使用配置)
-----------------------

AstrBot 在载入插件时会检测插件目录下是否有 `_conf_schema.json` 文件，如果有，会自动解析配置并保存在 `data/config/<plugin_name>_config.json` 下（依照 Schema 创建的配置文件实体），并在实例化插件类时传入给 `__init__()`。

py

```
from astrbot.api import AstrBotConfig

@register("config", "Soulter", "一个配置示例", "1.0.0")
class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict，拥有字典的所有方法
        super().__init__(context)
        self.config = config
        print(self.config)

        # 支持直接保存配置
        # self.config.save_config() # 保存配置
```

配置更新 [​](#配置更新)
---------------

如果您在发布不同版本时更新了 Schema，请注意，AstrBot 会递归检查 Schema 的配置项，如果发现配置文件中缺失了某个配置项，会自动添加默认值。但是 AstrBot 不会删除配置文件中**多余的**配置项，即使这个配置项在新的 Schema 中不存在（您在新的 Schema 中删除了这个配置项）。


## AI

AstrBot 内置了对多种大语言模型（LLM）提供商的支持，并且提供了统一的接口，方便插件开发者调用各种 LLM 服务。

您可以使用 AstrBot 提供的 LLM / Agent 接口来实现自己的智能体。

我们在 `v4.5.7` 版本之后对 LLM 提供商的调用方式进行了较大调整，推荐使用新的调用方式。新的调用方式更加简洁，并且支持更多的功能。当然，您仍然可以使用[旧的调用方式](https://docs.astrbot.app/dev/star/plugin.html#ai)。

获取当前会话使用的聊天模型 ID [​](#获取当前会话使用的聊天模型-id)
---------------------------------------

py

```
umo = event.unified_msg_origin
provider_id = await self.context.get_current_chat_provider_id(umo=umo)
```

调用大模型 [​](#调用大模型)
-----------------

py

```
llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id, # 聊天模型 ID
    prompt="Hello, world!",
)
# print(llm_resp.completion_text) # 获取返回的文本
```

Tool 是大语言模型调用外部工具的能力。

py

```
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class BilibiliTool(FunctionTool[AstrAgentContext]):
    name: str = "bilibili_videos"  # 工具名称
    description: str = "A tool to fetch Bilibili videos."  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Keywords to search for Bilibili videos.",
                },
            },
            "required": ["keywords"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        return "1. 视频标题：如何使用AstrBot\n视频链接：xxxxxx"
```

在上面定义好 Tool 之后，如果你需要实现的功能是让用户在使用 AstrBot 进行对话时自动调用该 Tool，那么你需要在插件的 **init** 方法中将 Tool 注册到 AstrBot 中：

py

```
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # >= v4.5.1 使用：
        self.context.add_llm_tools(BilibiliTool(), SecondTool(), ...)

        # < v4.5.1 之前使用：
        tool_mgr = self.context.provider_manager.llm_tools
        tool_mgr.func_list.append(BilibiliTool())
```

### 通过装饰器定义 Tool 和注册 Tool [​](#通过装饰器定义-tool-和注册-tool)

除了上述的通过 `@dataclass` 定义 Tool 的方式之外，你也可以使用装饰器的方式注册 tool 到 AstrBot。如果请务必按照以下格式编写一个工具（包括函数注释，AstrBot 会解析该函数注释，请务必将注释格式写对）

py

```
@filter.llm_tool() # 如果 name 不填，将使用函数名
async def get_weather(self, event: AstrMessageEvent, location: str) -> MessageEventResult:
    '''获取天气信息。

    Args:
        location(string): 地点
    '''
    resp = self.get_weather_from_api(location)
    yield event.plain_result("天气信息: " + resp)
```

在 `location(string): 地点` 中，`location` 是参数名，`string` 是参数类型，`地点` 是参数描述。

支持的参数类型有 `string`, `number`, `object`, `boolean`, `array`。在 v4.5.7 之后，支持对 `array` 类型参数指定子类型，例如 `array[string]`。

调用 Agent [​](#调用-agent)
-----------------------

Agent 可以被定义为 system_prompt + tools + llm 的结合体，可以实现更复杂的智能体行为。

在上面定义好 Tool 之后，可以通过以下方式调用 Agent：

py

```
llm_resp = await self.context.tool_loop_agent(
    event=event,
    chat_provider_id=prov_id,
    prompt="搜索一下 bilibili 上关于 AstrBot 的相关视频。",
    tools=ToolSet([BilibiliTool()]),
    max_steps=30, # Agent 最大执行步骤
    tool_call_timeout=60, # 工具调用超时时间
)
# print(llm_resp.completion_text) # 获取返回的文本
```

`tool_loop_agent()` 方法会自动处理工具调用和大模型请求的循环，直到大模型不再调用工具或者达到最大步骤数为止。

Multi-Agent [​](#multi-agent)
-----------------------------

Multi-Agent（多智能体）系统将复杂应用分解为多个专业化智能体，它们协同解决问题。不同于依赖单个智能体处理每一步，多智能体架构允许将更小、更专注的智能体组合成协调的工作流程。我们使用 `agent-as-tool` 模式来实现多智能体系统。

在下面的例子中，我们定义了一个主智能体（Main Agent），它负责根据用户查询将任务分配给不同的子智能体（Sub-Agents）。每个子智能体专注于特定任务，例如获取天气信息。

![](https://docs.astrbot.app/assets/multi-agent-example-1.BOUfMmmq.svg)

定义 Tools:

py

```
from pydantic import Field
from pydantic.dataclasses import dataclass

from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext

@dataclass
class AssignAgentTool(FunctionTool[AstrAgentContext]):
    """Main agent uses this tool to decide which sub-agent to delegate a task to."""

    name: str = "assign_agent"
    description: str = "Assign an agent to a task based on the given query"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        # Here you would implement the actual agent assignment logic.
        # For demonstration purposes, we'll return a dummy response.
        return "Based on the query, you should assign agent 1."


@dataclass
class WeatherTool(FunctionTool[AstrAgentContext]):
    """In this example, sub agent 1 uses this tool to get weather information."""

    name: str = "weather"
    description: str = "Get weather information for a location"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get weather information for.",
                },
            },
            "required": ["city"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        city = kwargs["city"]
        # Here you would implement the actual weather fetching logic.
        # For demonstration purposes, we'll return a dummy response.
        return f"The current weather in {city} is sunny with a temperature of 25°C."


@dataclass
class SubAgent1(FunctionTool[AstrAgentContext]):
    """Define a sub-agent as a function tool."""

    name: str = "subagent1_name"
    description: str = "subagent1_description"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        ctx = context.context.context
        event = context.context.event
        logger.info(f"the llm context messages: {context.messages}")
        llm_resp = await ctx.tool_loop_agent(
            event=event,
            chat_provider_id=await ctx.get_current_chat_provider_id(
                event.unified_msg_origin
            ),
            prompt=kwargs["query"],
            tools=ToolSet([WeatherTool()]),
            max_steps=30,
        )
        return llm_resp.completion_text


@dataclass
class SubAgent2(FunctionTool[AstrAgentContext]):
    """Define a sub-agent as a function tool."""

    name: str = "subagent2_name"
    description: str = "subagent2_description"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to call the sub-agent with.",
                },
            },
            "required": ["query"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        return "I am useless :(, you shouldn't call me :("
```

然后，同样地，通过 `tool_loop_agent()` 方法调用 Agent：

py

```
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    prov_id = await self.context.get_current_chat_provider_id(umo)
    llm_resp = await self.context.tool_loop_agent(
        event=event,
        chat_provider_id=prov_id,
        prompt="Test calling sub-agent for Beijing's weather information.",
        system_prompt=(
            "You are the main agent. Your task is to delegate tasks to sub-agents based on user queries."
            "Before delegating, use the 'assign_agent' tool to determine which sub-agent is best suited for the task."
        ),
        tools=ToolSet([SubAgent1(), SubAgent2(), AssignAgentTool()]),
        max_steps=30,
    )
    yield event.plain_result(llm_resp.completion_text)
```

对话管理器 [​](#对话管理器)
-----------------

### 获取会话当前的 LLM 对话历史 `get_conversation` [​](#获取会话当前的-llm-对话历史-get-conversation)

py

```
from astrbot.core.conversation_mgr import Conversation

uid = event.unified_msg_origin
conv_mgr = self.context.conversation_manager
curr_cid = await conv_mgr.get_curr_conversation_id(uid)
conversation = await conv_mgr.get_conversation(uid, curr_cid)  # Conversation
```

Conversation 类型定义

py

```
@dataclass
class Conversation:
    """The conversation entity representing a chat session."""

    platform_id: str
    """The platform ID in AstrBot"""
    user_id: str
    """The user ID associated with the conversation."""
    cid: str
    """The conversation ID, in UUID format."""
    history: str = ""
    """The conversation history as a string."""
    title: str | None = ""
    """The title of the conversation. For now, it's only used in WebChat."""
    persona_id: str | None = ""
    """The persona ID associated with the conversation."""
    created_at: int = 0
    """The timestamp when the conversation was created."""
    updated_at: int = 0
    """The timestamp when the conversation was last updated."""
```

### 快速添加 LLM 记录到对话 `add_message_pair` [​](#快速添加-llm-记录到对话-add-message-pair)

py

```
from astrbot.core.agent.message import (
    AssistantMessageSegment,
    UserMessageSegment,
    TextPart,
)

curr_cid = await conv_mgr.get_curr_conversation_id(event.unified_msg_origin)
user_msg = UserMessageSegment(content=[TextPart(text="hi")])
llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id, # 聊天模型 ID
    contexts=[user_msg], # 当未指定 prompt 时，使用 contexts 作为输入；同时指定 prompt 和 contexts 时，prompt 会被添加到 LLM 输入的最后
)
await conv_mgr.add_message_pair(
    cid=curr_cid,
    user_message=user_msg,
    assistant_message=AssistantMessageSegment(
        content=[TextPart(text=llm_resp.completion_text)]
    ),
)
```

### 主要方法 [​](#主要方法)

#### `new_conversation` [​](#new-conversation)

*   **Usage**  
    在当前会话中新建一条对话，并自动切换为该对话。
*   **Arguments**
    *   `unified_msg_origin: str` – 形如 `platform_name:message_type:session_id`
    *   `platform_id: str | None` – 平台标识，默认从 `unified_msg_origin` 解析
    *   `content: list[dict] | None` – 初始历史消息
    *   `title: str | None` – 对话标题
    *   `persona_id: str | None` – 绑定的 persona ID
*   **Returns**  
    `str` – 新生成的 UUID 对话 ID

#### `switch_conversation` [​](#switch-conversation)

*   **Usage**  
    将会话切换到指定的对话。
*   **Arguments**
    *   `unified_msg_origin: str`
    *   `conversation_id: str`
*   **Returns**  
    `None`

#### `delete_conversation` [​](#delete-conversation)

*   **Usage**  
    删除会话中的某条对话；若 `conversation_id` 为 `None`，则删除当前对话。
*   **Arguments**
    *   `unified_msg_origin: str`
    *   `conversation_id: str | None`
*   **Returns**  
    `None`

#### `get_curr_conversation_id` [​](#get-curr-conversation-id)

*   **Usage**  
    获取当前会话正在使用的对话 ID。
*   **Arguments**
    *   `unified_msg_origin: str`
*   **Returns**  
    `str | None` – 当前对话 ID，不存在时返回 `None`

#### `get_conversation` [​](#get-conversation)

*   **Usage**  
    获取指定对话的完整对象；若不存在且 `create_if_not_exists=True` 则自动创建。
*   **Arguments**
    *   `unified_msg_origin: str`
    *   `conversation_id: str`
    *   `create_if_not_exists: bool = False`
*   **Returns**  
    `Conversation | None`

#### `get_conversations` [​](#get-conversations)

*   **Usage**  
    拉取用户或平台下的全部对话列表。
*   **Arguments**
    *   `unified_msg_origin: str | None` – 为 `None` 时不过滤用户
    *   `platform_id: str | None`
*   **Returns**  
    `List[Conversation]`

#### `update_conversation` [​](#update-conversation)

*   **Usage**  
    更新对话的标题、历史记录或 persona_id。
*   **Arguments**
    *   `unified_msg_origin: str`
    *   `conversation_id: str | None` – 为 `None` 时使用当前对话
    *   `history: list[dict] | None`
    *   `title: str | None`
    *   `persona_id: str | None`
*   **Returns**  
    `None`

人格设定管理器 [​](#人格设定管理器)
---------------------

`PersonaManager` 负责统一加载、缓存并提供所有人格（Persona）的增删改查接口，同时兼容 AstrBot 4.x 之前的旧版人格格式（v3）。  
初始化时会自动从数据库读取全部人格，并生成一份 v3 兼容数据，供旧代码无缝使用。

py

```
persona_mgr = self.context.persona_manager
```

### 主要方法 [​](#主要方法-1)

#### `get_persona` [​](#get-persona)

*   **Usage** 获取根据人格 ID 获取人格数据。
*   **Arguments**
    *   `persona_id: str` – 人格 ID
*   **Returns**`Persona` – 人格数据，若不存在则返回 None
*   **Raises**`ValueError` – 当不存在时抛出

#### `get_all_personas` [​](#get-all-personas)

*   **Usage**  
    一次性获取数据库中所有人格。
*   **Returns**  
    `list[Persona]` – 人格列表，可能为空

#### `create_persona` [​](#create-persona)

*   **Usage**  
    新建人格并立即写入数据库，成功后自动刷新本地缓存。
*   **Arguments**
    *   `persona_id: str` – 新人格 ID（唯一）
    *   `system_prompt: str` – 系统提示词
    *   `begin_dialogs: list[str]` – 可选，开场对话（偶数条，user/assistant 交替）
    *   `tools: list[str]` – 可选，允许使用的工具列表；`None`= 全部工具，`[]`= 禁用全部
*   **Returns**  
    `Persona` – 新建后的人格对象
*   **Raises**  
    `ValueError` – 若 `persona_id` 已存在

#### `update_persona` [​](#update-persona)

*   **Usage**  
    更新现有人格的任意字段，并同步到数据库与缓存。
*   **Arguments**
    *   `persona_id: str` – 待更新的人格 ID
    *   `system_prompt: str` – 可选，新的系统提示词
    *   `begin_dialogs: list[str]` – 可选，新的开场对话
    *   `tools: list[str]` – 可选，新的工具列表；语义同 `create_persona`
*   **Returns**  
    `Persona` – 更新后的人格对象
*   **Raises**  
    `ValueError` – 若 `persona_id` 不存在

#### `delete_persona` [​](#delete-persona)

*   **Usage**  
    删除指定人格，同时清理数据库与缓存。
*   **Arguments**
    *   `persona_id: str` – 待删除的人格 ID
*   **Raises**  
    `Valueable` – 若 `persona_id` 不存在

#### `get_default_persona_v3` [​](#get-default-persona-v3)

*   **Usage**  
    根据当前会话配置，获取应使用的默认人格（v3 格式）。  
    若配置未指定或指定的人格不存在，则回退到 `DEFAULT_PERSONALITY`。
*   **Arguments**
    *   `umo: str | MessageSession | None` – 会话标识，用于读取用户级配置
*   **Returns**  
    `Personality` – v3 格式的默认人格对象

Persona / Personality 类型定义

py

```
class Persona(SQLModel, table=True):
    """Persona is a set of instructions for LLMs to follow.

    It can be used to customize the behavior of LLMs.
    """

    __tablename__ = "personas"

    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    persona_id: str = Field(max_length=255, nullable=False)
    system_prompt: str = Field(sa_type=Text, nullable=False)
    begin_dialogs: Optional[list] = Field(default=None, sa_type=JSON)
    """a list of strings, each representing a dialog to start with"""
    tools: Optional[list] = Field(default=None, sa_type=JSON)
    """None means use ALL tools for default, empty list means no tools, otherwise a list of tool names."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)},
    )

    __table_args__ = (
        UniqueConstraint(
            "persona_id",
            ,
        ),
    )


class Personality(TypedDict):
    """LLM 人格类。

    在 v4.0.0 版本及之后，推荐使用上面的 Persona 类。并且， mood_imitation_dialogs 字段已被废弃。
    """

    prompt: str
    name: str
    begin_dialogs: list[str]
    mood_imitation_dialogs: list[str]
    """情感模拟对话预设。在 v4.0.0 版本及之后，已被废弃。"""
    tools: list[str] | None
    """工具列表。None 表示使用所有工具，空列表表示不使用任何工具"""
```


## 文转图

基本 [​](#基本)
-----------

AstrBot 支持将文字渲染成图片。

python

```
@filter.command("image") # 注册一个 /image 指令，接收 text 参数。
async def on_aiocqhttp(self, event: AstrMessageEvent, text: str):
    url = await self.text_to_image(text) # text_to_image() 是 Star 类的一个方法。
    # path = await self.text_to_image(text, return_url = False) # 如果你想保存图片到本地
    yield event.image_result(url)
```

![](https://docs.astrbot.app/assets/image-3.6-Tj-zY5.png)

自定义 (基于 HTML) [​](#自定义-基于-html)
-------------------------------

如果你觉得上面渲染出来的图片不够美观，你可以使用自定义的 HTML 模板来渲染图片。

AstrBot 支持使用 `HTML + Jinja2` 的方式来渲染文转图模板。

py

```
# 自定义的 Jinja2 模板，支持 CSS
TMPL = '''
<div style="font-size: 32px;">
<h1 style="color: black">Todo List</h1>

<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</div>
'''

@filter.command("todo")
async def custom_t2i_tmpl(self, event: AstrMessageEvent):
    options = {} # 可选择传入渲染选项。
    url = await self.html_render(TMPL, {"items": ["吃饭", "睡觉", "玩原神"]}, options=options) # 第二个参数是 Jinja2 的渲染数据
    yield event.image_result(url)
```

返回的结果:

![](https://docs.astrbot.app/assets/fcc2dcb472a91b12899f617477adc5c7.BDrUgdtl.png)

这只是一个简单的例子。得益于 HTML 和 DOM 渲染器的强大性，你可以进行更复杂和更美观的的设计。除此之外，Jinja2 支持循环、条件等语法以适应列表、字典等数据结构。你可以从网上了解更多关于 Jinja2 的知识。

**图片渲染选项 (options)**：

请参考 Playwright 的 [screenshot](https://playwright.dev/python/docs/api/class-page#page-screenshot) API。

*   `timeout` (float, optional): 截图超时时间.
*   `type` (Literal["jpeg", "png"], optional): 截图图片类型.
*   `quality` (int, optional): 截图质量，仅适用于 JPEG 格式图片.
*   `omit_background` (bool, optional): 是否允许隐藏默认的白色背景，这样就可以截透明图了，仅适用于 PNG 格式
*   `full_page` (bool, optional): 是否截整个页面而不是仅设置的视口大小，默认为 True.
*   `clip` (dict, optional): 截图后裁切的区域。参考 Playwright screenshot API。
*   `animations`: (Literal["allow", "disabled"], optional): 是否允许播放 CSS 动画.
*   `caret`: (Literal["hide", "initial"], optional): 当设置为 hide 时，截图时将隐藏文本插入符号，默认为 hide.
*   `scale`: (Literal["css", "device"], optional): 页面缩放设置. 当设置为 css 时，则将设备分辨率与 CSS 中的像素一一对应，在高分屏上会使得截图变小. 当设置为 device 时，则根据设备的屏幕缩放设置或当前 Playwright 的 Page/Context 中的 device_scale_factor 参数来缩放.


## 会话控制

> 大于等于 v3.4.36

为什么需要会话控制？考虑一个 成语接龙 插件，某个 / 群用户需要和机器人进行多次对话，而不是一次性的指令。这时候就需要会话控制。

txt

```
用户: /成语接龙
机器人: 请发送一个成语
用户: 一马当先
机器人: 先见之明
用户: 明察秋毫
...
```

AstrBot 提供了开箱即用的会话控制功能：

导入：

py

```
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionController,
)
```

handler 内的代码可以如下：

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("成语接龙")
async def handle_empty_mention(self, event: AstrMessageEvent):
    """成语接龙具体实现"""
    try:
        yield event.plain_result("请发送一个成语~")

        # 具体的会话控制器使用方法
        @session_waiter(timeout=60, record_history_chains=False) # 注册一个会话控制器，设置超时时间为 60 秒，不记录历史消息链
        async def empty_mention_waiter(controller: SessionController, event: AstrMessageEvent):
            idiom = event.message_str # 用户发来的成语，假设是 "一马当先"

            if idiom == "退出":   # 假设用户想主动退出成语接龙，输入了 "退出"
                await event.send(event.plain_result("已退出成语接龙~"))
                controller.stop()    # 停止会话控制器，会立即结束。
                return

            if len(idiom) != 4:   # 假设用户输入的不是4字成语
                await event.send(event.plain_result("成语必须是四个字的呢~"))  # 发送回复，不能使用 yield
                return
                # 退出当前方法，不执行后续逻辑，但此会话并未中断，后续的用户输入仍然会进入当前会话

            # ...
            message_result = event.make_result()
            message_result.chain = [Comp.Plain("先见之明")] # import astrbot.api.message_components as Comp
            await event.send(message_result) # 发送回复，不能使用 yield

            controller.keep(timeout=60, reset_timeout=True) # 重置超时时间为 60s，如果不重置，则会继续之前的超时时间计时。

            # controller.stop() # 停止会话控制器，会立即结束。
            # 如果记录了历史消息链，可以通过 controller.get_history_chains() 获取历史消息链

        try:
            await empty_mention_waiter(event)
        except TimeoutError as _: # 当超时后，会话控制器会抛出 TimeoutError
            yield event.plain_result("你超时了！")
        except Exception as e:
            yield event.plain_result("发生错误，请联系管理员: " + str(e))
        finally:
            event.stop_event()
    except Exception as e:
        logger.error("handle_empty_mention error: " + str(e))
```

当激活会话控制器后，该发送人之后发送的消息会首先经过上面你定义的 `empty_mention_waiter` 函数处理，直到会话控制器被停止或者超时。

SessionController [​](#sessioncontroller)
-----------------------------------------

用于开发者控制这个会话是否应该结束，并且可以拿到历史消息链。

*   keep(): 保持这个会话
    *   timeout (float): 必填。会话超时时间。
    *   reset_timeout (bool): 设置为 True 时, 代表重置超时时间, timeout 必须 > 0, 如果 <= 0 则立即结束会话。设置为 False 时, 代表继续维持原来的超时时间, 新 timeout = 原来剩余的 timeout + timeout (可以 < 0)
*   stop(): 结束这个会话
*   get_history_chains() -> List[List[Comp.BaseMessageComponent]]: 获取历史消息链

自定义会话 ID 算子 [​](#自定义会话-id-算子)
-----------------------------

默认情况下，AstrBot 会话控制器会将基于 `sender_id` （发送人的 ID）作为识别不同会话的标识，如果想将一整个群作为一个会话，则需要自定义会话 ID 算子。

py

```
import astrbot.api.message_components as Comp
from astrbot.core.utils.session_waiter import (
    session_waiter,
    SessionFilter,
    SessionController,
)

# 沿用上面的 handler
# ...
class CustomFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        return event.get_group_id() if event.get_group_id() else event.unified_msg_origin

await empty_mention_waiter(event, session_filter=CustomFilter()) # 这里传入 session_filter
# ...
```

这样之后，当群内一个用户发送消息后，会话控制器会将这个群作为一个会话，群内其他用户发送的消息也会被认为是同一个会话。

甚至，可以使用这个特性来让群内组队！


## 杂项

获取消息平台实例 [​](#获取消息平台实例)
-----------------------

> v3.4.34 后

python

```
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("test")
async def test_(self, event: AstrMessageEvent):
    from astrbot.api.platform import AiocqhttpAdapter # 其他平台同理
    platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
    assert isinstance(platform, AiocqhttpAdapter)
    # platform.get_client().api.call_action()
```

调用 QQ 协议端 API [​](#调用-qq-协议端-api)
---------------------------------

py

```
@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    if event.get_platform_name() == "aiocqhttp":
        # qq
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        client = event.bot # 得到 client
        payloads = {
            "message_id": event.message_obj.message_id,
        }
        ret = await client.api.call_action('delete_msg', **payloads) # 调用 协议端  API
        logger.info(f"delete_msg: {ret}")
```

关于 CQHTTP API，请参考如下文档：

Napcat API 文档：[https://napcat.apifox.cn/](https://napcat.apifox.cn/)

Lagrange API 文档：[https://lagrange-onebot.apifox.cn/](https://lagrange-onebot.apifox.cn/)

获取载入的所有插件 [​](#获取载入的所有插件)
-------------------------

py

```
plugins = self.context.get_all_stars() # 返回 StarMetadata 包含了插件类实例、配置等等
```

获取加载的所有平台 [​](#获取加载的所有平台)
-------------------------

py

```
from astrbot.api.platform import Platform
platforms = self.context.platform_manager.get_insts() # List[Platform]
```


## 发布插件

发布插件到插件市场 [​](#发布插件到插件市场)
=========================

在编写完插件后，你可以选择将插件发布到 AstrBot 的插件市场，让更多用户使用你的插件。

AstrBot 使用 GitHub 托管插件，因此你需要先将插件代码推送到之前创建的 GitHub 插件仓库中。

你可以前往 [AstrBot 插件市场](https://plugins.astrbot.top) 提交你的插件。进入该网站后，点击右下角的 `+` 按钮，填写好基本信息、作者信息、仓库信息等内容后，点击 `提交到 GTIHUB` 按钮，你将会被导航到 AstrBot 仓库的 Issue 提交页面，请确认信息无误后点击 `Create` 按钮提交，即可完成插件发布。

![](https://docs.astrbot.app/assets/image.BB6vKQUk.png)


## 开发平台适配器

AstrBot 支持以插件的形式接入平台适配器，你可以自行接入 AstrBot 没有的平台。如飞书、钉钉甚至是哔哩哔哩私信、Minecraft。

我们以一个平台 `FakePlatform` 为例展开讲解。

首先，在插件目录下新增 `fake_platform_adapter.py` 和 `fake_platform_event.py` 文件。前者主要是平台适配器的实现，后者是平台事件的定义。

平台适配器 [​](#平台适配器)
-----------------

假设 FakePlatform 的客户端 SDK 是这样：

py

```
import asyncio

class FakeClient():
    '''模拟一个消息平台，这里 5 秒钟下发一个消息'''
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        # ...
                
    async def start_polling(self):
        while True:
            await asyncio.sleep(5)
            await getattr(self, 'on_message_received')({
                'bot_id': '123',
                'content': '新消息',
                'username': 'zhangsan',
                'userid': '123',
                'message_id': 'asdhoashd',
                'group_id': 'group123',
            })
            
    async def send_text(self, to: str, message: str):
        print('发了消息:', to, message)
        
    async def send_image(self, to: str, image_path: str):
        print('发了消息:', to, image_path)
```

我们创建 `fake_platform_adapter.py`：

py

```
import asyncio

from astrbot.api.platform import Platform, AstrBotMessage, MessageMember, PlatformMetadata, MessageType
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Plain, Image, Record # 消息链中的组件，可以根据需要导入
from astrbot.core.platform.astr_message_event import MessageSesion
from astrbot.api.platform import register_platform_adapter
from astrbot import logger
from .client import FakeClient
from .fake_platform_event import FakePlatformEvent
            
# 注册平台适配器。第一个参数为平台名，第二个为描述。第三个为默认配置。
@register_platform_adapter("fake", "fake 适配器", default_config_tmpl={
    "token": "your_token",
    "username": "bot_username"
})
class FakePlatformAdapter(Platform):

    def __init__(self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue) -> None:
        super().__init__(event_queue)
        self.config = platform_config # 上面的默认配置，用户填写后会传到这里
        self.settings = platform_settings # platform_settings 平台设置。
    
    async def send_by_session(self, session: MessageSesion, message_chain: MessageChain):
        # 必须实现
        await super().send_by_session(session, message_chain)
    
    def meta(self) -> PlatformMetadata:
        # 必须实现，直接像下面一样返回即可。
        return PlatformMetadata(
            "fake",
            "fake 适配器",
        )

    async def run(self):
        # 必须实现，这里是主要逻辑。

        # FakeClient 是我们自己定义的，这里只是示例。这个是其回调函数
        async def on_received(data):
            logger.info(data)
            abm = await self.convert_message(data=data) # 转换成 AstrBotMessage
            await self.handle_msg(abm) 
        
        # 初始化 FakeClient
        self.client = FakeClient(self.config['token'], self.config['username'])
        self.client.on_message_received = on_received
        await self.client.start_polling() # 持续监听消息，这是个堵塞方法。

    async def convert_message(self, data: dict) -> AstrBotMessage:
        # 将平台消息转换成 AstrBotMessage
        # 这里就体现了适配程度，不同平台的消息结构不一样，这里需要根据实际情况进行转换。
        abm = AstrBotMessage()
        abm.type = MessageType.GROUP_MESSAGE # 还有 friend_message，对应私聊。具体平台具体分析。重要！
        abm.group_id = data['group_id'] # 如果是私聊，这里可以不填
        abm.message_str = data['content'] # 纯文本消息。重要！
        abm.sender = MessageMember(user_id=data['userid'], nickname=data['username']) # 发送者。重要！
        abm.message = [Plain(text=data['content'])] # 消息链。如果有其他类型的消息，直接 append 即可。重要！
        abm.raw_message = data # 原始消息。
        abm.self_id = data['bot_id']
        abm.session_id = data['userid'] # 会话 ID。重要！
        abm.message_id = data['message_id'] # 消息 ID。
        
        return abm
    
    async def handle_msg(self, message: AstrBotMessage):
        # 处理消息
        message_event = FakePlatformEvent(
            message_str=message.message_str,
            message_obj=message,
            platform_meta=self.meta(),
            session_id=message.session_id,
            client=self.client
        )
        self.commit_event(message_event) # 提交事件到事件队列。不要忘记！
```

`fake_platform_event.py`：

py

```
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.platform import AstrBotMessage, PlatformMetadata
from astrbot.api.message_components import Plain, Image
from .client import FakeClient
from astrbot.core.utils.io import download_image_by_url

class FakePlatformEvent(AstrMessageEvent):
    def __init__(self, message_str: str, message_obj: AstrBotMessage, platform_meta: PlatformMetadata, session_id: str, client: FakeClient):
        super().__init__(message_str, message_obj, platform_meta, session_id)
        self.client = client
        
    async def send(self, message: MessageChain):
        for i in message.chain: # 遍历消息链
            if isinstance(i, Plain): # 如果是文字类型的
                await self.client.send_text(to=self.get_sender_id(), message=i.text)
            elif isinstance(i, Image): # 如果是图片类型的 
                img_url = i.file
                img_path = ""
                # 下面的三个条件可以直接参考一下。
                if img_url.startswith("file:///"):
                    img_path = img_url[8:]
                elif i.file and i.file.startswith("http"):
                    img_path = await download_image_by_url(i.file)
                else:
                    img_path = img_url

                # 请善于 Debug！
                    
                await self.client.send_image(to=self.get_sender_id(), image_path=img_path)

        await super().send(message) # 需要最后加上这一段，执行父类的 send 方法。
```

最后，main.py 只需这样，在初始化的时候导入 fake_platform_adapter 模块。装饰器会自动注册。

py

```
from astrbot.api.star import Context, Star, register
@register("helloworld", "Your Name", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        from .fake_platform_adapter import FakePlatformAdapter # noqa
```

搞好后，运行 AstrBot：

![](https://docs.astrbot.app/assets/QQ_1738155926221.BFUUxnZo.png)

这里出现了我们创建的 fake。

![](https://docs.astrbot.app/assets/QQ_1738155982211.DoUFCTrJ.png)

启动后，可以看到正常工作：

![](https://docs.astrbot.app/assets/QQ_1738156166893.dI_vHAXI.png)

有任何疑问欢迎加群询问~


## 自行部署文转图服务

AstrBot 使用 [AstrBotDevs/astrbot-t2i-service](https://github.com/AstrBotDevs/astrbot-t2i-service) 项目作为默认的文本转图像服务。默认使用的文转图服务接口是

plain

```
https://t2i.soulter.top/text2img
https://t2i.rcfortress.site/text2img
```

此接口能够保障大部分时间正常响应。但是由于部署在国外的（纽约）服务器，因此响应速度可能会比较慢。

TIP

欢迎通过 [爱发电](https://afdian.com/a/astrbot_team) 支持我们，以帮助我们支付服务器费用。

您可以选择自行部署文转图服务，以提升响应速度。

bash

```
docker run -itd -p 8999:8999 soulter/astrbot-t2i-service:latest
```

在部署完成后，前往 AstrBot 面板 -> 配置 -> 其他配置，修改`文本转图像服务接口` 为你部署好的 url。

> 如果部署在与 AstrBot 相同的机器上，url 应该为 `http://localhost:8999`。