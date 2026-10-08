"""Deferred Streamlit tutorials that can precede the AMCL mission in a future lab."""
from io import BytesIO

import matplotlib.pyplot as plt


def _figure(st, figure, width=600):
    output = BytesIO()
    figure.savefig(output, format="png", dpi=105, bbox_inches="tight")
    plt.close(figure)
    st.image(output.getvalue(), width=width)


def transition(st):
    st.header("Guided Tutorial 4: From SLAM to localization")
    st.code("During SLAM: estimate pose + estimate map\nDuring AMCL: fixed saved map + estimate pose")
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.2))
    for ax, title, box in (
        (axes[0], "SLAM while mapping", "Changing map\nChanging pose estimate"),
        (axes[1], "AMCL after saving", "Fixed reference map\nChanging pose estimate"),
    ):
        ax.text(0.5, 0.5, box, ha="center", va="center", fontsize=10,
                bbox={"boxstyle": "round,pad=0.7", "fc": "#d9e9f5", "ec": "#52677a"})
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    _figure(st, fig)
    st.write("Once a map is saved, localization treats it as a fixed reference. AMCL combines that map with wheel motion and LiDAR evidence to estimate where the robot is. A fixed map is not necessarily an accurate map. Missing coverage or doubled walls can mislead the pose estimate.")
    st.write("In the localization mission, choose one saved map and justify that choice using visual structure and measured map properties. Use the same map in every trial.")


def amcl(st):
    st.header("Guided Tutorial 5: Read AMCL")
    st.write("AMCL represents possible poses with particles. Several clusters mean competing location hypotheses. As the robot moves and receives scans, hypotheses gain or lose support. A tight cluster means the algorithm is confident, but it can be confidently wrong in similar corridors or with a poor map.")
    support = st.slider("Illustrative scan support for hypothesis A (%)", 0, 100, 50, 5, key="t5.support")
    fig, ax = plt.subplots(figsize=(5.6, 2.1))
    ax.barh(["Hypothesis A", "Hypothesis B"], [support, 100 - support], color=["#286f9f", "#d9a038"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Illustrative relative scan support (%)")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.2)
    _figure(st, fig, 550)
    st.caption("This two-hypothesis chart is illustrative. It is not AMCL's actual particle update.")
    st.info("Compare particle spread, estimated pose, known map, and scan alignment in RViz. Check the estimated location against independent simulation evidence when available. Low covariance measures concentration, not truth.")
