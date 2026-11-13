# FobSim
This project aims to introduce a reliable Fog-enhanced Blockchain simulation environment, namely FoBSim.

This environment shall facilitate easy simulation for different Fog-Blockchain integration scenarios.

FoBSim is implemented using Python 3.8, and it now features a **Modern Web Dashboard** built with Next.js and FastAPI.

---

### 💎 Web Dashboard (Professional Platform)
The new Next.js dashboard provides a research-grade interface with:
- **Authentication**: Secure Signup/Login for multi-user experiments.
- **Historical Analysis**: Persistent database records for all past runs.
- **Consensus Analytics**: Side-by-side performance comparison charts.
- **Live Monitoring**: Real-time CPU/Process utilization logs.

**How to run (Dashboard):**
1. **Install Backend Dependencies**:
   ```bash
   python3 -m pip install -r api/requirements.txt
   ```
2. **Configure and start the API Server** from the repository root:
   ```bash
   export APP_ENV=development
   export JWT_SECRET_KEY=development-secret
   export FRONTEND_URL=http://localhost:3000
   export DATABASE_URL=sqlite:///./fobsim-local.db
   export PYTHONPATH=.
   ./api/entrypoint.sh
   ```
3. **Start the Frontend**:
   ```bash
   cd frontend && npm run dev
   ```
4. Access at: `http://localhost:3000` (Signup to begin!)

> [!TIP]
> **Remote Access**: If running on a server and accessing from another machine:
> - The API server automatically binds to `0.0.0.0:8000`.
> - Ensure your firewall allows incoming traffic on ports **8000** (API) and **3000** (Frontend).
> - Access the dashboard using the server's IP (e.g., `http://10.64.68.21:3000`).
> - Set `FRONTEND_URL` to that exact frontend origin before starting the API.

### Backend deployment configuration

Build the backend from the repository root:

```bash
docker build -f api/Dockerfile -t fobsim-backend:m1 .
```

The container runs `alembic -c api/alembic.ini upgrade head` from `/app` before
executing `python3 api/server.py` with one Uvicorn worker. A failed migration
stops startup. API startup itself never creates tables; direct server launches
must follow a successful migration. Keep one backend instance while simulation
execution uses process-local state.

Production requires PostgreSQL 13 or newer: the migration uses the built-in
`gen_random_uuid()` function. PostgreSQL 16 is covered by the optional migration test.

Experiment saves/clones and simulation launches enforce the same hosted work
budget: `puzzle_difficulty` is 1–3, total users (fog nodes × users per fog node)
must be at most 500, and total tasks (users × tasks per user) at most 5,000.
Expected blocks are total tasks for Computational Services (function 2), or
`ceil(total tasks / numOfTXperBlock)` for other functions, with a limit of 1,000.
Parallel PoW (consensus 1 with `Parallel_PoW_mining=true`) permits at most 64
expected blocks. Payment/Trading (function 3) requires `Max_enduser_payment >= 1`;
DPoS (consensus 5) requires at least two effective miners in either placement.
Selector-only experiment edits are validated against the saved configuration.

Production is the default `APP_ENV`; Render also declares it explicitly.
Configure `DATABASE_URL` and a strong, randomly generated `JWT_SECRET_KEY` in
your deployment's environment settings. Missing, blank, and known default or
placeholder JWT secrets stop startup. The documented development secret is
accepted only with explicit `APP_ENV=development` or `APP_ENV=test`; tests use
an explicit disposable test secret. Never commit environment files or secrets.
Changing the JWT signing key invalidates previously issued access tokens.

