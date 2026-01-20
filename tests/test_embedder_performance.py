import time

import numpy as np
import torch

from relevance_scoring.embedder import Embedder


def sync():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def run_benchmark(device, batch_size, runs=5):
    texts = [
        "Graph-based retrieval systems improve relevance scoring in scientific search."
        for _ in range(batch_size)
    ]

    emb = Embedder(batch_size=batch_size)
    emb.device = device
    emb.model.to(device)

    # warm-up
    for _ in range(3):
        emb.embed_chunks(texts)
    sync()

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        emb.embed_chunks(texts)
        sync()
        times.append(time.perf_counter() - start)

    avg_time = float(np.mean(times))
    throughput = batch_size / avg_time

    return avg_time, throughput


if __name__ == "__main__":
    batch_sizes = [16, 32, 64, 128, 256, 512]

    print("\n=== Embedder Performance Benchmark ===\n")
    print(
        f"{'Batch':>6} | {'CPU ms':>8} | {'CPU docs/s':>10} | "
        f"{'GPU ms':>8} | {'GPU docs/s':>10} | {'Speedup':>8}"
    )
    print("-" * 78)

    for bs in batch_sizes:
        cpu_time, cpu_tp = run_benchmark("cpu", bs)

        if torch.cuda.is_available():
            gpu_time, gpu_tp = run_benchmark("cuda", bs)
            speedup = gpu_tp / cpu_tp
        else:
            gpu_time, gpu_tp, speedup = float("nan"), float("nan"), float("nan")

        print(
            f"{bs:6d} | "
            f"{cpu_time*1000:8.1f} | {cpu_tp:10.1f} | "
            f"{gpu_time*1000:8.1f} | {gpu_tp:10.1f} | "
            f"{speedup:8.2f}×"
        )

    print("\n=== Environment ===")
    print("Torch:", torch.__version__)
    print("HIP:", torch.version.hip)
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
