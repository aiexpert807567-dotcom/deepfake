# Private AI Face Studio

A private, consent-based, $0-infrastructure AI creative studio for high-fidelity face transformations on images and short videos (up to 30s) using free Kaggle GPU sessions.

## Architecture
- **Frontend**: Next.js 14, Tailwind CSS (Dark theme, 11-step wizard, face detection selector, comparison slider)
- **Backend**: FastAPI, Async file streaming, FFmpeg metadata analysis, JWT & worker security
- **GPU Worker**: PyTorch / CUDA worker with ArcFace multi-reference aggregation, Reinhard color transfer, feathered occlusion masks, temporal EMA stabilization, and GFPGAN face restoration
- **GPU Cloud**: Free Kaggle GPU sessions (NVIDIA T4 / P100)

## Quick Start
1. Run backend & frontend: `docker compose up -d`
2. Access Web UI at `http://localhost:3000` (Default: admin / admin123456)
3. Start the worker by running `worker/kaggle/start_worker.ipynb` in a free Kaggle GPU notebook.
