"""
Output contract schema for floor plan generation, damage detection,
and scope estimation per Round 1 and Round 2 specifications.
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field


class MeasurementWithCI(BaseModel):
    """Measurement value with calibrated confidence interval and standard error."""
    value: float = Field(..., description="Estimated metric measurement value")
    unit: str = Field(default="m", description="Unit of measurement: m, m2, deg, etc.")
    ci_lower: float = Field(..., description="Lower bound of confidence interval (95%)")
    ci_upper: float = Field(..., description="Upper bound of confidence interval (95%)")
    confidence_level: float = Field(default=0.95, description="Statistical confidence level (e.g. 0.95)")
    standard_error: float = Field(..., description="Calibrated standard error (1-sigma)")

    @classmethod
    def create(cls, value: float, std_err: float, unit: str = "m", confidence_level: float = 0.95):
        # 1.96 for 95% confidence interval
        z = 1.96 if confidence_level == 0.95 else 2.576
        margin = z * std_err
        return cls(
            value=round(float(value), 4),
            unit=unit,
            ci_lower=round(float(max(0.0, value - margin)), 4),
            ci_upper=round(float(value + margin), 4),
            confidence_level=confidence_level,
            standard_error=round(float(std_err), 4)
        )


class Opening(BaseModel):
    """Door, window, or passage opening on a wall."""
    opening_id: str
    type: str = Field(..., description="'door', 'window', or 'passage'")
    wall_id: str
    start_pos: float = Field(..., description="Distance along wall from start vertex (m)")
    width: MeasurementWithCI
    height: MeasurementWithCI
    connected_room_id: Optional[str] = Field(default=None, description="Adjoining room id if inter-room opening")
    center_world_2d: List[float] = Field(default_factory=list, description="Global [x, z] position")


class Wall(BaseModel):
    """Wall segment bounding a room."""
    wall_id: str
    start_point: List[float] = Field(..., description="[x, z] 2D coordinates of start vertex (m)")
    end_point: List[float] = Field(..., description="[x, z] 2D coordinates of end vertex (m)")
    length: MeasurementWithCI
    height: MeasurementWithCI
    normal: List[float] = Field(..., description="[nx, nz] 2D outward unit normal vector")
    surface_area: MeasurementWithCI
    openings: List[Opening] = Field(default_factory=list)


class DamageRegion(BaseModel):
    """Surface-level staged or discovered damage region."""
    damage_id: str
    surface_id: str = Field(..., description="Wall ID, 'floor', or 'ceiling'")
    damage_class: str = Field(..., description="'water_damage', 'structural_crack', 'mold_mildew', 'impact_puncture'")
    extent_width: MeasurementWithCI
    extent_height: MeasurementWithCI
    surface_area: MeasurementWithCI
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(default="moderate", description="'minor', 'moderate', 'severe'")
    bounding_box_3d: Optional[List[float]] = None
    description: str


class ConcealedDamageFlag(BaseModel):
    """Concealed damage risk flag fired by domain expert rules."""
    flag_id: str
    surface_id: str
    rule_id: str = Field(..., description="Unique code of the fired expert rule")
    rule_name: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    trigger_condition: str
    evidence: str
    recommended_action: str


class ScopeLineItem(BaseModel):
    """Remediation line item keyed to affected surfaces."""
    item_id: str
    surface_id: str
    code: str = Field(..., description="Xactimate / insurance standard remediation code")
    description: str
    quantity: MeasurementWithCI
    unit: str = Field(..., description="'m2', 'm', 'ea'")
    unit_price_usd: float
    total_price_usd: float


class RoomPlan(BaseModel):
    """Dimensioned per-room model."""
    room_id: str
    name: str
    room_type: str = Field(default="room", description="'living_room', 'bathroom', 'dining_room', 'hallway'")
    floor_area: MeasurementWithCI
    ceiling_height: MeasurementWithCI
    walls: List[Wall]
    openings: List[Opening]
    polygon_2d: List[List[float]] = Field(..., description="Closed 2D polygon vertices [[x, z], ...]")
    damage_regions: List[DamageRegion] = Field(default_factory=list)
    concealed_flags: List[ConcealedDamageFlag] = Field(default_factory=list)
    scope_items: List[ScopeLineItem] = Field(default_factory=list)


class PropertyPlan(BaseModel):
    """Complete stitched multi-room property floor plan and inspection contract."""
    capture_id: str
    input_tier: str = Field(..., description="'lidar', 'video', or 'photo'")
    device_model: str
    timestamp: str
    rooms: List[RoomPlan]
    total_floor_area: MeasurementWithCI
    total_walls_count: int
    total_openings_count: int
    adjacency_graph: List[Dict[str, Any]] = Field(default_factory=list, description="Adjoining room pairs and connectors")
    drift_correction_applied: bool = Field(default=True)
    drift_metrics: Dict[str, Any] = Field(default_factory=dict)
    remediation_total_usd: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
