#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Amia-py
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of the corresponding voice-model release and is free software:
# you can redistribute it and/or modify it under the terms of the GNU Affero General
# Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. See LICENSE for the full text.
"""Reproduce any of the three Mizuki voices with the settings this repo documents.

    python scripts/synthesize.py genki "おつかれさま。今日もなんとか生きてる？"
    python scripts/synthesize.py normal --batch lines.txt
    python scripts/synthesize.py sad "……ごめん。ボク、うまく言えなかった。"

Weights are not in the repo (the GPT checkpoint is 148 MB, over GitHub's per-file limit).
Download them from the latest release and point --repo at your GPT-SoVITS checkout.

The sampler settings below are the ones every sample in samples/ was produced with.
Changing them invalidates the comparison, so they are not exposed as flags.
"""
import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf
import librosa
import torch
import torchaudio


def _sf_load(path):
    data, sr = sf.read(path, dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return torch.from_numpy(np.ascontiguousarray(data)).unsqueeze(0), sr


torchaudio.load = _sf_load

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# fixed sampler settings - do not tune, these are what the samples use
SAMPLER = {
    "top_k": 15, "top_p": 1.0, "temperature": 1.0,
    "text_split_method": "cut5", "batch_size": 1, "speed_factor": 1.0,
    "parallel_infer": True, "repetition_penalty": 1.35, "seed": 42,
    "sample_steps": 128,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice", choices=["genki", "normal", "sad"])
    ap.add_argument("text", nargs="?", help="a single line; omit when using --batch")
    ap.add_argument("--batch", help="file with one line per line")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--repo", required=True, help="path to your GPT-SoVITS checkout")
    args = ap.parse_args()

    recipe = json.load(open(os.path.join(ROOT, "recipes", f"{args.voice}.json"), encoding="utf-8"))

    # the normal voice ships its mixed reference; the other two point at corpus paths that
    # are not in this repo, so allow an override via MZ_REF_DIR
    ref = os.path.join(ROOT, recipe["reference"]) if recipe["reference"].startswith("recipes/") \
        else os.path.join(os.environ.get("MZ_REF_DIR", ""), os.path.basename(recipe["reference"]))
    if not os.path.exists(ref):
        sys.exit(f"reference not found: {ref}\nSet MZ_REF_DIR to the folder holding it.")

    texts = [args.text] if args.text else [
        l.strip() for l in open(args.batch, encoding="utf-8") if l.strip()]
    if not texts:
        sys.exit("no input text")

    sys.path.insert(0, os.path.join(args.repo, "GPT_SoVITS"))
    sys.path.insert(0, os.path.join(args.repo, "GPT_SoVITS", "eres2net"))
    sys.path.insert(0, args.repo)
    import yaml
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config

    cfg_dict = yaml.safe_load(open(os.path.join(args.repo, "GPT_SoVITS", "configs", "tts_infer.yaml"),
                                   encoding="utf-8"))
    cfg_dict["custom"]["version"] = recipe["version"]
    cfg_dict["custom"]["t2s_weights_path"] = os.path.join(args.repo, recipe["t2s_weights"])
    cfg_dict["custom"]["vits_weights_path"] = os.path.join(args.repo, recipe["vits_weights"])
    tts = TTS(TTS_Config(cfg_dict))

    os.makedirs(args.out, exist_ok=True)
    for i, text in enumerate(texts, 1):
        chunks, sr = [], None
        for s, a in tts.run({"text": text, "text_lang": recipe["language"],
                             "ref_audio_path": ref, "prompt_text": recipe["reference_text"],
                             "prompt_lang": recipe["language"], **SAMPLER}):
            sr = s
            chunks.append(a)
        y = np.asarray(np.concatenate(chunks) if len(chunks) > 1 else chunks[0], dtype=np.float32)
        # peak normalise only - a denoise pass here measurably degrades the output
        peak = float(np.max(np.abs(y)))
        if peak > 0:
            y = y * (0.95 / peak)
        path = os.path.join(args.out, f"{args.voice}_{i:02d}.wav")
        sf.write(path, y, sr, subtype="PCM_16")
        print(f"{path}  {len(y) / sr:.2f}s", flush=True)


if __name__ == "__main__":
    main()
