from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "assets" / "shared-scripts"))

from drawio_check import check_flow  # noqa: E402
from figure_check import check_figure_script  # noqa: E402


def main() -> int:
    rounded = '<mxCell id="n1" value="step" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="0" y="0" width="100" height="40" as="geometry"/></mxCell>'
    straight = rounded.replace("rounded=1", "rounded=0")
    rounded_issues = check_flow(rounded, "rounded.drawio")
    straight_issues = check_flow(straight, "straight.drawio")
    assert any("矩形节点使用 rounded=1" in item for item in rounded_issues), rounded_issues
    assert not any("矩形节点使用 rounded=1" in item for item in straight_issues), straight_issues

    temp = ROOT.parent / "runtime_visual_contract_smoke.py"
    temp.write_text(
        "from 工具.plot_utils import setup_style, save_fig\n"
        "setup_style()\n"
        "fig, ax = plt.subplots()\n"
        "ax.plot([0, 1], [0, 1])\n"
        "ax.spines['top'].set_visible(False)\n"
        "ax.spines['right'].set_visible(False)\n"
        "fig.tight_layout()\n"
        "save_fig(fig, '图表/test.pdf')\n",
        encoding="utf-8",
    )
    issues = check_figure_script(str(temp))
    if temp.exists():
        temp.unlink()
    assert not any("视觉质量偏低" in item or "缺少渐变" in item for item in issues), issues
    print("visual contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
