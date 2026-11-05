"""
FobSim API Server
FastAPI backend to run simulations and return results
"""
from contextlib import asynccontextmanager
from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, BeforeValidator, Field, ValidationError
import json
from datetime import datetime, timedelta, timezone
import subprocess
import asyncio
import logging
import os
import psutil
from typing import Optional, Literal, Mapping, Any, Annotated
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal
import models, auth, email_service, password_reset
from config_schema import SimulationConfig, canonicalize_config, require_integer, to_engine_config
from fastapi.security import OAuth2PasswordRequestForm
from api.services.runs import list_owned_runs
from api.schemas.runs import SimulationHistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)
PASSWORD_RESET_COOLDOWN = timedelta(minutes=5)
password_reset_request_limiter = password_reset.PasswordResetRequestLimiter(
    per_ip_limit=int(os.environ.get("PASSWORD_RESET_PER_IP_LIMIT", "5")),
    global_limit=int(os.environ.get("PASSWORD_RESET_GLOBAL_LIMIT", "100")),
    window_seconds=int(os.environ.get("PASSWORD_RESET_RATE_WINDOW_SECONDS", "900")),
)

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=72)
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=72)

PASSWORD_RESET_RESPONSE = {
    "message": "If an account exists for that email, a reset link has been sent"
}

# Auth Routes
@router.post("/api/auth/signup", response_model=Token)
async def signup(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pass, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(
        email_service.send_welcome_email,
        full_name=new_user.full_name,
        email=new_user.email,
    )

    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/auth/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
):
    normalized_email = request.email.strip().lower()
    client_ip = http_request.client.host if http_request.client else "unknown"
    if password_reset_request_limiter.allow(client_ip):
        background_tasks.add_task(
            process_password_reset_request,
            normalized_email,
        )

    return PASSWORD_RESET_RESPONSE

async def process_password_reset_request(
    normalized_email: str,
    db_factory=SessionLocal,
    send_email=email_service.send_password_reset_email,
):
    db = db_factory()
    email_payload = None
    try:
        user = (
            db.query(models.User)
            .filter(func.lower(models.User.email) == normalized_email)
            .with_for_update()
            .first()
        )
        if not user:
            return

        cooldown_started_at = password_reset.utc_now() - PASSWORD_RESET_COOLDOWN
        recent_request = (
            db.query(models.PasswordResetToken)
            .filter(
                models.PasswordResetToken.user_id == user.id,
                models.PasswordResetToken.created_at >= cooldown_started_at,
            )
            .first()
        )
        if recent_request:
            return

        reset_token = password_reset.generate_password_reset_token()
        db.add(
            models.PasswordResetToken(
                user_id=user.id,
                token_hash=password_reset.hash_password_reset_token(reset_token),
                password_fingerprint=password_reset.password_fingerprint(
                    user.hashed_password
                ),
                expires_at=password_reset.password_reset_expiry(),
            )
        )
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to persist password reset request")
            return

        email_payload = {
            "full_name": user.full_name,
            "email": user.email,
            "reset_token": reset_token,
        }
    finally:
        db.close()

    if email_payload:
        await send_email(**email_payload)

