// Bug injection: PSLVERR logic inverted — asserts on valid addresses instead
// of invalid addresses. The slave reports a bus error during legitimate
// transfers to valid register addresses.

module apb_slave (
    input        PCLK,
    input        PRESETn,
    input        PSEL,
    input        PENABLE,
    input        PWRITE,
    input  [7:0] PADDR,
    input  [31:0] PWDATA,
    output [31:0] PRDATA,
    output       PREADY,
    output       PSLVERR
);

    // Internal 32-bit registers
    reg [31:0] reg0;
    reg [31:0] reg1;
    reg [31:0] reg2;
    reg [31:0] reg3;

    // Address decode
    wire [1:0] addr_sel;
    assign addr_sel = PADDR[3:2];

    // Valid transfer: both PSEL and PENABLE must be high
    wire valid_transfer;
    assign valid_transfer = PSEL & PENABLE;

    // Address validity: PADDR must be exactly one of the four word-aligned locations
    // within the 0x00–0x0C range (byte address, word-aligned).
    wire addr_valid;
    assign addr_valid = (PADDR[7:4] == 4'b0) & (PADDR[1:0] == 2'b0);

    // PREADY always 1 (zero wait states)
    assign PREADY = 1'b1;

    // PSLVERR: inverted — asserted on valid addresses instead of invalid
    assign PSLVERR = valid_transfer & addr_valid;

    // Read data mux
    reg [31:0] prdata_mux;
    always @(*) begin
        if (valid_transfer & ~PWRITE) begin
            case (addr_sel)
                2'b00:   prdata_mux = reg0;
                2'b01:   prdata_mux = reg1;
                2'b10:   prdata_mux = reg2;
                2'b11:   prdata_mux = reg3;
                default: prdata_mux = 32'b0;
            endcase
        end else begin
            prdata_mux = 32'b0;
        end
    end
    assign PRDATA = prdata_mux;

    // Write registers (synchronous)
    always @(posedge PCLK) begin
        if (~PRESETn) begin
            reg0 <= 32'b0;
            reg1 <= 32'b0;
            reg2 <= 32'b0;
            reg3 <= 32'b0;
        end else if (valid_transfer & PWRITE & addr_valid) begin
            case (addr_sel)
                2'b00:   reg0 <= PWDATA;
                2'b01:   reg1 <= PWDATA;
                2'b10:   reg2 <= PWDATA;
                2'b11:   reg3 <= PWDATA;
                default: ;
            endcase
        end
    end

endmodule
