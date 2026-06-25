//======================================================================
// AXI4-Lite Slave with 8 x 32-bit registers
// - AMBA AXI4-Lite protocol compliant
// - Independent write and read channel FSMs
// - WSTRB byte-enable support
// - Active-low synchronous reset (ARESETn)
//======================================================================

module axi4_lite_slave (
    // Write Address Channel
    input  wire        ACLK,
    input  wire        ARESETn,
    input  wire        AWVALID,
    input  wire [31:0] AWADDR,
    output reg         AWREADY,
    // Write Data Channel
    input  wire        WVALID,
    input  wire [31:0] WDATA,
    input  wire [ 3:0] WSTRB,
    output reg         WREADY,
    // Write Response Channel
    input  wire        BREADY,
    output reg         BVALID,
    output reg  [ 1:0] BRESP,
    // Read Address Channel
    input  wire        ARVALID,
    input  wire [31:0] ARADDR,
    output reg         ARREADY,
    // Read Data Channel
    input  wire        RREADY,
    output reg         RVALID,
    output reg  [31:0] RDATA,
    output reg  [ 1:0] RRESP
);

    //==================================================================
    // Register File: 8 x 32-bit
    //==================================================================
    reg [31:0] reg0;
    reg [31:0] reg1;
    reg [31:0] reg2;
    reg [31:0] reg3;
    reg [31:0] reg4;
    reg [31:0] reg5;
    reg [31:0] reg6;
    reg [31:0] reg7;

    //==================================================================
    // Address decode
    //==================================================================
    wire [31:0] w_addr;
    wire [31:0] r_addr;
    reg  [ 2:0] w_sel;
    reg  [ 2:0] r_sel;
    reg         w_addr_valid;
    reg         r_addr_valid;

    assign w_addr = AWADDR & 32'hFFFFFFFC;  // word-align
    assign r_addr = ARADDR & 32'hFFFFFFFC;

    always @(*) begin
        case (w_addr[4:2])
            3'h0   : w_sel = 3'h0;
            3'h1   : w_sel = 3'h1;
            3'h2   : w_sel = 3'h2;
            3'h3   : w_sel = 3'h3;
            3'h4   : w_sel = 3'h4;
            3'h5   : w_sel = 3'h5;
            3'h6   : w_sel = 3'h6;
            3'h7   : w_sel = 3'h7;
            default: w_sel = 3'h0;
        endcase
    end

    always @(*) begin
        case (r_addr[4:2])
            3'h0   : r_sel = 3'h0;
            3'h1   : r_sel = 3'h1;
            3'h2   : r_sel = 3'h2;
            3'h3   : r_sel = 3'h3;
            3'h4   : r_sel = 3'h4;
            3'h5   : r_sel = 3'h5;
            3'h6   : r_sel = 3'h6;
            3'h7   : r_sel = 3'h7;
            default: r_sel = 3'h0;
        endcase
    end

    always @(*) begin
        w_addr_valid = (w_addr[4:2] <= 3'h7);
    end

    always @(*) begin
        r_addr_valid = (r_addr[4:2] <= 3'h7);
    end

    //==================================================================
    // Write Channel FSM
    //==================================================================
    localparam W_IDLE     = 2'd0;
    localparam W_AW_PHASE = 2'd1;
    localparam W_W_PHASE  = 2'd2;
    localparam W_B_PHASE  = 2'd3;

    reg [1:0] w_state;
    reg [1:0] w_state_next;

    // State register
    always @(posedge ACLK) begin
        if (!ARESETn)
            w_state <= W_IDLE;
        else
            w_state <= w_state_next;
    end

    // Next-state logic
    always @(*) begin
        w_state_next = w_state;
        case (w_state)
            W_IDLE: begin
                if (AWVALID)
                    w_state_next = W_AW_PHASE;
            end
            W_AW_PHASE: begin
                if (WVALID)
                    w_state_next = W_W_PHASE;
                else if (!AWVALID)
                    w_state_next = W_IDLE;
            end
            W_W_PHASE: begin
                w_state_next = W_B_PHASE;
            end
            W_B_PHASE: begin
                if (BREADY)
                    w_state_next = W_IDLE;
            end
            default: w_state_next = W_IDLE;
        endcase
    end

    //==================================================================
    // Write channel outputs
    //==================================================================
    always @(posedge ACLK) begin
        if (!ARESETn) begin
            AWREADY <= 1'b0;
        end else begin
            case (w_state)
                W_IDLE:     AWREADY <= 1'b1;
                W_AW_PHASE: AWREADY <= 1'b0;
                default:    AWREADY <= 1'b0;
            endcase
        end
    end

    always @(posedge ACLK) begin
        if (!ARESETn) begin
            WREADY <= 1'b0;
        end else begin
            case (w_state)
                W_AW_PHASE: WREADY <= 1'b1;
                W_W_PHASE:  WREADY <= 1'b0;
                default:    WREADY <= 1'b0;
            endcase
        end
    end

    // Write register file
    always @(posedge ACLK) begin
        if (!ARESETn) begin
            reg0 <= 32'd0;
            reg1 <= 32'd0;
            reg2 <= 32'd0;
            reg3 <= 32'd0;
            reg4 <= 32'd0;
            reg5 <= 32'd0;
            reg6 <= 32'd0;
            reg7 <= 32'd0;
        end else if ((w_state == W_W_PHASE) && w_addr_valid) begin
            // Byte-enable write
            if (w_sel == 3'h0) begin
                if (WSTRB[0]) reg0[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg0[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg0[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg0[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h1) begin
                if (WSTRB[0]) reg1[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg1[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg1[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg1[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h2) begin
                if (WSTRB[0]) reg2[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg2[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg2[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg2[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h3) begin
                if (WSTRB[0]) reg3[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg3[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg3[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg3[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h4) begin
                if (WSTRB[0]) reg4[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg4[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg4[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg4[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h5) begin
                if (WSTRB[0]) reg5[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg5[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg5[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg5[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h6) begin
                if (WSTRB[0]) reg6[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg6[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg6[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg6[31:24] <= WDATA[31:24];
            end
            if (w_sel == 3'h7) begin
                if (WSTRB[0]) reg7[ 7: 0] <= WDATA[ 7: 0];
                if (WSTRB[1]) reg7[15: 8] <= WDATA[15: 8];
                if (WSTRB[2]) reg7[23:16] <= WDATA[23:16];
                if (WSTRB[3]) reg7[31:24] <= WDATA[31:24];
            end
        end
    end

    // BVALID and BRESP
    always @(posedge ACLK) begin
        if (!ARESETn) begin
            BVALID <= 1'b0;
            BRESP  <= 2'b00;
        end else begin
            case (w_state)
                W_W_PHASE: begin
                    BVALID <= 1'b1;
                    BRESP  <= w_addr_valid ? 2'b00 : 2'b10;
                end
                W_B_PHASE: begin
                    if (BREADY)
                        BVALID <= 1'b0;
                end
                default: begin
                    BVALID <= 1'b0;
                    BRESP  <= 2'b00;
                end
            endcase
        end
    end

    //==================================================================
    // Read Channel FSM
    //==================================================================
    localparam R_IDLE     = 2'd0;
    localparam R_AR_PHASE = 2'd1;
    localparam R_R_PHASE  = 2'd2;

    reg [1:0] r_state;
    reg [1:0] r_state_next;

    // State register
    always @(posedge ACLK) begin
        if (!ARESETn)
            r_state <= R_IDLE;
        else
            r_state <= r_state_next;
    end

    // Next-state logic
    always @(*) begin
        r_state_next = r_state;
        case (r_state)
            R_IDLE: begin
                if (ARVALID)
                    r_state_next = R_AR_PHASE;
            end
            R_AR_PHASE: begin
                r_state_next = R_R_PHASE;
            end
            R_R_PHASE: begin
                if (RREADY)
                    r_state_next = R_IDLE;
            end
            default: r_state_next = R_IDLE;
        endcase
    end

    //==================================================================
    // Read channel outputs
    //==================================================================
    always @(posedge ACLK) begin
        if (!ARESETn) begin
            ARREADY <= 1'b0;
        end else begin
            case (r_state)
                R_IDLE:     ARREADY <= 1'b1;
                R_AR_PHASE: ARREADY <= 1'b0;
                default:    ARREADY <= 1'b0;
            endcase
        end
    end

    // RVALID, RDATA, RRESP — registered in R_PHASE
    always @(posedge ACLK) begin
        if (!ARESETn) begin
            RVALID <= 1'b0;
            RDATA  <= 32'd0;
            RRESP  <= 2'b00;
        end else begin
            case (r_state)
                R_AR_PHASE: begin
                    RVALID <= 1'b1;
                    RRESP  <= r_addr_valid ? 2'b00 : 2'b10;
                    case (r_sel)
                        3'h0: RDATA <= reg0;
                        3'h1: RDATA <= reg1;
                        3'h2: RDATA <= reg2;
                        3'h3: RDATA <= reg3;
                        3'h4: RDATA <= reg4;
                        3'h5: RDATA <= reg5;
                        3'h6: RDATA <= reg6;
                        3'h7: RDATA <= reg7;
                    endcase
                end
                R_R_PHASE: begin
                    if (RREADY)
                        RVALID <= 1'b0;
                end
                default: begin
                    RVALID <= 1'b0;
                    RDATA  <= 32'd0;
                    RRESP  <= 2'b00;
                end
            endcase
        end
    end

endmodule
