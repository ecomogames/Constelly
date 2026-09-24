"""Contact sheet of all puzzles, solved: python tools/preview_puzzles.py [puzzles.json] [out.png]"""
import json, sys, matplotlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
matplotlib.use("Agg"); import matplotlib.pyplot as plt
ps=json.load(open(sys.argv[1] if len(sys.argv)>1 else ROOT/"puzzles"/"puzzles.json", encoding="utf-8"))
out=sys.argv[2] if len(sys.argv)>2 else "puzzle_preview.png"; cols=int(sys.argv[3]) if len(sys.argv)>3 else 6
rows=(len(ps)+cols-1)//cols
fig,axs=plt.subplots(rows,cols,figsize=(cols*2.6,rows*3.4),facecolor="#0b1020")
for ax in axs.flat: ax.axis("off")
for i,(ax,p) in enumerate(zip(axs.flat,ps)):
    d={x["id"]:x for x in p["dots"]}
    ax.set_facecolor("#141a33"); ax.set_xlim(0,1); ax.set_ylim(4/3,0); ax.set_aspect("equal")
    ax.add_patch(plt.Rectangle((0,0),1,4/3,fc="#141a33",ec="#334"))
    for a,b in p["edges"]: ax.plot([d[a]["x"],d[b]["x"]],[d[a]["y"],d[b]["y"]],c="#ffd84a",lw=1.6)
    for x in d.values():
        ax.add_patch(plt.Circle((x["x"],x["y"]),0.028,fc="#e8ecff",ec="#ffd84a",zorder=3))
        ax.text(x["x"],x["y"],str(x["degree"]),ha="center",va="center",fontsize=6,zorder=4,color="#111")
    ax.set_title(f"#{i+1} {p['title']} ({len(d)})",color="w",fontsize=9)
plt.tight_layout(); plt.savefig(out,dpi=90,facecolor=fig.get_facecolor())
