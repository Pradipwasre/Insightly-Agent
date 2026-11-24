# Docker Guide: Learn Docker Through Insightly Lite

> This guide explains Docker step by step, using a real project called **Insightly Lite**.
> Read it from top to bottom. Each part builds on the one before it.

---

## Table of Contents

1. [Why Docker Exists](#1-why-docker-exists)
2. [The 4 Key Words](#2-the-4-key-words)
3. [How Docker Is Used in Insightly Lite](#3-how-docker-is-used-in-insightly-lite)
4. [The Dockerfile, Line by Line](#4-the-dockerfile-line-by-line)
5. [The docker-compose.yml File, Block by Block](#5-the-docker-composeyml-file-block-by-block)
6. [Useful Commands](#6-useful-commands)
7. [Commands and Their Output](#7-commands-and-their-output)
8. [Summary](#8-summary)
9. [Practice Tasks](#9-practice-tasks)

---

## 1. Why Docker Exists

### The problem: "It works on my laptop!"

Imagine you build a Python app. Your laptop has:

- Python 3.12
- pandas version 3.1
- macOS

Your friend runs the same code. Their laptop has:

- Python 3.9
- an older pandas version
- Windows

**Result:** the app crashes.

The same thing happens with servers. The app works on the developer's laptop but fails on the production server, because the two machines are set up differently.

### The old solution: Virtual Machines (VMs)

A Virtual Machine is a full computer running inside your computer. It has its own operating system, its own RAM and its own disk.

It works, but it has problems:

- **Heavy.** Every VM contains a full operating system, which is several GB.
- **Slow.** A VM takes minutes to start.
- **Limited.** Most laptops can only run 2 or 3 VMs at the same time.

### The new solution: Docker (2013)

In 2013, **Solomon Hykes** showed the first demo of Docker at the PyCon conference. He built it inside his company, **dotCloud**.

The idea was simple:

> Do not copy the whole computer. Pack only the app and the things it needs into a **container**. All containers share the core of the operating system (the kernel).

### The shipping container idea

```
  Before containers                  After containers
  -----------------                  ----------------
  Ship carries sacks, boxes,         Ship carries identical steel boxes.
  drums. Every shape is different.   A crane lifts them, a truck carries
  Loading is hard and slow.          them, a train carries them.
                                     What is inside does not matter.
```

Real shipping containers changed world trade because the box is **standard**. Docker did the same for software. A Python app, a Java app or a database all look the same from outside: a container. And a container runs the same way everywhere.

### VM vs Container

| | Virtual Machine | Docker Container |
|---|---|---|
| What is inside | Full operating system + app | Only the app + its libraries |
| Size | Several GB | A few hundred MB |
| Start time | Minutes | Seconds |
| How many can run on one laptop | 2 to 4 | Dozens |

### Docker today

Docker is now the industry standard. Companies like Netflix, Spotify and Uber use containers. Tools like Kubernetes are also built on top of containers.

---

## 2. The 4 Key Words

You do not need to learn all of Docker. For this project, you only need **4 ideas**.

```
   Dockerfile  ──build──►  Image  ──run──►  Container
   (the recipe)            (packed food     (food heated up
                            in the freezer)  and served on a plate)

   docker-compose.yml = the full restaurant order
                        (which containers, which ports, in which order)
```

| Word | Simple meaning | What it does |
|---|---|---|
| **Dockerfile** | The recipe | A text file that says: which Python to use, which libraries to install, which code to copy, which command to run. |
| **Image** | The packed box | The ready package made by following the recipe. You can take it anywhere and it runs the same. It is read only and does not change. |
| **Container** | The running box | When you run an image, it becomes a container. One image can create many containers. |
| **docker-compose.yml** | The manager | When you have more than one container (this project has 2), Compose starts them all together with the right settings. |

### A helpful comparison

If you know Object Oriented Programming:

> **Image = Class**
> **Container = Object**

One class can create many objects. One image can create many containers.

---

## 3. How Docker Is Used in Insightly Lite

### Project structure

```
insightly-lite/
├─ app/                 ← FastAPI + AI agents (backend)
├─ ui/                  ← Streamlit web app (frontend)
├─ tests/, evals/       ← testing
├─ data/                ← shop.db, memory.db (database files)
├─ data files/          ← CSV files (the raw data)
├─ requirements.txt     ← list of Python libraries
├─ .env                 ← API keys (secret!)
├─ Dockerfile           ← the recipe
├─ docker-compose.yml   ← the manager
└─ .dockerignore        ← what must NOT go into the image
```

### Running the project without Docker

You would need to:

1. Install the correct Python version (3.12).
2. Create a virtual environment.
3. Install 13 libraries with the correct versions.
4. Start FastAPI in one terminal.
5. Start Streamlit in a second terminal.
6. Make sure the UI knows where the API is running.
7. Use different commands on Windows and on Mac.

Many people get stuck at step 3.

### Running the project with Docker

```bash
docker compose up --build
```

**That is it. One command.** It works the same on Windows and Mac.

### The big picture

This diagram is the most important part of the guide.

```
  Your Laptop (Mac / Windows)
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │   Browser                                                │
  │   localhost:8501 ──────┐        localhost:8000 ───┐      │
  │                        │                          │      │
  │  ┌─────────────────────┼── Docker ────────────────┼───┐  │
  │  │                     ▼                          ▼   │  │
  │  │  ┌──────────────────────┐   ┌──────────────────┐  │  │
  │  │  │  Container: "ui"     │   │ Container: "api" │  │  │
  │  │  │  Streamlit  :8501    │──►│ FastAPI   :8000  │──┼──┼──► Anthropic API
  │  │  │                      │   │ + LangGraph agents│  │  │   (internet)
  │  │  └──────────────────────┘   └────────┬─────────┘  │  │
  │  │   http://api:8000  (talk by name)    │            │  │
  │  └──────────────────────────────────────┼────────────┘  │
  │                                         │ volumes        │
  │      ./data   ./data files   ./evals ◄──┘ (folders on    │
  │                                           your laptop)   │
  └──────────────────────────────────────────────────────────┘
```

### 5 things to understand from this diagram

1. **Two containers, one image.**
   The `api` and `ui` containers are both made from the same image, `insightly-lite`. Only the start command is different. One runs FastAPI, the other runs Streamlit.

2. **Ports are doors.**
   Inside the container, the app listens on port 8000 or 8501. Docker connects that door to a port on your laptop. That is why `localhost:8501` opens in your browser.

3. **Containers talk to each other by name.**
   The UI container finds the API at `http://api:8000`. Here `api` is the service name. Docker creates a small private network where the name works as the address.

4. **Volumes are shared folders.**
   When a container is deleted, everything inside it is lost. But the database (`shop.db`) and chat history (`memory.db`) must survive. So the `data/` folder lives on your laptop, and the container only "mounts" it.

5. **The secret key never goes into the image.**
   The `.env` file is read when the container starts. It is not copied into the image. So even if you share the image, your API key stays safe.

---

## 4. The Dockerfile, Line by Line

The whole Dockerfile is only **9 lines** long:

```dockerfile
FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY ui ./ui
COPY tests ./tests
COPY evals ./evals
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `FROM python:3.12-slim`

**Where do we start?** From a ready-made image that already has Linux and Python 3.12 installed. It comes from Docker Hub, which is like an app store for images.

- `slim` means a smaller version without extra tools. The image stays light.
- **Benefit:** it does not matter which Python is on your laptop. The container always has 3.12.

### `WORKDIR /code`

Create a folder called `/code` inside the container and move into it. All the next commands run here.

Think of it as: "This is our counter in the kitchen."

### `COPY requirements.txt .`

Take `requirements.txt` from your laptop and put it in `/code/` inside the container. The `.` means "the current folder", which is `/code`.

### `RUN pip install --no-cache-dir -r requirements.txt`

Install all the libraries: FastAPI, LangGraph, langchain-anthropic, pandas, plotly, streamlit and others.

- `RUN` runs **while the image is being built** (only once).
- `--no-cache-dir` tells pip not to keep its download cache, so the image stays smaller.

### Why copy `requirements.txt` first, and the code later?

> **Question:** Why did we copy only `requirements.txt` first, and not all the code at once?

**Answer: Layer caching.** This is the smartest trick in the Dockerfile.

Docker saves every line as a **layer**. On the next build, any layer that has not changed is reused from the cache. It is not built again.

```
Layer 1: FROM python        ✓ from cache
Layer 2: WORKDIR            ✓ from cache
Layer 3: COPY requirements  ✓ from cache (file did not change)
Layer 4: RUN pip install    ✓ from cache  ← this saves 3 to 4 minutes!
Layer 5: COPY app           ✗ rebuilt (code changed)
```

Code changes every day. Libraries change rarely. So libraries go first and code goes after. If the order were reversed, every small code change would trigger a 4 minute `pip install`.

**Real example:** when only `ui/app.py` was changed in this project, the rebuild took a few seconds, because `pip install` came from the cache.

### `COPY app ./app` up to `COPY evals ./evals`

Now copy the project code. Notice what is **not** copied: `data/`, `data files/` and `.env`. The next file explains why.

### `.dockerignore` (the Dockerfile's partner)

```
.env
data
data files
**/__pycache__
*.pyc
*.html
```

This works like `.gitignore`. It says: "Never send these files to the image."

- `.env` is ignored so the API key does not leak into the image.
- `data` and `data files` are ignored because the 700+ MB database and CSV files are not needed in the image. They come in through volumes instead.

### `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

**What should run when the container starts?** The FastAPI server.

`CMD` runs **every time the container starts**.

### `RUN` vs `CMD`

| | `RUN` | `CMD` |
|---|---|---|
| When it runs | While **building** the image | When the container **starts** |
| How many times | Once | On every start |
| Example | `pip install` | `uvicorn ...` |

### Why `--host 0.0.0.0`?

It means: "Accept requests from outside the container, not only from inside."

If you write `127.0.0.1` instead, your browser will never be able to connect. This is a very common beginner mistake.

---

## 5. The docker-compose.yml File, Block by Block

```yaml
services:
  api:                                           # FastAPI + the agents
    build: .
    image: insightly-lite
    ports:
      - "${API_PORT:-8000}:8000"
    env_file:
      - path: .env
        required: false
    volumes:
      - ./data:/code/data
      - "./data files:/code/data files:ro"
      - ./evals:/code/evals
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 10s
      retries: 3
      start_period: 600s

  ui:                                            # Streamlit web app
    build: .
    image: insightly-lite
    command: streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "${UI_PORT:-8501}:8501"
    environment:
      API_URL: http://api:8000
      STREAMLIT_BROWSER_GATHER_USAGE_STATS: "false"
      STREAMLIT_THEME_BASE: light
      STREAMLIT_THEME_PRIMARY_COLOR: "#C96442"
      ...
    depends_on:
      api:
        condition: service_healthy
```

> **Remember:**
> The **Dockerfile** says **how to build one box**.
> **Compose** says **how many boxes, how they connect, and how they run**.

### `services:`

The list of containers. There are two services: `api` and `ui`.

### `build: .` and `image: insightly-lite`

- `build: .` means "build the image using the Dockerfile in this folder."
- `image: insightly-lite` means "name that image `insightly-lite`."
- Both services use the same image name, so the image is **built once and used twice**.

### `ports: - "${API_PORT:-8000}:8000"`

The format is **`LAPTOP_PORT : CONTAINER_PORT`**.

```
   Laptop :8000  ────────►  Container :8000
   (outside door)           (inside door)
```

`${API_PORT:-8000}` means: "If a variable called `API_PORT` is set, use it. Otherwise use 8000."

**When is this useful?** When another app on your laptop is already using port 8000:

```bash
API_PORT=8100 UI_PORT=8601 docker compose up
```

Everything inside the container stays the same. Only the outside door changes.

### `env_file: .env` (with `required: false`)

All variables in the `.env` file (like `ANTHROPIC_API_KEY` and `LLM_MODEL`) are added to the container's environment.

- They are loaded **at runtime**, not stored in the image. So the key stays safe.
- `required: false` means "do not crash if the `.env` file is missing."
- **Benefit:** to change the model, edit `LLM_MODEL` in `.env` and restart the container. No rebuild is needed.

### `volumes:` (the most important idea)

```yaml
- ./data:/code/data                       # database
- "./data files:/code/data files:ro"      # CSV files, read only
- ./evals:/code/evals                     # eval results
```

The format is **`LAPTOP_FOLDER : CONTAINER_FOLDER`**.

> **Question:** If there is no volume and the container is deleted, what happens to the database?
>
> **Answer:** It is **gone**. Data inside a container is temporary.

With volumes:

- `shop.db` (740 MB) is built from the CSV files on the first start. This takes a few minutes. It is saved in the `data/` folder on your laptop, so the next start takes only seconds.
- `memory.db` holds the chat history. Chats survive even after `docker compose down`.
- `:ro` means **read only**. The container can read the CSV files but cannot change or delete them. This keeps the raw data safe.
- `evals` results are written inside the container but appear directly in the folder on your laptop.

### `healthcheck:`

Every 10 seconds, Docker asks the API: "Are you alive?" It does this by calling the `/health` endpoint.

- `retries: 3` means 3 failures in a row mark the container as "unhealthy".
- `start_period: 600s` means "ignore failures during the first 10 minutes." This is because building `shop.db` on the first start takes time, and the API is not ready until it is done.

### What is different about the `ui` service?

- **`command:`** replaces the Dockerfile's `CMD`. Instead of uvicorn, it runs Streamlit. Same image, different job.
- **`environment: API_URL: http://api:8000`** tells the UI where the API is. `api` is the service name, and Docker's internal DNS sends it to the right container.

> **Question:** Why not write `localhost:8000` here?
>
> **Answer:** Inside the UI container, `localhost` means the UI container itself. The API lives in a different container, so we must use its name.

- **`STREAMLIT_THEME_...`** sets the UI colors through environment variables instead of hardcoding them in the code.

### `depends_on: condition: service_healthy`

This means: "Start the UI only after the API is **healthy**." Without it, the UI would open and show "API offline".

If you only wrote `depends_on: [api]`, Docker would wait for the API container to *start*, not to be *ready*. `service_healthy` waits until it is actually ready.

### Quick recap

> **Dockerfile** = the recipe for one box.
> **Compose** = two boxes, their doors (ports), their shared folders (volumes), their secrets (env), and who starts first (depends_on).

---

## 6. Useful Commands

### Command cheat sheet

| When to use it | Command |
|---|---|
| First time, or after changing the Dockerfile, requirements or code | `docker compose up --build` |
| Run in the background (keep the terminal free) | `docker compose up -d` |
| Rebuild only one service (for example, after a UI change) | `docker compose up --build -d ui` |
| See what is running | `docker compose ps` |
| Read logs (to find errors) | `docker compose logs -f api` |
| Run a command inside a container | `docker compose exec api python tests/backtest.py` |
| Open a shell inside a container | `docker compose exec api bash` |
| Restart after changing `.env` | `docker compose restart api` |
| Stop and remove everything | `docker compose down` |
| List images | `docker images` |
| List all running containers (from any project) | `docker ps` |
| See how much disk Docker uses | `docker system df` |
| Clean up old, unused images and containers | `docker system prune` |

### 3 common situations

**1. "I changed my code, but I do not see the change!"**

The code is copied into the image. Your image is old. Run:

```bash
docker compose up --build
```

**2. "I changed the model in `.env`."**

`.env` is read at runtime. Run:

```bash
docker compose up -d
```

Compose notices the config changed and recreates the container. No rebuild is needed.

**3. "Port already in use" error.**

Another app is using port 8000. Run:

```bash
API_PORT=8100 docker compose up
```

### `stop` vs `down` (a common interview question)

| Command | What happens | How to bring it back |
|---|---|---|
| `docker compose stop` | Containers pause. They are **not** deleted. | `docker compose start` |
| `docker compose down` | Containers and network are **deleted**. Data in volumes is **safe** because it lives on your laptop. | `docker compose up` |

---

## 7. Commands and Their Output

> **Note:** The outputs below are samples. On your machine, the IDs, times and sizes will be different. Do not try to match the exact numbers. Focus on the pattern.

### 7.1 Check that Docker is installed

```bash
docker --version
```

```
Docker version 28.x.x, build abc1234
```

```bash
docker compose version
```

```
Docker Compose version v2.x.x
```

If you get an error, Docker Desktop is probably not open. Start it first.

---

### 7.2 Start the project

```bash
cd ~/Desktop/insightly-lite
docker compose up --build
```

```
[+] Building 4.2s (14/14) FINISHED
 => [internal] load build definition from Dockerfile                    0.0s
 => [internal] load .dockerignore                                       0.0s
 => [1/8] FROM docker.io/library/python:3.12-slim                       0.0s
 => CACHED [2/8] WORKDIR /code                                          0.0s
 => CACHED [3/8] COPY requirements.txt .                                0.0s
 => CACHED [4/8] RUN pip install --no-cache-dir -r requirements.txt     0.0s
 => [5/8] COPY app ./app                                                0.1s
 => [6/8] COPY ui ./ui                                                  0.0s
 => [7/8] COPY tests ./tests                                            0.0s
 => [8/8] COPY evals ./evals                                            0.0s
 => exporting to image                                                  0.2s
[+] Running 3/3
 ✔ Network insightly-lite_default  Created                              0.1s
 ✔ Container insightly-lite-api-1  Healthy                             12.3s
 ✔ Container insightly-lite-ui-1   Started                             12.5s
api-1  | INFO:     Started server process [1]
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
ui-1   |   You can now view your Streamlit app in your browser.
ui-1   |   URL: http://0.0.0.0:8501
```

**How to read this output:**

| What you see | What it means |
|---|---|
| `[1/8] ... [8/8]` | The 8 build steps from the Dockerfile. (`CMD` does not run during the build, so it is not counted.) |
| `CACHED` | Layer caching in action. `pip install` took 0.0s because `requirements.txt` did not change. |
| `Network ... Created` | Compose created a private network for both containers. This is why `http://api:8000` works. |
| `api-1 Healthy`, then `ui-1 Started` | `depends_on: service_healthy` in action. The UI waited for the API. |
| `insightly-lite-api-1` | Container names follow the pattern `project-service-number`. |

On the very first run (no cache), the build takes 3 to 5 minutes, and you will also see `shop.db` being built:

```
api-1  | Building shop.db from 7 CSV files in 'data files' (first start only)...
api-1  |   loaded distribution_centers: 10 rows
api-1  |   loaded events: 2,427,931 rows
api-1  |   ...
api-1  | shop.db ready in 157s
```

Now open the app in your browser: **http://localhost:8501**

---

### 7.3 See what is running

```bash
docker compose ps
```

```
NAME                   IMAGE            COMMAND                  SERVICE   STATUS                   PORTS
insightly-lite-api-1   insightly-lite   "uvicorn app.main:ap…"   api       Up 2 minutes (healthy)   0.0.0.0:8000->8000/tcp
insightly-lite-ui-1    insightly-lite   "streamlit run ui/ap…"   ui        Up 2 minutes             0.0.0.0:8501->8501/tcp
```

**What to notice:**

- Both use the same `IMAGE`: `insightly-lite`.
- The `COMMAND` is different: uvicorn vs streamlit (`CMD` vs the `command:` override).
- `(healthy)` means the healthcheck passed.
- `0.0.0.0:8000->8000/tcp` is the port mapping: laptop port 8000 goes to container port 8000.

---

### 7.4 Check the API health

```bash
curl localhost:8000/health
```

```json
{"status":"ok","provider":"anthropic","model":"claude-haiku-5-5",
 "tables":["distribution_centers","events","inventory_items","order_items","orders","products","users"]}
```

`provider: anthropic` comes from the `.env` file. It is not hardcoded anywhere in the image.

---

### 7.5 Read the logs

```bash
docker compose logs -f api
```

```
api-1  | INFO:     172.18.0.3:54122 - "GET /health HTTP/1.1" 200 OK
api-1  | INFO:     172.18.0.3:54130 - "GET /threads HTTP/1.1" 200 OK
api-1  | INFO:     172.18.0.3:54144 - "POST /chat HTTP/1.1" 200 OK
api-1  | INFO:     127.0.0.1:41870 - "GET /health HTTP/1.1" 200 OK
```

**What to notice:**

- `172.18.0.3` is the IP of the UI container on Docker's private network. You can see the UI talking to the API.
- `127.0.0.1 ... /health` every 10 seconds is the healthcheck. The API is checking itself.
- `-f` means "follow". The logs keep streaming. Press `Ctrl+C` to exit. The container keeps running.

**Try it:** ask a question in the UI, such as "What was net revenue in 2023?", and watch a new `POST /chat` line appear in the logs.

---

### 7.6 Run tests inside the container

```bash
docker compose exec api python tests/backtest.py
```

```
PASS distribution_centers: 10 rows (csv has 10)
PASS events: 2,427,931 rows (csv has 2,427,931)
PASS orders: 125,530 rows (csv has 125,530)
...
PASS blocked: DELETE FROM orders
PASS blocked: DROP TABLE users
...
PASS memory keeps the last 6 turns, starting at a question

29 passed, 0 failed
```

`exec` runs a command inside a running container. Python, the libraries and the database are all already inside. Nothing was installed on your laptop.

---

### 7.7 Open a shell inside the container

```bash
docker compose exec api bash
```

```
root@3f2a9c1b7d4e:/code# ls
app  data  data files  evals  requirements.txt  tests  ui
root@3f2a9c1b7d4e:/code# python --version
Python 3.12.x
root@3f2a9c1b7d4e:/code# cat /etc/os-release | head -1
PRETTY_NAME="Debian GNU/Linux ..."
root@3f2a9c1b7d4e:/code# exit
```

**This is the most interesting part. Notice:**

- The prompt shows `/code`. That is `WORKDIR /code`.
- Python is 3.12. That comes from `FROM python:3.12-slim`, no matter which Python your laptop has.
- The operating system is **Debian Linux**, even if your laptop runs Mac or Windows. There is a small Linux inside the container.
- `3f2a9c1b7d4e` is the container ID.
- The `.env` file is not there, because `.dockerignore` blocked it. But its variables are in the environment. Try `echo $LLM_MODEL`.

---

### 7.8 List images

```bash
docker images
```

```
REPOSITORY       TAG       IMAGE ID       CREATED          SIZE
insightly-lite   latest    8b1e4c2d9f07   10 minutes ago   1.1GB
python           3.12-slim a3f5e7c91b2d   2 weeks ago      150MB
```

- `python:3.12-slim` is the base image (from `FROM`), downloaded from Docker Hub.
- `insightly-lite` is our image: the base image plus libraries plus code.
- Most of the size comes from the libraries (pandas, plotly, streamlit and others). The database is not in the image. It is in a volume. Otherwise the image would be about 700 MB bigger.

---

### 7.9 Check disk usage

```bash
docker system df
```

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          2         1         1.25GB    150MB (12%)
Containers      2         2         2.1MB     0B (0%)
Local Volumes   0         0         0B        0B
Build Cache     18        0         420MB     420MB
```

- The containers are only about 2 MB. A container is just the image plus a thin extra layer. This is why Docker is so efficient.
- `Local Volumes 0` is because this project uses **bind mounts** (folders on your laptop), not **named volumes**. That is why the data shows up directly in your `data/` folder.

---

### 7.10 Restart after changing `.env`

```bash
docker compose restart api
```

```
[+] Restarting 1/1
 ✔ Container insightly-lite-api-1  Started                              1.8s
```

---

### 7.11 Stop everything

```bash
docker compose down
```

```
[+] Running 3/3
 ✔ Container insightly-lite-ui-1   Removed                              1.2s
 ✔ Container insightly-lite-api-1  Removed                              0.9s
 ✔ Network insightly-lite_default  Removed                              0.2s
```

**What to notice:**

- The UI stopped first and the API stopped second. This is the reverse of the `depends_on` order.
- The containers and the network were deleted. But check the data folder:

```bash
ls data/
```

```
memory.db   shop.db
```

**The data is safe!** Run `docker compose up` again and your old chats appear in the sidebar. This is the power of volumes.

---

## 8. Summary

Remember these 5 points:

| # | Idea | In one line |
|---|---|---|
| 1 | **Dockerfile → Image → Container** | Recipe → packed box → running box |
| 2 | **Layer caching** | What did not change is not rebuilt. That is why requirements go first and code goes after. |
| 3 | **Compose** | The manager for many containers: ports, volumes, env, depends_on |
| 4 | **Volumes** | Data lives outside the container, on your laptop. The container can die, the data lives on. |
| 5 | **`.env` + `.dockerignore`** | Secrets never go into the image. |

> Insightly Lite has FastAPI, LangGraph, Streamlit, 13 libraries and a 700 MB database.
> Yet it starts with just one command: `docker compose up`.
>
> **That is Docker:** from *"It works on my laptop"* to *"It works on every laptop."*

---

## 9. Practice Tasks

1. **Change the model.**
   In `.env`, set `LLM_MODEL=claude-sonnet-5-5`. Run `docker compose up -d`. Then open `/health` and check that the model has changed.

2. **Change the UI port.**
   Run `UI_PORT=9000 docker compose up -d` and open the app at `localhost:9000`.

3. **See layer caching yourself.**
   Change the title in `ui/app.py`. Then run `docker compose up --build -d ui`. In the build output, check which layers say `CACHED` and which do not.

4. **Think about it.**
   What happens if you remove `./data:/code/data` from `volumes`?

   <details>
   <summary>Show answer</summary>

   `shop.db` will be rebuilt from the CSV files on every start, which takes minutes. And the chat history will disappear every time the container is removed.

   </details>
