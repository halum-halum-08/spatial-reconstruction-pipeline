"""
Per-Surface Damage Extraction, Concealed Damage Rule Engine,
and Scope Estimation Module.
"""

from typing import List, Dict, Any, Tuple
from pipeline.schema import (
    DamageRegion,
    ConcealedDamageFlag,
    ScopeLineItem,
    MeasurementWithCI
)
from pipeline.calibration import CalibrationEngine


class DamageAndScopeEngine:
    """Detects surface damages, fires concealed risk rules, and generates scope line items."""

    def __init__(self, calibration: CalibrationEngine):
        self.cal = calibration

        # Standard insurance unit pricing (Xactimate standard rates in USD)
        self.rates = {
            "WTR_EXTRACT": {"desc": "Water extraction and structural drying", "unit": "m2", "price": 42.50},
            "DRYWALL_CUT": {"desc": "Flood-cut drywall 2ft and dispose contaminated materials", "unit": "m", "price": 38.00},
            "DRYWALL_REPAIR": {"desc": "Hang, tape, float and finish 5/8\" drywall", "unit": "m2", "price": 68.00},
            "BASEBOARD_REPLACE": {"desc": "Remove and replace primed baseboard moulding", "unit": "m", "price": 28.50},
            "ANTIMICROBIAL": {"desc": "Apply EPA-registered botanical antimicrobial spray", "unit": "m2", "price": 14.50},
            "PAINT_STAIN_BLOCK": {"desc": "Apply shellac stain-blocking primer and two coats latex paint", "unit": "m2", "price": 32.00},
            "CRACK_EPOXY_STITCH": {"desc": "Clean, V-groove, epoxy inject and carbon fiber stitch structural crack", "unit": "m", "price": 95.00},
            "INSULATION_REPLACE": {"desc": "Remove wet fiberglass batt insulation and replace with R-13", "unit": "m2", "price": 26.00},
            "PLUMB_INSPECT": {"desc": "Plumbing wall exploratory opening and pressure diagnostic test", "unit": "ea", "price": 250.00}
        }

    def process_room_damages(
        self,
        room_id: str,
        damage_specs: List[Dict[str, Any]],
        wall_id_map: Dict[str, Any]
    ) -> Tuple[List[DamageRegion], List[ConcealedDamageFlag], List[ScopeLineItem]]:
        """
        Extracts damage regions, fires concealed-damage expert rules,
        and generates line items keyed to affected surfaces.
        """
        damage_regions: List[DamageRegion] = []
        concealed_flags: List[ConcealedDamageFlag] = []
        scope_items: List[ScopeLineItem] = []

        for dmg in damage_specs:
            did = dmg["damage_id"]
            sid = dmg["surface_id"]
            dclass = dmg["damage_class"]
            w = float(dmg["extent_width_m"])
            h = float(dmg["extent_height_m"])
            area = float(dmg["area_m2"])
            sev = dmg.get("severity", "moderate")

            # Measure with tier-specific calibration
            m_w = self.cal.measure_opening(w) # reuse opening noise for extent
            m_h = self.cal.measure_height(h)
            m_area = self.cal.measure_area(area)

            desc = f"{dclass.replace('_', ' ').capitalize()} detected on surface {sid} ({w:.2f}m x {h:.2f}m)"

            d_region = DamageRegion(
                damage_id=did,
                surface_id=sid,
                damage_class=dclass,
                extent_width=m_w,
                extent_height=m_h,
                surface_area=m_area,
                confidence=0.96 if self.cal.tier == "lidar" else (0.88 if self.cal.tier == "video" else 0.78),
                severity=sev,
                bounding_box_3d=[0.0, 0.0, 0.0, w, h, 0.1],
                description=desc
            )
            damage_regions.append(d_region)

            # --- CONCEALED DAMAGE EXPERT RULES ---
            if dclass == "water_damage":
                # Rule 1: Wet drywall baseboard -> Cavity Moisture Trap
                c_flag_1 = ConcealedDamageFlag(
                    flag_id=f"CONF_{room_id}_{did}_01",
                    surface_id=sid,
                    rule_id="RULE_CONCEALED_WTR_01",
                    rule_name="Wall Cavity Trapped Moisture & Insulation Saturation",
                    risk_score=0.92,
                    trigger_condition="Water damage detected on lower 0.6m of drywall surface",
                    evidence=f"Moisture staining spanning {w:.2f}m along baseboard of {sid}. Wicking height: {h:.2f}m.",
                    recommended_action="Perform 2-foot flood cut, inspect wall cavity and bottom plate, replace wet insulation."
                )
                concealed_flags.append(c_flag_1)

                # Rule 2: Plumbing adjacency check
                if "W2" in sid or "BATH" in room_id or "LIV" in room_id:
                    c_flag_2 = ConcealedDamageFlag(
                        flag_id=f"CONF_{room_id}_{did}_02",
                        surface_id=sid,
                        rule_id="RULE_PLUMB_SUPPLY_02",
                        rule_name="Concealed In-Wall Supply/Drain Stack Compromise",
                        risk_score=0.85,
                        trigger_condition="Moisture adjacent to kitchen/bath plumbing chase",
                        evidence="Damage pattern concentrates along vertical pipe riser chase in partition.",
                        recommended_action="Execute acoustic/thermal pipe leak isolation and inspect riser fittings."
                    )
                    concealed_flags.append(c_flag_2)

                # Scope Line Items for Water Damage
                # 1. Baseboard removal
                q_base = self.cal.measure_length(w + 0.6) # include 30cm buffer on each side
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_01",
                    surface_id=sid,
                    code="BASEBOARD_REPLACE",
                    description=self.rates["BASEBOARD_REPLACE"]["desc"],
                    quantity=q_base,
                    unit="m",
                    unit_price_usd=self.rates["BASEBOARD_REPLACE"]["price"],
                    total_price_usd=round(q_base.value * self.rates["BASEBOARD_REPLACE"]["price"], 2)
                ))

                # 2. Flood cut drywall
                q_cut = self.cal.measure_length(w + 0.6)
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_02",
                    surface_id=sid,
                    code="DRYWALL_CUT",
                    description=self.rates["DRYWALL_CUT"]["desc"],
                    quantity=q_cut,
                    unit="m",
                    unit_price_usd=self.rates["DRYWALL_CUT"]["price"],
                    total_price_usd=round(q_cut.value * self.rates["DRYWALL_CUT"]["price"], 2)
                ))

                # 3. Insulation Replacement
                q_ins = self.cal.measure_area((w + 0.6) * 0.61) # 2ft height = 0.61m
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_03",
                    surface_id=sid,
                    code="INSULATION_REPLACE",
                    description=self.rates["INSULATION_REPLACE"]["desc"],
                    quantity=q_ins,
                    unit="m2",
                    unit_price_usd=self.rates["INSULATION_REPLACE"]["price"],
                    total_price_usd=round(q_ins.value * self.rates["INSULATION_REPLACE"]["price"], 2)
                ))

                # 4. Antimicrobial spray
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_04",
                    surface_id=sid,
                    code="ANTIMICROBIAL",
                    description=self.rates["ANTIMICROBIAL"]["desc"],
                    quantity=q_ins,
                    unit="m2",
                    unit_price_usd=self.rates["ANTIMICROBIAL"]["price"],
                    total_price_usd=round(q_ins.value * self.rates["ANTIMICROBIAL"]["price"], 2)
                ))

                # 5. Drywall patch & paint
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_05",
                    surface_id=sid,
                    code="DRYWALL_REPAIR",
                    description=self.rates["DRYWALL_REPAIR"]["desc"],
                    quantity=q_ins,
                    unit="m2",
                    unit_price_usd=self.rates["DRYWALL_REPAIR"]["price"],
                    total_price_usd=round(q_ins.value * self.rates["DRYWALL_REPAIR"]["price"], 2)
                ))
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_06",
                    surface_id=sid,
                    code="PAINT_STAIN_BLOCK",
                    description=self.rates["PAINT_STAIN_BLOCK"]["desc"],
                    quantity=self.cal.measure_area(max(4.0, q_ins.value * 2.0)), # paint entire affected wall section
                    unit="m2",
                    unit_price_usd=self.rates["PAINT_STAIN_BLOCK"]["price"],
                    total_price_usd=round(max(4.0, q_ins.value * 2.0) * self.rates["PAINT_STAIN_BLOCK"]["price"], 2)
                ))

            elif dclass == "structural_crack":
                # Rule 3: Diagonal crack near ceiling/opening -> Settlement / Deflection
                c_flag_3 = ConcealedDamageFlag(
                    flag_id=f"CONF_{room_id}_{did}_03",
                    surface_id=sid,
                    rule_id="RULE_STRUCT_CORNER_03",
                    rule_name="Differential Structural Settlement & Framing Deflection",
                    risk_score=0.79,
                    trigger_condition="Diagonal stepped shear fracture adjacent to corner/header opening",
                    evidence=f"Continuous fracture propagating {w:.2f}m at upper corner junction of {sid}.",
                    recommended_action="Conduct foundation level survey, check header bearing, and perform structural epoxy stitch."
                )
                concealed_flags.append(c_flag_3)

                # Scope Line Items for Structural Crack
                q_crack = self.cal.measure_length(w)
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_07",
                    surface_id=sid,
                    code="CRACK_EPOXY_STITCH",
                    description=self.rates["CRACK_EPOXY_STITCH"]["desc"],
                    quantity=q_crack,
                    unit="m",
                    unit_price_usd=self.rates["CRACK_EPOXY_STITCH"]["price"],
                    total_price_usd=round(q_crack.value * self.rates["CRACK_EPOXY_STITCH"]["price"], 2)
                ))
                scope_items.append(ScopeLineItem(
                    item_id=f"SCOPE_{room_id}_{did}_08",
                    surface_id=sid,
                    code="PAINT_STAIN_BLOCK",
                    description="Spot prime and blend paint over repaired fracture",
                    quantity=self.cal.measure_area(2.5),
                    unit="m2",
                    unit_price_usd=self.rates["PAINT_STAIN_BLOCK"]["price"],
                    total_price_usd=round(2.5 * self.rates["PAINT_STAIN_BLOCK"]["price"], 2)
                ))

        return damage_regions, concealed_flags, scope_items
