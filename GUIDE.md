# Tiny Shop: step-by-step guide (for total beginners)

You don't need to know anything yet. Do one step at a time, and don't move on until the step works.
Everything here is **free** and runs on your own laptop.

---

## Step 0: What you're building (read this first, 5 minutes)

You're building a tiny online store and running it the way real companies run their apps.

| Word | What it means in plain English |
|---|---|
| **Container** | Your app packed in a box with everything it needs, so it runs the same on any computer. |
| **Docker** | The tool that builds and runs containers. |
| **Image** | The "recipe" for a container. A `Dockerfile` describes how to build it. |
| **Kubernetes (K8s)** | A manager that runs many containers, restarts them if they crash, and adds more when traffic is high. |
| **Cluster** | A group of computers Kubernetes manages. Here it's just your laptop, using a tool called **kind**. |
| **Pod** | One running copy of a container inside Kubernetes. |
| **Deployment** | Tells Kubernetes "keep 2 copies of my API running at all times". |
| **Service** | Gives pods a fixed name (like `api`) so other pods can find them. |
| **Autoscaler (HPA)** | Adds more pods when they get busy, removes them when quiet. |
| **Prometheus** | Collects numbers about your app (requests, speed). |
| **Grafana** | Draws those numbers as dashboards. |
| **CI/CD** | GitHub automatically tests and builds your code every time you push. |

The app has 3 parts:

```
Browser ──> frontend (web page, nginx) ──> api (Python) ──> redis (database)
```

Folder map:

```
api/            Python API code + its Dockerfile + tests
frontend/       The web page + its Dockerfile
k8s/            Kubernetes files (one per part of the app)
k8s/monitoring/ Monitoring and load-test files
.github/        The automatic CI pipeline
docker-compose.yml  Runs everything with Docker only (Step 2)
kind-config.yaml    Creates your laptop Kubernetes cluster (Step 3)
```

---

## Step 1: Install the tools (about 30 minutes, one time)

You need about **8 GB of RAM**. Close Chrome tabs while doing this.

1. **Docker Desktop**: https://www.docker.com/products/docker-desktop/ (free for students)
   - **Windows:** it will ask to turn on **WSL 2**. Say yes and restart. Run all the commands below in the **Ubuntu (WSL)** terminal.
   - After installing, open Docker Desktop and leave it running.
2. **kubectl** (talks to Kubernetes): https://kubernetes.io/docs/tasks/tools/
3. **kind** (Kubernetes on your laptop): https://kind.sigs.k8s.io/docs/user/quick-start/#installation
4. **Helm** (installs ready-made apps into Kubernetes): https://helm.sh/docs/intro/install/
5. **Git**: https://git-scm.com/downloads

Check everything works. Each command should print a version, not an error:

```bash
docker --version
kubectl version --client
kind version
helm version
git --version
```

---

## Step 2: Run the app with just Docker (about 10 minutes)

Open a terminal **inside the `tiny-shop` folder** and run:

```bash
docker compose up --build
```

The first time takes a few minutes. When the logs calm down, open **http://localhost:8080**.
You should see the shop. Click **Buy**, and an order appears. 🎉

Stop it with `Ctrl+C`, then run `docker compose down`.

**What just happened:** Docker built two images (`api` and `frontend`) from their Dockerfiles, downloaded Redis, and connected all three.

---

## Step 3: Create your Kubernetes cluster

```bash
kind create cluster --config kind-config.yaml
kubectl get nodes
```

You should see one node called `tiny-shop-control-plane` with status `Ready` (it can take a minute).

---

## Step 4: Deploy the shop to Kubernetes

```bash
# 1. Build the images
docker build -t tiny-shop-api:local ./api
docker build -t tiny-shop-frontend:local ./frontend

# 2. Copy them into the kind cluster
kind load docker-image tiny-shop-api:local tiny-shop-frontend:local --name tiny-shop

# 3. Tell Kubernetes to run everything in the k8s folder
kubectl apply -f k8s/

# 4. Watch the pods start (press Ctrl+C when all say Running)
kubectl get pods -n tiny-shop -w
```

Open **http://localhost:8080** again. Refresh a few times and look at **"Served by pod"**: the name changes, because 2 API pods are sharing the work.

Open the files in `k8s/` and read the comments. Each file is one part of the app.

---

## Step 5: Show off self-healing

Kubernetes keeps your app alive even if something crashes. Try it:

```bash
kubectl get pods -n tiny-shop
kubectl delete pod -n tiny-shop -l app=api      # "crash" all API pods
kubectl get pods -n tiny-shop -w                # new ones appear in seconds
```

