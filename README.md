# Autonomous Wall Finisher

A robust, database-driven control system for an autonomous wall-finishing robot with intelligent path planning, real-time visualization, and obstacle avoidance.

## 🎯 Features

- **Smart Coverage Planning**: Grid-based boustrophedon algorithm with A* obstacle avoidance
- **FastAPI Backend**: Optimized SQLite database with proper indexing and PRAGMA settings
- **Interactive Frontend**: Canvas-based 2D visualization with trajectory playback controls
- **Obstacle Support**: Rectangular obstacle handling with collision-free path planning
- **RESTful API**: CRUD operations for trajectory storage and retrieval
- **Production Ready**: Docker support, comprehensive tests, and deployment guides

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```powershell
git clone https://github.com/Anisha-Maan/Autonomous-wall-finisher.git
cd Autonomous-wall-finisher
```

2. **Setup Python environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

3. **Start the backend**
```powershell
uvicorn backend.main:app --reload
# Backend runs at: http://localhost:8000
```

4. **Serve the frontend** (new terminal)
```powershell
cd frontend
python -m http.server 8001
# Open browser to: http://localhost:8001
```

### Using Docker (Recommended)

```powershell
docker-compose up -d
# Access at: http://localhost
```

## 📖 Documentation

- **[Quick Deploy Guide](DEPLOY.md)** - 5-minute deployment instructions
- **[Full Deployment Guide](DEPLOYMENT.md)** - Comprehensive deployment options
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## 🎮 Usage

1. **Enter Wall Dimensions**: Width and height in meters
2. **Add Obstacles**: Use top-left coordinates (X, Y, Width, Height)
3. **Click "Plan & Save"**: Generate and store trajectory
4. **Playback Controls**: Play, pause, step through, or scrub the trajectory

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  FastAPI     │─────▶│   SQLite    │
│   (Canvas)  │      │  Backend     │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                     ┌──────▼──────┐
                     │   Planner   │
                     │ (Boustro +  │
                     │    A* )     │
                     └─────────────┘
```

## 🧮 Algorithm Overview

Wall Coverage Planner (Boustrophedon + A* Path Stitching)

This project generates a complete, obstacle-aware painting trajectory for a rectangular wall.
It creates a boustrophedon (raster) coverage path for painting and then uses A* to safely connect all painting segments without driving through obstacles.

The final output is a list of waypoints the robot can follow, each specifying (x, y, tool_on).

### How It Works

**1. Grid Construction**
- The wall is discretized into a 2D grid
- Cells inside obstacles are marked as blocked

**2. Boustrophedon Coverage**
- Wall is divided into horizontal strips based on brush width
- Each strip is scanned left-to-right or right-to-left (alternating)
- Free paintable segments are extracted
- Centerlines of these segments become painting targets

**3. A* Path Stitching**
To move safely between painting segments:
- A* runs on the occupancy grid
- Returns a collision-free cell path
- Cell path is converted into (x, y) world coordinates
- `tool_on = False` during transit, `True` while painting

**4. Final Output**
- Ordered list of waypoints
- Continuous coordinates
- Paint + transit phases
- Path length and bounding box

## 📁 Project Structure

```
autonomous-wall-finisher/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── planning.py          # Coverage planner + A*
│   ├── db.py                # Database setup & connection
│   ├── routers/
│   │   └── trajectory.py    # API endpoints
│   └── utils/
│       └── logger.py        # Request logging
├── frontend/
│   ├── index.html           # UI layout
│   ├── app.js               # Visualization & controls
│   └── styles.css           # Styling
├── tests/
│   └── test_api.py          # API tests
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Backend container
├── nginx.conf               # Frontend proxy config
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🧪 Testing

Run the test suite:
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Run all tests
pytest -q

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::test_plan_with_obstacle -v
```

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

### Plan Trajectory
```http
POST /api/plan
Content-Type: application/json

