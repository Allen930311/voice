# Whisper STT Performance Benchmark Report

Evaluating speech-to-text (STT) acceleration on Intel Core Ultra 9 / Arc iGPU platform.

## Objective
Benchmark Whisper models (`tiny`, `base`, `small`) across multiple backends to identify the most efficient configuration for local transcription in the Voicebox project.

## Results Summary (RTF Comparison)

| Model | Size | PyTorch (CPU) | **OpenVINO (iGPU/Arc)** | OpenVINO (CPU) | **Winner (Perf/RTF)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **tiny** | 39M | **7.20** | 6.81 | 3.25 | **PyTorch CPU** (Low overhead) |
| **base** | 74M | 4.30 | **5.64** | 2.50 | **OpenVINO iGPU** |
| **small** | 244M | 2.24 | **3.63** | 0.95 | **OpenVINO iGPU** |

> [!NOTE]
> **RTF (Real-Time Factor)** represents how many seconds of audio are processed per second. An RTF of 3.63 means 1 second of inference handles 3.63 seconds of speech.

## Key Findings

- **Intel Arc iGPU is the Best Performer for Quality**: For the `small` model (which offers significantly better transcription quality than `tiny/base`), the **Intel Arc GPU is ~60% faster than the CPU**, achieving an RTF of **3.63**.
- **PyTorch CPU Efficiency for Small Models**: Surprisingly, for the smallest model (`tiny`), the standard PyTorch CPU implementation was slightly faster than the OpenVINO backends due to the lower graph initialization and memory copy overhead.
- **NPU Limitations**: The NPU (Intel AI Boost) was detected but currently lacks support for the dynamic input shapes used by the `model.generate()` method in Whisper's standard OpenVINO implementation. Update drivers and using static padding might enable this in the future.
- **CPU Scaling**: Standard OpenVINO CPU scaling was less efficient than PyTorch's optimized internal kernels for this specific workload.

## Recommendations for Voicebox Backend

1. **Default to OpenVINO iGPU for `base` and `small` models**: This offloads intensive computations from the CPU, keeping the system responsive while providing superior transcription speed.
2. **Use PyTorch CPU for users on low-end systems or for `tiny` model usage**: The overhead of OpenVINO isn't worth it for the smallest model size.
3. **Optimized Configuration**: The current implementation of `OVModelForSpeechSeq2Seq.from_pretrained(model_id, device="GPU")` is highly effective when paired with pre-exported IR files to eliminate the 30-40s "First Export" delay.

---
*Created by Antigravity on 2026-03-28*
