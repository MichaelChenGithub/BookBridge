# [LOCAL]
## Run service
PORT=9090 python Backend/api/main.py

## Health check
curl -i http://localhost:9090/health

## Recommendations (requires OPENAI_API_KEY set)
curl -i -X POST http://localhost:9090/recommendations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Suggest sci-fi books with strong female leads","history":["Dune"]}'
