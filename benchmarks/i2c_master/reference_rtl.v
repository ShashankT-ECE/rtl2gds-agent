// I2C Master Controller
// Supports write and read transactions with ACK/NACK detection
// Uses SDA input for bus sensing (open-drain bidirectional)
// Synthesizable, active-low synchronous rst_n

module i2c_master (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire        rw,
    input  wire [6:0]  addr,
    input  wire [7:0]  wdata,
    input  wire [15:0] scl_div,
    input  wire        sda,          // SDA bus input (wired-AND)
    output reg         scl,
    output reg         sda_out,
    output reg         sda_oe,
    output reg  [7:0]  rdata,
    output reg         busy,
    output reg         ack_error,
    output reg         done
);

    localparam IDLE      = 4'd0;
    localparam START     = 4'd1;
    localparam ADDR      = 4'd2;     // send 7-bit addr + R/W
    localparam ADDR_ACK  = 4'd3;     // sample slave ACK
    localparam DATA_W    = 4'd4;     // write data byte
    localparam DATA_R    = 4'd5;     // read data byte
    localparam DATA_ACK  = 4'd6;     // ACK phase for data
    localparam STOP_S    = 4'd7;     // generate STOP condition
    localparam DONE_S    = 4'd8;

    reg [3:0] state;
    reg [3:0] next_state;

    reg [15:0] timer;
    reg  [3:0] bit_cnt;
    reg  [7:0] shift_reg;
    reg        ack_sample;
    reg        read_mode;    // latched rw

    // ── Next-state logic ──
    always @(*) begin
        next_state = state;
        case (state)
            IDLE:     if (start && !busy) next_state = START;
            START:    if (timer == scl_div) next_state = ADDR;
            ADDR:     if (timer == scl_div && bit_cnt == 4'd8) next_state = ADDR_ACK;
            ADDR_ACK: if (timer == scl_div) begin
                          if (ack_sample) next_state = STOP_S;   // NACK
                          else if (read_mode) next_state = DATA_R;
                          else next_state = DATA_W;
                      end
            DATA_W:   if (timer == scl_div && bit_cnt == 4'd8) next_state = DATA_ACK;
            DATA_R:   if (timer == scl_div && bit_cnt == 4'd8) next_state = DATA_ACK;
            DATA_ACK: if (timer == scl_div) next_state = STOP_S;
            STOP_S:   if (timer == scl_div + scl_div[15:1]) next_state = DONE_S;
            DONE_S:   next_state = IDLE;
            default:  next_state = IDLE;
        endcase
    end

    // ── SCL edge timing helper ──
    wire scl_low_phase  = (timer <  scl_div[15:1]);
    wire scl_high_phase = (timer >= scl_div[15:1] && timer < scl_div);
    wire scl_rising     = (timer == scl_div[15:1]);   // SCL just rose
    wire bit_done       = (timer == scl_div);          // bit period complete

    // ── Sequential logic ──
    always @(posedge clk) begin
        if (!rst_n) begin
            state      <= IDLE;
            scl        <= 1'b1;
            sda_out    <= 1'b1;
            sda_oe     <= 1'b0;
            rdata      <= 8'd0;
            busy       <= 1'b0;
            ack_error  <= 1'b0;
            done       <= 1'b0;
            timer      <= 16'd0;
            bit_cnt    <= 4'd0;
            shift_reg  <= 8'd0;
            ack_sample <= 1'b0;
            read_mode  <= 1'b0;
        end else begin
            state     <= next_state;
            done      <= 1'b0;

            case (state)
                IDLE: begin
                    scl       <= 1'b1;
                    sda_out   <= 1'b1;
                    sda_oe    <= 1'b0;
                    busy      <= 1'b0;
                    timer     <= 16'd0;
                    bit_cnt   <= 4'd0;
                    if (start && !busy) begin
                        busy      <= 1'b1;
                        read_mode <= rw;
                        shift_reg <= {addr, rw};
                        ack_error <= 1'b0;
                    end
                end

                START: begin
                    // SCL high, pull SDA low → START condition
                    sda_oe  <= 1'b1;
                    sda_out <= 1'b0;
                    scl     <= 1'b1;
                    if (timer < scl_div) timer <= timer + 1;
                    else begin
                        timer <= 16'd0;
                        bit_cnt <= 4'd0;
                    end
                end

                ADDR: begin
                    sda_oe  <= 1'b1;
                    sda_out <= shift_reg[7];
                    if (scl_low_phase) begin
                        scl <= 1'b0;
                        timer <= timer + 1;
                    end else if (scl_high_phase) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                    end else begin
                        // bit done
                        scl <= 1'b0;
                        timer <= 16'd0;
                        shift_reg <= {shift_reg[6:0], 1'b0};
                        bit_cnt <= bit_cnt + 1;
                    end
                end

                ADDR_ACK: begin
                    sda_oe  <= 1'b0;      // release for slave ACK
                    if (scl_low_phase) begin
                        scl <= 1'b0;
                        timer <= timer + 1;
                    end else if (scl_rising) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                        ack_sample <= sda;   // sample SDA at SCL rise
                    end else if (scl_high_phase) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                    end else begin
                        scl <= 1'b0;
                        timer <= 16'd0;
                        bit_cnt <= 4'd0;
                        if (!ack_sample) begin
                            // ACK received
                            if (!read_mode) begin
                                shift_reg <= wdata;   // load data for write
                            end
                        end else begin
                            ack_error <= 1'b1;
                        end
                    end
                end

                DATA_W: begin
                    sda_oe  <= 1'b1;
                    sda_out <= shift_reg[7];
                    if (scl_low_phase) begin
                        scl <= 1'b0;
                        timer <= timer + 1;
                    end else if (scl_high_phase) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                    end else begin
                        scl <= 1'b0;
                        timer <= 16'd0;
                        shift_reg <= {shift_reg[6:0], 1'b0};
                        bit_cnt <= bit_cnt + 1;
                    end
                end

                DATA_R: begin
                    sda_oe  <= 1'b0;      // release, slave drives
                    if (scl_low_phase) begin
                        scl <= 1'b0;
                        timer <= timer + 1;
                    end else if (scl_rising) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                        shift_reg <= {shift_reg[6:0], sda};  // sample data
                    end else if (scl_high_phase) begin
                        scl <= 1'b1;
                        timer <= timer + 1;
                    end else begin
                        scl <= 1'b0;
                        timer <= 16'd0;
                        bit_cnt <= bit_cnt + 1;
                        if (bit_cnt == 4'd7) begin
                            rdata <= {shift_reg[6:0], sda};
                        end
                    end
                end

                DATA_ACK: begin
                    if (!read_mode) begin
                        // Write: release SDA, sample slave ACK
                        sda_oe  <= 1'b0;
                        if (scl_low_phase) begin
                            scl <= 1'b0; timer <= timer + 1;
                        end else if (scl_rising) begin
                            scl <= 1'b1; timer <= timer + 1;
                            ack_sample <= sda;
                        end else if (scl_high_phase) begin
                            scl <= 1'b1; timer <= timer + 1;
                        end else begin
                            scl <= 1'b0; timer <= 16'd0;
                            if (ack_sample) ack_error <= 1'b1;
                        end
                    end else begin
                        // Read: drive SDA low (master ACK)
                        sda_oe  <= 1'b1;
                        sda_out <= 1'b0;
                        if (scl_low_phase) begin
                            scl <= 1'b0; timer <= timer + 1;
                        end else if (scl_high_phase) begin
                            scl <= 1'b1; timer <= timer + 1;
                        end else begin
                            scl <= 1'b0; timer <= 16'd0;
                            sda_oe <= 1'b0;
                        end
                    end
                end

                STOP_S: begin
                    sda_oe  <= 1'b1;
                    sda_out <= 1'b0;
                    if (timer < scl_div[15:1]) begin
                        scl <= 1'b0;       // SCL low half
                        timer <= timer + 1;
                    end else if (timer < scl_div) begin
                        scl <= 1'b1;       // SCL high first half
                        timer <= timer + 1;
                    end else if (timer < scl_div + scl_div[15:1]) begin
                        scl <= 1'b1;
                        sda_out <= 1'b1;   // SDA rises while SCL high → STOP
                        timer <= timer + 1;
                    end else begin
                        scl <= 1'b1;
                        sda_oe  <= 1'b0;   // release bus
                        timer   <= 16'd0;
                    end
                end

                DONE_S: begin
                    done  <= 1'b1;
                    busy  <= 1'b0;
                    scl   <= 1'b1;
                    sda_oe <= 1'b0;
                    sda_out <= 1'b1;
                end

                default: begin
                end
            endcase
        end
    end

endmodule
