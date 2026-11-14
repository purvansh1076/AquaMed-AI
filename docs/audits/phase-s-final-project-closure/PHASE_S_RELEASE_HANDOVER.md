# Phase S Release Handover

## Environment

- Backend: python -m uvicorn main:app --host 127.0.0.1 --port 8000
- Frontend: npm run dev
- Tests: pytest (backend), npm test (frontend)
- Build: npm run build

## Model artifacts

- backend/data/models/xgb_model.joblib
- backend/data/models/rf_model.joblib
- backend/data/models/encoders.joblib

## Known issues

See PHASE_S_REMAINING_RISKS.md.
