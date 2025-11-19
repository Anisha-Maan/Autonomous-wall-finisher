Wall Coverage Planner (Boustrophedon + A* Path Stitching)

This project generates a complete, obstacle-aware painting trajectory for a rectangular wall.
It creates a boustrophedon (raster) coverage path for painting and then uses A* to safely connect all painting segments without driving through obstacles.

The final output is a list of waypoints the robot can follow, each specifying (x, y, tool_on).

Overview

This system takes in:

Wall dimensions (width, height)

Brush/tool width

Grid resolution

Rectangular obstacles

Starting point (optional)

…and produces:

A full painting trajectory

Transit + painting waypoints

Total path length

Bounding box of the path

Clean visualization-ready coordinates

How It Works
1. Grid Construction

The wall is discretized into a 2D grid.
Cells inside obstacles are marked as blocked.

2. Boustrophedon Coverage

Wall is divided into horizontal strips based on brush width.

Each strip is scanned left-to-right or right-to-left (alternating).

Free paintable segments are extracted.

Centerlines of these segments become painting targets.

3. A* Path Stitching

To move safely between painting segments:

A* runs on the occupancy grid.

Returns a collision-free cell path.

Cell path is converted into (x, y) world coordinates.

tool_on = False during transit, True while painting.

4. Final Output

Ordered list of waypoints

Continuous coordinates

Paint + transit phases

Path length and bounding box

Project Structure

/wall_coverage_planner
│
├── planner.py          # Core coverage & A* logic
├── utils.py            # Helpers for grid, math, merging
├── visualize.py        # Optional plotting utilities
├── tests/              # Test cases
└── README.md
