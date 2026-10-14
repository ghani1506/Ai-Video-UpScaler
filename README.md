# Clarity AI Video Upscaler — GitHub + Streamlit

A browser interface for local Apple Silicon Mac video enhancement. MP4, AVI and 3GP inputs; MP4 output. AI uses **Real-ESRGAN NCNN Vulkan** (external executable). Includes a non-AI FFmpeg fallback. AI is not guaranteed to run on every macOS/Vulkan installation.

## Run locally (recommended for 16 GB Apple Silicon)

1. Install [Homebrew](https://brew.sh) and run `brew install python@3.12 ffmpeg`.
2. Open Terminal and go to the folder containing `app.py` (e.g. `cd ~/Desktop/clarity-github-streamlit`).
3. Run:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

4. Visit http://localhost:8501.

## Real-ESRGAN AI engine

The Python package does **not** install Real-ESRGAN. Obtain a **macOS-compatible** `realesrgan-ncnn-vulkan` executable and `models/` folder from a trusted release or build the [upstream project](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) for your system. Ensure `realesrgan-x4plus` model files exist in `models/`. On macOS, Vulkan normally requires MoltenVK. Verify with `./realesrgan-ncnn-vulkan -h` and a test image. The executable must have permission to run.

Configure the executable path in the same terminal before launching Streamlit:

```bash
export REALESRGAN_BIN="$HOME/clarity-ai-engine/realesrgan-ncnn-vulkan"
python -m streamlit run app.py
```

Or put the executable in `~/clarity-ai-engine/` alongside its `models/` folder for automatic detection. The app reports exact subprocess errors. If the AI executable cannot be installed, use the **Standard resize** mode (not neural upscaling).

## GitHub workflow

Create a new GitHub repository, upload `app.py`, `requirements.txt`, `.streamlit/config.toml`, `.gitignore`, and `README.md` (not `.venv` or video files). Clone or download the repo to your Mac, then run the commands above. GitHub stores source code, **not the GPU processing service**.

## Streamlit Community Cloud

The UI can be deployed from GitHub to Streamlit Community Cloud, but this does **not** make Apple Silicon / MoltenVK available in the cloud. AI conversion requires a compatible server with the executable, models, sufficient compute, FFmpeg and persistent job capacity. Local Mac hosting is the reliable path for this project. Video uploads and outputs are processed on the machine running Streamlit.

## Notes

- Start with a 5–10 second sample, 1080p, tile size 128.
- AI inference upscales each frame x4 and then resizes to the requested height; output detail is estimated, not recovered.
- Input and output are temporary during conversion; completed MP4 bytes remain in the Streamlit session until it resets.
- Processing long videos can exhaust RAM/disk; do not use a shared public deployment without authentication, quotas and job isolation.
