# Mizuki Voice

[English](README.md) · **简体中文** · [日本語](README.ja.md)

基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) v4 微调的 **暁山瑞希（Akiyama Mizuki）** 语音模型，角色出自《世界计划 多彩舞台！feat. 初音未来》。

三个独立声线，各自使用不同的参考音频、各有不同的听感定位。三者共用同一组权重 —— 区别只在参考音频以及它所携带的语调。

| 版本 | 实测 F0 | 听感 | 参考音频 |
|---|---|---|---|
| **genki** | 399–464 Hz | 冲、元气足、略带关西腔的语调起伏 | `voice_ev_shuffle_54_03_12_20` |
| **normal** | 258–302 Hz | 标准语（关东腔）、日常语气 | 混合：`area3_242_003` + `voice_ev_shuffle_63_07_38_20` |
| **sad** | 316–388 Hz | 低沉、克制、无气声 | `voice_ev_shuffle_41_04_61_20` |

作为对照，游戏内瑞希成年声线的实测音域是 **212–443 Hz**（中位 307 Hz），三版都落在她的真实区间内。

## 样本

```
samples/genki/    10 句，冲的那一版
samples/normal/   10 句，同一批台词，标准语调
samples/sad/       4 句，悲伤版
```

genki 与 normal 使用完全相同的台词，便于直接对比两个声线。

## 权重

权重放在 [最新 Release](../../releases/latest)，不进 git —— GPT 检查点 148 MB，超过 GitHub 单文件 100 MB 限制。

| 文件 | 大小 | 作用 |
|---|---|---|
| `mizuki-e1.ckpt` | 148 MB | GPT / AR 模型（语义 → token） |
| `mizuki_e2_s5336_l64.pth` | 83 MB | SoVITS 模型（LoRA rank 64），第 2 epoch |

放进你的 GPT-SoVITS 目录：

```
GPT-SoVITS/GPT_weights_v4/mizuki-e1.ckpt
GPT-SoVITS/SoVITS_weights_v4/mizuki_e2_s5336_l64.pth
```

## 用法

本仓库所有样本用的都是同一套采样参数：

```python
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

cfg_dict["custom"]["version"] = "v4"
cfg_dict["custom"]["t2s_weights_path"] = "GPT_weights_v4/mizuki-e1.ckpt"
cfg_dict["custom"]["vits_weights_path"] = "SoVITS_weights_v4/mizuki_e2_s5336_l64.pth"

tts.run({
    "text": text, "text_lang": "ja",
    "ref_audio_path": reference_wav,          # 见 recipes/*.json
    "prompt_text": reference_text,            # 该参考音频的逐字文本
    "prompt_lang": "ja",
    "top_k": 15, "top_p": 1.0, "temperature": 1.0,
    "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
    "parallel_infer": True, "repetition_penalty": 1.35, "seed": 42,
    "sample_steps": 128,
})
```

后处理**只做峰值归一化到 0.95，别的一律不加**。

不要加谱减降噪。在这套配置上实测过：谐波度从 0.903 掉到 0.821，时长从 3.16 s 缩到 2.80 s —— 谱减门控会留下 musical noise 并吃掉气口尾音，听感变得机械、没活力。如果某一版听着吵，原因在素材或模型本身，不是缺了一道清理工序。

## 配方

`recipes/*.json` 记录每一版的完整配置：参考路径、参考文本、全部采样参数、实测 F0、后处理方式。`recipes/normal_mixed_ref.wav` 是 normal 版使用的 9.72 秒拼接参考。

## 怎么训的

语料共 11,258 条语音，从日服客户端数据经 [sekai.best](https://sekai.best) 抓取，一行一个文件，逐条带精确文本。清洗版 11,179 条 / 11,140 个唯一音频，剔除幼年声线，并按游戏自带的 `FacialName` / `MotionName` 数据附上情感标签。

训练上，GPT 阶段全量微调 `s1v3.ckpt`，SoVITS 阶段在 `s2Gv4.pth` 上挂 **LoRA（rank 64）适配器**，fp32、batch 4、2 个 epoch（5,336 步）。约 1.07 万条音频、14 小时。

两条规矩是这次踩出来的，值得留着：

**微调后的模型，改参考音频的 pitch 没用。** 把参考降 1–2 个半音，测试句反而从 619 Hz 升到 652、658 Hz。音高活在权重里，不在参考里。要改音域只能改训练数据再重训。

**参考音频绝不能按单一指标排序取极值。** 按 F0 降序挑，挑到的是最喊的 take（762–865 Hz，而中位只有 307）；按时长降序挑，挑到的是气声最重的。要用多目标打分。

## 局限

- 只有日语。语料没有其他语言。
- `genki` 的参考是一句起伏很大的感叹句，模型会照抄那个语调轮廓，听感上可能被认作关西腔。`normal` 就是为覆盖标准语调这个场景而做的。
- 有一句特定的悲伤台词（`……どうして、こうなっちゃったんだろう。`）会让模型崩到 98–156 Hz，已记在 `recipes/sad.json` 里，避开这个句式。
- 在一张 8 GB 笔记本 GPU 上以 fp32 训练与验证，半精度未做评估。
- 没有跑说话人验证或 MOS 评测。这里的质量判断基于声学测量加听感，不是基准测试。

## 许可与声明

版权所有 (C) 2026 Amia-py，以 **AGPL-3.0-or-later** 发布，全文见 [LICENSE](LICENSE)。

本仓库中的脚本与配方即发布权重的对应源码。若你通过网络与这些权重交互，AGPL 第 13 条赋予你获取该源码的权利 —— 即本仓库。


模型权重与样本音频：**AGPL-3.0**，与 GPT-SoVITS 一致。

角色「暁山瑞希」、语音素材及相关资产版权归 SEGA、Colorful Palette 与 Crypton Future Media 所有。本仓库包含基于游戏音频训练的衍生物，仅供个人、非商业的研究与同人使用，与上述公司无隶属或授权关系。请勿商用，也不要将输出冒充官方配音。

## 致谢

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) —— 语音转换框架
- [sekai.best](https://sekai.best) 与 [Sekai-World](https://github.com/Sekai-World) master 数据库 —— 语料与剧本数据
- 《世界计划 多彩舞台！feat. 初音未来》 —— SEGA / Colorful Palette
