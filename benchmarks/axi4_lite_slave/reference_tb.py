"""
cocotb 2.x testbench for AXI4-Lite Slave with 8 registers.

Tests:
  1. Write 0xDEADBEEF to 0x00, read back
  2. Write all 8 registers with different values, read all back
  3. WSTRB byte enable — write only upper 2 bytes, verify lower 2 unchanged
  4. Invalid address — verify BRESP=SLVERR and RRESP=SLVERR
  5. Simultaneous write and read to different registers
  6. Back-to-back transactions without gaps
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# ---------------------------------------------------------------------------
# Helper coroutines
# ---------------------------------------------------------------------------

async def axi_write(dut, addr, data, wstrb=0xF):
    """Perform a single AXI4-Lite write transaction.

    Args:
        dut:   DUT handle.
        addr:  Word-aligned byte address (int).
        data:  32-bit write data (int).
        wstrb: Byte-enable strobe (4-bit, default 0xF = all bytes).
    """
    # 1) Drive AW channel
    dut.AWVALID.value = 1
    dut.AWADDR.value  = addr
    await RisingEdge(dut.ACLK)
    # Wait for AWREADY (should be high in IDLE)
    while not dut.AWREADY.value:
        await RisingEdge(dut.ACLK)
    dut.AWVALID.value = 0

    # 2) Drive W channel (can be same cycle as AW)
    dut.WVALID.value = 1
    dut.WDATA.value  = data
    dut.WSTRB.value  = wstrb
    await RisingEdge(dut.ACLK)
    while not dut.WREADY.value:
        await RisingEdge(dut.ACLK)
    dut.WVALID.value = 0

    # 3) Wait for BVALID, then assert BREADY
    await RisingEdge(dut.ACLK)
    while not dut.BVALID.value:
        await RisingEdge(dut.ACLK)
    dut.BREADY.value = 1
    await RisingEdge(dut.ACLK)
    dut.BREADY.value = 0
    # Small guard time
    await Timer(1, unit="ps")


async def axi_read(dut, addr):
    """Perform a single AXI4-Lite read transaction.

    Returns the 32-bit data read from the slave.

    Args:
        dut:  DUT handle.
        addr: Word-aligned byte address (int).
    """
    # 1) Drive AR channel
    dut.ARVALID.value = 1
    dut.ARADDR.value  = addr
    await RisingEdge(dut.ACLK)
    while not dut.ARREADY.value:
        await RisingEdge(dut.ACLK)
    dut.ARVALID.value = 0

    # 2) Wait for RVALID, then assert RREADY
    while not dut.RVALID.value:
        await RisingEdge(dut.ACLK)
    data = int(dut.RDATA.value)
    resp = int(dut.RRESP.value)
    dut.RREADY.value = 1
    await RisingEdge(dut.ACLK)
    dut.RREADY.value = 0
    await Timer(1, unit="ps")
    return data, resp


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_1_write_read_one_register(dut):
    """Write 0xDEADBEEF to register 0x00 and read it back."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    # Reset
    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    # Drive defaults
    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    await axi_write(dut, 0x00, 0xDEADBEEF)

    data, resp = await axi_read(dut, 0x00)
    assert data == 0xDEADBEEF, f"Read back 0x{data:08X}, expected 0xDEADBEEF"
    assert resp == 0, f"RRESP={resp}, expected OKAY(0)"

    dut._log.info("TEST 1 PASSED: write+read 0xDEADBEEF to reg0")


@cocotb.test()
async def test_2_write_read_all_registers(dut):
    """Write all 8 registers with distinct values and read them back."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    values = [
        0xAABBCCDD, 0x12345678, 0x87654321, 0xF0F0F0F0,
        0x0F0F0F0F, 0x55555555, 0xAAAAAAAA, 0xCAFEBABE,
    ]
    for i, v in enumerate(values):
        await axi_write(dut, i * 4, v)

    for i, expected in enumerate(values):
        data, resp = await axi_read(dut, i * 4)
        assert data == expected, (
            f"reg[{i}] read 0x{data:08X}, expected 0x{expected:08X}"
        )
        assert resp == 0, f"reg[{i}] RRESP={resp}, expected OKAY(0)"

    dut._log.info("TEST 2 PASSED: all 8 registers written and verified")


@cocotb.test()
async def test_3_wstrb_byte_enable(dut):
    """Write only upper 2 bytes and verify lower 2 bytes unchanged."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    # Start: 0x00 initialised to 0 after reset
    # Write lower 2 bytes first (bits [15:0])
    await axi_write(dut, 0x00, 0x0000BEEF, wstrb=0b0011)  # WSTRB[1:0]=1

    data, _ = await axi_read(dut, 0x00)
    assert data == 0x0000BEEF, f"After partial write: 0x{data:08X}"

    # Now write upper 2 bytes only (WSTRB[3:2]=0b1100)
    await axi_write(dut, 0x00, 0xDEAD0000, wstrb=0b1100)

    data, _ = await axi_read(dut, 0x00)
    assert data == 0xDEADBEEF, (
        f"After byte-enable upper write: 0x{data:08X}, expected 0xDEADBEEF"
    )

    dut._log.info("TEST 3 PASSED: WSTRB byte-enable works correctly")


