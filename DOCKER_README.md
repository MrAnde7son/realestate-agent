# 🐳 Docker Setup for Real Estate Agent

This Docker setup provides a complete, containerized environment for all Real Estate Agent services. Everything runs in isolated containers with proper networking and data persistence.

## 🚀 **Quick Start**

### **Prerequisites**
- Docker Desktop or Docker Engine
- Docker Compose (included with Docker Desktop)

### **Start All Services**
```bash
# Make the script executable (first time only)
chmod +x docker-start.sh

# Start everything
./docker-start.sh start-all
```

### **Start Only MCP Servers (Data Access)**
```bash
./docker-start.sh start-mcp
```

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   MCP Servers   │
│   (Next.js)     │◄──►│   (Backend)     │◄──►│   (Data)        │
│   Port: 3000    │    │   Port: 8000    │    │   Ports: 8001-4 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Databases     │
                       │ Redis + Postgres│
                       │   Ports: 6379,  │
                       │       5432      │
                       └─────────────────┘
```

## 📋 **Service Details**

### **🌐 Frontend (Next.js)**
- **Port**: 3000
- **URL**: http://localhost:3000
- **Purpose**: Professional broker dashboard
- **Features**: Property management, mortgage calculator, alerts

### **🔧 Django Backend**
- **Port**: 8000
- **URL**: http://localhost:8000
- **Purpose**: API backend, database management
- **Features**: REST API, Celery tasks, user management

### **🏠 Yad2 MCP Server**
- **Port**: 8001
- **Purpose**: Real estate scraping and search
- **Features**: 58+ search parameters, market analysis

### **🏛️ RAMI MCP Server**
- **Port**: 8002
- **Purpose**: Israeli planning documents
- **Features**: Document downloads, TabaSearch API

### **🗺️ GIS MCP Server**
- **Port**: 8003
- **Purpose**: Tel Aviv spatial data
- **Features**: Geocoding, permits, land use

### **📊 Government Data MCP Server**
- **Port**: 8004
- **Purpose**: Government datasets and comparables
- **Features**: Transaction data, appraisals

### **🗄️ PostgreSQL**
- **Port**: 5432
- **Purpose**: Primary database
- **Features**: User data, property listings, alerts

### **🔴 Redis**
- **Port**: 6379
- **Purpose**: Celery broker and caching
- **Features**: Task queue, session storage

## 🛠️ **Management Commands**

### **Start Services**
```bash
# Start everything
./docker-start.sh start-all

# Start only MCP servers (for data access)
./docker-start.sh start-mcp

# Start only backend services
./docker-start.sh start-backend

# Start only frontend
./docker-start.sh start-frontend
```

### **Monitor Services**
```bash
# Show service status
./docker-start.sh status

# Show logs for all services
./docker-start.sh logs

# Show logs for specific service
./docker-start.sh logs yad2-mcp
./docker-start.sh logs django
./docker-start.sh logs frontend
```

### **Manage Services**
```bash
# Stop all services
./docker-start.sh stop

# Rebuild all services
./docker-start.sh rebuild

# Rebuild specific service
./docker-start.sh rebuild frontend

# Clean up everything (containers, volumes, images)
./docker-start.sh cleanup
```

## 🔧 **Configuration**

### **Environment Variables**
Copy `env.example` to `.env` and modify as needed:

```bash
cp env.example .env
# Edit .env with your configuration
```

### **Key Configuration Options**
- **Database**: PostgreSQL connection string
- **Redis**: Celery broker configuration
- **Email**: SendGrid API key for alerts
- **WhatsApp**: Twilio credentials for notifications
- **MCP Ports**: Customize MCP server ports if needed

### **Port Customization**
To change ports, modify `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Change 3001 to your preferred port
```

## 📊 **Data Access Methods**

### **1. Natural Language (LLM Integration)**
Start MCP servers and use with Claude Desktop or other LLM:

```bash
./docker-start.sh start-mcp
```

**Example Queries:**
- "Find 4-room apartments in Tel Aviv under 8M NIS"
- "Get planning documents for Gush 6638 Chelka 96"
- "Find building permits near Dizengoff 50"

### **2. Web Dashboard**
Access the professional interface:

```bash
./docker-start.sh start-frontend
# Open http://localhost:3000
```

### **3. API Endpoints**
Use the Django REST API:

```bash
./docker-start.sh start-backend
# API available at http://localhost:8000
```

### **4. Direct MCP Access**
Connect directly to MCP servers:

```bash
# Test Yad2 MCP server
curl http://localhost:8001/health

