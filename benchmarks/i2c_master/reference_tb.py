"""
I2C Master Testbench — mirror SDA + edge-triggered ACK
"""
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

@cocotb.test()
async def test_i2c(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit='ns').start())

    # Set all inputs before reset
    dut.scl_div.value = 50
    dut.addr.value = 0
    dut.rw.value = 0
    dut.wdata.value = 0
    dut.start.value = 0
    dut.sda.value = 1

    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Background: mirror SDA bus
    slave_sda = [1]
    async def sda_mirror():
        while True:
            await Timer(1, unit='ns')
            if dut.sda_oe.value:
                dut.sda.value = dut.sda_out.value
            else:
                dut.sda.value = slave_sda[0]
    cocotb.start_soon(sda_mirror())

    # === WRITE ===
    dut._log.info("=== WRITE ===")
    dut.addr.value = 0x48
    dut.rw.value = 0
    dut.wdata.value = 0xAB
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    await RisingEdge(dut.busy)

    # ADDR_ACK: sda_oe falls → drive ACK
    await FallingEdge(dut.sda_oe)
    slave_sda[0] = 0
    await RisingEdge(dut.sda_oe)
    slave_sda[0] = 1

    # DATA_ACK
    await FallingEdge(dut.sda_oe)
    slave_sda[0] = 0
    await RisingEdge(dut.sda_oe)
    slave_sda[0] = 1

    # Wait for done
    for _ in range(10000):
        await Timer(1, unit='ns')
        if dut.done.value:
            break
    await Timer(10, unit='ns')

    assert dut.ack_error.value == 0, f"Write ack_error={dut.ack_error.value}"
    dut._log.info("Write PASS")

    # === NACK ===
    dut._log.info("=== NACK ===")
    dut.addr.value = 0x70
    dut.rw.value = 0
    dut.wdata.value = 0x00
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    await RisingEdge(dut.busy)
    slave_sda[0] = 1  # always NACK

    for _ in range(10000):
        await Timer(1, unit='ns')
        if dut.done.value:
            break
    await Timer(10, unit='ns')

    assert dut.ack_error.value == 1, f"NACK test got ack_error={dut.ack_error.value}"
    dut._log.info("NACK PASS")
