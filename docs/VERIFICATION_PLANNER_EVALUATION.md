# Verification Planner Agent Evaluation Report

**Date:** 2026-06-15
**Benchmarks Evaluated:** 5 (alu_8bit, sync_fifo_8x16, fsm_traffic_light, uart_tx, apb_slave)
**Method:** Each benchmark's spec was parsed via SpecParserAgent, then a verification plan was generated via VerificationPlannerAgent. Plans were evaluated against reference RTL/TB ground truth.

## Summary Table

| Dimension | alu_8bit | sync_fifo_8x16 | fsm_traffic_light | uart_tx | apb_slave |
|-----------|----------|----------------|-------------------|---------|------------|
| Tier Structure | EXCELLENT | EXCELLENT | POOR | EXCELLENT | EXCELLENT |
| Test ID Structure | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT |
| Coverage Completeness | EXCELLENT | EXCELLENT | FAIR | EXCELLENT | EXCELLENT |
| Reference Model | EXCELLENT | EXCELLENT | POOR | EXCELLENT | EXCELLENT |
| Forbidden Behaviors | EXCELLENT | EXCELLENT | POOR | EXCELLENT | EXCELLENT |
| Timing Requirements | EXCELLENT | EXCELLENT | POOR | EXCELLENT | EXCELLENT |
| Redundancy (cross-tier) | EXCELLENT | FAIR | EXCELLENT | EXCELLENT | EXCELLENT |

### Overall Scores

| Benchmark | Overall Score | Details |
|-----------|---------------|---------|
| alu_8bit | **EXCELLENT** (avg=4.00) | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT |
| sync_fifo_8x16 | **EXCELLENT** (avg=3.71) | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | FAIR |
| fsm_traffic_light | **FAIR** (avg=2.00) | POOR | EXCELLENT | FAIR | POOR | POOR | POOR | EXCELLENT |
| uart_tx | **EXCELLENT** (avg=4.00) | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT |
| apb_slave | **EXCELLENT** (avg=4.00) | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT | EXCELLENT |

### Test Counts Summary

| Benchmark | Tier 1 | Tier 2 | Tier 3 | Total | TB Tests | Coverage |
|-----------|--------|--------|--------|-------|----------|----------|
| alu_8bit | 2 | 8 | 6 | 16 | 4 | 4/4 |
| sync_fifo_8x16 | 2 | 5 | 4 | 11 | 6 | 6/6 |
| fsm_traffic_light | 0 | 0 | 0 | 0 | 4 | 0/4 |
| uart_tx | 2 | 2 | 3 | 7 | 5 | 5/5 |
| apb_slave | 2 | 2 | 3 | 7 | 5 | 5/5 |

## Per-Benchmark Detailed Analysis

### alu_8bit

- **Design Type:** combinational
- **Spec Analysis Quality:** 9 behaviors, 4 corner cases

#### Tier Structure
- Score: **EXCELLENT**
- Tiers found: 3 (Reset and Initialization, Functional Verification, Boundary and Corner Cases)

#### Test ID Structure
- Score: **EXCELLENT**
- Total tests: 16
- IDs: T1_RESET_001, T1_RESET_002, T2_FUNC_001, T2_FUNC_002, T2_FUNC_003, T2_FUNC_004, T2_FUNC_005, T2_FUNC_006, T2_FUNC_007, T2_FUNC_008, T3_BOUNDARY_001, T3_BOUNDARY_002, T3_BOUNDARY_003, T3_BOUNDARY_004, T3_BOUNDARY_005, T3_BOUNDARY_006

#### Tests Per Tier
**Tier 1: Reset and Initialization** (2 tests)
  - `T1_RESET_001`: Check all outputs when all inputs are zero (no operation selected)
    - Stimulus: {"A": "00000000", "B": "00000000", "opcode": "000"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}
  - `T1_RESET_002`: Check zero_flag is 0 for non-zero result with addition opcode
    - Stimulus: {"A": "00000001", "B": "00000001", "opcode": "000"}
    - Expected: {"Y": "00000010", "zero_flag": "0"}
