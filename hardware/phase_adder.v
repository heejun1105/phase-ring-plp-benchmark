// Adaptation of Paper VIII Listing 1. See docs/paper_review.md and LICENSE.
// Memory inference and initialization support depend on the target toolchain.
module phase_adder #(
    parameter BITS = 10,
    parameter INIT_FILE = "hardware/sine_q15_1024.hex"
) (
    input wire clk,
    input wire rst_n,
    input wire [BITS-1:0] in_phase_x,
    input wire [BITS-1:0] in_phase_w,
    output reg [15:0] sram_data_out
);
    wire [BITS-1:0] local_phase_sum;
    assign local_phase_sum = in_phase_x + in_phase_w;
    reg [15:0] sram_matrix [0:(1<<BITS)-1];
    initial $readmemh(INIT_FILE, sram_matrix);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) sram_data_out <= 16'h0000;
        else sram_data_out <= sram_matrix[local_phase_sum];
    end
endmodule
