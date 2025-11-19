from typing import Dict
import math

def plan_coverage(wall) -> Dict:
    """
    Grid-based boustrophedon planner with obstacle avoidance.
    Accepts wall object with: width, height, brush_width, resolution, obstacles (list of dicts)
    Returns dict with waypoints, length, bbox.
    """
    # Grid dimensions
    nx = max(1, int(round(wall.width / wall.resolution)))
    ny = max(1, int(round(wall.height / wall.resolution)))
    brush_cells = max(1, int(round(wall.brush_width / wall.resolution)))
    grid = [[0]*nx for _ in range(ny)]

    # Mark obstacles on grid
    # Support obstacles provided as dicts or Pydantic model instances
    for ob in getattr(wall, "obstacles", []):
        if isinstance(ob, dict):
            x = ob.get("x", 0)
            y = ob.get("y", 0)
            w = ob.get("width", ob.get("w", 0))
            h = ob.get("height", ob.get("h", 0))
        else:
            # Pydantic model or object-like
            x = getattr(ob, "x", 0)
            y = getattr(ob, "y", 0)
            w = getattr(ob, "w", getattr(ob, "width", 0))
            h = getattr(ob, "h", getattr(ob, "height", 0))
        # Convert obstacle coordinates to grid indices and clamp to grid bounds
        # Convert obstacle (bottom-left coords) to top-origin grid indices
        try:
            x0 = int(math.floor(x / wall.resolution))
            x1 = int(math.ceil((x + w) / wall.resolution)) - 1
            # top-origin y: top_y = wall.height - (y + h)
            top_y = wall.height - (y + h)
            top_y_end = wall.height - y
            y0 = int(math.floor(top_y / wall.resolution))
            y1 = int(math.ceil(top_y_end / wall.resolution)) - 1
        except Exception:
            continue

        # Clamp indices within grid
        x0 = max(0, min(nx-1, x0))
        y0 = max(0, min(ny-1, y0))
        x1 = max(0, min(nx-1, x1))
        y1 = max(0, min(ny-1, y1))

        if x1 < x0 or y1 < y0:
            continue

        for yy in range(y0, y1+1):
            for xx in range(x0, x1+1):
                grid[yy][xx] = 1

    # Plan boustrophedon coverage
    pts = []
    for row in range(0, ny, brush_cells):
        y_cells = list(range(row, min(row+brush_cells, ny)))
        segments = []
        start = None
        for col in range(nx):
            blocked = any(grid[y][col]==1 for y in y_cells)
            if not blocked and start is None:
                start = col
            if (blocked or col==nx-1) and start is not None:
                end = col - (1 if blocked else 0)
                if end >= start:
                    segments.append((start,end))
                start = None
        if not segments:
            continue
        left_to_right = (row//brush_cells)%2==0
        for s,e in (segments if left_to_right else reversed(segments)):
            # y_m is calculated with top-origin (row 0 at top). Convert to bottom-origin
            y_m_top = (row + 0.5) * wall.resolution
            y_m = wall.height - y_m_top
            x_s = (s + 0.5) * wall.resolution
            x_e = (e + 0.5) * wall.resolution
            if left_to_right:
                pts.append((x_s, y_m))
                pts.append((x_e, y_m))
            else:
                pts.append((x_e, y_m))
                pts.append((x_s, y_m))

    # Fallback if no free points
    if not pts:
        pts = [(0,0),(wall.width,0),(wall.width,wall.height),(0,wall.height)]

    # Merge very close points
    merged = []
    eps = wall.resolution * 0.5
    for p in pts:
        if not merged or math.hypot(p[0]-merged[-1][0], p[1]-merged[-1][1]) > eps:
            merged.append(p)

    # Build waypoints. To ensure we do not traverse obstacle cells when moving between
    # painted segments, stitch the centers using a simple A* on the occupancy grid.
    from heapq import heappush, heappop

    def neighbors(cell):
        r,c = cell
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc = r+dr, c+dc
            if 0 <= nr < ny and 0 <= nc < nx and grid[nr][nc] == 0:
                yield (nr,nc)

    def heuristic(a,b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def astar(start, goal):
        # start/goal are (row,col)
        if start == goal:
            return [start]
        open_set = []
        heappush(open_set, (0 + heuristic(start, goal), 0, start, None))
        came_from = {}
        gscore = {start: 0}
        while open_set:
            _, g, node, parent = heappop(open_set)
            if node in came_from:
                continue
            came_from[node] = parent
            if node == goal:
                break
            for nb in neighbors(node):
                ng = g + 1
                if ng < gscore.get(nb, 1e9):
                    gscore[nb] = ng
                    heappush(open_set, (ng + heuristic(nb, goal), ng, nb, node))
        if goal not in came_from:
            return None
        # reconstruct path
        path = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = came_from.get(cur)
        path.reverse()
        return path

    # Convert merged centers (x,y) (bottom-origin) to grid cells (top-origin)
    cells = []
    for x,y in merged:
        col = min(nx-1, max(0, int(x / wall.resolution)))
        # convert bottom-origin y to top-origin row index
        row = min(ny-1, max(0, int((wall.height - y) / wall.resolution)))
        cells.append((row, col))

    path_cells = []
    for i in range(len(cells)):
        if i == 0:
            path_cells.append(cells[0])
            continue
        s = path_cells[-1]
        goal = cells[i]
        p = astar(s, goal)
        if p is None:
            # if no path found, fall back to direct jump (should be rare)
            path_cells.append(goal)
        else:
            # append path excluding first because it's already present
            path_cells.extend(p[1:])

    # Convert path cells to continuous waypoints (center of cells), return in bottom-origin coords
    waypoints = []
    for (r,c) in path_cells:
        x = (c + 0.5) * wall.resolution
        # convert top-origin row to bottom-origin y
        y_top = (r + 0.5) * wall.resolution
        y = wall.height - y_top
        waypoints.append({"x": round(x,6), "y": round(y,6), "tool_on": True})

    # Compute path length
    length = sum(math.hypot(waypoints[i]["x"]-waypoints[i-1]["x"], waypoints[i]["y"]-waypoints[i-1]["y"]) 
                 for i in range(1,len(waypoints)))

    # Bounding box
    xs = [p["x"] for p in waypoints] or [0]
    ys = [p["y"] for p in waypoints] or [0]
    bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}

    return {"waypoints": waypoints, "length_m": length, "bbox": bbox}

