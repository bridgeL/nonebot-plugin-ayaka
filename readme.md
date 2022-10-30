<div align="center">

# Ayaka 0.3.12

适用于[nonebot2机器人](https://github.com/nonebot/nonebot2)的文字游戏开发辅助插件 

<img src="https://img.shields.io/badge/python-3.8%2B-blue">

[仓库](https://github.com/bridgeL/nonebot-plugin-ayaka) - 
[文档](https://bridgel.github.io/ayaka_doc/)

</div>

ayaka 通过二次封装nonebot2提供的api，提供专用api，便于其他文字游戏插件（ayaka衍生插件）的编写

单独安装ayaka插件没有意义，ayaka插件的意义在于帮助ayaka衍生插件实现功能

任何问题欢迎issue

## 已有的ayaka衍生插件

- [示例库](https://github.com/bridgeL/ayaka_plugins)
- [小游戏合集](https://github.com/bridgeL/nonebot-plugin-ayaka-games)

## 安装

1. 修改nonebot工作目录下的`pyproject.toml`文件，将`python = "^3.7.3"`修改为`python = "^3.8.0"`
2. `poetry add nonebot-plugin-ayaka` 
3. `poetry run playwright install chromium`

注意：

如果没有用到无头浏览器截图的功能，可忽略最后一步

不需要特意在`bot.py`中加载ayaka插件，只要正常加载ayaka衍生插件即可

ayaka衍生插件中也只需正常导入ayaka就行 `from ayaka import AyakaApp`

## 配置

推荐配置（非强制要求）
```
COMMAND_START=["#"]
COMMAND_SEP=[" "]
```

## 文档
https://bridgel.github.io/ayaka_doc/
