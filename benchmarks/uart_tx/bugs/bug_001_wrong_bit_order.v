// Bug injection: bit order changed from LSB-first to MSB-first.
// The shift register shifts left instead of right, and the output takes
// shift_reg[7] (MSB) instead of shift_reg[0] (LSB). This corrupts the
// transmitted byte order on the wire.

//============================================================
// UART Transmitter (uart_tx)
// Buggy version — MSB-first instead of LSB-first
// Frame: 1 start bit (low), 8 data bits (MSB first), 1 stop bit (high)
//============================================================

module uart_tx (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,
    input  wire [7:0] tx_data,
    input  wire [15:0] baud_div,
    output reg        tx,
    output reg        tx_busy
);

    //------------------------------------------------------
    // State encoding
    //------------------------------------------------------
    localparam IDLE  = 2'b00;
    localparam START = 2'b01;
    localparam DATA  = 2'b10;
    localparam STOP  = 2'b11;

    reg [1:0] state, next_state;

    //------------------------------------------------------
    // Registers for counters and shift
    //------------------------------------------------------
    reg [15:0] baud_cnt;
    reg [2:0]  bit_cnt;       // 0..7 for 8 data bits
    reg [7:0]  shift_reg;     // serialiser shift register

    //------------------------------------------------------
    // Next-state logic
    //------------------------------------------------------
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (tx_start && !tx_busy)
                    next_state = START;
            end
            START: begin
                if (baud_cnt == baud_div - 1)
                    next_state = DATA;
            end
            DATA: begin
                if (baud_cnt == baud_div - 1 && bit_cnt == 3'd7)
                    next_state = STOP;
            end
            STOP: begin
                if (baud_cnt == baud_div - 1)
                    next_state = IDLE;
            end
        endcase
    end

    //------------------------------------------------------
    // Combinational output logic — MSB first
    //------------------------------------------------------
    always @(*) begin
        case (state)
            IDLE:  begin tx = 1'b1; tx_busy = 1'b0; end
            START: begin tx = 1'b0; tx_busy = 1'b1; end
            DATA:  begin tx = shift_reg[7]; tx_busy = 1'b1; end
            STOP:  begin tx = 1'b1; tx_busy = 1'b1; end
            default: begin tx = 1'b1; tx_busy = 1'b0; end
        endcase
    end

    //------------------------------------------------------
    // Sequential logic — shift left (MSB first)
    //------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= IDLE;
            baud_cnt  <= 16'd0;
            bit_cnt   <= 3'd0;
            shift_reg <= 8'd0;
        end else begin
            state <= next_state;

            // Defaults: counters increment unless reset below
            baud_cnt <= baud_cnt + 1'b1;

            case (state)
                IDLE: begin
                    baud_cnt  <= 16'd0;
                    bit_cnt   <= 3'd0;
                    shift_reg <= tx_data;    // latch data while idle
                end

                START: begin
                    if (baud_cnt == baud_div - 1) begin
                        baud_cnt <= 16'd0;
                        // Reload shift register on entry to DATA
                        shift_reg <= tx_data;
                    end
                end

                DATA: begin
                    if (baud_cnt == baud_div - 1) begin
                        baud_cnt  <= 16'd0;
                        shift_reg <= {shift_reg[6:0], 1'b0}; // shift left, MSB first
                        if (bit_cnt == 3'd7)
                            bit_cnt <= 3'd0;
                        else
                            bit_cnt <= bit_cnt + 1'b1;
                    end
                end

                STOP: begin
                    if (baud_cnt == baud_div - 1) begin
                        baud_cnt <= 16'd0;
                        bit_cnt  <= 3'd0;
                    end
                end
            endcase
        end
    end

endmodule