{
  "wall": {
    "width": 5.0,
    "height": 5.0,
    "brush_width": 0.05,
    "resolution": 0.02,
    "obstacles": [
      {"x": 0.5, "y": 0.5, "w": 0.25, "h": 0.25}
    ]
  },
  "name": "my_trajectory"
}
```

### Get Trajectory
```http
GET /api/trajectory/{trajectory_id}
```

### List Trajectories
```http
GET /api/trajectories?limit=50
```

### Delete Trajectory
```http
DELETE /api/trajectory/{trajectory_id}
```

**Interactive API Docs**: Start the backend and visit http://localhost:8000/docs

## 🚢 Deployment Options

### 1. Docker (Fastest)
```powershell
docker-compose up -d
```

### 2. Render.com (Free Cloud)
- Push to GitHub → Connect on Render
- See [DEPLOY.md](DEPLOY.md) for step-by-step

### 3. VPS/Cloud Server
- Deploy to DigitalOcean, AWS, Azure
- See [DEPLOYMENT.md](DEPLOYMENT.md) for full guide

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLite
- **Frontend**: Vanilla JavaScript, HTML5 Canvas
- **Testing**: pytest, TestClient
- **Deployment**: Docker, Nginx, Gunicorn

## 📊 Performance

- **Database**: SQLite with WAL mode, indexed queries
- **Path Planning**: ~100-500ms for 5x5m wall with obstacles
- **Memory**: <50MB typical usage
- **Scalability**: Handles walls up to 20x20m at 2cm resolution

## 🔐 Security Checklist

For production deployment:

- [ ] Update CORS origins (remove `allow_origins=["*"]`)
- [ ] Add rate limiting
- [ ] Enable HTTPS/SSL
- [ ] Use environment variables for secrets
- [ ] Add authentication if needed
- [ ] Set up monitoring and logging

## 🐛 Troubleshooting

### Frontend shows "Plan failed"
- Check backend is running: `curl http://localhost:8000/health`
- Check browser console (F12) for errors
- Verify CORS settings

### Database locked error
- SQLite doesn't handle high concurrency
- Consider PostgreSQL for production

### Docker port conflicts
- Change port in docker-compose.yml: `"8080:80"`
- Stop conflicting services (IIS, Apache)

## 📝 Sample Usage

```javascript
// Plan a 5x5 meter wall with one obstacle
const response = await fetch('http://localhost:8000/api/plan', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    wall: {
      width: 5.0,
      height: 5.0,
      brush_width: 0.05,
      resolution: 0.02,
      obstacles: [{x: 1.0, y: 1.0, w: 0.5, h: 0.5}]
    },
    name: "demo_plan"
  })
});

const result = await response.json();
console.log(`Created trajectory with ${result.points} waypoints`);
```

## 🎓 Educational Value

This project demonstrates:
- Grid-based motion planning algorithms
- A* pathfinding in robotics
- RESTful API design patterns
- Real-time data visualization
- Database optimization techniques
- Full-stack application architecture

## 🔮 Future Enhancements

- [ ] Path smoothing and optimization
- [ ] 8-connected A* for diagonal movement
- [ ] Support for non-rectangular obstacles
- [ ] Real-time robot communication (MQTT/ROS)
- [ ] Multi-robot coordination
- [ ] Machine learning for paint coverage prediction
- [ ] 3D wall surface modeling

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Author

**Anisha Maan** - [GitHub](https://github.com/Anisha-Maan)

## 🙏 Acknowledgments

- FastAPI framework for excellent async API support
- A* algorithm and boustrophedon coverage planning literature
- Open source robotics community

---

**Need Help?** 
- 📚 [Full Documentation](DEPLOYMENT.md)
- 🚀 [Quick Deploy](DEPLOY.md)  
- 🐛 [Report Issues](https://github.com/Anisha-Maan/Autonomous-wall-finisher/issues)

**Star ⭐ this repo if you find it useful!**

