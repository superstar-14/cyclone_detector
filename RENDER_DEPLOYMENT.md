# 🚀 Deploying IMD Cyclone Detector to Render (Free Tier Guide)

This project has been refactored and optimized specifically for **Render's Free Plan** (512 MB RAM limit, 0.1 vCPU).

---

## ⚡ Key Optimizations Implemented for the 512MB Limit

| Area | Before | After (Optimized) | Impact on Free Plan |
| :--- | :--- | :--- | :--- |
| **Active Memory** | 350 MB - 600 MB+ | **~55 MB - 65 MB** | **>440 MB headroom** under the 512 MB cap |
| **Worker Count** | Unconstrained / Multi-worker | **1 Worker (`--workers 1`)** | Avoids duplicating memory per worker process |
| **Concurrency Safeguard** | Unlimited | **`--limit-concurrency 50`** | Prevents RAM spikes during sudden request bursts |
| **Socket Timeout** | 65s (default) | **`--timeout-keep-alive 5`** | Drops idle sockets quickly to free OS buffers |
| **Thread Pool** | 32-40 threads (default) | **4 threads (`ThreadPoolExecutor`)** | Saves ~30-50MB stack memory |
| **Dependencies** | Included PyTorch, GDAL, GeoPandas | **Lean wheels only** (Moved heavy ML to `requirements-full.txt`) | Build time drops from 15 min to **~45 seconds** |
| **Architecture** | Required 2 separate services | **Unified Single-Service SPA** | FastAPI serves both API & React UI on 1 free service |

---

## 🛠️ Deployment Methods

### Option 1: Render Blueprint (Easiest - 1 Click)

1. Push your repository to GitHub / GitLab.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** > **Blueprint**.
3. Select your repository.
4. Render will automatically read [`render.yaml`](file:///d:/Cyclone_Predictor/render.yaml) and configure the build and start commands with zero manual setup.
5. Click **Apply**.

---

### Option 2: Manual Web Service Deployment (Native Python)

1. In Render Dashboard, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `cyclone-detector`
   - **Region**: Any (e.g. *Oregon* or *Singapore*)
   - **Branch**: `main` (or your feature branch)
   - **Runtime**: `Python`
   - **Build Command**:
     ```bash
     chmod +x ./build.sh && ./build.sh
     ```
   - **Start Command**:
     ```bash
     chmod +x ./start.sh && ./start.sh
     ```
   - **Instance Type**: `Free` (0.1 CPU, 512 MB RAM)

4. Under **Advanced** > **Environment Variables**, add:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `APP_ENV` | `production` | Production mode |
   | `DEMO_MODE` | `true` | Enables in-memory historical & demo storms |
   | `PYTHONUNBUFFERED` | `1` | Real-time console logs |
   | `LOG_LEVEL` | `INFO` | Minimal logging overhead |

5. Under **Health Check Path**, enter:
   ```
   /healthz
   ```
6. Click **Create Web Service**.

---

### Option 3: Manual Docker Deployment

If you prefer deploying with Docker:
1. In Render Dashboard, select **Runtime**: `Docker`.
2. Leave Dockerfile path as `./Dockerfile`.
3. Set **Health Check Path** to `/healthz`.
4. Click **Create Web Service**.

---

## 🔍 Verification & Health Checking

Once deployed, Render will provide a live URL (e.g., `https://cyclone-detector.onrender.com`):

- **Web Application Dashboard**: `https://<your-app>.onrender.com/`
- **Satellite Timeline**: `https://<your-app>.onrender.com/satellite`
- **Active Storms API**: `https://<your-app>.onrender.com/api/storms/active`
- **Health Check Probe**: `https://<your-app>.onrender.com/healthz`
- **Interactive API Docs**: `https://<your-app>.onrender.com/docs`

---

## 💡 Notes on Render Free Tier Behavior
- **Cold Starts**: On the free plan, Render spins down web services after 15 minutes of inactivity. When a new request arrives, it may take 30-50 seconds to wake up.
- **Zero-Downtime Health Checks**: Render queries `GET /healthz` during deploy swaps to ensure the service is ready before routing traffic.
