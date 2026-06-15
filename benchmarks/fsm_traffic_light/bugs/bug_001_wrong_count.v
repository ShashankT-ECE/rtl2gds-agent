// Bug injection: RED_COUNT changed from 15 to 10, causing the red light to
// transition to green too early.

module fsm_traffic_light (
    input  wire       clk,
    input  wire       rst_n,
    output reg        red_light,
    output reg        green_light,
    output reg        yellow_light,
    output reg  [1:0] state_out
);

    // State encoding
    localparam RED    = 2'b00;
    localparam GREEN  = 2'b01;
    localparam YELLOW = 2'b10;

    // Timing parameters
    localparam RED_COUNT    = 10;
    localparam GREEN_COUNT  = 20;
    localparam YELLOW_COUNT = 5;

    // State and counter registers
    reg [1:0] state, next_state;
    reg [4:0] counter; // Max count = 20, so 5 bits

    // Asynchronous reset and state/counter update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= RED;
            counter     <= 0;
            red_light    <= 1;
            green_light  <= 0;
            yellow_light <= 0;
            state_out   <= RED;
        end else begin
            state   <= next_state;
            state_out <= next_state;
            // Update lights based on next state
            case (next_state)
                RED: begin
                    red_light    <= 1;
                    green_light  <= 0;
                    yellow_light <= 0;
                end
                GREEN: begin
                    red_light    <= 0;
                    green_light  <= 1;
                    yellow_light <= 0;
                end
                YELLOW: begin
                    red_light    <= 0;
                    green_light  <= 0;
                    yellow_light <= 1;
                end
                default: begin
                    red_light    <= 0;
                    green_light  <= 0;
                    yellow_light <= 0;
                end
            endcase
        end
    end

    // Next state logic and counter control
    always @(*) begin
        // Default: stay in same state, counter increments
        next_state = state;
        case (state)
            RED: begin
                if (counter == RED_COUNT - 1)
                    next_state = GREEN;
            end
            GREEN: begin
                if (counter == GREEN_COUNT - 1)
                    next_state = YELLOW;
            end
            YELLOW: begin
                if (counter == YELLOW_COUNT - 1)
                    next_state = RED;
            end
            default: next_state = RED;
        endcase
    end

    // Counter sequential logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 0;
        end else begin
            if (state != next_state) begin
                // Transition occurred, reset counter
                counter <= 0;
            end else begin
                // Stay in same state, increment counter
                counter <= counter + 1;
            end
        end
    end

endmodule
