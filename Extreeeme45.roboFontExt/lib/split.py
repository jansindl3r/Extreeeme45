from fontTools.misc.bezierTools import (
    calcCubicBounds,
    solveQuadratic,
    calcCubicParameters,
    calcBounds,
    splitCubicAtT,
)
from lib.fontObjects.fontPartsWrappers import RGlyph
from typing import List, Tuple, Generator
import math


class Extreme:
    # A class to add extremes on a path under 45 degrees

    def __init__(
        self,
        g: RGlyph,
        angle: float = math.pi / 4,
        horizontal=True,
        vertical=True,
        roundAligned=True,
    ) -> None:
        self.g: RGlyph = g
        self.horizontal = horizontal
        self.vertical = vertical
        assert horizontal or vertical, "cut somewhere"
        self.angle: float = angle
        self.selectedCS: dict = self.getSelectedCS()
        self.coos: list = self.getCoos()
        self.splits: list = self.getSplits()
        if roundAligned and angle == math.pi / 4:
            self.roundAlignedLoop()

    def getSelectedCS(self) -> dict:
        # creates a tree of selected contours and segments
        collector: dict = {}
        selectAll: bool = True if g.selection else False
        print(selectAll)
        for c in self.g:
            for seg in c:
                if seg.selected or not selectAll:
                    collector.setdefault(c.index, []).append(seg.index)
        return collector

    def getCoos(self) -> List[List[tuple]]:
        # gets points of each segment containing last point of previous segment
        collector: list = []
        for c in self.g:
            collector.append([])
            for lastSeg, seg in zip([c[-1]] + c[:-1], c):
                points = tuple([lastSeg[-1]]) + seg.points
                coos = [pt.position for pt in points]
                collector[-1].append(coos)
        return collector

    def rotatePoint(
        self, point: Tuple[int, int], origin: Tuple[int, int] = (0, 0)
    ) -> Tuple[float, float]:
        # rotates a point on twodimensional matrix
        ox, oy = origin
        px, py = point
        qx: float = ox + math.cos(self.angle) * (px - ox) - math.sin(self.angle) * (
            py - oy
        )
        qy: float = oy + math.sin(self.angle) * (px - ox) + math.cos(self.angle) * (
            py - oy
        )
        return qx, qy

    def getExtremes(self, point=Tuple[int, ...]) -> list:
        # gets extremes of a cubic bezier curve
        pt1, pt2, pt3, pt4 = point
        (ax, ay), (bx, by), (cx, cy), _ = calcCubicParameters(pt1, pt2, pt3, pt4)
        ax3 = ax * 3.0
        ay3 = ay * 3.0
        bx2 = bx * 2.0
        by2 = by * 2.0
        collector: list = []
        if self.horizontal:
            collector += [t for t in solveQuadratic(ax3, bx2, cx) if 0 <= t < 1]
        if self.vertical:
            collector += [t for t in solveQuadratic(ay3, by2, cy) if 0 <= t < 1]
        return sorted(collector)

    def getSplits(self) -> list:
        # gets points that need to be added on selected curves
        collector: list = []
        for cIndex, segIndexes in self.selectedCS.items():
            for segIndex in segIndexes[::-1]:
                if self.g[cIndex][segIndex].type != "curve":
                    continue
                segCoos = self.coos[cIndex][segIndex]
                segRotated = map(lambda x: self.rotatePoint(x), segCoos)
                extremes = self.getExtremes(segRotated)
                if len(extremes) == 1 and sum(extremes) in [0, 1]:
                    # make more sofisticated conditions. Check if the splits themselves are of at least some length
                    continue
                splits = splitCubicAtT(*segCoos, *extremes)
                splits = list(map(list, splits))
                collector.append((cIndex, segIndex, splits))
        return collector

    def roundAligned(self, off1, base, off2) -> Tuple[list, ...]:
        base = [round(i) for i in base]
        baseX, baseY = base
        off1, off2 = [(x - baseX, y - baseY) for x, y in [off1, off2]]
        if self.angle == math.pi / 4:
            # special logic for 45 precise degrees
            step1, step2 = [map(abs, xy) for xy in [off1, off2]]
            step1Int, step2Int = [sum(xy) for xy in [step1, step2]]
            step1, step2 = [round(xy / 2) for xy in [step1Int, step2Int]]
        else:
            pass
            # logic for not 45 deg, and 1 and last off
        off1 = [b + step1 if o > 0 else b - step1 for b, o in zip(base, off1)]
        off2 = [b + step2 if o > 0 else b - step2 for b, o in zip(base, off2)]
        return off1, base, off2

    def roundAlignedLoop(self) -> None:
        for *_, splits in self.splits:
            for i, split in enumerate(splits):
                for j in range(len(split)):
                    if j != 2 or i == len(splits) - 1:
                        continue
                    split[2], splits[i + 1][0], splits[i + 1][1] = self.roundAligned(
                        split[2], split[3], splits[i + 1][1]
                    )

    def perform(self) -> None:
        # inserts points
        type_: str
        smooth: bool
        for cIndex, segIndex, splits in self.splits:
            indexIn: int = self.g[cIndex][segIndex][0].index
            self.g[cIndex][segIndex][-2].position = splits[-1][-2]
            self.g[cIndex][segIndex][0].position = splits[0][1]
            for i, split in enumerate(splits[::-1]):
                for j, coo in enumerate(split[::-1][1:]):
                    if i == 0 and j == 0 or i == len(splits) - 1 and j > 0:
                        continue
                    type_, smooth = ("curve", True) if j == 2 else ("offcurve", False)
                    self.g[cIndex].insertPoint(indexIn + 1, coo, type_, smooth=smooth)


if __name__ == "__main__":

    g = CurrentGlyph()
    e = Extreme(g, angle=math.pi / 4)
    with g.undo(f"Extreme points under 45° in {g.name}"):
        e.perform()
    g.deselect()
