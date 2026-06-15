// Bug injection: rst_n condition removed from all sequential logic blocks.
// The module still accepts rst_n as input but never uses it — state registers
// and counters are not initialized on reset.

module sync_fifo_8x16 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       wr_en,
    input  wire       rd_en,
    input  wire [7:0] din,
    output reg  [7:0] dout,
    output wire       full,
    output wire       empty
);

    reg [7:0] mem [0:15];
    reg [4:0] wr_ptr;
    reg [4:0] rd_ptr;
    reg [4:0] count;

    // Write pointer — no reset
    always @(posedge clk) begin
        if (wr_en && !full)
            wr_ptr <= wr_ptr + 1'b1;
    end

    // Read pointer — no reset
    always @(posedge clk) begin
        if (rd_en && !empty)
            rd_ptr <= rd_ptr + 1'b1;
    end

    // Memory write — no reset
    always @(posedge clk) begin
        if (wr_en && !full) begin
            mem[wr_ptr[3:0]] <= din;
        end
    end

    // Memory read — no reset
    always @(posedge clk) begin
        if (rd_en && !empty)
            dout <= (wr_en && !full && (wr_ptr[3:0] == rd_ptr[3:0])) ? din : mem[rd_ptr[3:0]];
    end

    // Counter for full/empty — no reset
    always @(posedge clk) begin
        case ({wr_en && !full, rd_en && !empty})
            2'b10: count <= count + 1'b1;
            2'b01: count <= count - 1'b1;
            default: count <= count;
        endcase
    end

    assign full  = (count == 5'd16);
    assign empty = (count == 5'd0);

endmodule
