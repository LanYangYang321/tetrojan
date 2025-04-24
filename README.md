# tetrojan
a simple websocket based RAT framework

[![Bilibili 粉丝](https://img.shields.io/badge/dynamic/json?color=blue&label=BiliBili&labelColor=white&query=$.data.follower&url=https://api.bilibili.com/x/relation/stat?vmid=1084866085&logo=bilibili&style=flat-square)](https://space.bilibili.com/1084866085)
[![YouTube](https://img.shields.io/badge/YouTube-white?logo=youtube&logoColor=FF0000&style=flat-square)](https://www.youtube.com/@lyyontop)
[![GitHub last commit](https://img.shields.io/github/last-commit/LanYangYang321/tetrojan?color=yellow&logo=github&labelColor=black&label=Latest&style=flat-square)](https://github.com/LanYangYang321/Clash-For-Python)

免责声明:

本项目仅用于网络安全教育、技术研究与合法授权的测试用途。
本项目中的所有代码、工具和演示内容，仅供学习参考，禁止将其用于任何未获授权的实际入侵或控制行为。

请注意以下法律风险与责任：

本项目所涉及的远程访问功能，如被用于非法控制他人设备、窃取信息、破坏数据等行为，均属违法。

任何使用者擅自将本项目用于非法目的（如入侵他人计算机系统、传播恶意程序等），其行为所产生的一切后果由其本人承担，作者不对任何违法使用行为承担责任。

# 部署服务端:

## 🧱 环境依赖

- Python 3.8+
- 推荐使用 `virtualenv` 或 `conda` 虚拟环境

安装依赖：

```bash
pip install -r requirements.txt
```

## 🚀 快速部署

1. 克隆仓库：

```bash
git clone https://github.com/LanYangYang321/tetrojan.git
cd tetrojan
cd server
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 启动服务端（监听控制端）：

```bash
python main.py
```

## 证书:
GNU AFFERO GENERAL PUBLIC LICENSE V3
