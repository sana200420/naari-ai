FROM python:3.11-slim

# Hugging Face Spaces runs the container as UID 1000, never root. Anything
# written at runtime -- the model cache above all -- must be owned by that
# user, or the first weight download fails with a permission error at boot.
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the CPU-only torch build BEFORE requirements.txt, so the ML packages
# there resolve against it instead of pulling the default wheel. The default
# torch on Linux drags in ~3GB of nvidia-* CUDA libraries that a CPU-only host
# can never execute. That is dead weight in the image, and the most likely
# reason every build since requirements.txt gained its ML dependencies
# (892aaa1, 2026-09-01) has failed -- leaving the last *successful* deploy as
# the Phase 0 mock from 27dcd4f.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER user
COPY --chown=user . /app

# Hugging Face Spaces uses port 7860
EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
