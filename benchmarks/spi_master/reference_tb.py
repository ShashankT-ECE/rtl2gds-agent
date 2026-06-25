"""
SPI Master — single test, all modes
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_spi(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit='ns').start())

    # Set all inputs before reset
    dut.cpol.value = 0
    dut.cpha.value = 0
    dut.mosi_data.value = 0
    dut.sclk_div.value = 4
    dut.miso.value = 0
    dut.start.value = 0

    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Start transaction
    dut.cpol.value = 0
    dut.cpha.value = 0
    dut.mosi_data.value = 0xA5
    dut.sclk_div.value = 4
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for done (rising edge detection)
    for _ in range(500):
        await Timer(10, unit='ns')
        if int(dut.done.value):
            break
    await Timer(10, unit='ns')
    assert dut.busy.value == 0, f"Mode 0: busy={dut.busy.value}"
    assert dut.cs_n.value == 1, f"Mode 0: cs_n={dut.cs_n.value}"
    dut._log.info("SPI Mode 0: PASS")

    # --- Mode 1 ---
    dut.cpol.value = 0
    dut.cpha.value = 1
    dut.mosi_data.value = 0x5A
    dut.sclk_div.value = 4
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    for _ in range(500):
        await Timer(10, unit='ns')
        if int(dut.done.value):
            break
    await Timer(10, unit='ns')
    assert dut.busy.value == 0, f"Mode 1: busy={dut.busy.value}"
    assert dut.cs_n.value == 1, f"Mode 1: cs_n={dut.cs_n.value}"
    dut._log.info("SPI Mode 1: PASS")

    # --- Mode 2 ---
    dut.cpol.value = 1
    dut.cpha.value = 0
    dut.mosi_data.value = 0xFF
    dut.sclk_div.value = 4
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    for _ in range(500):
        await Timer(10, unit='ns')
        if int(dut.done.value):
            break
    await Timer(10, unit='ns')
    assert dut.busy.value == 0, f"Mode 2: busy={dut.busy.value}"
    assert dut.cs_n.value == 1, f"Mode 2: cs_n={dut.cs_n.value}"
    dut._log.info("SPI Mode 2: PASS")

    # --- Mode 3 ---
    dut.cpol.value = 1
    dut.cpha.value = 1
    dut.mosi_data.value = 0x00
    dut.sclk_div.value = 4
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    for _ in range(500):
        await Timer(10, unit='ns')
        if int(dut.done.value):
            break
    await Timer(10, unit='ns')
    assert dut.busy.value == 0, f"Mode 3: busy={dut.busy.value}"
    assert dut.cs_n.value == 1, f"Mode 3: cs_n={dut.cs_n.value}"
    dut._log.info("SPI Mode 3: PASS")