# Test RAMI MCP server  
curl http://localhost:8002/health
```

## 🧪 **Development Workflow**

### **Code Changes**
The Docker setup uses volume mounts, so code changes are reflected immediately:

```bash
# Edit your Python/JavaScript files
# Changes are automatically reflected in running containers
```

### **Rebuilding Services**
When you modify Dockerfiles or dependencies:

```bash
# Rebuild specific service
./docker-start.sh rebuild yad2-mcp

# Rebuild all services
./docker-start.sh rebuild
```

### **Debugging**
View logs in real-time:

```bash
# Follow all logs
./docker-start.sh logs

# Follow specific service
./docker-start.sh logs django
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Check what's using the port
lsof -i :3000

# Stop conflicting service or change port in docker-compose.yml
```

#### **Service Won't Start**
```bash
# Check logs
./docker-start.sh logs service-name

# Rebuild service
./docker-start.sh rebuild service-name
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL status
./docker-start.sh logs postgres

# Restart database
docker-compose restart postgres
```

#### **MCP Server Connection Issues**
```bash
# Check MCP server logs
./docker-start.sh logs yad2-mcp

# Verify ports are accessible
curl http://localhost:8001/health
```

### **Reset Everything**
```bash
# Complete cleanup
./docker-start.sh cleanup

# Start fresh
./docker-start.sh start-all
```

## 📈 **Performance & Scaling**

### **Resource Limits**
Default Docker Compose doesn't set resource limits. To add them:

```yaml
services:
  django:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### **Scaling Services**
```bash
# Scale Django workers
docker-compose up --scale django=3

# Scale Celery workers
docker-compose up --scale celery-worker=2
```

### **Monitoring**
```bash
# Resource usage
docker stats

# Service health
./docker-start.sh status
```

## 🔒 **Security Considerations**

### **Production Deployment**
- Change default passwords in `.env`
- Use secrets management for sensitive data
- Enable HTTPS with reverse proxy
- Restrict network access

### **Development vs Production**
```bash
# Development (current setup)
docker-compose up

# Production (separate compose file)
docker-compose -f docker-compose.prod.yml up
```

## 📚 **Advanced Usage**

### **Custom MCP Server Configuration**
```yaml
services:
  yad2-mcp:
    environment:
      - MCP_PORT=8001
      - YAD2_API_KEY=${YAD2_API_KEY}
      - LOG_LEVEL=DEBUG
```

### **External Service Integration**
```yaml
services:
  django:
    environment:
      - EXTERNAL_API_URL=https://api.external.com
      - API_KEY=${EXTERNAL_API_KEY}
```

### **Data Persistence**
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/your/data
```

## 🎯 **Use Cases**

### **Data Analyst**
```bash
# Start only MCP servers for data access
./docker-start.sh start-mcp

# Use with Python scripts or LLM tools
# Access data through MCP protocol
```

### **Broker/Appraiser**
```bash
# Start full dashboard
./docker-start.sh start-all

# Use web interface for property management
# Access http://localhost:3000
```

### **Developer**
```bash
# Start backend for API development
./docker-start.sh start-backend

# Test API endpoints at http://localhost:8000
# View logs for debugging
```

## 🚀 **Next Steps**

1. **Start with MCP servers**: `./docker-start.sh start-mcp`
2. **Test data access** with your LLM tool
3. **Add frontend**: `./docker-start.sh start-frontend`
4. **Configure alerts**: Set up email/WhatsApp in `.env`
5. **Customize**: Modify ports, add services as needed

## 📞 **Support**

- **Logs**: `./docker-start.sh logs [service]`
- **Status**: `./docker-start.sh status`
- **Rebuild**: `./docker-start.sh rebuild [service]`
- **Cleanup**: `./docker-start.sh cleanup`

---

**🎉 You're now ready to run all Real Estate Agent services with Docker!**
