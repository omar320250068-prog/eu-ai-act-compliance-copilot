import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncpg
import os
import uuid

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")

app = FastAPI(title="EU AI Act Compliance Backend")

class AssessRequest(BaseModel):
    submitter_email: str
    system_name: str = "Test Assessment System"
    domain: str = "Legal"
    purpose_description: str = "Testing backend database pipeline"
    tech_stack: str = "FastAPI + Docker"

@app.on_event("startup")
async def startup_event():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set inside internal backend .env")
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.pool.close()

@app.post("/api/assess")
async def assess(req: AssessRequest):
    project_id = str(uuid.uuid4())
    assessment_id = str(uuid.uuid4())
    
    async with app.state.pool.acquire() as conn:
        try:
            # 1. Insert into projects table (aligned with Omar's schema)
            await conn.execute("""
                INSERT INTO projects (id, name, description, submitter_email, deployment_context)
                VALUES ($1, $2, $3, $4, $5)
            """, 
            project_id, 
            req.system_name, 
            f"Tech Stack: {req.tech_stack} | Purpose: {req.purpose_description}", 
            req.submitter_email, 
            req.domain
            )
            
            # 2. Insert into assessments table (aligned with Omar's schema)
            raw_output = json.dumps({"ai_notes": "Mock validation connecting Ahmed's backend with Omar's DB layer."})
            await conn.execute("""
                INSERT INTO assessments (id, project_id, risk_tier, confidence_score, reasoning, raw_model_output, model_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
            assessment_id, 
            project_id, 
            "HIGH", 
            0.9850, 
            "System identified as High Risk based on preliminary test data.", 
            raw_output, 
            "v1.0"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")
            
    return {
        "assessment_id": assessment_id, 
        "project_id": project_id,
        "status": "Success, AI results pushed directly to Omar's DB layer."
    }

@app.get("/api/rules")
async def get_compliance_rules(tier: str = None):
    """Fetch compliance rules from the seeded database (Ismail's work)."""
    async with app.state.pool.acquire() as conn:
        try:
            query = "SELECT rule_code, title, risk_tier, description FROM compliance_rules WHERE is_active = TRUE"
            args = []
            
            if tier:
                query += " AND risk_tier = $1"
                args.append(tier.upper())
                
            query += " ORDER BY rule_code"
            
            records = await conn.fetch(query, *args)
            return {"count": len(records), "rules": [dict(r) for r in records]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failure: {str(e)}")
