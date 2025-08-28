# Climate Risk Lens Runbook

## Emergency Contacts

- **On-call Engineer**: [Contact Information]
- **ML Team Lead**: [Contact Information]
- **Infrastructure Team**: [Contact Information]

## System Overview

Climate Risk Lens is a real-time geospatial platform for forecasting local climate hazards. The system consists of:

- **Frontend**: Next.js application with MapLibre GL
- **Backend**: FastAPI with PostgreSQL + PostGIS
- **ML Pipeline**: PyTorch models with MLflow tracking
- **Infrastructure**: Docker Compose with Redis, MinIO, Prometheus, Grafana

## Common Issues and Solutions

### 1. Database Connection Issues

**Symptoms:**
- API returns 500 errors
- "Database connection failed" in logs
- Health check fails

**Diagnosis:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Check database connectivity
docker-compose exec backend python -c "
from app.db.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database OK')
asyncio.run(test())
"
```

**Solutions:**
1. Restart PostgreSQL: `docker-compose restart postgres`
2. Check disk space: `df -h`
3. Check PostgreSQL logs: `docker-compose logs postgres`
4. Verify connection string in `.env`

### 2. Redis Connection Issues

**Symptoms:**
- Celery tasks not executing
- Cache misses
- "Redis connection failed" in logs

**Diagnosis:**
```bash
# Check Redis status
docker-compose ps redis

# Test Redis connectivity
docker-compose exec redis redis-cli ping
```

**Solutions:**
1. Restart Redis: `docker-compose restart redis`
2. Check Redis memory: `docker-compose exec redis redis-cli info memory`
3. Clear Redis cache if needed: `docker-compose exec redis redis-cli flushall`

### 3. MLflow Tracking Issues

**Symptoms:**
- Model training fails to log metrics
- MLflow UI not accessible
- "MLflow connection failed" in logs

**Diagnosis:**
```bash
# Check MLflow status
docker-compose ps mlflow

# Test MLflow connectivity
curl http://localhost:5000/health
```

**Solutions:**
1. Restart MLflow: `docker-compose restart mlflow`
2. Check MinIO connectivity for artifacts
3. Verify MLflow configuration in `.env`

### 4. Frontend Not Loading

**Symptoms:**
- Frontend returns 404 or 500
- Map not rendering
- API calls failing

**Diagnosis:**
```bash
# Check frontend status
docker-compose ps frontend

# Check frontend logs
docker-compose logs frontend

# Test API connectivity
curl http://localhost:8000/api/v1/healthz
```

**Solutions:**
1. Restart frontend: `docker-compose restart frontend`
2. Check API URL configuration
3. Verify CORS settings
4. Check browser console for errors

### 5. Model Inference Failures

**Symptoms:**
- Risk predictions not updating
- "Model inference failed" in logs
- Empty risk data in API responses

**Diagnosis:**
```bash
# Check worker status
docker-compose ps worker

# Check worker logs
docker-compose logs worker

# Check Celery task status
docker-compose exec backend celery -A app.workers.celery inspect active
```

**Solutions:**
1. Restart workers: `docker-compose restart worker`
2. Check model files in MinIO
3. Verify MLflow model registry
4. Check data ingestion pipeline

## Monitoring and Alerts

### Key Metrics to Monitor

1. **API Response Time**
   - Target: < 500ms p95
   - Alert: > 1s p95

2. **Database Connection Pool**
   - Target: < 80% utilization
   - Alert: > 90% utilization

3. **Redis Memory Usage**
   - Target: < 80% of available memory
   - Alert: > 90% of available memory

4. **Model Inference Latency**
   - Target: < 2s p95
   - Alert: > 5s p95

5. **Data Freshness**
   - Target: < 15 minutes old
   - Alert: > 30 minutes old

### Grafana Dashboards

- **System Overview**: http://localhost:3001/d/system
- **API Metrics**: http://localhost:3001/d/api
- **ML Pipeline**: http://localhost:3001/d/ml
- **Infrastructure**: http://localhost:3001/d/infra

### Prometheus Queries

```promql
# API request rate
rate(http_requests_total[5m])

# Database connections
pg_stat_database_numbackends

# Redis memory usage
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Model inference duration
histogram_quantile(0.95, model_inference_duration_seconds)
```

## Deployment Procedures

### Development Deployment

```bash
# Start all services
make dev

# Check service health
make health-check

# View logs
docker-compose logs -f
```

### Production Deployment

```bash
# Build and deploy
make k8s-deploy

# Verify deployment
kubectl get pods -n climate-risk

# Check service status
kubectl get svc -n climate-risk
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
```

## Data Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres climate_risk > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres climate_risk < backup.sql
```

### Redis Backup

```bash
# Create backup
docker-compose exec redis redis-cli --rdb /data/backup.rdb

# Restore backup
docker-compose exec redis redis-cli --rdb /data/backup.rdb
```

### MinIO Backup

```bash
# List buckets
docker-compose exec minio mc ls minio/

# Backup specific bucket
docker-compose exec minio mc mirror minio/climate-risk /backup/climate-risk
```

## Performance Tuning

### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE;

-- Reindex if needed
REINDEX DATABASE climate_risk;
```

### Redis Optimization

```bash
# Check memory usage
docker-compose exec redis redis-cli info memory

# Optimize memory
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru
```

### Application Optimization

```bash
# Check worker processes
docker-compose exec backend ps aux

# Monitor memory usage
docker-compose exec backend python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

## Security Procedures

### SSL Certificate Renewal

```bash
# Check certificate expiry
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Renew certificate (if using Let's Encrypt)
certbot renew --nginx
```

### Security Updates

```bash
# Update system packages
apt update && apt upgrade

# Update Docker images
docker-compose pull
docker-compose up -d
```

### Access Control

```bash
# Check user permissions
docker-compose exec postgres psql -U postgres -c "
SELECT usename, usesuper, usecreatedb 
FROM pg_user;
"

# Rotate API keys
# Update JWT_SECRET in .env
# Restart services
```

## Troubleshooting Checklist

1. **Check service status**: `docker-compose ps`
2. **Check logs**: `docker-compose logs [service]`
3. **Check resource usage**: `docker stats`
4. **Check disk space**: `df -h`
5. **Check network connectivity**: `ping [service]`
6. **Check configuration**: Verify `.env` settings
7. **Check dependencies**: Ensure all services are healthy
8. **Check data freshness**: Verify data ingestion pipeline
9. **Check model status**: Verify MLflow model registry
10. **Check alerts**: Review alert processing logs

## Escalation Procedures

1. **Level 1**: Check logs and restart services
2. **Level 2**: Investigate configuration and dependencies
3. **Level 3**: Engage ML team for model issues
4. **Level 4**: Engage infrastructure team for system issues
5. **Level 5**: Escalate to engineering leadership

## Post-Incident Procedures

1. **Document the incident** in the incident log
2. **Root cause analysis** within 24 hours
3. **Update runbook** with new procedures
4. **Implement preventive measures**
5. **Schedule post-mortem** within 1 week