**Tier 2: Functional Verification** (8 tests)
  - `T2_FUNC_001`: Addition operation: 3 + 5 = 8
    - Stimulus: {"A": "00000011", "B": "00000101", "opcode": "000"}
    - Expected: {"Y": "00001000", "zero_flag": "0"}
  - `T2_FUNC_002`: Subtraction operation: 10 - 3 = 7
    - Stimulus: {"A": "00001010", "B": "00000011", "opcode": "001"}
    - Expected: {"Y": "00000111", "zero_flag": "0"}
  - `T2_FUNC_003`: Bitwise AND: 0x0F & 0xF0 = 0x00
    - Stimulus: {"A": "00001111", "B": "11110000", "opcode": "010"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}
  - `T2_FUNC_004`: Bitwise OR: 0x0F | 0xF0 = 0xFF
    - Stimulus: {"A": "00001111", "B": "11110000", "opcode": "011"}
    - Expected: {"Y": "11111111", "zero_flag": "0"}
  - `T2_FUNC_005`: Bitwise XOR: 0x0F ^ 0xF0 = 0xFF
    - Stimulus: {"A": "00001111", "B": "11110000", "opcode": "100"}
    - Expected: {"Y": "11111111", "zero_flag": "0"}
  - `T2_FUNC_006`: NOT A: ~0x55 = 0xAA
    - Stimulus: {"A": "01010101", "B": "00000000", "opcode": "101"}
    - Expected: {"Y": "10101010", "zero_flag": "0"}
  - `T2_FUNC_007`: Shift left: 0x01 << 1 = 0x02
    - Stimulus: {"A": "00000001", "B": "00000000", "opcode": "110"}
    - Expected: {"Y": "00000010", "zero_flag": "0"}
  - `T2_FUNC_008`: Shift right: 0x80 >> 1 = 0x40
    - Stimulus: {"A": "10000000", "B": "00000000", "opcode": "111"}
    - Expected: {"Y": "01000000", "zero_flag": "0"}
