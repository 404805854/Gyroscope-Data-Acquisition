import serial.tools.list_ports
import serial
from loguru import logger
from typing import Optional
import time


class Gyros():
    class Metadata():
        yaw: float
        pitch: float
        roll: float

        def __str__(self):
            return f"yaw : {self.yaw}, pitch : {self.pitch}, roll : {self.roll}"

    def __init__(self, key: str = "arduino", baudrate: int = 115200, timeout: int = 5) -> None:
        self.key = key
        self.baudrate = baudrate
        self.timeout = timeout
        self.port = None
        self.serial = None

        self._set_available_port()
        logger.info(f"port : {self.port}")
        self._init_serial()

    def _get_port_list(self) -> list:
        import serial.tools.list_ports
        return list(serial.tools.list_ports.comports())

    def _set_available_port(self) -> None:
        ret = []

        port_list = self._get_port_list()
        for port in port_list:
            if self.key in port.description.lower():
                ret.append(port.device)

        if len(ret) == 1:
            self.port = ret[0]
        else:
            for port in port_list:
                logger.error(str(port))

    def _init_serial(self) -> None:
        if self.port is not None:
            time.sleep(0.5)
            self.serial = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            time.sleep(0.5)

    def _write(self, data: str) -> bool:
        data = data.strip() + "\n"
        if self.check():
            self.serial.write(data.encode("utf8"))

    def _readline(self) -> Optional[str]:
        if self.check():
            return self.serial.readline().decode("utf8")

    def check(self) -> bool:
        return self.serial is not None and not self.serial.closed

    def start(self) -> None:
        if self.serial is None:
            self._init_serial()
            
        self._write("start")
        while True:
            data = self._readline()
            if data is None:
                break
            if "ready" in data.lower():
                logger.info("gyros start")
                break

    def get(self) -> Optional[Metadata]:
        if self.check():
            data = self._readline()
            arr = data.strip().split("\t")
            metadata = self.Metadata()
            metadata.yaw = float(arr[1])
            metadata.pitch = float(arr[2])
            metadata.roll = float(arr[3])
            return metadata

    def close(self) -> None:
        if self.serial is not None:
            self._write("soft_reboot")
            self.serial.close()
            logger.info("gyros close")
        self.serial = None

    def restart(self) -> None:
        self.close()
        time.sleep(1)
        self.start()

    def __del__(self) -> None:
        self.close()


def main():
    gyros = Gyros()
    if not gyros.check():
        print(gyros._get_port_list())
        exit()
    gyros.start()
    for _ in range(10):
        logger.info(str(gyros.get()))
    gyros.restart()
    for _ in range(10):
        logger.info(str(gyros.get()))


if __name__ == "__main__":
    main()