`FRONTEND_URL` must contain exactly one HTTP(S) origin (scheme, hostname, and
optional port), with no trailing slash, path, wildcard, or origin list. It is
the only allowed credentialed CORS origin, including for `PATCH` requests.
Render declares `https://fobsim-frontend.onrender.com`.

Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` in the Render dashboard for welcome
and password-reset emails. `render.yaml` declares these and `JWT_SECRET_KEY`
with `sync: false`, so their values stay outside source control. Without the
email settings, sending is skipped using the existing email behavior.

---

This research work is a part of a paper that is published in the PeerJ-Computer Science journal. The open-access paper can be found at:

https://peerj.com/articles/cs-431/

DOI: 10.7717/peerj-cs.431

IMPORTANT NOTE: Published code should be considered copyrighted whether or not it includes an explicit copyright notice. This means that no one can distribute, reproduce, display, or create derivative works of the software, for commercial purposes, without permission of the copyright owner. Nevertheless, permission is granted for reproducing and creating derivative works for noncommercial activities (e.g. Research), given that appropriate crediting is provided, and changes that were made were indicated. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.

# To run FoBSim using Docker:
1-	Update apt-get:

Sudo apt-get update

2-	Install Docker Desktop from:

https://www.docker.com/get-started/

(for ubunto: sudo apt install docker.io)

3-	Check the version of the Docker installation:

docker -v

4-	Clone the FoBSim repository

5-	Go to the FoBSim Directory in the command line and build the docker image:

sudo docker build -t fobsim .

6-	Start the FoBSim container by typing:

sudo docker run -it fobsim

# To run FoBSim (CLI Only):

1- update installer: sudo apt-get update

2- install git: sudo apt-get install git-all

3- clone FoBSim: git clone https://github.com/sed-szeged/FobSim.git

4- install pip: sudo apt install python3-pip

5- install rsa: pip install rsa

6- run: python3 main.py

# The components implemented in FoBSim contains:
1- Fog layer implementation.

2- Blockchain network Implementation.

3- End-User layer implemetation.

4- Consensus algorithms.

5- Incentivization Mechanisms.

6- Parallel Mining.

7- Gossip Protocol.

8- Easy network topology and unique identities management.

# FoBSim allows the placement of the Blockchain network in either:
1- The Fog layer.

2- The End-User layer.

# The Blockchain in FoBSim provides the following services/immutable distributed ledgers:
1- Payment/Trading

2- Data management

3- Identity management

4- Computational Services through Smart Contracts

5- NEW: Federated Learning (FL) Aggregation

# The Blockchain in FoBSim allows the use of one of the following Consensus algorithms during each run:
1- Proof-of-Work (PoW)

2- Proof-of-Stake (PoS)

3- Proof-of-Authority (PoA)

4- NEW: Proof-of-Elapsed-Time (PoET)

5- NEW: delegated Proof-of-Stack (dPoS)

6- NEW: Directed Acyclic Graph (DAG) (Tangle/Hashgraph)

# NEW: Layer 2 Scaling & State Channels
FoBSim now supports simulating high-throughput off-chain transactions. When **Layer 2 Rollups** are enabled, the Fog nodes act as L2 Sequencers, batching user transactions and posting bundled zero-knowledge "proofs" to the L1 mempool, drastically increasing simulated TPS metrics and drastically mirroring modern Ethereum L2 architectures.

# Running FoBSim simulation:
After you clone the repository as clarified above, modify the 'Sim_parameters.json' either directly or on the command line (using e.g. vim or nano tools)

# Steps to add a new consensus algorithm (proof-based):
0- You must be familiar with Python language.

1- in the 'new_consensus_module.py', there are two groups of functions: Modifiable and Non-Modifiable (declared by comments).

2- in the Modifiable part, follow the seven steps declared in the comments. Make sure to add instead of modify on the modifiable part. Thus, other code related to other consensus algorithms is not affected.

# ☁️ Cloud Deployment Guide (AWS / GCP)

FobSim is now fully containerized and cloud-ready. Follow these steps to deploy to any cloud provider with Docker support.

### 1. Provision Server
- **Recommended Instance**: `t3.medium` (AWS) or `e2-standard-2` (GCP)
- **OS**: Ubuntu 22.04 LTS

### 2. Configure Security Groups / Firewall
Allow the following ports:
- `3000`: Frontend Dashboard
- `8000`: Backend API (FastAPI)

### 3. Deploy with Docker Compose
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose -y

# Clone and Run
git clone https://github.com/rebrahimy/FobSim.git
cd FobSim
docker-compose up -d --build
```

### 4. Verify
Access the platform at `http://<YOUR_SERVER_IP>:3000`. The frontend will automatically detect the server IP and connect to the backend on port 8000.

3- As an example, we added a 'dummy consensus algorithm' which clarifies the main parts that should be added for a new proof-based algorithm. You can perform the same steps.

4- Additional functionalities can be added "if necessary" to any other module in the tool so that the proposed consensus algorithm works smoothly. For example, we added some conditional statements related to PoET to the 'build_block' method in the 'miner.py' file, and we added a 'PoET_server.py' (which includes only one method only) to forbid any confusions. However, we could simply add this method to the 'new_consensus_module.py'. Read the functions of all the available 5 consensus algorithms so that you get your self familiar of how a proof-based algorithm works.

5- run the FoBSim tool after modifying on the 'Sim_parameters.json' file as required by your simulation scenario (steps 3 and 4 above ^^)
