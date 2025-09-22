# Real Pfeiffer System

# Imports for communication with Pfeiffer gauge and Eurotherm temperature controller
import RealPfeifferTC110 as rpt
import PfiefferVacuumProtocol as pvp
from pymodbus.client import ModbusTcpClient

# Other imports
import sys
import serial
import time
import random
from dataclasses import dataclass
from PySide6.QtCore import (
    Qt, QObject, QThread, QTimer, Signal, Slot, QTime, QMetaObject
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStatusBar,
    QSizePolicy,
)

# -------------------------------
# Small reusable "card" widget
# -------------------------------
class SensorCard(QWidget):
    """
    A compact widget that shows:
      - Title (e.g., Temperature)
      - Big numeric value
      - Units (e.g., °C, mTorr)
      - Status dot (green/amber/red)
      - Last update time
    """
    def __init__(self, title: str, units: str, parent=None, scientific=False):
        super().__init__(parent)

        self._title = QLabel(title)
        self._title.setStyleSheet("font-weight: 600; font-size: 16px;")
        self._title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._scientific = scientific

        self._value = QLabel("--")
        self._value.setStyleSheet("font-size: 40px; font-weight: 700;")
        self._value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._units = QLabel(units)
        self._units.setStyleSheet("font-size: 16px; color: #666;")
        self._units.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color: #999; font-size: 14px;")
        self._status_txt = QLabel("Idle")
        self._status_txt.setStyleSheet("color: #666;")

        self._last_update = QLabel("Last update: --:--:--")
        self._last_update.setStyleSheet("color: #666;")

        outer = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._status_dot)
        header.addWidget(self._status_txt)

        value_row = QHBoxLayout()
        value_row.addStretch(1)
        value_row.addWidget(self._value)
        value_row.addSpacing(8)
        value_row.addWidget(self._units)

        footer = QHBoxLayout()
        footer.addWidget(self._last_update)
        footer.addStretch(1)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 10px; }")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.addLayout(header)
        frame_layout.addSpacing(6)
        frame_layout.addLayout(value_row)
        frame_layout.addSpacing(6)
        frame_layout.addLayout(footer)

        outer.addWidget(frame)

    @Slot(float)
    def set_value(self, val: float, decimals: int = 2):
        try:
            if self._scientific:
                self._value.setText(f"{val:.{decimals}e}")
            else:
                self._value.setText(f"{val:.{decimals}f}")
        except Exception:
            self._value.setText(str(val))

        t = QTime.currentTime().toString("HH:mm:ss")
        self._last_update.setText(f"Last update: {t}")

    def set_status(self, status: str):
        status = status.lower()
        color = "#999"
        text = status.capitalize()
        if status == "connected":
            color = "#3BA55D"
            text = "Connected"
        elif status == "disconnected":
            color = "#E3B341"
            text = "Disconnected"
        elif status == "error":
            color = "#D83C3E"
            text = "Error"
        elif status == "idle":
            color = "#999"
            text = "Idle"

        self._status_dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._status_txt.setText(text)


# -------------------------------
# Worker scaffolding
# -------------------------------
@dataclass
class WorkerConfig:
    """Extend as needed."""
    name: str
    poll_interval_ms: int = 200

