// SPI Master Controller — simple, robust, synthesizable
// Supports all 4 CPOL/CPHA modes, MSB-first

module spi_master (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [7:0] mosi_data,
    input  wire       cpol,
    input  wire       cpha,
    input  wire [7:0] sclk_div,
    input  wire       miso,
    output reg        sclk,
    output reg        mosi,
    output reg        cs_n,
    output reg  [7:0] miso_data,
    output reg        busy,
    output reg        done
);

    localparam IDLE  = 2'd0;
    localparam ACTIVE = 2'd1;
    localparam FINISH = 2'd2;

    reg [1:0] state, next;

    reg [7:0] cnt;
    reg [2:0] bits;
    reg [7:0] tx;
    reg [7:0] rx;
    reg       sclk_i;
    reg       done_i;

    // sclk_div must be >= 2 for correct operation
    wire [7:0] half = (sclk_div < 8'd2) ? 8'd2 : sclk_div;

    always @(*) begin
        next = state;
        case (state)
            IDLE:   if (start && !busy) next = ACTIVE;
            ACTIVE: if (done_i)         next = FINISH;
            FINISH:                     next = IDLE;
        endcase
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= IDLE;
            sclk      <= cpol;
            mosi      <= 1'b0;
            cs_n      <= 1'b1;
            miso_data <= 8'd0;
            busy      <= 1'b0;
            done      <= 1'b0;
            cnt       <= 8'd0;
            bits      <= 3'd0;
            tx        <= 8'd0;
            rx        <= 8'd0;
            sclk_i    <= cpol;
            done_i    <= 1'b0;
        end else begin
            state <= next;
            done_i <= 1'b0;

            case (state)
                IDLE: begin
                    cs_n   <= 1'b1;
                    busy   <= 1'b0;
                    sclk_i <= cpol;
                    sclk   <= cpol;
                    cnt    <= half;
                    bits   <= 3'd0;
                    if (start && !busy) begin
                        busy <= 1'b1;
                        cs_n <= 1'b0;
                        tx   <= mosi_data;
                        rx   <= 8'd0;
                        mosi <= mosi_data[7];
                    end
                end

                ACTIVE: begin
                    if (cnt == 8'd1) begin
                        cnt    <= half;
                        sclk_i <= ~sclk_i;
                        sclk   <= ~sclk;

                        // Clock edge: determine if sample or drive
                        // sclk_i before toggle == cpol ? first edge : second edge
                        // CPHA=0: sample on first, drive on second
                        // CPHA=1: drive on first, sample on second
                        if ((sclk_i == cpol) ^ (cpha == 1'b1)) begin
                            // Sample MISO
                            rx <= {rx[6:0], miso};
                            if (bits == 3'd7) begin
                                miso_data <= {rx[6:0], miso};
                                done_i <= 1'b1;
                                done <= 1'b1;
                            end
                        end else begin
                            // Drive MOSI
                            if (bits <= 3'd7) begin
                                tx  <= {tx[6:0], 1'b0};
                                mosi <= tx[6];
                            end
                            if (bits < 3'd7) bits <= bits + 1;
                        end
                    end else begin
                        cnt <= cnt - 1;
                    end
                end

                FINISH: begin
                    done  <= 1'b0;
                    busy  <= 1'b0;
                    cs_n  <= 1'b1;
                    sclk  <= cpol;
                    sclk_i <= cpol;
                    cnt   <= half;
                end
            endcase
        end
    end

endmodule