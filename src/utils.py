"""
Utility functions for Smart Waste Management System.
Includes Haversine distance, distance matrix computations,
ReportLab PDF exporter, and Ollama LLM integration with heuristic fallback.
"""

import math
import os
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees).
    Formula:
        d = 2R * arcsin(sqrt(sin^2(Δlat/2) + cos(lat1)*cos(lat2)*sin^2(Δlon/2)))
    Returns distance in kilometers.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_KM * c


def compute_distance_matrix(coords: List[Tuple[float, float]]) -> List[List[float]]:
    """
    Compute pairwise Haversine distance matrix for a list of (latitude, longitude) tuples.
    Returns n x n 2D array of distances in km.
    """
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


def generate_pdf_report(
    priority_data: List[Dict[str, Any]],
    output_path: str,
    summary_stats: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a formal PDF Dispatch Manifest / Priority Collection Report.
    Uses reportlab if available; falls back to generating a markdown/text summary report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1b5e20'),
            spaceAfter=8
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#424242'),
            spaceAfter=14
        )
        
        # Header
        elements.append(Paragraph("Smart Waste Management & Collection Optimization", title_style))
        elements.append(Paragraph(f"Daily Collection Dispatch Manifest — Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Summary Metrics block
        if summary_stats:
            stats_text = (
                f"<b>Total Priority Bins:</b> {summary_stats.get('total_priority_bins', len(priority_data))} &nbsp;|&nbsp; "
                f"<b>Critical / Overflow:</b> {summary_stats.get('critical_count', 'N/A')} &nbsp;|&nbsp; "
                f"<b>Est. Route Distance:</b> {summary_stats.get('total_distance_km', 'N/A')} km"
            )
            elements.append(Paragraph(stats_text, styles['Normal']))
            elements.append(Spacer(1, 12))

        # Table data
        headers = ["Rank", "Bin ID", "Location", "Waste Type", "Fill %", "Category", "Overflow", "Score"]
        table_rows = [headers]
        for row in priority_data[:50]:  # Cap to top 50 in PDF
            table_rows.append([
                str(row.get('rank', '-')),
                str(row.get('bin_id', '-')),
                str(row.get('location_name', '-'))[:20],
                str(row.get('waste_type', '-')),
                f"{row.get('fill_level', 0):.1f}%",
                str(row.get('fill_category', '-')),
                "YES" if row.get('overflow_status') in [True, 1, 'True'] else "No",
                f"{row.get('priority_score', 0):.1f}"
            ])

        col_widths = [36, 54, 130, 75, 48, 64, 54, 45]
        t = Table(table_rows, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f9f9f9')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (4, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(t)
        doc.build(elements)
        return output_path

    except ImportError:
        # Fallback: create plain-text / formatted PDF substitute
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== SMART WASTE MANAGEMENT & COLLECTION OPTIMIZATION ===\n")
            f.write(f"Daily Dispatch Manifest — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            if summary_stats:
                f.write(f"Summary: {json.dumps(summary_stats, indent=2)}\n\n")
            f.write("Rank | Bin ID | Location | Waste Type | Fill % | Category | Overflow | Priority Score\n")
            f.write("-" * 80 + "\n")
            for row in priority_data:
                f.write(f"{row.get('rank','-')} | {row.get('bin_id','-')} | {row.get('location_name','-')} | "
                        f"{row.get('waste_type','-')} | {row.get('fill_level',0):.1f}% | {row.get('fill_category','-')} | "
                        f"{'YES' if row.get('overflow_status') in [True, 1] else 'No'} | {row.get('priority_score',0):.1f}\n")
        return output_path


def query_ollama_llm(prompt: str, model: str = "llama3.2:3b", endpoint: str = "http://localhost:11434/api/generate") -> Dict[str, Any]:
    """
    Attempt to invoke a local Ollama LLM instance for AI summary generation.
    Gracefully falls back to heuristic generation if offline.
    """
    try:
        import urllib.request
        data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as response:
            result = json.loads(response.read().decode("utf-8"))
            return {"success": True, "response": result.get("response", ""), "source": f"Ollama ({model})"}
    except Exception as e:
        return {"success": False, "error": str(e), "source": "heuristic_fallback"}


def generate_heuristic_executive_summary(kpis: Dict[str, Any]) -> str:
    """
    Generate an intelligent analytical summary in plain English when LLM is unavailable.
    """
    total_bins = kpis.get("total_bins", 0)
    critical_bins = kpis.get("critical_bins", 0)
    overflow_bins = kpis.get("overflow_bins", 0)
    avg_fill = kpis.get("avg_fill", 0.0)
    route_dist = kpis.get("optimized_distance_km", 0.0)
    savings = kpis.get("distance_reduction_pct", 0.0)

    urgency_status = "CRITICAL ACTION REQUIRED" if overflow_bins > 0 or critical_bins > 5 else "NORMAL OPERATIONS"

    summary = (
        f"### Operational Status: **{urgency_status}**\n\n"
        f"- **Fleet Assessment:** Monitoring **{total_bins} waste bins** across municipal zones. "
        f"The current fleet average fill level stands at **{avg_fill:.1f}%**.\n"
        f"- **Immediate Urgency:** **{critical_bins} bins** have reached or exceeded the critical threshold (86%+ fill), "
        f"with **{overflow_bins} active overflow alerts** demanding priority dispatch.\n"
        f"- **Route Efficiency:** Optimized dispatch sequencing traverses **{route_dist:.2f} km**, achieving an estimated "
        f"**{savings:.1f}% reduction in travel distance** compared to conventional static-route collection schedules.\n"
        f"- **Actionable Recommendation:** Dispatch Collection Vehicle #1 immediately to clear critical bins in high-density areas "
        f"to prevent secondary spillages and minimize environmental footprint."
    )
    return summary
