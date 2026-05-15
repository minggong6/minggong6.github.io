---
permalink: /
title: ""
excerpt: ""
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

{% if site.google_scholar_stats_use_cdn %}
{% assign gsDataBaseUrl = "https://cdn.jsdelivr.net/gh/" | append: site.repository | append: "@" %}
{% else %}
{% assign gsDataBaseUrl = "https://raw.githubusercontent.com/" | append: site.repository | append: "/" %}
{% endif %}
{% assign url = gsDataBaseUrl | append: "google-scholar-stats/gs_data_shieldsio.json" %}

<span class='anchor' id='about-me'></span>

Hi，我是华中科技大学 电子信息与通信学院 大二在读生，目前是[DianRobot](https://dianrobot.github.io/)的成员


我的研究兴趣涵盖：
- 视觉-语言-动作模型 (Vision-Language-Action Model)
- 世界模型 (World Model)
- 机器人模仿学习 (Imitation Learning)
- 具身智能 (Embodied Intelligence)



<span class='anchor' id='-xl'></span>

# 🎓 学历
- *2024.06 - 至今*, <a href="https://www.hust.edu.cn/"><img class="svg" src="/images/HUST_logo.svg" width="23pt"></a> 华中科技大学 电子信息与通信学院, 湖北武汉


<span class='anchor' id='project-experience'></span>

# 🔬 项目经历

### MAIR GROUP — VLA 世界模型研究
- *2025.03 - 至今*, 华中科技大学 MAIR GROUP, 导师：<a href="https://mazhiyuan2002.github.io/">马志远 副教授</a>
- 研究方向：面向具身操作的视觉-语言-动作 (VLA) 模型与世界模型 (World Model)
- 工作内容：
  - 参与构建基于扩散策略 (Diffusion Policy) 的机器人动作生成框架，探索 VLA 模型在桌面操作任务中的泛化能力
  - 研究世界模型在机器人决策中的应用，通过学习环境动态实现模型预测控制 (Model Predictive Control)
  - 调研并复现具身智能领域前沿工作，包括 RT-2、Octo、UniPi 等代表性方法

### DianRobot Lab — 模仿学习系统开发与部署
- *2024.10 - 至今*, <a href="https://dianrobot.github.io/">DianRobot 实验室</a>, 华中科技大学
- 工作内容：
  - 基于 ACT (Action Chunking with Transformers) 等模仿学习算法，完成机器人抓取与操作任务的策略学习
  - 搭建数据采集管线，利用遥操作系统 (Teleoperation) 收集机器人演示数据，并进行数据增强与预处理
  - 将训练好的策略模型部署至真实机器人平台，实现 sim-to-real 迁移与在线调试
  - 初步探索深度学习在感知与控制中的应用，包括视觉编码器 (ViT)、Transformer 架构及强化学习基础