class ReadingWorker(QObject):
    """
    Generic data-polling worker that emits a float value periodically.
    QTimer is created in start() (worker's thread), not in __init__.
    """
    reading = Signal(float)
    status = Signal(str)
    error = Signal(str)
    started = Signal()
    stopped = Signal()

    def __init__(self, cfg: WorkerConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self._timer: QTimer | None = None
        self._running = False

    @Slot()
    def start(self):
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setInterval(self.cfg.poll_interval_ms)
            self._timer.timeout.connect(self._on_poll)
        self._running = True
        self._timer.start()
        self.status.emit("connected")
        self.started.emit()

    @Slot()
    def stop(self):
        self._running = False
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        self.status.emit("disconnected")
        self.stopped.emit()

    @Slot()
    def _on_poll(self):
        if not self._running:
            return
        try:
            value = self.read_device_value()
            self.reading.emit(value)
        except Exception as exc:
            # surface error; keep polling (will attempt lazy reconnect in read_device_value)
            self.status.emit("error")
            self.error.emit(f"{self.cfg.name}: {exc}")

    def read_device_value(self) -> float:
        raise NotImplementedError


# -------------------------------
# Temperature worker (Modbus TCP)
# -------------------------------
class TempWorker(ReadingWorker):
    """
    Opens ONE persistent Modbus TCP connection in start(), reuses it every poll.
    Attempts lazy reconnect if disconnected.
    """
    def __init__(self, cfg: WorkerConfig, parent=None):
        super().__init__(cfg, parent)
        self._client: ModbusTcpClient | None = None
        self._ip = "192.168.111.222"   # Eurotherm IP
        self._address = 1            # Holding register address to read
        self._reconnect_cooldown_s = 1.5
        self._next_reconnect_ts = 0.0

    def _ensure_connected(self):
        now = time.monotonic()
        if self._client is None:
            self._client = ModbusTcpClient(self._ip, timeout=1)  # 2s socket timeout
        if not self._client.connected:
            if now < self._next_reconnect_ts:
                raise RuntimeError("Modbus not connected (cooling down)")
            if not self._client.connect():
                self._next_reconnect_ts = now + self._reconnect_cooldown_s
                raise RuntimeError("Could not connect to Modbus TCP server")

    def start(self):
        # Establish initial connection (will throw if fails)
        try:
            self._ensure_connected()
        except Exception as e:
            # We'll still start the timer to attempt reconnects later
            self.error.emit(f"{self.cfg.name}: {e}")
        super().start()

    def stop(self):
        super().stop()
        try:
            if self._client is not None:
                self._client.close()
        finally:
            self._client = None

    def read_device_value(self) -> float:
        # Make sure we're connected; may raise on cooldown
        self._ensure_connected()

        # Read one holding register; use correct signature with unit=
        rr = self._client.read_holding_registers(self._address, count=1)
        print(rr)
        if rr.isError():
            # communication level ok but device returned a Modbus exception
            raise RuntimeError(f"Modbus error: {rr}")

        raw = rr.registers[0]
        # Apply scaling if needed. For now, return raw (or convert to °C if you know the scale).
        return float(raw)


# -------------------------------
# Pressure worker (Serial + Pfeiffer)
# -------------------------------
class PressureWorker(ReadingWorker):
    """
    Opens ONE persistent serial port in start(), reuses it every poll.
    Attempts lazy reopen on failure.
    """
    def __init__(self, cfg: WorkerConfig, parent=None):
        super().__init__(cfg, parent)
        self._ser: serial.Serial | None = None
        self._port = "/dev/tty.usbserial-BG000M9B"
        self._baud = 9600
        self._timeout = 1
        self._address = 122
        self._reconnect_cooldown_s = 1.5
        self._next_reconnect_ts = 0.0

    def _ensure_open(self):
        now = time.monotonic()
        if self._ser is None or not self._ser.is_open:
            if now < self._next_reconnect_ts:
                raise RuntimeError("Serial not open (cooling down)")
            try:
                self._ser = serial.Serial(self._port, baudrate=self._baud, timeout=self._timeout)
            except Exception as e:
                self._next_reconnect_ts = now + self._reconnect_cooldown_s
                raise RuntimeError(f"Serial open failed: {e}")

    def start(self):
        try:
            self._ensure_open()
        except Exception as e:
            self.error.emit(f"{self.cfg.name}: {e}")
        super().start()

    def stop(self):
        super().stop()
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        finally:
            self._ser = None

    def read_device_value(self) -> float:
        self._ensure_open()
        # Read pressure once from the persistent port
        p = pvp.read_pressure(self._ser, self._address)
        return float(p)


# -------------------------------
# Main window
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Temperature & Pressure Monitor")
        self.resize(640, 420)
        self.setStatusBar(QStatusBar(self))

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        self.temp_card = SensorCard("Temperature", "°C", scientific=False)
        self.pres_card = SensorCard("Pressure", "mTorr", scientific=True)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addStretch(1)

        root.addLayout(controls)
        root.addWidget(self.temp_card)
        root.addWidget(self.pres_card)

        self.setCentralWidget(central)

        self._threads: list[QThread] = []
        self._workers: list[ReadingWorker] = []

        self._setup_workers()

        self.start_btn.clicked.connect(self._start_workers)
        self.stop_btn.clicked.connect(self._stop_workers)

    def _setup_workers(self):
        temp_cfg = WorkerConfig(name="TempWorker", poll_interval_ms=200)
        pres_cfg = WorkerConfig(name="PressureWorker", poll_interval_ms=200)
        self._add_worker(temp_cfg, self.temp_card, worker_cls=TempWorker)
        self._add_worker(pres_cfg, self.pres_card, worker_cls=PressureWorker)

    def _add_worker(self, cfg: WorkerConfig, card: SensorCard, worker_cls=ReadingWorker):
        thread = QThread(self)
        worker = worker_cls(cfg)
        worker.moveToThread(thread)

        thread.started.connect(worker.start)
        thread.finished.connect(worker.deleteLater)

        worker.reading.connect(lambda v, c=card: c.set_value(v))
        worker.status.connect(lambda s, c=card, name=cfg.name: self._on_status(c, name, s))
        worker.error.connect(self._on_error)

        self._threads.append(thread)
        self._workers.append(worker)
    
    def _teardown_workers(self):
        # ask workers to stop in their own threads
        for w in self._workers:
            QMetaObject.invokeMethod(w, "stop", Qt.QueuedConnection)
        # stop threads
        for t in self._threads:
            if t.isRunning():
                t.quit()
                t.wait(1500)
            t.deleteLater()
        # workers were deleteLater()’d by thread.finished, so just clear lists
        self._threads.clear()
        self._workers.clear()

    def _start_workers(self):
        if any(t.isRunning() for t in self._threads):
            return
        if not self._threads:          # nothing exists -> (re)create
            self._setup_workers()
        for t in self._threads:
            t.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage("Polling started")

    def _stop_workers(self):
        self._teardown_workers()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Polling stopped")

    def _on_status(self, card: SensorCard, name: str, status: str):
        card.set_status(status)
        self.statusBar().showMessage(f"{name}: {status}")

    def _on_error(self, msg: str):
        self.statusBar().showMessage(f"Error: {msg}")

    def closeEvent(self, event):
        try:
            self._stop_workers()
        finally:
            super().closeEvent(event)


# File-saving directories

# -------------------------------
# Harness (run this file directly)
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
