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
@app.get("/analytics")
def get_dashboard_analytics(peer_weight: float = 0.4, manager_weight: float = 0.6):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # JOIN the tables to get the Name, Role, and Retention Risk alongside the scores
        cursor.execute('''
            SELECT c.employeeid, c.fullname, c.jobrole, c.retentionriskscore, 
                   p.peerfeedbackscore, p.managerfeedbackscore, p.trainingrecommended 
            FROM Consultants c
            LEFT JOIN PerformanceAppraisals p ON c.employeeid = p.employeeid;
        ''')
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        team_data = []
        for row in rows:
            emp_id, name, role, risk_score, peer, manager, training = row
            
            # Handle empty values just in case an employee hasn't been reviewed yet
            peer = peer or 0
            manager = manager or 0
            risk_score = risk_score or 0.0
            
            final_score = (peer * peer_weight) + (manager * manager_weight)
            
            team_data.append({
                "employee_id": emp_id,
                "name": name,
                "role": role,
                "appraisal_score": round(final_score, 2),
                "retention_risk_percent": int(risk_score * 100),
                "suggested_track": training or "Pending Review"
            })
            
        return {"team_analytics": team_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
