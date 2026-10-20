`timescale 1ns/1ps
// Exhaustive address-pair check against loaded Q15 memory for both widths.
module tb_phase_adder;
    reg clk=0;
    always #5 clk=~clk;
    reg rst_n=0;
    reg [9:0] x10=0,w10=0;
    reg [10:0] x11=0,w11=0;
    wire [15:0] out10,out11;
    reg [15:0] lut10[0:1023],lut11[0:2047];
    integer a,b;
    phase_adder #(.BITS(10),.INIT_FILE("hardware/sine_q15_1024.hex")) dut10(clk,rst_n,x10,w10,out10);
    phase_adder #(.BITS(11),.INIT_FILE("hardware/sine_q15_2048.hex")) dut11(clk,rst_n,x11,w11,out11);
    initial begin
        $readmemh("hardware/sine_q15_1024.hex",lut10);
        $readmemh("hardware/sine_q15_2048.hex",lut11);
        #1; rst_n=1; #1; rst_n=0; #1;
        if(out10!==0 || out11!==0) $fatal(1,"Reset failed");
        #1;rst_n=1;
        for(a=0;a<2048;a=a+1) begin
            for(b=0;b<2048;b=b+1) begin
                @(negedge clk);x10=a;w10=b;x11=a;w11=b;
                @(posedge clk);#1;
                if(out10!==lut10[(a+b)&1023]) $fatal(1,"10-bit mismatch");
                if(out11!==lut11[(a+b)&2047]) $fatal(1,"11-bit mismatch");
            end
        end
        $display("PASS: reset and 4194304 pairs at both widths");
        $finish;
    end
endmodule
