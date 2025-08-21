# main.py - Enhanced FastAPI backend for Zerim To-Do Application
# Integrates with the advanced frontend features and provides comprehensive API

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
import json
import os
from pathlib import Path

# Pydantic Models
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: str = "#4F46E5"
    icon: Optional[str] = "📋"
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    category_id: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    tags: List[str] = []
    subtasks: List[Subtask] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # minutes
    actual_duration: Optional[int] = None  # minutes
    notes: Optional[str] = None
    reminder_enabled: bool = False
    reminder_time: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    category_id: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    tags: List[str] = []
    estimated_duration: Optional[int] = None
    notes: Optional[str] = None
    reminder_enabled: bool = False
    reminder_time: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    category_id: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    tags: Optional[List[str]] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    notes: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[datetime] = None

class AnalyticsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    tasks_by_priority: Dict[str, int]
    tasks_by_category: Dict[str, int]
    tasks_by_status: Dict[str, int]
    productivity_streak: int
    daily_completion_average: float
    weekly_stats: Dict[str, int]
    monthly_stats: Dict[str, int]

class BulkTaskUpdate(BaseModel):
    task_ids: List[str]
    updates: TaskUpdate

# Initialize FastAPI app
app = FastAPI(
    title="Zerim To-Do API",
    description="Advanced To-Do List API with comprehensive task management features",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# In-memory storage (in production, use a proper database)
tasks: List[Task] = []
categories: List[Category] = []

# Initialize default categories
default_categories = [
    Category(name="Personal", color="#10B981", icon="👤", description="Personal tasks and activities"),
    Category(name="Work", color="#3B82F6", icon="💼", description="Work-related tasks and projects"),
    Category(name="Shopping", color="#F59E0B", icon="🛒", description="Shopping lists and errands"),
    Category(name="Health", color="#EF4444", icon="❤️", description="Health and fitness goals"),
    Category(name="Learning", color="#8B5CF6", icon="📚", description="Educational and learning tasks"),
    Category(name="Home", color="#06B6D4", icon="🏠", description="Household chores and maintenance")
]
categories.extend(default_categories)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/icons", StaticFiles(directory="icons"), name="icons")

# Root endpoint - serve the main HTML file
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/settings.html", response_class=HTMLResponse)
async def read_settings():
    with open("settings.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/analytics.html", response_class=HTMLResponse)
async def read_analytics():
    with open("analytics.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/manifest.json")
async def read_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def read_service_worker():
    return FileResponse("sw.js")

# Task Management Endpoints
@app.get("/api/tasks", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[Priority] = None,
    category_id: Optional[str] = None,
    completed: Optional[bool] = None,
    overdue: Optional[bool] = None,
    search: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1),
    offset: Optional[int] = Query(0, ge=0)
):
    """Get tasks with optional filtering and pagination"""
    filtered_tasks = tasks.copy()
    
    # Apply filters
    if status:
        filtered_tasks = [t for t in filtered_tasks if t.status == status]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
    if category_id:
        filtered_tasks = [t for t in filtered_tasks if t.category_id == category_id]
    if completed is not None:
        filtered_tasks = [t for t in filtered_tasks if t.completed == completed]
    if overdue:
        now = datetime.now()
        filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date < now and not t.completed]
    if search:
        search_lower = search.lower()
        filtered_tasks = [
            t for t in filtered_tasks 
            if search_lower in t.title.lower() or 
            (t.description and search_lower in t.description.lower()) or
            any(search_lower in tag.lower() for tag in t.tags)
        ]
    
    # Sort by created_at descending
    filtered_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    if limit:
        filtered_tasks = filtered_tasks[offset:offset + limit]
    else:
        filtered_tasks = filtered_tasks[offset:]
    
    return filtered_tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    task = Task(**task_data.dict())
    tasks.append(task)
    return task

@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task by ID"""
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate):
    """Update a specific task"""
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    for field, value in task_update.dict(exclude_unset=True).items():
        if hasattr(task, field):
            setattr(task, field, value)
    
    task.updated_at = datetime.now()
    
    # Handle completion
    if task_update.completed is not None:
        if task_update.completed and not task.completed:
            task.completed_at = datetime.now()
            task.status = TaskStatus.COMPLETED
        elif not task_update.completed and task.completed:
            task.completed_at = None
            task.status = TaskStatus.PENDING
    
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a specific task"""
    global tasks
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks = [t for t in tasks if t.id != task_id]
    return {"message": "Task deleted successfully"}

