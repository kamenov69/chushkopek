"""Hardware-free model of the Chushkopek Arduino command interface.

Only synthetic data. Never opens a serial port. See SIMULATOR.md for fidelity.
"""
import math
import random
import time

from .pykiba import Pykiba


# Registration order in main.cpp and its setup_* functions. CmdArduino prepends.
VARIABLES = {
    'crdy': (1, 0, 0), 't0': (1, 0, 0), 't1': (1, 0, 0),
    'pwm0': (0, 0, 1023), 'pwm1': (0, 0, 1023),
    'sp0': (10, 0, 370), 'sp1': (10, 0, 370),
    'kp': (50, 0.01, 1000), 'tau': (50 / 3, 0.05, 600),
    'pidm': (0, 0, 2), 'peepm': (1, 0, 1),
}
REGISTRATION = (
    ['hlp', 'echo', 'hello', 'mode']
    + [f'buf{i}' for i in range(4)] + [f'sum{i}' for i in range(4)]
    + ['adctst', 'adcclr', 'crdy', 't0', 't1', 'pwm0', 'pwm1',
       'sp0', 'sp1', 'kp', 'tau', 'pidm', 'pid', 'peep', 'peepm', 'varlst']
)


class SimulatedDevice:
    """Expose firmware commands directly as methods, like PykiDev."""

    def __init__(self, clock=time.monotonic, seed=1):
        self._clock = clock
        self._origin = clock()
        self._offset = 0.0
        self._ticks = 0
        self._random = random.Random(seed)
        self._buffers = [[0.0] * n for n in (64, 64, 8, 8)]
        self._counts = [0, 0, 0, 0]
        self._temperature = [22.0, 22.0]
        self._faults = [False, False]
        self._integral = [0.0, 0.0]
        self._previous_input = [1.0, 1.0]
        self._capture_start = 0.0
        self._updated = {name: True for name in VARIABLES}
        self._values = {name: float(spec[0]) for name, spec in VARIABLES.items()}
        self._mode = 0
        self._echo = 1
        for name in self.commands_list():
            setattr(self, name, self._bind(name))

    def _set(self, name, value):
        if self._values[name] != value:
            self._values[name] = value
            self._updated[name] = True

    def _sync(self):
        target = int(max(0.0, self._clock() - self._origin + self._offset) * 32)
        while self._ticks < target:
            self._ticks += 1
            self._tick()

    def _tick(self):
        # 32 conversions/s, round-robin: approximately 8 samples/s per channel.
        v = self._values
        mode = int(v['pidm'])
        for i in range(2):
            self._temperature[i] += (
                4.0 * v[f'pwm{i}'] / 1023 - (self._temperature[i] - 22) / 90
            ) / 32
        channel = (self._ticks - 1) % 4
        elapsed = self._ticks / 32 - self._capture_start
        if channel < 2:
            # Illustrative optical pulse in mV, NOT a model of the real detector.
            value = 100 + (1200 if channel == 0 else 750) * math.exp(-elapsed / 2)
            value += self._random.gauss(0, 0.5)
        else:
            i = channel - 2
            t = self._temperature[i]
            resistance = 100 * (1 + 3.9083e-3 * t - 5.775e-7 * t * t)
            value = 0 if self._faults[i] else 3300 * resistance / (1003 + resistance)
        if channel >= 2 or self._counts[channel] < 64:
            self._buffers[channel] = self._buffers[channel][1:] + [value]
            self._counts[channel] += 1
        if min(self._counts[:2]) >= 64:
            self._set('crdy', 1.0)
            self._mode = 0
        if self._ticks % 32 == 0:
            for i in range(2):
                voltage = sum(self._buffers[i + 2]) / 8
                temperature = 3333.3
                if 0 < voltage < 3300:
                    resistance = 1003 * voltage / (3300 - voltage)
                    disc = 3.9083e-3 ** 2 - 4 * -5.775e-7 * (1 - resistance / 100)
                    if disc >= 0:
                        t = (-3.9083e-3 + math.sqrt(disc)) / (2 * -5.775e-7)
                        if 3 <= t <= 333:
                            temperature = t
                self._set(f't{i}', temperature)
        for i in range(2):
            if mode == 0:
                self._set(f'pwm{i}', 0.0)
                self._integral[i] = 0.0
            elif mode == 2:
                self._set(f'pwm{i}', 1023.0 if v[f't{i}'] < v[f'sp{i}'] else 0.0)
            elif self._ticks % 32 == 0:
                kp = v['kp']
                ki, kd = kp / v['tau'], kp * v['tau'] * 2 / 3
                current = v[f't{i}']
                error = v[f'sp{i}'] - current
                self._integral[i] = min(1023, max(0, self._integral[i] + ki * error))
                output = kp * error + self._integral[i] - kd * (current - self._previous_input[i])
                self._set(f'pwm{i}', min(1023, max(0, output)))
                self._previous_input[i] = current
        # These flags are consumed by the firmware's loop functions.
        for name in ('sp0', 'sp1', 'kp', 'tau', 'pidm', 'pwm0', 'pwm1'):
            self._updated[name] = False

    def sim_advance(self, seconds):
        """Advance synthetic time without waiting (max one hour per call)."""
        seconds = float(seconds)
        if not math.isfinite(seconds) or not 0 <= seconds <= 3600:
            raise ValueError('seconds must be finite and between 0 and 3600')
        self._offset += seconds
        self._sync()
        return self.sim_status()

    def sim_sensor_error(self, channel, enabled=True):
        """Simulate an open/invalid Pt100 input (channel 0 or 1)."""
        if channel not in (0, 1):
            raise ValueError('temperature channel must be 0 or 1')
        self._sync()
        self._faults[channel] = bool(enabled)
        return self._faults[channel]

    def sim_status(self):
        self._sync()
        return {'simulated': True, 'seconds': self._ticks / 32,
                'samples': self._counts[:2], 'ready': self._values['crdy'],
                'sensor_errors': list(self._faults)}

    def _bind(self, name):
        def call(*args):
            return self.command(name, *args)
        return call

    def commands_list(self):
        return list(reversed(REGISTRATION))

    def _parsed(self, lines):
        result = [Pykiba.parse_line(self, line.encode()) for line in lines if line.strip()]
        return result[0] if len(result) == 1 else result or None

    def command(self, name, *args, timeout=2.5):
        self._sync()
        # Match the existing driver's float truncation and integer/string encoding.
        wire = Pykiba.prepare_line_to_send(self, name, *args).decode().strip().split()
        name, words = wire[0], wire[1:]
        if name in VARIABLES:
            _, low, high = VARIABLES[name]
            if words and high - low > 0.3:
                value = float(words[0]) * (10 ** int(words[1]) if len(words) > 1 else 1)
                self._set(name, min(high, max(low, value)))
            return self._parsed([f'{self._values[name]:.4f}'])
        if name == 'hello':
            return 'Protecta'
        if name == 'hlp':
            return self.commands_list()
        if name == 'mode':
            if words:
                self._mode = min(3, int(words[0]) % 256)
            return self._mode
        if name == 'echo':
            if words:
                self._echo = int(bool(int(words[0])))
            return self._echo
        if name == 'adcclr':
            self._counts[0] = self._counts[1] = 0
            self._capture_start = self._ticks / 32
            self._set('crdy', 0.0)
            self._mode = 1
            return 1
        if name.startswith('buf') and name in REGISTRATION:
            return self._parsed([', '.join(f'{v:.4f}' for v in self._buffers[int(name[-1])])])
        if name.startswith('sum') and name in REGISTRATION:
            return self._parsed([f'{sum(self._buffers[int(name[-1])]):.4f}'])
        if name == 'pid':
            kp, tau = self._values['kp'], self._values['tau']
            return self._parsed([f'{kp:.2f}, {kp / tau:.2f}, {kp * tau * 2 / 3:.2f}'])
        if name == 'varlst':
            return self._parsed([
                f'{key}, {self._values[key]:.2f}, {spec[1]:.2f}, {spec[2]:.2f}, {int(self._updated[key])}'
                for key, spec in reversed(list(VARIABLES.items()))
            ])
        if name == 'peep':
            return 1
        if name == 'adctst':
            return self._parsed(['ADC OK'])
        return self._parsed(['CMD:Command not recognized.'])


def main(argv=None):
    """Start an independent synthetic device, served directly through ZeroRPC."""
    import argparse
    import signal
    import gevent
    import zerorpc

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', default='tcp://127.0.0.1:2020')
    parser.add_argument('--seed', type=int, default=1, help='repeatable synthetic noise seed')
    args = parser.parse_args(argv)
    device = SimulatedDevice(seed=args.seed)
    server = zerorpc.Server(device)
    # No serial device, DeviceService, setup.ini, or real-device startup commands.
    try:
        server.bind(args.bind)
        watchers = [gevent.signal_handler(sig, server.stop)
                    for sig in (signal.SIGINT, signal.SIGTERM)]
        print(f'SIMULATOR: synthetic data only; serving at {args.bind}', flush=True)
        try:
            server.run()
        finally:
            for watcher in watchers:
                watcher.cancel()
    finally:
        server.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
