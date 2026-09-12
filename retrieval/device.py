"""Where the models run.

One place, because three modules -- embed, rerank, translate -- all have to
agree, and one of them getting it wrong fails quietly: the model lands on a
device that isn't there and either dies at first use or runs at a fraction of
the speed you think it's running at.

The reason this isn't simply `torch.cuda.is_available()` is ZeroGPU. On a
ZeroGPU Space, `import spaces` monkey-patches `torch.cuda.*` in the main web
process so module-scope `.to("cuda")` works *without* a GPU attached --
meaning `torch.cuda.is_available()` answers True in a process that has no GPU.
Naari AI runs CPU-resident on that hardware on purpose: a free HF account
can't host a Gradio Space on `cpu-basic` (that needs PRO), so the Space sits
on `zero-a10g` with a single no-op `@spaces.GPU` function and all the real
work outside it. Nothing ever requests a GPU, so no ZeroGPU quota is burned --
but it does mean the patched answer has to be ignored.
"""

import os


def force_cpu() -> bool:
    """True when we must ignore torch's answer and stay on CPU.

    `SPACES_ZERO_GPU` is set only on ZeroGPU hardware, so this is
    self-configuring there. `NAARI_FORCE_CPU` is the manual override for
    anywhere else that needs it.
    """
    if os.getenv("SPACES_ZERO_GPU"):
        return True
    return os.getenv("NAARI_FORCE_CPU", "").strip().lower() in ("1", "true", "yes")


def device() -> str:
    if force_cpu():
        return "cpu"
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def use_fp16() -> bool:
    """fp16 only when there's a real GPU to run it on.

    FlagEmbedding applies `use_fp16` unconditionally (`if self.use_fp16:
    self.model.half()` -- no device check), and x86 has no native fp16
    kernels, so torch upcasts per operation. On CPU that makes half precision
    *slower* than fp32 while saving memory we'd rather spend than pay latency
    for.
    """
    return device() == "cuda"