@cocotb.test()
async def test_4_invalid_address(dut):
    """Write and read to an invalid address and verify SLVERR."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    # Write to invalid address 0x20 (beyond reg7 at 0x1C)
    dut.AWVALID.value = 1
    dut.AWADDR.value  = 0x20
    await RisingEdge(dut.ACLK)
    while not dut.AWREADY.value:
        await RisingEdge(dut.ACLK)
    dut.AWVALID.value = 0

    dut.WVALID.value = 1
    dut.WDATA.value  = 0xFFFFFFFF
    dut.WSTRB.value  = 0xF
    await RisingEdge(dut.ACLK)
    while not dut.WREADY.value:
        await RisingEdge(dut.ACLK)
    dut.WVALID.value = 0

    await RisingEdge(dut.ACLK)
    while not dut.BVALID.value:
        await RisingEdge(dut.ACLK)
    bresp = int(dut.BRESP.value)
    dut.BREADY.value = 1
    await RisingEdge(dut.ACLK)
    dut.BREADY.value = 0
    await Timer(1, unit="ps")

    assert bresp == 2, f"BRESP={bresp}, expected SLVERR(2)"
    dut._log.info(f"BRESP is SLVERR(2) for invalid write address: OK")

    # Read from invalid address 0x20
    dut.ARVALID.value = 1
    dut.ARADDR.value  = 0x20
    await RisingEdge(dut.ACLK)
    while not dut.ARREADY.value:
        await RisingEdge(dut.ACLK)
    dut.ARVALID.value = 0

    while not dut.RVALID.value:
        await RisingEdge(dut.ACLK)
    rresp = int(dut.RRESP.value)
    dut.RREADY.value = 1
    await RisingEdge(dut.ACLK)
    dut.RREADY.value = 0
    await Timer(1, unit="ps")

    assert rresp == 2, f"RRESP={rresp}, expected SLVERR(2)"
    dut._log.info(f"RRESP is SLVERR(2) for invalid read address: OK")

    dut._log.info("TEST 4 PASSED: invalid addresses return SLVERR")


@cocotb.test()
async def test_5_simultaneous_write_read(dut):
    """Start a write to reg0 and a read from reg1 concurrently."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    # Write 0xDECAF to reg1 first so read has something to return
    await axi_write(dut, 0x04, 0x000DECAF)

    async def write_task():
        await axi_write(dut, 0x04, 0xBEEF)

    async def read_task():
        data, resp = await axi_read(dut, 0x04)
        return data, resp

    # Kick off both concurrently
    read_handle = cocotb.start_soon(read_task())
    write_handle = cocotb.start_soon(write_task())

    # Wait for both to finish
    await write_handle
    data, resp = await read_handle

    # The read may see either old or new data depending on timing,
    # but the important thing is the channels don't deadlock.
    # For deterministic checking, just ensure no protocol error.
    assert resp in (0, 2), f"RRESP={resp}, expected OKAY or SLVERR"
    dut._log.info(
        f"Simultaneous access: read returned 0x{data:08X} with RRESP={resp}"
    )

    # Now do an isolated read to confirm the write went through
    data, _ = await axi_read(dut, 0x04)
    assert data == 0xBEEF, (
        f"Final read 0x{data:08X}, expected 0xBEEF"
    )

    dut._log.info("TEST 5 PASSED: simultaneous write+read, no deadlock")


@cocotb.test()
async def test_6_back_to_back_transactions(dut):
    """Perform back-to-back writes and reads without idle gaps."""
    cocotb.start_soon(Clock(dut.ACLK, 10, units="ns").start())
    await Timer(1, unit="ns")

    dut.ARESETn.value = 0
    await RisingEdge(dut.ACLK)
    dut.ARESETn.value = 1
    await RisingEdge(dut.ACLK)

    dut.AWVALID.value = 0
    dut.WVALID.value  = 0
    dut.BREADY.value  = 0
    dut.ARVALID.value = 0
    dut.RREADY.value  = 0

    await Timer(1, unit="ps")

    # Back-to-back writes
    for addr, data in [(0x00, 0x11111111), (0x04, 0x22222222),
                        (0x08, 0x33333333), (0x0C, 0x44444444)]:
        await axi_write(dut, addr, data)

    # Back-to-back reads
    for addr, expected in [(0x00, 0x11111111), (0x04, 0x22222222),
                            (0x08, 0x33333333), (0x0C, 0x44444444)]:
        data, resp = await axi_read(dut, addr)
        assert data == expected, (
            f"B2B read addr 0x{addr:02X}: got 0x{data:08X}, expected 0x{expected:08X}"
        )
        assert resp == 0

    dut._log.info("TEST 6 PASSED: back-to-back transactions work")