📸 Screenshot this for your report. It's the main reason companies use Kubernetes.

---

## Step 6: Autoscaling (add pods automatically under load)

The autoscaler needs a small helper called metrics-server:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# kind needs this extra setting for metrics-server to work
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

Wait a minute, then start fake traffic and watch:

```bash
kubectl apply -f k8s/monitoring/load-test.yaml
kubectl get hpa -n tiny-shop -w
```

After 1 or 2 minutes, `REPLICAS` goes up from 2 toward 6. 📸 Screenshot it.
Stop the traffic and it scales back down after about 5 minutes:

```bash
kubectl delete -f k8s/monitoring/load-test.yaml
```

---

## Step 7: Monitoring dashboards (Prometheus + Grafana)

This needs about 2 GB of extra RAM.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# wait until everything says Running
kubectl get pods -n monitoring -w

# tell Prometheus to collect the shop's metrics
kubectl apply -f k8s/monitoring/servicemonitor.yaml
```

Open Grafana:

```bash
# get the admin password
kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d; echo

# open Grafana at http://localhost:3000 (keep this terminal open)
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

Log in as `admin` with that password.

- Go to **Dashboards** and open **Kubernetes / Compute Resources / Namespace (Pods)**, then pick namespace `tiny-shop`.
- To chart your own app: **Explore**, choose **Prometheus**, and type `sum(rate(shop_requests_total[1m]))`. Run the load test from Step 6 and watch the line go up.
- Save it as your own dashboard. 📸 Screenshot it.

---

## Step 8: Put it on GitHub (this turns on CI/CD)

1. Create a free account at https://github.com and a new **public** repo called `tiny-shop`.
2. In the `tiny-shop` folder:

```bash
git init
git add .
git commit -m "Tiny Shop: Kubernetes microservices project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/tiny-shop.git
git push -u origin main
```

3. Open the **Actions** tab on GitHub. The pipeline runs the tests, starts a real Kubernetes cluster inside GitHub, deploys the shop, checks it works, and publishes the images. It turns green ✅ when done. That green badge is great to show in interviews.

Tip: get the free **GitHub Student Developer Pack** at https://education.github.com/pack

---

## Step 9 (optional): Run it in the real cloud for your demo

Only do this right before your presentation, and **delete it right after**.

- **Azure for Students** ($100 free credit, no credit card): https://azure.microsoft.com/free/students
  Create a 1-node AKS cluster (size `Standard_B2s`), change the image names in `k8s/20-api.yaml` and `k8s/30-frontend.yaml` to your `ghcr.io/...` images from Step 8, and change the frontend Service to `type: LoadBalancer`.
- **Set a budget alert** of $5 in the Azure portal before creating anything.

Ask Claude for help when you get here. It's easy to get stuck on this step.

---

## Cleaning up (free up your laptop)

```bash
kind delete cluster --name tiny-shop
```

---

## When things go wrong

| Problem | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Open Docker Desktop and wait until it says "running". |
| Pods stuck in `ImagePullBackOff` or `ErrImageNeverPull` | You forgot `kind load docker-image ...` in Step 4. Run it again. |
| Pods stuck in `Pending` | Your laptop is out of RAM. Close apps, or skip Step 7. |
| `localhost:8080` doesn't load | Run `kubectl get pods -n tiny-shop`. Every pod must say `Running`. Also check Docker Compose from Step 2 is stopped. |
| HPA shows `<unknown>` | metrics-server isn't ready yet. Wait 2 minutes, and check you ran the `patch` command. |
| Anything else | `kubectl describe pod <pod-name> -n tiny-shop` and `kubectl logs <pod-name> -n tiny-shop` show what's wrong. Paste the output to Claude. |

---

## What to put on your resume

**Tiny Shop: Kubernetes microservices platform** · Docker, Kubernetes, Helm, Prometheus, Grafana, GitHub Actions

- Containerized a 3-tier e-commerce app (Python/Flask API, nginx frontend, Redis) and deployed it to Kubernetes with health checks, resource limits and zero-downtime rolling updates.
- Configured a Horizontal Pod Autoscaler that scaled the API from 2 to 6 pods under load, and showed self-healing by recovering from pod failures automatically.
- Built observability with Prometheus and Grafana, adding custom request, latency and order metrics to the API.
- Built a CI/CD pipeline in GitHub Actions that runs unit tests, deploys to an ephemeral Kubernetes cluster for smoke testing, and publishes images to GitHub Container Registry.
