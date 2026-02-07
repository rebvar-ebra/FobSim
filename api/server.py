"""
FobSim API Server
FastAPI backend to run simulations and return results
"""
from fastapi import FastAPI, WebSocket, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import subprocess
import asyncio
import os
import psutil
from typing import Optional, List
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal
import models, auth
from fastapi.security import OAuth2PasswordRequestForm

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FobSim API", version="1.0.0")

# Auth Models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Auth Routes
@app.post("/api/auth/signup", response_model=Token)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pass, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Store simulation output
simulation_output = []
simulation_running = False


class SimConfig(BaseModel):
    NumOfFogNodes: int = 5
    num_of_users_per_fog_node: int = 5
    NumOfTaskPerUser: int = 5
    NumOfMiners: int = 4
    number_of_each_miner_neighbours: int = 3
    numOfTXperBlock: int = 5
    puzzle_difficulty: int = 2
    poet_block_time: int = 1
    Max_enduser_payment: int = 100
    miners_initial_wallet_value: int = 1000
    mining_award: int = 5
    delay_between_fog_nodes: int = 0
    delay_between_end_users: int = 0
    Gossip_Activated: bool = True
    Automatic_PoA_miners_authorization: bool = True
    Parallel_PoW_mining: bool = False
    Asymmetric_key_length: int = 512
    Num_of_DPoS_delegates: int = 2
    STOR_PLC: int = 0


class RunSimulation(BaseModel):
    blockchain_function: int = 1  # 1-4
    blockchain_placement: int = 1  # 1=Fog, 2=EndUser
    consensus_algorithm: int = 1  # 1-9
    config: Optional[SimConfig] = None


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
}

BLOCKCHAIN_FUNCTIONS = {
    1: "Data Management",
    2: "Computational Services",
    3: "Payment/Trading",
    4: "Identity Management",
}


@app.get("/")
async def root():
    return {"message": "FobSim API Server", "version": "1.0.0"}


@app.get("/api/config")
async def get_config():
    """Get current simulation configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config


@app.post("/api/config")
async def update_config(config: SimConfig):
    """Update simulation configuration"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
    try:
        with open(config_path, "r") as f:
            existing_config = json.load(f)

        # Merge new values
        new_vals = config.dict(exclude_unset=True)
        existing_config.update(new_vals)

        with open(config_path, "w") as f:
            json.dump(existing_config, f, indent=2)

        return {"status": "updated", "config": existing_config}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/simulations", response_model=List[dict])
async def get_simulations(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get history of simulations for current user"""
    sims = db.query(models.Simulation).filter(models.Simulation.user_id == current_user.id).order_by(models.Simulation.started_at.desc()).all()
    # Convert to dict and handle datetimes
    return [
        {
            "id": s.id,
            "function": s.function,
            "placement": s.placement,
            "consensus": s.consensus,
            "status": s.status,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "blocks_mined": s.blocks_mined,
            "avg_cpu": round(s.avg_cpu, 2)
        } for s in sims
    ]

@app.get("/api/analytics/compare")
async def get_comparison_data(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get aggregated comparison data across consensus algorithms"""
    from sqlalchemy import func

    stats = db.query(
        models.Simulation.consensus,
        func.avg(models.Simulation.blocks_mined).label('avg_blocks'),
        func.avg(models.Simulation.avg_cpu).label('avg_cpu_load'),
        func.count(models.Simulation.id).label('run_count')
    ).filter(models.Simulation.user_id == current_user.id)\
     .group_by(models.Simulation.consensus).all()

    return [
        {
            "name": s.consensus,
            "blocks": round(float(s.avg_blocks), 2),
            "cpu": round(float(s.avg_cpu_load), 2),
            "runs": s.run_count
        } for s in stats
    ]

@app.get("/api/consensus")
async def get_consensus_options():
    """Get available consensus algorithms"""
    return CONSENSUS_ALGORITHMS


@app.get("/api/functions")
async def get_blockchain_functions():
    """Get available blockchain functions"""
    return BLOCKCHAIN_FUNCTIONS


@app.post("/api/run")
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

    # Update Sim_parameters.json if config is provided
    if params.config:
        config_path = os.path.join(os.path.dirname(__file__), "..", "Sim_parameters.json")
        try:
            with open(config_path, "r") as f:
                existing_config = json.load(f)

            new_vals = params.config.dict(exclude_unset=True)
            existing_config.update(new_vals)

            with open(config_path, "w") as f:
                json.dump(existing_config, f, indent=2)
        except Exception as e:
            print(f"Error updating config: {e}")

    # Create DB record
    db_sim = models.Simulation(
        user_id=current_user.id,
        function=BLOCKCHAIN_FUNCTIONS.get(params.blockchain_function),
        placement="Fog" if params.blockchain_placement == 1 else "End User",
        consensus=CONSENSUS_ALGORITHMS.get(params.consensus_algorithm),
        status="running",
        config=params.config.dict() if params.config else {}
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


@app.post("/api/stop")
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

        # Finalize DB record
        try:
            db_session = SessionLocal()
            sim = db_session.query(models.Simulation).filter(models.Simulation.id == sim_id).first()
            if sim:
                sim.status = "completed" if simulation_process and simulation_process.returncode == 0 else "stopped"
                if not simulation_running and simulation_process and simulation_process.returncode is None:
                    sim.status = "stopped"

                sim.ended_at = datetime.utcnow()

                # Calculate final stats from output
                blocks = 0
                for line in simulation_output:
                    if "block has been proposed" in line or "Block" in line:
                        blocks += 1

                sim.blocks_mined = blocks // 2 # Rough estimate based on current logic
                if cpu_readings:
                    sim.avg_cpu = sum(cpu_readings) / len(cpu_readings)

                db_session.commit()
            db_session.close()
        except Exception as db_e:
            print(f"Failed to update final sim status: {db_e}")


@app.get("/api/status")
async def get_status():
    """Get simulation status and output"""
    return {
        "running": simulation_running,
        "output": simulation_output,
        "line_count": len(simulation_output)
    }


@app.get("/api/results")
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


@app.websocket("/ws/output")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
