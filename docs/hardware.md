# RTL adaptation and validation

`phase_adder.v` parameterizes Paper VIII Listing 1 for 10-bit and 11-bit addresses. Assignment to the narrow wire discards carry automatically. A registered output reads a 16-bit signed-Q15 sine entry from a generated memory initialization file. A paired cosine LUT is used only in the Python complex-output comparison; the RTL matches the paper's scalar sine-output interface.

The original paper's memory was uninitialized. This adaptation adds an explicit `$readmemh` initialization, so simulation has deterministic output. Target tools may infer ROM, registers or block RAM; ASIC SRAM requires a specific macro wrapper and initialization/loading scheme. This file does not demonstrate an ASIC memory macro, physical PIM, power, timing closure or area.

The generated Q15 files use truncation toward zero of `sin(2*pi*k/N)*32767`, matching the paper's Python conversion. `scripts/reproduce.py` regenerates them. All address-pair sums, every scalar LUT entry and numerical reconstruction bounds are checked in Python.

## Optional Icarus Verilog test

Install Icarus Verilog separately, then run from the repository root:

```bash
iverilog -g2012 -s tb_phase_adder -o phase_adder_tb hardware/phase_adder.v hardware/tb_phase_adder.v
vvp phase_adder_tb
```

The testbench checks asynchronous reset and 4,194,304 input pairs at both widths against the loaded Q15 table. A failing simulation returns an error with `$fatal`.

## Status of the supplied run

No Icarus/Verilator executable was installed in the measurement environment. **The RTL testbench was supplied but not executed.** Passing Python arithmetic tests must not be reported as RTL simulation, synthesis, FPGA, SRAM or silicon verification. No area, power or delay result was generated. Future verification should run this bench, review memory inference, use a documented standard-cell/PDK flow, and retain tool versions, constraints, netlists, timing and switching reports.
