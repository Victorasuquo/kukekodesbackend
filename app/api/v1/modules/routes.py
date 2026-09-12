"""
Module API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.db.postgres import get_db
from app.dependencies import get_instructor_user
from app.api.v1.modules.service import ModuleService

router = APIRouter(
    prefix="/api/v1/modules",
    tags=["Modules"],
)


# ============================================================================
# SCHEMAS
# ============================================================================

class ModuleCreateRequest(BaseModel):
    course_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[int] = None


class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order: Optional[int] = None


class ModuleResponse(BaseModel):
    id: str
    course_id: str
    title: str
    description: Optional[str]
    order: int
    created_at: str
    
    class Config:
        from_attributes = True


class ModuleReorderRequest(BaseModel):
    course_id: str
    module_orders: List[dict]  # [{"module_id": str, "order": int}]


# ============================================================================
# ROUTES
# ============================================================================

@router.get("/{module_id}", response_model=dict)
async def get_module(
    module_id: str,
    db: Session = Depends(get_db),
):
    """Get a module with its lessons."""
    return ModuleService.get_module_with_lessons(db, module_id)


@router.get("/course/{course_id}", response_model=List[ModuleResponse])
async def get_course_modules(
    course_id: str,
    db: Session = Depends(get_db),
):
    """Get all modules for a course."""
    modules = ModuleService.get_modules_by_course(db, course_id)
    return [
        ModuleResponse(
            id=str(m.id),
            course_id=str(m.course_id),
            title=m.title,
            description=m.description,
            order=m.order,
            created_at=m.created_at.isoformat(),
        )
        for m in modules
    ]


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    request: ModuleCreateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Create a new module (instructor only)."""
    module = ModuleService.create_module(
        db=db,
        course_id=request.course_id,
        title=request.title,
        description=request.description,
        order=request.order,
    )
    
    return ModuleResponse(
        id=str(module.id),
        course_id=str(module.course_id),
        title=module.title,
        description=module.description,
        order=module.order,
        created_at=module.created_at.isoformat(),
    )


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    request: ModuleUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Update a module (instructor only)."""
    module = ModuleService.update_module(
        db=db,
        module_id=module_id,
        title=request.title,
        description=request.description,
        order=request.order,
    )
    
    return ModuleResponse(
        id=str(module.id),
        course_id=str(module.course_id),
        title=module.title,
        description=module.description,
        order=module.order,
        created_at=module.created_at.isoformat(),
    )


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: str,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Delete a module (instructor only)."""
    ModuleService.delete_module(db, module_id)


@router.post("/reorder", response_model=List[ModuleResponse])
async def reorder_modules(
    request: ModuleReorderRequest,
    current_user: Dict[str, Any] = Depends(get_instructor_user),
    db: Session = Depends(get_db),
):
    """Reorder modules in a course (instructor only)."""
    modules = ModuleService.reorder_modules(
        db=db,
        course_id=request.course_id,
        module_orders=request.module_orders,
    )
    
    return [
        ModuleResponse(
            id=str(m.id),
            course_id=str(m.course_id),
            title=m.title,
            description=m.description,
            order=m.order,
            created_at=m.created_at.isoformat(),
        )
        for m in modules
    ]
