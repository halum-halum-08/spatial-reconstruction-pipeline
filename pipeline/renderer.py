"""
Plan Rendering Engine: Generates architectural SVG floor plans
and interactive, self-contained HTML visualizers.
"""

import os
from typing import Dict, Any, List
import numpy as np
from pipeline.schema import PropertyPlan


class FloorplanRenderer:
    """Renders complete 2D floor plans with dimensions, openings, and damage tags."""

    def __init__(self, plan: PropertyPlan):
        self.plan = plan

    def render_svg(self, output_svg_path: str):
        """Generates clean, dimensioned SVG floor plan."""
        # Find global bounding box
        all_pts = []
        for r in self.plan.rooms:
            for w in r.walls:
                all_pts.append(w.start_point)
                all_pts.append(w.end_point)

        if not all_pts:
            return

        xs = [p[0] for p in all_pts]
        zs = [p[1] for p in all_pts]
        min_x, max_x = min(xs) - 1.0, max(xs) + 1.0
        min_z, max_z = min(zs) - 1.0, max(zs) + 1.0

        scale = 80.0 # pixels per meter
        width_px = int((max_x - min_x) * scale)
        height_px = int((max_z - min_z) * scale)

        def to_svg_x(x: float) -> float:
            return (x - min_x) * scale

        def to_svg_y(z: float) -> float:
            return (z - min_z) * scale

        room_colors = {
            "living_room": "#EBF3FB",
            "bathroom": "#E8F8F5",
            "dining_room": "#FEF9E7",
            "hallway": "#F4F6F6"
        }

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px} {height_px}" width="100%" height="100%">')
        svg.append('<defs>')
        svg.append('  <style>')
        svg.append('    .room-poly { stroke: none; fill-opacity: 0.85; transition: fill 0.3s; }')
        svg.append('    .wall-line { stroke: #2C3E50; stroke-width: 6; stroke-linecap: round; }')
        svg.append('    .opening-door { stroke: #E67E22; stroke-width: 5; stroke-dasharray: 4,4; }')
        svg.append('    .opening-win { stroke: #2980B9; stroke-width: 4; }')
        svg.append('    .room-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: bold; fill: #2C3E50; text-anchor: middle; }')
        svg.append('    .dim-label { font-family: monospace; font-size: 11px; fill: #7F8C8D; text-anchor: middle; }')
        svg.append('    .damage-marker { fill: #E74C3C; stroke: #C0392B; stroke-width: 2; cursor: pointer; }')
        svg.append('  </style>')
        svg.append('</defs>')
        svg.append(f'<rect width="{width_px}" height="{height_px}" fill="#FAFAFA" />')

        # 1. Draw Room Polygons (Background Fills)
        for r in self.plan.rooms:
            if len(r.polygon_2d) >= 3:
                pts_str = " ".join([f"{to_svg_x(p[0])},{to_svg_y(p[1])}" for p in r.polygon_2d])
                fill_col = room_colors.get(r.room_type, "#F2F4F4")
                svg.append(f'<polygon class="room-poly" points="{pts_str}" fill="{fill_col}" id="poly-{r.room_id}"/>')

        # 2. Draw Walls and Openings
        for r in self.plan.rooms:
            for w in r.walls:
                x1, y1 = to_svg_x(w.start_point[0]), to_svg_y(w.start_point[1])
                x2, y2 = to_svg_x(w.end_point[0]), to_svg_y(w.end_point[1])
                svg.append(f'<line class="wall-line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" />')

                # Wall Dimension label
                mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                nx, ny = w.normal[0] * 14.0, w.normal[1] * 14.0
                svg.append(f'<text class="dim-label" x="{mx + nx:.1f}" y="{my + ny:.1f}">{w.length.value:.2f}m (±{w.length.standard_error*100:.1f}cm)</text>')

                # Draw Openings on Wall
                for op in w.openings:
                    # Interpolate along wall line
                    t_start = op.start_pos / max(1e-4, w.length.value)
                    t_end = min(1.0, (op.start_pos + op.width.value) / max(1e-4, w.length.value))
                    ox1 = x1 + t_start * (x2 - x1)
                    oy1 = y1 + t_start * (y2 - y1)
                    ox2 = x1 + t_end * (x2 - x1)
                    oy2 = y1 + t_end * (y2 - y1)
                    op_cls = "opening-win" if op.type == "window" else "opening-door"
                    svg.append(f'<line class="{op_cls}" x1="{ox1:.1f}" y1="{oy1:.1f}" x2="{ox2:.1f}" y2="{oy2:.1f}" />')

        # 3. Room Labels & Area
        for r in self.plan.rooms:
            if r.polygon_2d:
                poly_pts = np.array(r.polygon_2d)
                cx, cy = np.mean(poly_pts[:, 0]), np.mean(poly_pts[:, 1])
                sx, sy = to_svg_x(cx), to_svg_y(cy)
                svg.append(f'<text class="room-label" x="{sx:.1f}" y="{sy:.1f}">{r.name}</text>')
                svg.append(f'<text class="dim-label" x="{sx:.1f}" y="{sy + 18:.1f}">{r.floor_area.value:.2f} m² | H: {r.ceiling_height.value:.2f}m</text>')

        # 4. Damage Markers
        for r in self.plan.rooms:
            for dmg in r.damage_regions:
                # Place near affected room center
                if r.polygon_2d:
                    cx = np.mean([p[0] for p in r.polygon_2d]) + 0.5
                    cy = np.mean([p[1] for p in r.polygon_2d]) - 0.4
                    sx, sy = to_svg_x(cx), to_svg_y(cy)
                    svg.append(f'<circle class="damage-marker" cx="{sx:.1f}" cy="{sy:.1f}" r="8" />')
                    svg.append(f'<text x="{sx + 12:.1f}" y="{sy + 4:.1f}" font-size="10" font-weight="bold" fill="#C0392B">{dmg.damage_class.upper()} ({dmg.extent_width.value:.2f}m)</text>')

        svg.append('</svg>')

        with open(output_svg_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(svg))

    def render_interactive_html(self, output_html_path: str, svg_rel_path: str = "floorplan.svg"):
        """Generates self-contained interactive inspection dashboard."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Property Survey Plan - {self.plan.capture_id}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --primary: #1A365D;
      --accent: #3182CE;
      --bg: #F7FAFC;
      --card-bg: #FFFFFF;
      --border: #E2E8F0;
      --text: #2D3748;
      --danger: #E53E3E;
      --warning: #DD6B20;
      --success: #38A169;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      margin: 0;
      padding: 24px;
      background: var(--bg);
      color: var(--text);
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      padding: 20px 28px;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      margin-bottom: 24px;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-lidar {{ background: #C6F6D5; color: #22543D; }}
    .badge-video {{ background: #BEE3F8; color: #2A4365; }}
    .badge-photo {{ background: #FEFCBF; color: #744210; }}
    .grid {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }}
    .card {{
      background: var(--card-bg);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .plan-viewer {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #FAFAFA;
      padding: 16px;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 13px;
    }}
    th {{
      background: #EDF2F7;
      font-weight: 600;
      color: var(--primary);
    }}
    .flag-box {{
      background: #FFF5F5;
      border-left: 4px solid var(--danger);
      padding: 12px 16px;
      margin-bottom: 12px;
      border-radius: 4px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="margin:0 0 6px 0; font-size:24px; color:var(--primary);">Survey Floor Plan & Scope Report</h1>
      <div style="font-size:14px; color:#718096;">
        Capture ID: <strong>{self.plan.capture_id}</strong> | Device: <strong>{self.plan.device_model}</strong> | Recorded: {self.plan.timestamp}
      </div>
    </div>
    <div>
      <span class="badge badge-{self.plan.input_tier}">{self.plan.input_tier.upper()} TIER</span>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2 style="margin-top:0; font-size:18px;">Dimensioned Floor Plan</h2>
      <div class="plan-viewer">
        <img src="{svg_rel_path}" alt="Floor Plan" style="max-width:100%; height:auto;" />
      </div>
      <div style="display:flex; justify-content:space-around; margin-top:20px; font-size:14px;">
        <div><strong>Total Interior Area:</strong> {self.plan.total_floor_area.value:.2f} m² (CI: [{self.plan.total_floor_area.ci_lower:.2f}, {self.plan.total_floor_area.ci_upper:.2f}])</div>
        <div><strong>Total Rooms:</strong> {len(self.plan.rooms)}</div>
        <div><strong>Walls Bounded:</strong> {self.plan.total_walls_count}</div>
        <div><strong>Openings Detected:</strong> {self.plan.total_openings_count}</div>
      </div>
    </div>

    <div>
      <div class="card" style="margin-bottom:24px;">
        <h2 style="margin-top:0; font-size:18px; color:var(--danger);">Concealed Damage Risk Flags</h2>
        {"".join([f'''
        <div class="flag-box">
          <div style="font-weight:bold; color:var(--danger);">{f.rule_name}</div>
          <div style="font-size:12px; margin-top:4px;"><strong>Trigger:</strong> {f.trigger_condition}</div>
          <div style="font-size:12px; margin-top:4px;"><strong>Evidence:</strong> {f.evidence}</div>
          <div style="font-size:12px; margin-top:4px; color:#742A2A;"><strong>Recommended Action:</strong> {f.recommended_action}</div>
        </div>
        ''' for r in self.plan.rooms for f in r.concealed_flags]) if any(r.concealed_flags for r in self.plan.rooms) else '<p style="color:#718096;">No concealed damage risks flagged.</p>'}
      </div>

      <div class="card">
        <h2 style="margin-top:0; font-size:18px; color:var(--primary);">Xactimate Remediation Scope</h2>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Surface</th>
              <th>Qty</th>
              <th>Total ($)</th>
            </tr>
          </thead>
          <tbody>
            {"".join([f'''
            <tr>
              <td><strong>{item.code}</strong></td>
              <td>{item.surface_id}</td>
              <td>{item.quantity.value:.2f} {item.unit}</td>
              <td>${item.total_price_usd:.2f}</td>
            </tr>
            ''' for r in self.plan.rooms for item in r.scope_items])}
          </tbody>
          <tfoot>
            <tr style="font-weight:bold; background:#EDF2F7;">
              <td colspan="3">Estimated Remediation Total:</td>
              <td>${self.plan.remediation_total_usd:,.2f}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</body>
</html>
"""
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html)
