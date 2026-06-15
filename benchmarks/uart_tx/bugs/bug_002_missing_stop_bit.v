// Bug injection: stop bit transmission removed — the FSM transitions directly
// from DATA to IDLE, skipping the STOP state. The serial output returns to
// idle (high) immediately after the last data bit instead of sending a stop bit.

//============================================================
// UART Transmitter (uart_tx)
// Buggy version — no stop bit transmitted
// Frame: 1 start bit (low), 8 data bits (LSB first), NO stop bit
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
    // Next-state logic — skip STOP, go directly from DATA to IDLE
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
                    next_state = IDLE;
            end
            STOP: begin
                if (baud_cnt == baud_div - 1)
                    next_state = IDLE;
            end
        endcase
    end

    //------------------------------------------------------
    // Combinational output logic
    //------------------------------------------------------
    always @(*) begin
        case (state)
            IDLE:  begin tx = 1'b1; tx_busy = 1'b0; end
            START: begin tx = 1'b0; tx_busy = 1'b1; end
            DATA:  begin tx = shift_reg[0]; tx_busy = 1'b1; end
            STOP:  begin tx = 1'b1; tx_busy = 1'b1; end
            default: begin tx = 1'b1; tx_busy = 1'b0; end
        endcase
    end

    //------------------------------------------------------
    // Sequential logic (state and counters only)
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
                        shift_reg <= {1'b0, shift_reg[7:1]}; // shift right, LSB first
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