**Tier 3: Boundary and Corner Cases** (6 tests)
  - `T3_BOUNDARY_001`: Addition overflow: 200 + 100 = 300 truncated to 44 (0x2C)
    - Stimulus: {"A": "11001000", "B": "01100100", "opcode": "000"}
    - Expected: {"Y": "00101100", "zero_flag": "0"}
  - `T3_BOUNDARY_002`: Subtraction underflow: 3 - 5 = 254 (two's complement)
    - Stimulus: {"A": "00000011", "B": "00000101", "opcode": "001"}
    - Expected: {"Y": "11111110", "zero_flag": "0"}
  - `T3_BOUNDARY_003`: Shift left with overflow: 0x80 << 1 = 0x00 with zero_flag=1
    - Stimulus: {"A": "10000000", "B": "00000000", "opcode": "110"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}
  - `T3_BOUNDARY_004`: Shift right of 0x01 loses LSB: result 0, zero_flag=1
    - Stimulus: {"A": "00000001", "B": "00000000", "opcode": "111"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}
  - `T3_BOUNDARY_005`: NOT operation: ~0xFF = 0x00, zero_flag=1
    - Stimulus: {"A": "11111111", "B": "00000000", "opcode": "101"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}
  - `T3_BOUNDARY_006`: All opcodes with A=0, B=0 produce Y=0, zero_flag=1
    - Stimulus: {"A": "00000000", "B": "00000000", "opcode": "011"}
    - Expected: {"Y": "00000000", "zero_flag": "1"}

#### Coverage Completeness
- Score: **EXCELLENT**
- TB Functions: 4
- Covered in Plan: 4/4

#### Redundancy
- Score: **EXCELLENT**
- No redundant tests detected across tiers

#### Extra Tests (Not in Reference TB)
- 4 test(s) in the plan do not correspond to any reference TB test:
  - `T2_FUNC_001`: addition operation: 3 + 5 = 8
  - `T2_FUNC_002`: subtraction operation: 10 - 3 = 7
  - `T3_BOUNDARY_001`: addition overflow: 200 + 100 = 300 truncated to 44 (0x2c)
  - `T3_BOUNDARY_002`: subtraction underflow: 3 - 5 = 254 (two's complement)

#### Reference Model Quality
- Score: **EXCELLENT**
- Code length: 607 chars

```python
def reference_model(inputs):
    A = int(inputs['A'], 2)
    B = int(inputs['B'], 2)
    opcode = int(inputs['opcode'], 2)
    if opcode == 0:
        Y = (A + B) & 0xFF
    elif opcode == 1:
        Y = (A - B) & 0xFF
    elif opcode == 2:
        Y = A & B
    elif opcode == 3:
        Y = A | B
    elif opcode == 4:
        Y = A ^ B
    elif opcode == 5:
        Y = (~A) & 0xFF
    elif opcode == 6:
        Y = (A << 1) & 0xFF
    elif opcode == 7:
        Y = (A >> 1) & 0xFF
    else:
        Y = 0
    zero_flag = 1 if Y == 0 else 0
    return {'Y': format(Y, '08b'), 'zero_flag': str(zero_flag)}
```

#### Forbidden Behaviors
- Score: **EXCELLENT**
- Count: 5
  - Output Y should never be more than 8 bits wide or contain X/Z values
  - zero_flag should never be 1 when Y is non-zero
  - zero_flag should never be 0 when Y is zero
  - Output should never depend on previous inputs (combinational design)
  - Unused opcode values (if any) should produce a defined output (Y=0, zero_flag=1)

#### Timing Requirements
- Score: **EXCELLENT**
- Clock Signal: None
- Clock Period: None ns
- Skip STA: True

#### Overall Assessment
- **Overall: EXCELLENT** (average score: 4.00/4.0)

**Strengths:**
  - Tier Structure: EXCELLENT
  - Test ID Structure: EXCELLENT
  - Coverage Completeness: EXCELLENT
  - Reference Model: EXCELLENT
  - Forbidden Behaviors: EXCELLENT
  - Timing Requirements: EXCELLENT
  - Redundancy (cross-tier): EXCELLENT

**Weaknesses:**
  (none rated FAIR or POOR)

---

### sync_fifo_8x16

- **Design Type:** sequential
- **Spec Analysis Quality:** 5 behaviors, 4 corner cases

#### Tier Structure
- Score: **EXCELLENT**
- Tiers found: 3 (Reset and Initialization, Functional Verification, Boundary and Corner Cases)

#### Test ID Structure
- Score: **EXCELLENT**
- Total tests: 11
- IDs: T1_RESET, T1_RESET_DURING_OPERATION, T2_FUNC_001, T2_FUNC_002, T2_FUNC_003, T2_FUNC_004, T2_FUNC_005, T3_BOUNDARY_001, T3_BOUNDARY_002, T3_BOUNDARY_003, T3_BOUNDARY_004

#### Tests Per Tier
**Tier 1: Reset and Initialization** (2 tests)
  - `T1_RESET`: Assert reset and check that FIFO is empty and output is zero
    - Stimulus: {"clk": "posedge", "rst_n": "0", "wr_en": "0", "rd_en": "0", "din": "0"}
    - Expected: {"dout": "0", "full": "0", "empty": "1"}
  - `T1_RESET_DURING_OPERATION`: Reset while FIFO is partially full and then check it is cleared
    - Stimulus: {"clk": "posedge", "rst_n": "0 after some writes", "wr_en": "0", "rd_en": "0", "
    - Expected: {"dout": "0", "full": "0", "empty": "1"}
**Tier 2: Functional Verification** (5 tests)
  - `T2_FUNC_001`: Write one data word and read it back
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1", "rd_en": "0", "din": "0xA5"}
    - Expected: {"dout": "0x00", "full": "0", "empty": "0"}
  - `T2_FUNC_002`: Fill FIFO with 16 writes then check full
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1 for 16 cycles", "rd_en": "0", "din"
    - Expected: {"dout": "0x00", "full": "1", "empty": "0"}
  - `T2_FUNC_003`: Read from empty FIFO should not change state
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "0", "rd_en": "1", "din": "0"}
    - Expected: {"dout": "0", "full": "0", "empty": "1"}
  - `T2_FUNC_004`: Write to full FIFO should be ignored
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1 when full=1", "rd_en": "0", "din": 
    - Expected: {"dout": "0", "full": "1", "empty": "0"}
  - `T2_FUNC_005`: Simultaneous write and read when FIFO has 1 entry
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1", "rd_en": "1", "din": "0x42"}
    - Expected: {"dout": "previous data", "full": "0", "empty": "1"}
**Tier 3: Boundary and Corner Cases** (4 tests)
  - `T3_BOUNDARY_001`: Write when FIFO is almost full (15 entries) then write again
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1 for 15 cycles then 1 more", "rd_en"
    - Expected: {"dout": "0", "full": "1", "empty": "0"}
  - `T3_BOUNDARY_002`: Read when FIFO has 1 entry then read again
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1 for 1 cycle", "rd_en": "1 for 2 cyc
    - Expected: {"dout": "0x33 then 0x00", "full": "0", "empty": "1"}
  - `T3_BOUNDARY_003`: Concurrent write and read when FIFO is full
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1", "rd_en": "1", "din": "0xAA"}
    - Expected: {"dout": "valid data", "full": "0", "empty": "0"}
  - `T3_BOUNDARY_004`: Concurrent write and read when FIFO is empty
    - Stimulus: {"clk": "posedge", "rst_n": "1", "wr_en": "1", "rd_en": "1", "din": "0xBB"}
    - Expected: {"dout": "0", "full": "0", "empty": "0"}

#### Coverage Completeness
- Score: **EXCELLENT**
- TB Functions: 6
- Covered in Plan: 6/6

#### Redundancy
- Score: **FAIR**
- Redundant: 'T2_FUNC_005' (T2) matches 'T3_BOUNDARY_002' (T3)
- Redundant: 'T2_FUNC_005' (T2) matches 'T3_BOUNDARY_003' (T3)
- Redundant: 'T2_FUNC_005' (T2) matches 'T3_BOUNDARY_004' (T3)

#### Extra Tests (Not in Reference TB)
- All plan tests correspond to reference TB tests.

#### Reference Model Quality
- Score: **EXCELLENT**
- Code length: 1386 chars

```python
def reference_model(inputs: dict) -> dict:
    depth = 16
    wr_en = inputs.get('wr_en', 0)
    rd_en = inputs.get('rd_en', 0)
    din = inputs.get('din', 0)
    rst_n = inputs.get('rst_n', 1)
    # Assume internal state is passed via inputs for simulation purposes (simplified)
    # For a pure function, we model behavior assuming a given internal state
    # In practice, this would be part of a testbench with persistent state.
    # Here we return expected outputs based on inputs only for a simple one-cycle operation.
    # This is a placeholder; real reference model would require state.
    full = inputs.get('full', 0)
    empty = inputs.get('empty', 1)
    if not rst_n:
        return {'dout': 0, 'full': 0, 'empty': 1}
    new_full = full
    new_empty = empty
    dout = 0
    if wr_en and not full:
        if rd_en and not empty:
            # both: write is ignored if full, read is ignored if empty
            new_empty = 1 if empty else 0
            new_full = 0
            dout = din  # placeholder
        else:
            new_empty = 0
            new_full = (depth == 1)
    if rd_en and not empty:
        if wr_en and not full:
            # both: handled above
            pass
        else:
            new_empty = (depth == 1)
            new_full = 0
            dout = din  # placeholder
    return {'dout': dout, 'full': new_full, 'empty': new_empty}
```

#### Forbidden Behaviors
- Score: **EXCELLENT**
- Count: 5
  - Writing to FIFO when full is asserted
  - Reading from FIFO when empty is asserted
  - Data loss or corruption on simultaneous write and read
  - X or Z values on outputs after reset or during normal operation
  - Outputs changing on falling edge of clock (need to be synchronized to rising edge)

#### Timing Requirements
- Score: **EXCELLENT**
- Clock Signal: clk
- Clock Period: 10.0 ns
- Skip STA: False

#### Overall Assessment
- **Overall: EXCELLENT** (average score: 3.71/4.0)

**Strengths:**
  - Tier Structure: EXCELLENT
  - Test ID Structure: EXCELLENT
  - Coverage Completeness: EXCELLENT
  - Reference Model: EXCELLENT
  - Forbidden Behaviors: EXCELLENT
  - Timing Requirements: EXCELLENT

**Weaknesses:**
  - Redundancy (cross-tier): FAIR

---

### fsm_traffic_light

- **Design Type:** unknown
- **Spec Analysis Quality:** 4 behaviors, 2 corner cases

#### Tier Structure
- Score: **POOR**
- Tiers found: 0 ()
- Issue: Expected exactly 3 tiers, got 0
- Issue: Missing Tier 1 (Reset and Initialization)
- Issue: Missing Tier 2 (Functional Verification)
- Issue: Missing Tier 3 (Boundary and Corner Cases)

#### Test ID Structure
- Score: **EXCELLENT**
- Total tests: 0

#### Tests Per Tier

#### Coverage Completeness
- Score: **FAIR**
- TB Functions: 4
- Covered in Plan: 0/4

**Tests MISSING from plan (present in reference TB):**
  - `test_reset_initial_state`: After reset, verify RED state with correct output signals.
  - `test_red_to_green_transition`: Verify RED state holds for RED_COUNT=14 cycles,
    then transitions to GREEN at the 14th RisingEdge.
  - `test_green_to_yellow_transition`: Verify GREEN state holds for GREEN_COUNT=19 cycles,
    then transitions to YELLOW.
  - `test_yellow_to_red_transition`: Verify YELLOW state holds for YELLOW_COUNT=4 cycles,
    then transitions back to RED (completing the loop).

#### Redundancy
- Score: **EXCELLENT**
- No redundant tests detected across tiers

#### Extra Tests (Not in Reference TB)
- All plan tests correspond to reference TB tests.

#### Reference Model Quality
- Score: **POOR**
- Code length: 0 chars
- Issue: No reference model code provided

#### Forbidden Behaviors
- Score: **POOR**
- Count: 0
- No forbidden behaviors listed

#### Timing Requirements
- Score: **POOR**
- Clock Signal: None
- Clock Period: None ns
- Skip STA: True
- Issue: Sequential design but clock_signal is null
- Issue: Sequential design but clock_period_ns is null
- Issue: Sequential design but skip_sta=True, expected false

#### Overall Assessment
- **Overall: FAIR** (average score: 2.00/4.0)

**Strengths:**
  - Test ID Structure: EXCELLENT
  - Redundancy (cross-tier): EXCELLENT

**Weaknesses:**
  - Tier Structure: POOR
  - Coverage Completeness: FAIR
  - Reference Model: POOR
  - Forbidden Behaviors: POOR
  - Timing Requirements: POOR

---

### uart_tx

- **Design Type:** fsm
- **Spec Analysis Quality:** 7 behaviors, 4 corner cases

#### Tier Structure
- Score: **EXCELLENT**
- Tiers found: 3 (Reset and Initialization, Functional Verification, Boundary and Corner Cases)

#### Test ID Structure
- Score: **EXCELLENT**
- Total tests: 7
- IDs: T1_RESET_ASSERT, T1_RESET_DEASSERT, T2_FUNC_TRANSMIT_BYTE, T2_FUNC_BUSY_IDLE, T3_BOUNDARY_BAUD_DIV_MIN, T3_CORNER_RESET_DURING_TX, T3_CORNER_START_WHILE_BUSY

#### Tests Per Tier
**Tier 1: Reset and Initialization** (2 tests)
  - `T1_RESET_ASSERT`: Assert synchronous active-low reset and check outputs go to idle state
    - Stimulus: {"clk": "rising edge", "rst_n": "0", "tx_start": "0", "tx_data": "0", "baud_div"
    - Expected: {"tx": "1", "tx_busy": "0"}
  - `T1_RESET_DEASSERT`: Deassert reset synchronously and verify staying in idle state
    - Stimulus: {"clk": "rising edge", "rst_n": "0 for 2 cycles then 1", "tx_start": "0", "tx_da
    - Expected: {"tx": "1", "tx_busy": "0"}
**Tier 2: Functional Verification** (2 tests)
  - `T2_FUNC_TRANSMIT_BYTE`: Transmit a single byte and verify frame: start bit, 8 data bits LSB first, stop bit, and tx_busy timing
    - Stimulus: {"clk": "rising edge", "rst_n": "1", "tx_start": "pulse high for 1 cycle", "tx_d
    - Expected: {"tx": "after start: 0, then bits: 1,0,1,0,1,0,1,0, then stop: 1", "tx_busy": "1
  - `T2_FUNC_BUSY_IDLE`: Ensure tx_busy is low when idle and high during transmission, and external start ignored when busy
    - Stimulus: {"clk": "rising edge", "rst_n": "1", "tx_start": "pulse high for 1 cycle, then p
    - Expected: {"tx_busy": "0 -> 1 after first start -> 0 after stop, second start ignored"}
**Tier 3: Boundary and Corner Cases** (3 tests)
  - `T3_BOUNDARY_BAUD_DIV_MIN`: Test with baud_div=1 (minimum non-zero) to verify fastest baud rate
    - Stimulus: {"clk": "rising edge", "rst_n": "1", "tx_start": "pulse high", "tx_data": "0x01"
    - Expected: {"tx": "start=0, bits:1,0,0,0,0,0,0,0, stop=1, each for 1 clock cycle", "tx_busy
  - `T3_CORNER_RESET_DURING_TX`: Assert reset during active transmission and verify immediate reversion to idle
    - Stimulus: {"clk": "rising edge", "rst_n": "1 initially, then assert 0 mid-transmission", "
    - Expected: {"tx": "1", "tx_busy": "0"}
  - `T3_CORNER_START_WHILE_BUSY`: Assert tx_start while tx_busy is high should be ignored and current transmission continues
    - Stimulus: {"clk": "rising edge", "rst_n": "1", "tx_start": "pulse high when idle and again
    - Expected: {"tx_busy": "stays high for full duration of first transmission", "tx": "correct

#### Coverage Completeness
- Score: **EXCELLENT**
- TB Functions: 5
- Covered in Plan: 5/5

#### Redundancy
- Score: **EXCELLENT**
- No redundant tests detected across tiers

#### Extra Tests (Not in Reference TB)
- All plan tests correspond to reference TB tests.

#### Reference Model Quality
- Score: **EXCELLENT**
- Code length: 2578 chars

```python
def reference_model(inputs: dict) -> dict:
    # inputs: clk, rst_n, tx_start, tx_data, baud_div
    # State: IDLE=0, START_BIT=1, DATA_BITS=2, STOP_BIT=3
    state = getattr(reference_model, 'state', 0)
    bit_count = getattr(reference_model, 'bit_count', 0)
    timer = getattr(reference_model, 'timer', 0)
    shift_reg = getattr(reference_model, 'shift_reg', 0)
    latched_data = getattr(reference_model, 'latched_data', 0)
    tx = getattr(reference_model, 'tx', 1)
    tx_busy = getattr(reference_model, 'tx_busy', 0)
    
    clk = inputs['clk']
    rst_n = inputs['rst_n']
    tx_start = inputs['tx_start']
    tx_data = inputs['tx_data']
    baud_div = inputs['baud_div']
    
    if baud_div == 0:
        baud_div = 1  # avoid division by zero; undefined behavior, assume minimal
    
    # Reset behavior (synchronous on rising edge)
    if not rst_n:
        state = 0
        bit_count = 0
        timer = 0
        tx = 1
        tx_busy = 0
        reference_model.state = state
        reference_model.bit_count = bit_count
        reference_model.timer = timer
        reference_model.tx = tx
        reference_model.tx_busy = tx_busy
        return {'tx': 1, 'tx_busy': 0}
    
    # On rising edge
    if state == 0:  # IDLE
        if tx_start and not tx_busy:
            latched_data = tx_data
            shift_reg = latched_data
            bit_count = 0
            timer = 1
            state = 1  # START_BIT
            tx = 0
            tx_busy = 1
        else:
            tx = 1
            tx_busy = 0
    elif state == 1:  # START_BIT
        if timer < baud_div:
            timer += 1
        else:
            timer = 1
            state = 2  # DATA_BITS
            tx = (shift_reg >> 0) & 1
            bit_count = 1
    elif state == 2:  # DATA_BITS
        if timer < baud_div:
            timer += 1
        else:
            timer = 1
            if bit_count < 8:
                tx = (shift_reg >> bit_count) & 1
                bit_count += 1
            else:
                state = 3  # STOP_BIT
                tx = 1
    elif state == 3:  # STOP_BIT
        if timer < baud_div:
            timer += 1
        else:
            timer = 0
            state = 0  # IDLE
            tx = 1
            tx_busy = 0
    
    reference_model.state = state
    reference_model.bit_count = bit_count
    reference_model.timer = timer
    reference_model.shift_reg = shift_reg
    reference_model.latched_data = latched_data
    reference_model.tx = tx
    reference_model.tx_busy = tx_busy
    return {'tx': tx, 'tx_busy': tx_busy}
```

#### Forbidden Behaviors
- Score: **EXCELLENT**
- Count: 3
  - tx_start asserted during tx_busy=1 causing premature termination or corruption of current transmission
  - Reset deassertion causing metastable or unknown output values
  - tx line going high-Z or unknown during transmission other than defined start/data/stop states
- No design-type-specific forbidden behaviors found for 'fsm'

#### Timing Requirements
- Score: **EXCELLENT**
- Clock Signal: clk
- Clock Period: 10.0 ns
- Skip STA: False

#### Overall Assessment
- **Overall: EXCELLENT** (average score: 4.00/4.0)

**Strengths:**
  - Tier Structure: EXCELLENT
  - Test ID Structure: EXCELLENT
  - Coverage Completeness: EXCELLENT
  - Reference Model: EXCELLENT
  - Forbidden Behaviors: EXCELLENT
  - Timing Requirements: EXCELLENT
  - Redundancy (cross-tier): EXCELLENT

**Weaknesses:**
  (none rated FAIR or POOR)

---

### apb_slave

- **Design Type:** sequential
- **Spec Analysis Quality:** 6 behaviors, 3 corner cases

#### Tier Structure
- Score: **EXCELLENT**
- Tiers found: 3 (Reset and Initialization, Functional Verification, Boundary and Corner Cases)

#### Test ID Structure
- Score: **EXCELLENT**
- Total tests: 7
- IDs: T1_RESET_001, T1_RESET_002, T2_FUNC_001, T2_FUNC_002, T3_BOUNDARY_001, T3_BOUNDARY_002, T3_BOUNDARY_003

#### Tests Per Tier
**Tier 1: Reset and Initialization** (2 tests)
  - `T1_RESET_001`: Assert reset and verify all registers are zero
    - Stimulus: {"PRESETn": "0", "PCLK": "positive edge", "PSEL": "0", "PENABLE": "0", "PWRITE":
    - Expected: {"PRDATA": "32'h00000000", "PREADY": "1", "PSLVERR": "0"}
  - `T1_RESET_002`: Assert reset during operation and verify registers clear
    - Stimulus: {"PRESETn": "0", "PCLK": "positive edge", "PSEL": "1", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "32'h00000000", "PREADY": "1", "PSLVERR": "0"}
**Tier 2: Functional Verification** (2 tests)
  - `T2_FUNC_001`: Write to reg0 and read back
    - Stimulus: {"PRESETn": "1", "PCLK": "positive edge", "PSEL": "1", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "32'hDEADBEEF", "PREADY": "1", "PSLVERR": "0"}
  - `T2_FUNC_002`: Write to all four registers and read back
    - Stimulus: {"PRESETn": "1", "PCLK": "positive edge", "PSEL": "1", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "32'h12345678", "PREADY": "1", "PSLVERR": "0"}
**Tier 3: Boundary and Corner Cases** (3 tests)
  - `T3_BOUNDARY_001`: Write to invalid address (0x10) and check PSLVERR
    - Stimulus: {"PRESETn": "1", "PCLK": "positive edge", "PSEL": "1", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "don't care", "PREADY": "1", "PSLVERR": "1"}
  - `T3_BOUNDARY_002`: Read from invalid address (0x14) and check PSLVERR
    - Stimulus: {"PRESETn": "1", "PCLK": "positive edge", "PSEL": "1", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "32'h00000000", "PREADY": "1", "PSLVERR": "1"}
  - `T3_BOUNDARY_003`: PSEL=0 and PENABLE=1 should not trigger any transfer
    - Stimulus: {"PRESETn": "1", "PCLK": "positive edge", "PSEL": "0", "PENABLE": "1", "PWRITE":
    - Expected: {"PRDATA": "32'h00000000", "PREADY": "1", "PSLVERR": "0"}

#### Coverage Completeness
- Score: **EXCELLENT**
- TB Functions: 5
- Covered in Plan: 5/5

#### Redundancy
- Score: **EXCELLENT**
- No redundant tests detected across tiers

#### Extra Tests (Not in Reference TB)
- 1 test(s) in the plan do not correspond to any reference TB test:
  - `T3_BOUNDARY_003`: psel=0 and penable=1 should not trigger any transfer

#### Reference Model Quality
- Score: **EXCELLENT**
- Code length: 883 chars

```python
def reference_model(inputs: dict) -> dict:
    # Registers
    regs = {'reg0': 0x00000000, 'reg1': 0x00000000, 'reg2': 0x00000000, 'reg3': 0x00000000}
    addr_map = {0x00: 'reg0', 0x04: 'reg1', 0x08: 'reg2', 0x0C: 'reg3'}
    
    psel = inputs.get('PSEL', 0)
    penable = inputs.get('PENABLE', 0)
    pwrite = inputs.get('PWRITE', 0)
    paddr = inputs.get('PADDR', 0x00)
    pwdata = inputs.get('PWDATA', 0x00000000)
    
    slverr = 0
    prdata = 0x00000000
    
    if psel and penable:
        addr_key = paddr & 0x0C  # word-aligned
        if addr_key in addr_map:
            if pwrite:
                regs[addr_map[addr_key]] = pwdata
            else:
                prdata = regs[addr_map[addr_key]]
        else:
            slverr = 1
            if not pwrite:
                prdata = 0x00000000
    
    return {'PRDATA': prdata, 'PREADY': 1, 'PSLVERR': slverr}
```

#### Forbidden Behaviors
- Score: **EXCELLENT**
- Count: 3
  - Register content changed during read from invalid address
  - PSLVERR asserted when PSEL=0 or PENABLE=0
  - PRDATA contains X or Z values (must be driven to 0 or valid data)
- No design-type-specific forbidden behaviors found for 'sequential'

#### Timing Requirements
- Score: **EXCELLENT**
- Clock Signal: PCLK
- Clock Period: 10.0 ns
- Skip STA: False

#### Overall Assessment
- **Overall: EXCELLENT** (average score: 4.00/4.0)

**Strengths:**
  - Tier Structure: EXCELLENT
  - Test ID Structure: EXCELLENT
  - Coverage Completeness: EXCELLENT
  - Reference Model: EXCELLENT
  - Forbidden Behaviors: EXCELLENT
  - Timing Requirements: EXCELLENT
  - Redundancy (cross-tier): EXCELLENT

**Weaknesses:**
  (none rated FAIR or POOR)

---

## Cross-Benchmark Analysis

### Strengths Across Benchmarks

- **Tier Structure:** 4/5 EXCELLENT, 0/5 GOOD
- **Test ID Structure:** 5/5 EXCELLENT, 0/5 GOOD
- **Coverage Completeness:** 4/5 EXCELLENT, 0/5 GOOD
- **Reference Model:** 4/5 EXCELLENT, 0/5 GOOD
- **Forbidden Behaviors:** 4/5 EXCELLENT, 0/5 GOOD
- **Timing Requirements:** 4/5 EXCELLENT, 0/5 GOOD
- **Redundancy (cross-tier):** 4/5 EXCELLENT, 0/5 GOOD

### Weaknesses Across Benchmarks

- **Tier Structure:** 1/5 benchmarks rated FAIR or POOR
- **Coverage Completeness:** 1/5 benchmarks rated FAIR or POOR
- **Reference Model:** 1/5 benchmarks rated FAIR or POOR
- **Forbidden Behaviors:** 1/5 benchmarks rated FAIR or POOR
- **Timing Requirements:** 1/5 benchmarks rated FAIR or POOR
- **Redundancy (cross-tier):** 1/5 benchmarks rated FAIR or POOR

### Key Findings

**Tests consistently missing from plans:**
- fsm_traffic_light: `test_reset_initial_state` — After reset, verify RED state with correct output signals.
- fsm_traffic_light: `test_red_to_green_transition` — Verify RED state holds for RED_COUNT=14 cycles,
    then transitions to GREEN at the 14th RisingEdge.
- fsm_traffic_light: `test_green_to_yellow_transition` — Verify GREEN state holds for GREEN_COUNT=19 cycles,
    then transitions to YELLOW.
- fsm_traffic_light: `test_yellow_to_red_transition` — Verify YELLOW state holds for YELLOW_COUNT=4 cycles,
    then transitions back to RED (completing the loop).

### Recommendations

1. **Improve Reference Model Generation**: Reference models often lack complete opcode/behavior coverage. Consider few-shot examples or a dedicated reference model generator.
2. **Enforce Forbidden Behavior Completeness**: The planner frequently generates fewer than 3 forbidden behaviors or misses design-type-specific ones.
3. **Better Coverage of Corner Cases**: Some benchmarks miss important corner cases that the reference TB covers (e.g., simultaneous operations, overflow boundaries).
4. **Cross-Tier Redundancy**: Rare but should be checked — some tests appeared similar across functional and boundary tiers.
5. **Consistent Test ID Naming**: Ensure all test IDs follow T{1,2,3}_XXX format correctly.
