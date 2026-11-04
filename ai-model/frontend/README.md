# Frontend (React + Vite) — Phase 7

> **Note**: Frontend development is deferred for now as per project plan.

When you are ready to build the frontend interface in Phase 7:

```bash
# Initialize Vite React project
npm create vite@latest . -- --template react

# Install dependencies
npm install axios lucide-react

# Run dev server
npm run dev
```

### Integration Details:
- **Backend API**: `http://127.0.0.1:8000`
- **Inference Endpoint**: `POST /predict`
- **Request Payload**: `{"area": 1800}`
- **Response**: `{"area": 1800, "predicted_price": 369154.79, "formatted_price": "$369,154.79"}`

