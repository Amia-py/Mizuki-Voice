# Mizuki Voice

[English](README.md) · [简体中文](README.zh.md) · **日本語**

[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) v4 をファインチューニングした、**暁山瑞希（あきやま みずき）** の音声モデルです。『プロジェクトセカイ カラフルステージ！ feat. 初音ミク』のキャラクターを対象としています。

3 つの独立した声域で、それぞれ参照音声と聴感の性格が異なります。重みは共通で、違うのは参照音声と、それが持つイントネーションだけです。

| バージョン | 実測 F0 | 聴感 | 参照音声 |
|---|---|---|---|
| **genki** | 399–464 Hz | 強め、元気、関西風の抑揚 | `voice_ev_shuffle_54_03_12_20` |
| **normal** | 258–302 Hz | 標準語（関東）の抑揚、日常のトーン | 混合：`area3_242_003` + `voice_ev_shuffle_63_07_38_20` |
| **sad** | 316–388 Hz | 低め、抑制的、息混じりでない | `voice_ev_shuffle_41_04_61_20` |

参考までに、ゲーム内の瑞希の成人声は **212–443 Hz**（中央値 307 Hz）です。3 バージョンとも実際の音域に収まっています。

## サンプル

```
samples/genki/    10 文、強めのトーン
samples/normal/   10 文、同じ台詞、標準的な抑揚
samples/sad/       4 文、悲しみのトーン
```

genki と normal は同一の台詞なので、2 つの声域を直接聴き比べられます。

## 重み

重みは [最新リリース](../../releases/latest) に添付しています。GPT チェックポイントが 148 MB で GitHub の 1 ファイル 100 MB 制限を超えるため、git には含めていません。

| ファイル | サイズ | 役割 |
|---|---|---|
| `mizuki-e1.ckpt` | 148 MB | GPT / AR モデル（意味 → トークン） |
| `mizuki_e2_s5336_l64.pth` | 83 MB | SoVITS モデル（LoRA rank 64）、第 2 エポック |

GPT-SoVITS のディレクトリに配置してください：

```
GPT-SoVITS/GPT_weights_v4/mizuki-e1.ckpt
GPT-SoVITS/SoVITS_weights_v4/mizuki_e2_s5336_l64.pth
```

## 使い方

本リポジトリのサンプルはすべて同じサンプリング設定で生成しています。

```python
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

cfg_dict["custom"]["version"] = "v4"
cfg_dict["custom"]["t2s_weights_path"] = "GPT_weights_v4/mizuki-e1.ckpt"
cfg_dict["custom"]["vits_weights_path"] = "SoVITS_weights_v4/mizuki_e2_s5336_l64.pth"

tts.run({
    "text": text, "text_lang": "ja",
    "ref_audio_path": reference_wav,          # recipes/*.json を参照
    "prompt_text": reference_text,            # その参照音声の逐字テキスト
    "prompt_lang": "ja",
    "top_k": 15, "top_p": 1.0, "temperature": 1.0,
    "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
    "parallel_infer": True, "repetition_penalty": 1.35, "seed": 42,
    "sample_steps": 128,
})
```

後処理は**ピークを 0.95 に正規化するだけ**で、他は何も加えません。

スペクトルゲート型のノイズ除去は加えないでください。この構成で実測したところ、倍音性が 0.903 から 0.821 に下がり、長さが 3.16 秒から 2.80 秒に縮みました。ゲートは musical noise を残し、息の尾を削ります。結果として機械的で活気のない音になります。ノイズが気になる場合、原因は素材かモデル側で、掃除の工程が足りないわけではありません。

## レシピ

`recipes/*.json` に各バージョンの完全な設定（参照パス、参照テキスト、全サンプリングパラメータ、実測 F0、後処理）を記録しています。`recipes/normal_mixed_ref.wav` は normal が使う 9.72 秒の連結参照音声です。

## 学習方法

コーパスは日本語版クライアントのデータから [sekai.best](https://sekai.best) 経由で取得した 11,258 文です。1 行 1 ファイルで、それぞれ正確なテキストが付いています。クリーニング版は 11,179 文 / 11,140 個の一意な音声で、幼少期の声を除外し、ゲーム内の `FacialName` / `MotionName` データから感情タグを付けています。

学習は、GPT 段階が `s1v3.ckpt` の全量ファインチューニング、SoVITS 段階が `s2Gv4.pth` に **LoRA（rank 64）アダプタ**を載せる構成です。fp32、batch 4、2 エポック（5,336 ステップ）。約 1.07 万文、14 時間分。

今回の作業で痛い目を見て分かった 2 つの原則があります：

**ファインチューニング済みモデルでは、参照音声のピッチ変更は効きません。** 参照を 1〜2 半音下げたところ、テスト文は 619 Hz から 652、658 Hz へと*上がりました*。声域は重みの中にあり、参照の中にはありません。ピッチを変えたいなら学習データを変えて再学習するしかありません。

**参照音声を単一指標の極値で選んではいけません。** F0 の降順で選ぶと最も張り上げたテイク（762–865 Hz、中央値は 307 Hz）を拾い、長さの降順で選ぶと最も息混じりのテイクを拾います。多目的スコアで選んでください。

## 制限事項

- 日本語のみです。コーパスに他言語はありません。
- `genki` の参照は抑揚の大きい感嘆文で、モデルはその輪郭を写します。聴き手によっては関西風に聞こえることがあります。`normal` は標準的な抑揚をカバーするために用意しました。
- 特定の悲しみの一文（`……どうして、こうなっちゃったんだろう。`）でモデルが 98–156 Hz まで崩れます。`recipes/sad.json` に記録済みです。この言い回しは避けてください。
- 8 GB のノート PC GPU 1 枚、fp32 で学習・検証しています。半精度は未評価です。
- 話者照合や MOS 評価は行っていません。ここでの品質判断は音響測定と聴感によるもので、ベンチマークではありません。

## ライセンスと免責

Copyright (C) 2026 Amia-py。**AGPL-3.0-or-later** で公開しています。全文は [LICENSE](LICENSE) を参照してください。

本リポジトリのスクリプトとレシピが、公開している重みに対応するソースです。ネットワーク経由でこれらの重みを利用する場合、AGPL 第 13 条によりそのソースを取得する権利があります。それは本リポジトリです。


モデルの重みとサンプル音声：**AGPL-3.0**（GPT-SoVITS に準拠）。

キャラクター「暁山瑞希」、音声素材および関連アセットの権利は SEGA、Colorful Palette、Crypton Future Media に帰属します。本リポジトリはゲーム音声で学習した派生物を含み、個人・非商用の研究およびファン活動向けに公開しています。上記各社との提携・許諾関係はありません。商用利用は行わないでください。また、出力を公式の音声として提示しないでください。

## 謝辞

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) —— 音声変換フレームワーク
- [sekai.best](https://sekai.best) と [Sekai-World](https://github.com/Sekai-World) master データベース —— コーパスとシナリオデータ
- 『プロジェクトセカイ カラフルステージ！ feat. 初音ミク』 —— SEGA / Colorful Palette
