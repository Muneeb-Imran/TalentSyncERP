from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import psycopg2

app = FastAPI()

# Enable CORS so your frontend can talk to your backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the database URL from environment variables (secure practice)
DATABASE_URL = os.getenv("DATABASE_URL", "your_local_fallback_connection_string")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.get("/")
def home():
    return {"status": "TalentSync ERP Backend is running successfully!"}

@app.get("/appraisal/{employee_id}")
def get_performance_review(employee_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQL query modified for PostgreSQL syntax
        cursor.execute(
            'SELECT "peerfeedbackscore", "managerfeedbackscore" FROM "performanceappraisals" WHERE "employeeid" = %s;', 
            (employee_id,)
        )
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Employee performance record not found")
            
        peer_score, manager_score = row
        
        # Strategic HR Logic: Weighted Performance Calculation
        final_appraisal_score = (peer_score * 0.4) + (manager_score * 0.6)
        
        return {
            "employee_id": employee_id,
            "final_appraisal_score": round(final_appraisal_score, 2),
            "status": "Processed",
            "action_item": "Promote" if final_appraisal_score >= 4.5 else "Standard Review"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))