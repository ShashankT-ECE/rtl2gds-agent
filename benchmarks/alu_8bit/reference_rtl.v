module alu_8bit (
    input  [7:0] A,
    input  [7:0] B,
    input  [2:0] opcode,
    output reg [7:0] Y,
    output reg zero_flag
);

always @(*) begin
    case (opcode)
        3'b000: Y = A + B;
        3'b001: Y = A - B;
        3'b010: Y = A & B;
        3'b011: Y = A | B;
        3'b100: Y = A ^ B;
        3'b101: Y = ~A;
        3'b110: Y = A << 1;
        3'b111: Y = A >> 1;
        default: Y = 8'b0;
    endcase

    zero_flag = (Y == 8'b0) ? 1'b1 : 1'b0;
end

endmodule
