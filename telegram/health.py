from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, generate_latest
import psutil

app = FastAPI()

# Metrics
BOT_MESSAGES = Counter('bot_messages_total', 'Total number of bot messages')
BOT_ERRORS = Counter('bot_errors_total', 'Total number of bot errors')
BOT_MEMORY_USAGE = Gauge('bot_memory_usage_bytes', 'Memory usage in bytes')
BOT_CPU_USAGE = Gauge('bot_cpu_usage_percent', 'CPU usage percentage')

@app.get("/health")
async def health_check():
    try:
        # Update metrics
        process = psutil.Process()
        BOT_MEMORY_USAGE.set(process.memory_info().rss)
        BOT_CPU_USAGE.set(process.cpu_percent())
        
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain") 