@router.post("/api/auth/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    token_hash = password_reset.hash_password_reset_token(request.token)
    reset_record = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )
    now = password_reset.utc_now()
    if (
        not reset_record
        or reset_record.used_at is not None
        or reset_record.expires_at <= now
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user = (
        db.query(models.User)
        .filter(models.User.id == reset_record.user_id)
        .with_for_update()
        .first()
    )
    if (
        not user
        or reset_record.password_fingerprint
        != password_reset.password_fingerprint(user.hashed_password)
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    reset_record.used_at = now
    user.hashed_password = auth.get_password_hash(request.new_password)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to update password")
        raise HTTPException(status_code=500, detail="Could not update password")
    return {"message": "Password updated successfully"}

@router.get("/api/auth/me")
async def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

# Store simulation output
simulation_output = []
simulation_running = False


class RunSimulation(BaseModel):
    blockchain_function: Annotated[Literal[1, 2, 3, 4, 5], BeforeValidator(require_integer)] = 1
    blockchain_placement: Annotated[Literal[1, 2], BeforeValidator(require_integer)] = 1
    consensus_algorithm: Annotated[Literal[1, 2, 3, 4, 5, 6, 8, 9, 10], BeforeValidator(require_integer)] = 1
    config: Optional[SimulationConfig] = None

    def effective_config(self, existing: Mapping[str, Any]) -> SimulationConfig:
        """Validate the complete merged snapshot using this run's placement."""
        overrides = self.config.model_dump(exclude_unset=True) if self.config else {}
        return SimulationConfig.model_validate(
            {**canonicalize_config(existing), **overrides},
            context={"placement": self.blockchain_placement},
        )


# Consensus algorithm names
CONSENSUS_ALGORITHMS = {
    1: "Proof of Work (PoW)",
    2: "Proof of Stake (PoS)",
    3: "Proof of Authority (PoA)",
    4: "Proof of Elapsed Time (PoET)",
    5: "Delegated Proof of Stake (DPoS)",
    6: "Practical Byzantine Fault Tolerance (PBFT)",
    8: "Proof of Activity (PoA-Hybrid)",
    9: "Proof of Burn (PoB)",
    10: "Directed Acyclic Graph (DAG)",
}

BLOCKCHAIN_FUNCTIONS = {
    1: "Data Management",
    2: "Computational Services",
    3: "Payment/Trading",
    4: "Identity Management",
    5: "Federated Learning",
}


@router.get("/")
async def root():
    return {"message": "FobSim API Server", "version": "1.0.0"}


@router.get("/api/config")
async def get_config():
    """Get current simulation configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return to_engine_config(SimulationConfig.model_validate(config))


@router.post("/api/config")
async def update_config(config: SimulationConfig):
    """Update simulation configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
    try:
        with open(config_path, "r") as f:
            existing_config = json.load(f)

        effective = SimulationConfig.model_validate({
            **canonicalize_config(existing_config),
            **config.model_dump(exclude_unset=True),
        })
        engine_config = to_engine_config(effective)

        with open(config_path, "w") as f:
            json.dump(engine_config, f, indent=2)

        return {"status": "updated", "config": engine_config}
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=json.loads(e.json())) from e
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/api/simulations", response_model=list[SimulationHistoryResponse])
async def get_simulations(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Keep the frontend's flat history shape using public, owner-scoped run pages."""
    sims = []
    cursor = None
    while True:
        page = list_owned_runs(db, current_user.id, cursor=cursor, limit=100)
        sims.extend(page.items)
        if page.next_cursor is None:
            break
        cursor = page.next_cursor
    sims.sort(key=lambda run: (
        run.started_at is not None,
        run.started_at or datetime.min.replace(tzinfo=timezone.utc),
        run.id,
    ), reverse=True)
    return [
        {
            "id": s.id,
            "function": s.function,
            "placement": s.placement,
            "consensus": s.consensus,
            "status": s.status,
            "started_at": s.started_at,
            "ended_at": s.ended_at,
            "blocks_mined": s.blocks_mined,
            "avg_cpu": round(s.avg_cpu, 2) if s.avg_cpu is not None else None,
            "energy_used": round(s.energy_used, 6) if s.energy_used is not None else None
        } for s in sims
    ]

@router.get("/api/analytics/compare")
async def get_comparison_data(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get aggregated comparison data across consensus algorithms with scientific metrics"""
    from sqlalchemy import func

    stats = db.query(
        models.Simulation.consensus,
        func.avg(models.Simulation.blocks_mined).label('avg_blocks'),
        func.avg(models.Simulation.avg_cpu).label('avg_cpu_load'),
        func.avg(models.Simulation.forks).label('avg_forks'),
        func.avg(models.Simulation.consistency).label('avg_consistency'),
        func.avg(models.Simulation.throughput).label('avg_throughput'),
        func.avg(models.Simulation.latency).label('avg_latency'),
        func.avg(models.Simulation.energy_used).label('avg_energy'),
        func.count(models.Simulation.id).label('run_count')
    ).filter(models.Simulation.user_id == current_user.id)\
     .group_by(models.Simulation.consensus).all()

    # We also need to get BPS which is in a JSON field (harder to AVG in SQL)
    # We'll do a quick manual average for BPS per consensus type
    raw_sims = db.query(models.Simulation).filter(models.Simulation.user_id == current_user.id).all()
    bps_map = {}
    for r in raw_sims:
        if r.consensus not in bps_map: bps_map[r.consensus] = []
        if r.config and 'bps' in r.config:
            bps_map[r.consensus].append(r.config['bps'])

    results = []
    for s in stats:
        avg_bps = sum(bps_map[s.consensus]) / len(bps_map[s.consensus]) if s.consensus in bps_map and bps_map[s.consensus] else 0
        results.append({
            "name": s.consensus,
            "blocks": round(float(s.avg_blocks), 2),
            "cpu": round(float(s.avg_cpu_load), 2),
            "forks": round(float(s.avg_forks), 2),
            "consistency": round(float(s.avg_consistency), 2),
            "throughput": round(float(s.avg_throughput or 0), 2),
            "latency": round(float(s.avg_latency or 0), 4),
            "energy": round(float(s.avg_energy or 0), 6),
            "bps": round(avg_bps, 4),
            "runs": s.run_count
        })
    return results

@router.get("/api/consensus")
async def get_consensus_options():
    """Get available consensus algorithms"""
    return CONSENSUS_ALGORITHMS


@router.get("/api/functions")
async def get_blockchain_functions():
    """Get available blockchain functions"""
    return BLOCKCHAIN_FUNCTIONS


@router.post("/api/run")
async def run_simulation(
    params: RunSimulation,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Run a simulation with specified parameters"""
    global simulation_running, simulation_output

    if simulation_running:
        return {"status": "error", "message": "Simulation already running"}

    # Snapshot and validate all effective inputs before writing or creating a run.
    config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
    try:
        with open(config_path, "r") as f:
            effective = params.effective_config(json.load(f))
        with open(config_path, "w") as f:
            json.dump(to_engine_config(effective), f, indent=2)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=json.loads(e.json())) from e
    except (OSError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail="Could not load or write simulation configuration") from e

    # Create DB record
    db_sim = models.Simulation(
        user_id=current_user.id,
        function=BLOCKCHAIN_FUNCTIONS.get(params.blockchain_function),
        placement="Fog" if params.blockchain_placement == 1 else "End User",
        consensus=CONSENSUS_ALGORITHMS.get(params.consensus_algorithm),
        status="running",
        config=effective.model_dump(mode="json")
    )
    db.add(db_sim)
    db.commit()
    db.refresh(db_sim)

    simulation_output = []
    simulation_running = True

    # Run simulation in background
    background_tasks.add_task(
        execute_simulation,
        params.blockchain_function,
        params.blockchain_placement,
        params.consensus_algorithm,
        db_sim.id
    )

    return {
        "status": "started",
        "simulation_id": db_sim.id,
        "params": {
            "function": db_sim.function,
            "consensus": db_sim.consensus,
        }
    }


# Global process reference for stopping
simulation_process = None


@router.post("/api/stop")
async def stop_simulation():
    """Stop the running simulation"""
    global simulation_running, simulation_process, simulation_output

    if simulation_process:
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(simulation_process.pid), 9)
            await simulation_process.wait()
        except:
            pass
        simulation_process = None

    simulation_running = False
    simulation_output.append("⏹️ Simulation stopped by user")

    return {"status": "stopped"}


async def execute_simulation(blockchain_function: int, placement: int, consensus: int, sim_id: int):
    """Execute the simulation process"""
    global simulation_running, simulation_output, simulation_process

    try:
        # Build input sequence - handle all interactive prompts
        # The simulation has multiple interactive prompts that need responses
        inputs = [str(blockchain_function), str(placement)]

        # For Identity Management (function 4), need to send "done" to skip attributes
        if blockchain_function == 4:
            inputs.append("done")

        # Consensus is asked after network init
        inputs.append(str(consensus))

        # Answer "N" to AI-assisted mining question (asked for PoW)
        if consensus == 1:  # PoW
            inputs.append("N")

        # Add multiple empty responses for "Press Enter to proceed" prompts
        # The simulation may ask this multiple times
        for _ in range(10):
            inputs.append("")

        sim_input = "\n".join(inputs) + "\n"

        simulation_output.append(f"Starting simulation with Function={blockchain_function}, Placement={placement}, Consensus={consensus}")

        # Log server details
        sv = psutil.virtual_memory()
        simulation_output.append(f"🖥️ SERVER: {psutil.cpu_count()} Cores | {sv.total // (1024**3)}GB RAM | {psutil.cpu_percent()}% CPU Load")

        simulation_process = await asyncio.create_subprocess_exec(
            "python3", "-u", "main.py",  # -u for unbuffered output
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            preexec_fn=os.setsid  # Create a new process group
        )

        cpu_readings = []

        # Monitor resources in background
        async def monitor_resources():
            while simulation_running and simulation_process.returncode is None:
                try:
                    p = psutil.Process(simulation_process.pid)
                    # Get process CPU (can be >100% for multi-core)
                    proc_cpu = p.cpu_percent(interval=None)
                    cpu_readings.append(proc_cpu)
                    sys_cpu = psutil.cpu_percent()
                    sys_mem = psutil.virtual_memory().percent

                    simulation_output.append(f"📊 MONITOR: Proc CPU: {proc_cpu}% | Sys CPU: {sys_cpu}% | Sys RAM: {sys_mem}%")
                except:
                    pass
                await asyncio.sleep(5) # Report every 5 seconds

        # Add monitoring to loop
        asyncio.create_task(monitor_resources())

        # Send all inputs at once
        simulation_process.stdin.write(sim_input.encode())
        await simulation_process.stdin.drain()
        simulation_process.stdin.close()

        # Patterns to filter out (menu prompts and errors)
        skip_patterns = [
            "EOF when reading a line",
            "Please choose the function",
            "Please choose the placement",
            "Please choose the Consensus",
            "Proof of Work",
            "Proof of Stake",
            "Proof of Authority",
            "Proof of Elapsed Time",
            "Delegated Proof of Stake",
            "Practical Byzantine Fault Tolerance",
            "Proof of Activity",
            "Proof of Burn",
            "Would you like to simulate AI-assisted",
            "Input is incorrect",
            "input Y/y to agree",
            "Data Management",
            "Computational services",
            "Payment",
            "Identity Management",
            "Fog Layer",
            "End-User layer",
            "If you don't want other attributes",
            "If you want other attributes",
            "Press Enter to proceed",
            "(1)",
            "(2)",
            "(3)",
            "(4)",
            "6:",
            "7:",
            "8:",
            "9:",
        ]

        # Read output line by line in real-time
        while simulation_running:
            try:
                # Use wait_for to avoid blocking forever if process dies
                line = await asyncio.wait_for(simulation_process.stdout.readline(), timeout=0.1)
                if not line:
                    break
                decoded_line = line.decode().rstrip()
                # Filter out prompts, EOF errors, and empty lines
                if decoded_line and not any(pattern in decoded_line for pattern in skip_patterns):
                    simulation_output.append(decoded_line)
            except asyncio.TimeoutError:
                if simulation_process.returncode is not None:
                    break
                continue

        await simulation_process.wait()
        simulation_output.append("Simulation completed!")

    except Exception as e:
        simulation_output.append(f"Error: {str(e)}")
    finally:
        simulation_running = False

        # Finalize DB record with scientific metrics
        try:
            db_session = SessionLocal()
            sim = db_session.query(models.Simulation).filter(models.Simulation.id == sim_id).first()
            if sim:
                sim.status = "completed" if simulation_process and simulation_process.returncode == 0 else "stopped"
                if not simulation_running and simulation_process and simulation_process.returncode is None:
                    sim.status = "stopped"

                sim.ended_at = models.utc_now()

                # --- Scientific Analytics Parsing ---
                temp_dir = os.path.join(os.path.dirname(__file__), "..", "temporary")
                chains = []

                # 1. Load all miner chains to check consistency
                try:
                    for filename in os.listdir(temp_dir):
                        if filename.endswith("_local_chain.json"):
                            with open(os.path.join(temp_dir, filename), "r") as f:
                                chain_data = json.load(f)
                                if chain_data:
                                    chains.append(chain_data)
                except Exception as e:
                    print(f"Analytics Error: Could not read chain files: {e}")

                if chains:
                    # 2. Calculate Scientific Metrics
                    longest_chain = max(chains, key=len)
                    total_blocks = len(longest_chain)
                    sim.blocks_mined = total_blocks

                    # Consistency & Fork Detection
                    heads = []
                    for c in chains:
                        if c:
                            last_idx = str(len(c) - 1)
                            if last_idx in c:
                                heads.append(c[last_idx]['Header']['hash'])

                    if heads:
                        sim.forks = len(set(heads))
                        from collections import Counter
                        most_common_count = Counter(heads).most_common(1)[0][1]
                        sim.consistency = (most_common_count / len(heads)) * 100

                    # BPS, TPS, and Latency Calculation
                    if total_blocks > 1:
                        ts_list = [longest_chain[i]['Body']['timestamp'] for i in longest_chain if 'Body' in longest_chain[i]]
                        if len(ts_list) > 1:
                            duration = max(ts_list) - min(ts_list)
                            if duration > 0:
                                # Throughput (TPS)
                                tx_per_block = sim.config.get('numOfTXperBlock', 5) if sim.config else 5
                                l2_multiplier = sim.config.get('Layer2_Batch_Size', 100) if (sim.config and sim.config.get('Layer2_Rollup_Enabled')) else 1
                                sim.throughput = round((total_blocks * tx_per_block * l2_multiplier) / duration, 4)

                                # Latency (Sec per Block)
                                sim.latency = round(duration / total_blocks, 4)

                                # BPS for backward compatibility in config
                                if not sim.config: sim.config = {}
                                sim.config['bps'] = round(total_blocks / duration, 4)

                    # 3. CPU Load
                    if cpu_readings:
                        sim.avg_cpu = sum(cpu_readings) / len(cpu_readings)

                    # 4. Energy Consumption
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
                    import blockchain as bc_core
                    started_at = sim.started_at
                    # SQLite returns naive datetimes even for timezone-aware
                    # columns; these legacy/test values represent UTC.
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=timezone.utc)
                    duration_sec = (sim.ended_at - started_at).total_seconds()
                    sim.energy_used = bc_core.calculate_energy_consumption(sim.consensus, duration_sec)

                else:
                    # Fallback to line counting if no chains found
                    blocks = 0
                    for line in simulation_output:
                        if "block has been proposed" in line or "Block" in line:
                            blocks += 1
                    sim.blocks_mined = blocks // 2
                    if cpu_readings:
                        sim.avg_cpu = sum(cpu_readings) / len(cpu_readings)

                db_session.commit()
            db_session.close()
        except Exception as db_e:
            print(f"Failed to update final sim status: {db_e}")