# Subtask Management
@app.post("/api/tasks/{task_id}/subtasks", response_model=Task)
async def add_subtask(task_id: str, subtask_title: str = Body(..., embed=True)):
    """Add a subtask to a task"""
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    subtask = Subtask(title=subtask_title)
    task.subtasks.append(subtask)
    task.updated_at = datetime.now()
    return task

@app.put("/api/tasks/{task_id}/subtasks/{subtask_id}", response_model=Task)
async def update_subtask(task_id: str, subtask_id: str, completed: bool = Body(..., embed=True)):
    """Update a subtask's completion status"""
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    subtask = next((s for s in task.subtasks if s.id == subtask_id), None)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    subtask.completed = completed
    task.updated_at = datetime.now()
    return task

@app.delete("/api/tasks/{task_id}/subtasks/{subtask_id}", response_model=Task)
async def delete_subtask(task_id: str, subtask_id: str):
    """Delete a subtask from a task"""
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.subtasks = [s for s in task.subtasks if s.id != subtask_id]
    task.updated_at = datetime.now()
    return task

# Bulk Operations
@app.put("/api/tasks/bulk", response_model=List[Task])
async def bulk_update_tasks(bulk_update: BulkTaskUpdate):
    """Update multiple tasks at once"""
    updated_tasks = []
    
    for task_id in bulk_update.task_ids:
        task = next((t for t in tasks if t.id == task_id), None)
        if task:
            for field, value in bulk_update.updates.dict(exclude_unset=True).items():
                if hasattr(task, field):
                    setattr(task, field, value)
            task.updated_at = datetime.now()
            updated_tasks.append(task)
    
    return updated_tasks

@app.delete("/api/tasks/bulk")
async def bulk_delete_tasks(task_ids: List[str] = Body(...)):
    """Delete multiple tasks at once"""
    global tasks
    deleted_count = 0
    
    for task_id in task_ids:
        if any(t.id == task_id for t in tasks):
            tasks = [t for t in tasks if t.id != task_id]
            deleted_count += 1
    
    return {"message": f"Deleted {deleted_count} tasks"}

@app.post("/api/tasks/clear-completed")
async def clear_completed_tasks():
    """Remove all completed tasks"""
    global tasks
    completed_count = len([t for t in tasks if t.completed])
    tasks = [t for t in tasks if not t.completed]
    return {"message": f"Cleared {completed_count} completed tasks"}

