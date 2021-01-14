# Extreeeme45

An extension for RoboFont which adds extreme point under 45 degrees. default shortcut is *cmd+shift+e*. Constant angles across family help better interpolation. I recommend to use this tool in combination with 45 degree angle constrain. To activate it, tick the box in `preferences/Glyph View` titled *use shift 45 deg constrain*.

1. Empty selection counts as the whole glyph was selected.
1. It rounds on-curve points which the extension added and ensures that their off-curve points are exactly 45 degrees when rounded to the grid.
1. It only modifies selected segments, rest of the data stays untouched.
1. It is prepared to support other angles in the future. Possibly also supporting step-checking of safe angles. This is the diagonal's degree of rectangle having ratio of its sides in whole numbers.

## plans
- add support for customization of angle where to put extreme point
- add contextual menu for people preferring to work with mouse