@router.get("/api/status")
async def get_status():
    """Get simulation status and output"""
    return {
        "running": simulation_running,
        "output": simulation_output,
        "line_count": len(simulation_output)
    }


@router.get("/api/results")
async def get_results():
    """Get simulation results from temporary files"""
    results = {
        "blocks": [],
        "stakes": {},
        "burned": {}
    }

    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temporary")

    # Try to read various result files
    try:
        for filename in os.listdir(temp_dir):
            if filename.endswith("_local_chain.json"):
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, "r") as f:
                    chain = json.load(f)
                    results["blocks"].extend(chain)
    except Exception:
        pass

    try:
        stakes_file = os.path.join(temp_dir, "miners_stake_amounts.json")
        if os.path.exists(stakes_file):
            with open(stakes_file, "r") as f:
                results["stakes"] = json.load(f)
    except Exception:
        pass

    try:
        burned_file = os.path.join(temp_dir, "burned_coins.json")
        if os.path.exists(burned_file):
            with open(burned_file, "r") as f:
                results["burned"] = json.load(f)
    except Exception:
        pass

    return results


@router.websocket("/ws/output")
async def websocket_output(websocket: WebSocket):
    """WebSocket for live simulation output"""
    await websocket.accept()
    last_index = 0

    try:
        while True:
            if len(simulation_output) > last_index:
                new_lines = simulation_output[last_index:]
                for line in new_lines:
                    await websocket.send_text(line)
                last_index = len(simulation_output)

            await websocket.send_json({
                "running": simulation_running,
                "total_lines": len(simulation_output)
            })

            await asyncio.sleep(0.5)
    except Exception:
        pass


@asynccontextmanager
async def initialize_database(app):
    """Initialize tables only when the deployed server actually starts."""
    models.Base.metadata.create_all(bind=engine)
    yield


from app_factory import create_app

app = create_app()
app.router.lifespan_context = initialize_database


if __name__ == "__main__":
    import uvicorn
    # Use PORT from env var (Render/Railway/Heroku) or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
