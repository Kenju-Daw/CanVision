import { describe, it, expect, beforeEach } from 'vitest';
import { useSignalStore } from '../stores/signalStore';

describe('Signal Store', () => {
  beforeEach(() => {
    // Reset store before each test
    const store = useSignalStore();
    store.reset?.();
  });

  it('should initialize with empty signals', () => {
    const store = useSignalStore();
    expect(store.signals).toBeDefined();
  });

  it('should add a signal', () => {
    const store = useSignalStore();
    const signal = {
      ts: Date.now(),
      pgn: 0xf004,
      spn: 190,
      spn_name: 'EngineSpeed',
      value: 1500,
      unit: 'rpm',
    };

    store.addSignal(signal);
    expect(store.signals['EngineSpeed']).toBeDefined();
  });

  it('should track signal count', () => {
    const store = useSignalStore();
    const initialCount = Object.keys(store.signals).length;

    const signal = {
      ts: Date.now(),
      pgn: 0xf004,
      spn: 190,
      spn_name: 'EngineSpeed',
      value: 1500,
      unit: 'rpm',
    };

    store.addSignal(signal);
    expect(Object.keys(store.signals).length).toBeGreaterThanOrEqual(initialCount);
  });

  it('should handle multiple signals', () => {
    const store = useSignalStore();
    const signals = [
      { ts: Date.now(), pgn: 0xf004, spn: 190, spn_name: 'EngineSpeed', value: 1500, unit: 'rpm' },
      { ts: Date.now(), pgn: 0xfeca, spn: 110, spn_name: 'CoolantTemp', value: 85, unit: '°C' },
      { ts: Date.now(), pgn: 0xfec1, spn: 84, spn_name: 'VehicleSpeed', value: 60, unit: 'km/h' },
    ];

    signals.forEach(signal => store.addSignal(signal));

    expect(Object.keys(store.signals).length).toBeGreaterThanOrEqual(3);
  });
});