# Category Management
@app.get("/api/categories", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    return categories

@app.post("/api/categories", response_model=Category, status_code=201)
async def create_category(category: Category):
    """Create a new category"""
    categories.append(category)
    return category

@app.put("/api/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, category_update: Category):
    """Update a category"""
    category = next((c for c in categories if c.id == category_id), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for field, value in category_update.dict(exclude_unset=True).items():
        if hasattr(category, field):
            setattr(category, field, value)
    
    return category

@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: str):
    """Delete a category and unassign it from tasks"""
    global categories
    category = next((c for c in categories if c.id == category_id), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Unassign category from tasks
    for task in tasks:
        if task.category_id == category_id:
            task.category_id = None
    
    categories = [c for c in categories if c.id != category_id]
    return {"message": "Category deleted successfully"}

# Analytics Endpoints
@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get comprehensive analytics data"""
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.completed])
    pending_tasks = len([t for t in tasks if not t.completed])
    
    now = datetime.now()
    overdue_tasks = len([
        t for t in tasks 
        if t.due_date and t.due_date < now and not t.completed
    ])
    
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Tasks by priority
    tasks_by_priority = {
        priority.value: len([t for t in tasks if t.priority == priority])
        for priority in Priority
    }
    
    # Tasks by category
    tasks_by_category = {}
    for category in categories:
        count = len([t for t in tasks if t.category_id == category.id])
        if count > 0:
            tasks_by_category[category.name] = count
    
    # Tasks by status
    tasks_by_status = {
        status.value: len([t for t in tasks if t.status == status])
        for status in TaskStatus
    }
    
    # Calculate productivity streak and averages
    productivity_streak = calculate_productivity_streak()
    daily_average = completed_tasks / max((now - min([t.created_at for t in tasks] + [now])).days, 1) if tasks else 0
    
    return AnalyticsResponse(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        completion_rate=completion_rate,
        tasks_by_priority=tasks_by_priority,
        tasks_by_category=tasks_by_category,
        tasks_by_status=tasks_by_status,
        productivity_streak=productivity_streak,
        daily_completion_average=daily_average,
        weekly_stats=get_weekly_stats(),
        monthly_stats=get_monthly_stats()
    )

@app.get("/api/analytics/daily")
async def get_daily_analytics(days: int = Query(7, ge=1, le=365)):
    """Get daily completion statistics"""
    daily_stats = {}
    
    for i in range(days):
        day = datetime.now().date() - timedelta(days=i)
        completed_on_day = [
            t for t in tasks 
            if t.completed_at and t.completed_at.date() == day
        ]
        daily_stats[day.isoformat()] = len(completed_on_day)
    
    return daily_stats

# Data Management
@app.get("/api/export")
async def export_data():
    """Export all data as JSON"""
    return {
        "tasks": [task.dict() for task in tasks],
        "categories": [category.dict() for category in categories],
        "export_date": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/import")
async def import_data(data: Dict[str, Any] = Body(...)):
    """Import data from JSON"""
    global tasks, categories
    
    if "tasks" in data:
        imported_tasks = []
        for task_data in data["tasks"]:
            try:
                task = Task(**task_data)
                imported_tasks.append(task)
            except Exception as e:
                continue
        tasks.extend(imported_tasks)
    
    if "categories" in data:
        imported_categories = []
        for category_data in data["categories"]:
            try:
                category = Category(**category_data)
                # Avoid duplicate categories
                if not any(c.id == category.id for c in categories):
                    imported_categories.append(category)
            except Exception as e:
                continue
        categories.extend(imported_categories)
    
    return {
        "message": "Data imported successfully",
        "tasks_imported": len(data.get("tasks", [])),
        "categories_imported": len(data.get("categories", []))
    }

@app.post("/api/reset")
async def reset_all_data():
    """Reset all data (tasks and categories)"""
    global tasks, categories
    tasks = []
    categories = default_categories.copy()
    return {"message": "All data has been reset"}

# Utility functions
def calculate_productivity_streak():
    """Calculate current productivity streak (days with completed tasks)"""
    if not tasks:
        return 0
    
    completed_tasks_by_date = {}
    for task in tasks:
        if task.completed_at:
            date_key = task.completed_at.date()
            if date_key not in completed_tasks_by_date:
                completed_tasks_by_date[date_key] = 0
            completed_tasks_by_date[date_key] += 1
    
    if not completed_tasks_by_date:
        return 0
    
    streak = 0
    current_date = datetime.now().date()
    
    while current_date in completed_tasks_by_date:
        streak += 1
        current_date -= timedelta(days=1)
    
    return streak

def get_weekly_stats():
    """Get weekly completion statistics"""
    weekly_stats = {}
    for i in range(4):  # Last 4 weeks
        week_start = datetime.now() - timedelta(weeks=i+1)
        week_end = datetime.now() - timedelta(weeks=i)
        
        completed_in_week = [
            t for t in tasks 
            if t.completed_at and week_start <= t.completed_at <= week_end
        ]
        weekly_stats[f"Week {i+1}"] = len(completed_in_week)
    
    return weekly_stats

def get_monthly_stats():
    """Get monthly completion statistics"""
    monthly_stats = {}
    for i in range(6):  # Last 6 months
        month_start = datetime.now().replace(day=1) - timedelta(days=i*30)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        
        completed_in_month = [
            t for t in tasks 
            if t.completed_at and month_start <= t.completed_at <= month_end
        ]
        monthly_stats[month_start.strftime("%B %Y")] = len(completed_in_month)
    
    return monthly_stats

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tasks_count": len(tasks),
        "categories_count": len(categories)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)