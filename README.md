# Mizuki Voice

**English** · [简体中文](README.zh.md) · [日本語](README.ja.md)

Fine-tuned [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) v4 voice models for **Akiyama Mizuki (暁山瑞希)** from *Project SEKAI COLORFUL STAGE! feat. Hatsune Miku*.

Three separate registers, each with its own reference clip and its own character. They share one Weights pair — what changes between them is the reference audio and the intonation it carries.

| Version | F0 (measured) | Character | Reference |
|---|---|---|---|
| **genki** | 399–464 Hz | Punchy, high-energy, slight Kansai-like swing | `voice_ev_shuffle_54_03_12_20` |
| **normal** | 258–302 Hz | Standard (Kanto) intonation, everyday register | mixed: `area3_242_003` + `voice_ev_shuffle_63_07_38_20` |
| **sad** | 316–388 Hz | Quiet, restrained, no breathiness | `voice_ev_shuffle_41_04_61_20` |

For reference, Mizuki's adult voice in the source game measures **212–443 Hz** (median 307 Hz), so all three sit inside her real range.

## Samples

```
samples/genki/    10 lines, the punchy register
samples/normal/   10 lines, same text, standard intonation
samples/sad/       4 lines, the sad register
```

The genki and normal sets use identical text so the two registers can be compared directly.

## Weights

The weights are attached to the [latest release](../../releases/latest), not stored in git — the GPT checkpoint is 148 MB, over GitHub's 100 MB per-file limit.

| File | Size | Role |
|---|---|---|
| `mizuki-e1.ckpt` | 148 MB | GPT / AR model (semantic → tokens) |
| `mizuki_e2_s5336_l64.pth` | 83 MB | SoVITS model (LoRA rank 64), epoch 2 |

Place both in your GPT-SoVITS checkout:

```
GPT-SoVITS/GPT_weights_v4/mizuki-e1.ckpt
GPT-SoVITS/SoVITS_weights_v4/mizuki_e2_s5336_l64.pth
```

## Usage

Every sample in this repo was produced with the same sampler settings. Reproduce them with:

```python
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

cfg_dict["custom"]["version"] = "v4"
cfg_dict["custom"]["t2s_weights_path"] = "GPT_weights_v4/mizuki-e1.ckpt"
cfg_dict["custom"]["vits_weights_path"] = "SoVITS_weights_v4/mizuki_e2_s5336_l64.pth"

tts.run({
    "text": text, "text_lang": "ja",
    "ref_audio_path": reference_wav,          # see recipes/*.json
    "prompt_text": reference_text,            # transcript of that exact clip
    "prompt_lang": "ja",
    "top_k": 15, "top_p": 1.0, "temperature": 1.0,
    "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
    "parallel_infer": True, "repetition_penalty": 1.35, "seed": 42,
    "sample_steps": 128,
})
```

Post-processing is **peak normalisation to 0.95 and nothing else**.

Do not add spectral-gate denoising. It was measured on this exact setup: harmonicity dropped 0.903 → 0.821 and clips shortened 3.16 s → 2.80 s, because the gate leaves musical noise and eats breath tails. It sounded mechanical and lifeless. If a render sounds noisy, the cause is the source material or the model, not a missing cleanup pass.

## Recipes

`recipes/*.json` records the exact configuration for each voice — reference path, reference transcript, all sampler parameters, measured F0, and post-processing. `recipes/normal_mixed_ref.wav` is the 9.72 s concatenated reference used by the normal voice.

## How it was built

The corpus is 11,258 voice lines harvested from the Japanese client data via [sekai.best](https://sekai.best), one line per file with an exact transcript. A cleaned edition (11,179 lines, 11,140 unique clips) removes child-voice lines and attaches an emotion tag derived from the game's own `FacialName` / `MotionName` data.

Training is a full fine-tune of `s1v3.ckpt` for the GPT stage and a **LoRA (rank 64) adapter on top of `s2Gv4.pth`** for the SoVITS stage, fp32, batch 4, 2 epochs (5,336 steps). About 10.7k clips, 14 hours of audio.

Two rules came out of this build the hard way and are worth keeping:

**Reference pitch shifting does not work on a fine-tuned model.** Pitching a reference down 1–2 semitones moved a test line *up*, from 619 Hz to 652 to 658 Hz. The register lives in the weights, not in the reference. To change pitch, pitch the training data and retrain.

**Never pick a reference by a single metric sorted to its extreme.** Sorting by descending F0 selects the most strained takes (762–865 Hz, against a 307 Hz median); sorting by descending duration selects the breathiest. Use a multi-objective score.

## Limitations

- Japanese only. The corpus has no other language.
- The `genki` reference is an exclamatory line with wide pitch swings, and the model copies that contour — a listener may hear it as Kansai-flavoured. The `normal` voice exists to cover the standard-intonation case.
- One specific sad sentence (`……どうして、こうなっちゃったんだろう。`) makes the model collapse to 98–156 Hz. Recorded in `recipes/sad.json`; avoid that phrasing.
- Trained and verified on a single 8 GB laptop GPU at fp32. Half precision was not evaluated.
- No speaker-verification or MOS evaluation was run. Quality judgements here are acoustic measurements plus listening, not a benchmark.

## Licence and disclaimer

Copyright (C) 2026 Amia-py. Licensed under **AGPL-3.0-or-later**; the full text is in [LICENSE](LICENSE).

The scripts and recipes in this repository are the corresponding source for the released weights. If you interact with these weights over a network, AGPL section 13 entitles you to obtain that source — it is this repository.


Model weights and sample audio: **AGPL-3.0**, matching GPT-SoVITS.

The character Akiyama Mizuki, the voice recordings, and all related assets belong to SEGA, Colorful Palette and Crypton Future Media. This repository contains a derivative trained on game audio and is published for personal, non-commercial research and fan use. It is not affiliated with or endorsed by any of those companies. Do not use it commercially, and do not present the output as official voice work.

## Acknowledgements

- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — the voice conversion framework
- [sekai.best](https://sekai.best) and the [Sekai-World](https://github.com/Sekai-World) master database — corpus and scenario data
- *Project SEKAI COLORFUL STAGE! feat. Hatsune Miku* — SEGA / Colorful Palette
