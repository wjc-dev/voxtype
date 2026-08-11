#!/usr/bin/env python3
"""Record once in memory and compare Qwen with Doubao on identical PCM.

The recording is never written to disk. Both providers receive byte-for-byte
identical 16 kHz mono PCM chunks. This is a diagnostic tool, not an app mode.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.transcription.doubao_streaming import DoubaoStreamingProcessor
from src.transcription.qwen_streaming import QwenStreamingProcessor


def load_credentials() -> None:
    app_env = Path.home() / "Library/Application Support/VoxType Next/.env"
    load_dotenv(app_env, override=False)
    load_dotenv(ROOT / ".env", override=False)


def record_pcm(duration: float) -> bytes:
    sample_rate = 16000
    print(f"3 秒后开始录音，持续 {duration:g} 秒。请用平时的小声音读测试句子。", flush=True)
    for remaining in (3, 2, 1):
        print(remaining, flush=True)
        time.sleep(1)
    print("开始录音…", flush=True)
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocking=True,
    ).reshape(-1)
    print("录音结束，正在用同一份音频比较。", flush=True)
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
    rms = float(np.sqrt(np.mean(pcm.astype(np.float32) ** 2))) if pcm.size else 0.0
    peak = int(np.max(np.abs(pcm.astype(np.int32)))) if pcm.size else 0
    print(f"音频诊断：RMS={rms:.1f}，Peak={peak}（仅数值，不保存录音）", flush=True)
    return pcm.tobytes()


async def recognize(processor_type, pcm: bytes) -> dict[str, object]:
    processor = processor_type()
    if not processor.is_available():
        return {"error": f"{processor.engine_label}凭证未配置"}
    chunk_bytes = 16000 * 2 // 10  # 100 ms, mono PCM16
    first_preview: float | None = None
    started = time.monotonic()
    preview_count = 0
    final_text = ""
    error = ""

    async def chunks():
        for offset in range(0, len(pcm), chunk_bytes):
            yield pcm[offset : offset + chunk_bytes]
            await asyncio.sleep(0.1)

    def on_preview(text: str) -> None:
        nonlocal first_preview, preview_count
        preview_count += 1
        if first_preview is None:
            first_preview = time.monotonic() - started

    def on_final(text: str) -> None:
        nonlocal final_text
        final_text = text

    def on_complete() -> None:
        return

    def on_error(message: str) -> None:
        nonlocal error
        error = message

    await processor.process_audio_stream(
        chunks(),
        on_preview,
        on_final,
        on_complete,
        on_error,
        sample_rate=16000,
    )
    return {
        "engine": processor.engine_label,
        "text": final_text,
        "first_preview": first_preview,
        "elapsed": time.monotonic() - started,
        "preview_count": preview_count,
        "error": error,
    }


async def main_async(duration: float) -> int:
    pcm = record_pcm(duration)
    # Sequential calls avoid network contention; input bytes are identical.
    qwen = await recognize(QwenStreamingProcessor, pcm)
    doubao = await recognize(DoubaoStreamingProcessor, pcm)
    print("\n=== 同音频识别结果 ===")
    for result in (qwen, doubao):
        name = result.get("engine") or "未知引擎"
        if result.get("error"):
            print(f"\n{name}：失败：{result['error']}")
            continue
        first = result.get("first_preview")
        first_label = f"{first:.2f}s" if isinstance(first, float) else "无"
        print(
            f"\n{name}（首字 {first_label}，总耗时 {result['elapsed']:.2f}s，"
            f"预览 {result['preview_count']} 次）：\n{result['text']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=12.0)
    args = parser.parse_args()
    load_credentials()
    return asyncio.run(main_async(max(2.0, min(60.0, args.duration))))


if __name__ == "__main__":
    raise SystemExit(main())

