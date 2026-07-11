# LaTeX figure contract

- Every `\includegraphics` must have bounded width or height and `keepaspectratio`.
- Default ordinary figure: `width=0.72\linewidth,height=0.70\textheight,keepaspectratio`.
- Square or portrait figure: normally `0.55--0.72\linewidth`.
- Wide time-series or heatmap: normally `0.80--0.90\linewidth`.
- Width must not exceed `1.0\linewidth`/`1.0\textwidth`; height must not exceed `0.70\textheight`.
- If labels become unreadable, redraw, simplify, split, or move the figure; do not keep shrinking it.
- Overfull boxes, clipped graphics, distorted aspect ratios, and unconstrained `\includegraphics{...}` are hard failures.
