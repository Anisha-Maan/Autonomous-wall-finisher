# backend/routers/trajectory.py
from fastapi import APIRouter, HTTPException
from ..models import PlanRequest
from ..planning import plan_coverage
from ..db import get_db_conn
from ..utils.logger import logger
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/api")

@router.post("/plan")
async def plan_and_store(req: PlanRequest):
    start = datetime.utcnow().isoformat()
    try:
        # Plan trajectory with obstacle avoidance
        result = plan_coverage(req.wall)
    except Exception as e:
        logger.exception("Error during planning")
        # Return a clear error to the client for debugging (avoid exposing sensitive internals in prod)
        raise HTTPException(status_code=500, detail=f"planning_failed: {str(e)}")

    # Prepend a non-painting start waypoint at the top-left corner so UI/traversal begins there
    try:
        start_wp = {"x": 0.0, "y": req.wall.height, "tool_on": False}
        # insert at beginning of waypoints
        result["waypoints"].insert(0, start_wp)
        # recompute length and bbox
        waypoints = result["waypoints"]
        import math
        length = sum(math.hypot(waypoints[i]["x"]-waypoints[i-1]["x"], waypoints[i]["y"]-waypoints[i-1]["y"]) for i in range(1,len(waypoints)))
        xs = [p["x"] for p in waypoints] or [0]
        ys = [p["y"] for p in waypoints] or [0]
        result["length_m"] = length
        result["bbox"] = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
    except Exception:
        # If anything goes wrong, keep original result
        pass

    traj_id = str(uuid.uuid4())
    name = req.name or f"plan_{traj_id[:8]}"

    payload = json.dumps(result["waypoints"])
    # Make sure obstacles are JSON serializable (Pydantic v2 models need model_dump)
    try:
        serializable_obs = [o.model_dump() if hasattr(o, "model_dump") else (o.dict() if hasattr(o, "dict") else o) for o in req.wall.obstacles]
    except Exception:
        # Last-resort: attempt to coerce to dicts
        serializable_obs = []
        for o in req.wall.obstacles:
            if isinstance(o, dict):
                serializable_obs.append(o)
            else:
                serializable_obs.append({
                    "x": getattr(o, "x", 0),
                    "y": getattr(o, "y", 0),
                    "w": getattr(o, "w", getattr(o, "width", 0)),
                    "h": getattr(o, "h", getattr(o, "height", 0)),
                })
    obstacles_payload = json.dumps(serializable_obs)
    bbox = result["bbox"]

    with get_db_conn() as conn:
        cur = conn.cursor()
        # Insert trajectory along with obstacles
        cur.execute("""
            INSERT INTO trajectories 
            (id, name, created_at, min_x, max_x, min_y, max_y, length_m, payload_json, obstacles_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            traj_id, name, start,
            bbox["min_x"], bbox["max_x"], bbox["min_y"], bbox["max_y"],
            result["length_m"], payload, obstacles_payload
        ))
        conn.commit()

    logger.info(f"Stored plan {traj_id} points={len(result['waypoints'])} length={result['length_m']:.3f}")
    return {"id": traj_id, "points": len(result["waypoints"]), "length_m": result["length_m"]}


@router.get("/trajectory/{traj_id}")
async def get_trajectory(traj_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, created_at, min_x, max_x, min_y, max_y, length_m, payload_json, obstacles_json
            FROM trajectories WHERE id = ?
        """, (traj_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="trajectory not found")

        return {
            "id": row[0],
            "name": row[1],
            "created_at": row[2],
            "bbox": {"min_x": row[3], "max_x": row[4], "min_y": row[5], "max_y": row[6]},
            "length_m": row[7],
            "waypoints": json.loads(row[8]),
            "obstacles": json.loads(row[9])  # return obstacles for frontend rendering
        }


@router.get("/trajectories")
async def query_trajectories(min_x: float = None, max_x: float = None, min_y: float = None, max_y: float = None, limit: int = 50):
    conds = []
    args = []
    if min_x is not None: conds.append("max_x >= ?"); args.append(min_x)
    if max_x is not None: conds.append("min_x <= ?"); args.append(max_x)
    if min_y is not None: conds.append("max_y >= ?"); args.append(min_y)
    if max_y is not None: conds.append("min_y <= ?"); args.append(max_y)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    q = f"SELECT id,name,created_at,min_x,max_x,min_y,max_y,length_m FROM trajectories {where} ORDER BY created_at DESC LIMIT ?"
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(q, (*args, limit))
        rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r[0], 
            "name": r[1], 
            "created_at": r[2], 
            "bbox": {"min_x": r[3], "max_x": r[4], "min_y": r[5], "max_y": r[6]}, 
            "length_m": r[7]
        })
    return {"count": len(results), "results": results}


@router.delete("/trajectory/{traj_id}")
async def delete_trajectory(traj_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM trajectories WHERE id = ?", (traj_id,))
        deleted = cur.rowcount
        conn.commit()
    return {"deleted": deleted}
