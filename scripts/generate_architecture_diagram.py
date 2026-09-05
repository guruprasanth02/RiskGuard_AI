"""
scripts/generate_architecture_diagram.py
Generates docs/architecture.png illustrating RiskGuard AI system architecture.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = DOCS_DIR / "architecture.png"

fig, ax = plt.subplots(figsize=(12, 14), dpi=300)
fig.patch.set_facecolor('#0a0e1a')
ax.set_facecolor('#0a0e1a')
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Title
ax.text(50, 96, "RiskGuard AI — System Architecture", fontsize=20, fontweight='bold',
        color='#f0f4ff', ha='center', va='center')
ax.text(50, 93, "Explainable Transaction Risk Manager for Fintech & Payments", fontsize=11,
        color='#8b9dc3', ha='center', va='center')

def draw_box(x, y, w, h, title, subtitle, color, border_color='#3b82f6', is_sub=False):
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.5,rounding_size=1.5",
        linewidth=2 if not is_sub else 1.2,
        edgecolor=border_color,
        facecolor=color,
    )
    ax.add_patch(rect)
    ax.text(x + w/2, y + h*0.62 if subtitle else y + h/2, title,
            fontsize=12 if not is_sub else 10, fontweight='bold', color='#ffffff', ha='center', va='center')
    if subtitle:
        ax.text(x + w/2, y + h*0.30, subtitle,
                fontsize=8.5 if not is_sub else 8, color='#94a3b8', ha='center', va='center')

def draw_arrow(x1, y1, x2, y2, label=""):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color="#38bdf8", lw=2.0, mutation_scale=15)
    )
    if label:
        mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
        ax.text(mid_x + 1.5, mid_y, label, fontsize=8, color="#38bdf8", fontweight='semibold')

# Layer 1: Frontend
draw_box(20, 82, 60, 7, "React 18 + Vite Frontend Dashboard", "Interactive Risk Dashboard · SHAP Factor Visualizer · Manual Audit Workflow", "#1e293b", "#38bdf8")

# Arrow 1 -> 2
draw_arrow(50, 82, 50, 75, "HTTPS / REST JSON")

# Layer 2: API Gateway
draw_box(20, 68, 60, 7, "FastAPI Backend Service", "Pydantic v2 Validation · /predict · /investigate · Session Metrics Engine", "#1e293b", "#38bdf8")

# Arrow 2 -> 3
draw_arrow(50, 68, 50, 60, "Validated Payload")

# Layer 3: Risk Prediction Engine Container
container = patches.FancyBboxPatch(
    (14, 27), 72, 33,
    boxstyle="round,pad=0.8,rounding_size=2",
    linewidth=1.8, linestyle='--',
    edgecolor='#6366f1',
    facecolor='#111827',
)
ax.add_patch(container)
ax.text(50, 57.5, "CORE RISK PREDICTION & EXPLAINABILITY ENGINE", fontsize=11,
        fontweight='bold', color='#a5b4fc', ha='center', va='center')

# Sub-components inside Container
draw_box(18, 46, 64, 8, "Zero-Leakage Pre-Authorization Preprocessor",
         "Amount Scaling · Hourly Rhythms · Drain Attempt Flag · Balance Ratios", "#1e293b", "#818cf8", is_sub=True)

draw_arrow(50, 46, 50, 41)

draw_box(18, 33, 30, 8, "Fraud ML Model", "RandomForest (Val PR-AUC 1.000) / XGBoost", "#1e293b", "#10b981", is_sub=True)
draw_box(52, 33, 30, 8, "SHAP Explainability", "TreeExplainer Attribution · Positive & Mitigating Factors", "#1e293b", "#f59e0b", is_sub=True)

draw_arrow(50, 33, 50, 24, "Probability + Top SHAP Factors")

# Layer 4: Deterministic Decision Engine
draw_box(20, 17, 60, 7, "Deterministic Risk Policy Engine", "Validation-Optimized Bands: ALLOW (<30%) | REVIEW (30-60%) | BLOCK (≥60%)", "#1e293b", "#ef4444")

# Arrow 4 -> 5
draw_arrow(50, 17, 50, 11, "Structured Evidence Docket")

# Layer 5: AI Investigation Layer
draw_box(20, 4, 60, 7, "AI Risk Investigator & Agentic Layer", "LLM-Assisted Case Summaries · Advisory Action Protocols · Strictly Read-Only Tools", "#1e293b", "#a855f7")

plt.tight_layout()
plt.savefig(OUT_PATH, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
plt.close()
print(f"Architecture diagram saved to {OUT_PATH}")
