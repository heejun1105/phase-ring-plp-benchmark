# What the three arithmetic demos explain

This project has two separate experiments. The phase demos test a way to compute
with wave angles. The photograph demos test image filters. The CPU speed ratios
come from the first experiment; they do not predict the filters' speed or quality.

## A lookup replaces repeated trigonometry

Phase means where a repeating wave is in its cycle. A clock hand pictures the
angle: one full turn completes a cycle.

[The arithmetic demo](../animations/public_phase_computing.gif) shows two routes
to approximately the same wave. Each input has a fixed strength of one; only
its position around a wave cycle changes. Multiplying these complex signals
adds their angles around a circle.

The blue route calculates the two complex inputs and multiplies them. The cyan
route assigns each angle a whole-number position on a circle, adds those
positions, and reads a stored answer from a lookup table (LUT). The table holds
precomputed sine and cosine values. Reusing it avoids evaluating these functions
for every output. Building the table is excluded from the repeated CPU timings.

This shortcut loses some precision. It also applies to this restricted wave
task, rather than all multiplication. The animation explains the arithmetic;
the separate speed demo supplies the measured CPU comparison.

## More positions reduce the approximation error

[The precision demo](../animations/public_phase_precision.gif) shows the price
of replacing a continuous angle with a whole-number position. Z1024 divides the
circle into 1,024 positions, spaced 0.3515625° apart. Z2048 uses twice as many,
spaced 0.17578125° apart. Its smaller steps generally follow the input more
closely, with twice as many table entries.

The code chooses the lower position for each input, so both errors can add to
the output error. The stored answers also have limited precision. The enlarged
steps make these effects easier to see; they do not show a speed advantage.

## The bit demo checks the address and answer

[The bit/LUT demo](../animations/phase_bits_to_lut.gif) checks the mechanism behind
the shortcut. Ten bits hold numbers from 0 to 1023. When 750 + 400 produces
1150, discarding the extra carry bit leaves 126. That is the same position as
continuing around a 1,024-position circle. Address 126 then selects the stored
sine value 22883 in the signed 16-bit table.

This demonstrates correct wraparound and table selection. It is not a second
speed result or a measurement inside a memory chip. The supplied hardware
testbench has not been executed; [hardware status](hardware.md) distinguishes
the software checks from hardware validation.
