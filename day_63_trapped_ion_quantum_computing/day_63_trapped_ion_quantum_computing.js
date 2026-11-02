'use strict';

/*
 * Trapped-ion quantum computing: event-driven laser-control model.
 *
 * The implementation focuses on a control stack rather than reproducing
 * the Python state-vector simulator. It represents ions, trap modes,
 * calibrated laser channels, pulse events, gate policies, and measurement.
 *
 * Node.js standard library only.
 */

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const crypto = require('node:crypto');

class ControlError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ControlError';
  }
}

const GateType = Object.freeze({
  SINGLE: 'single-qubit',
  ENTANGLING: 'entangling',
  MEASUREMENT: 'measurement'
});

class Ion {
  constructor(id, massAmu, axialFrequencyMHz) {
    if (!Number.isInteger(id) || id < 0) {
      throw new ControlError('Ion ID must be a non-negative integer.');
    }
    if (!(massAmu > 0) || !(axialFrequencyMHz > 0)) {
      throw new ControlError('Ion mass and frequency must be positive.');
    }

    this.id = id;
    this.massAmu = massAmu;
    this.axialFrequencyMHz = axialFrequencyMHz;
  }
}

class Trap {
  constructor({ radialFrequencyMHz, axialFrequencyMHz, wavelengthNm }) {
    if (radialFrequencyMHz <= axialFrequencyMHz) {
      throw new ControlError(
        'Radial frequency must exceed axial frequency for this model.'
      );
    }

    if (wavelengthNm < 200 || wavelengthNm > 2000) {
      throw new ControlError('Laser wavelength is outside the supported range.');
    }

    this.radialFrequencyMHz = radialFrequencyMHz;
    this.axialFrequencyMHz = axialFrequencyMHz;
    this.wavelengthNm = wavelengthNm;
  }

  modeSpacingMHz() {
    return this.radialFrequencyMHz - this.axialFrequencyMHz;
  }
}

class LaserChannel {
  constructor(name, maxPowerMw) {
    if (!name || !(maxPowerMw > 0)) {
      throw new ControlError('Laser channel requires a name and positive power.');
    }

    this.name = name;
    this.maxPowerMw = maxPowerMw;
    this.calibration = {
      rabiScale: 1,
      frequencyOffsetMHz: 0
    };
  }

  calibrate({ rabiScale, frequencyOffsetMHz }) {
    if (!(rabiScale > 0) || !Number.isFinite(frequencyOffsetMHz)) {
      throw new ControlError('Invalid laser calibration.');
    }

    this.calibration = { rabiScale, frequencyOffsetMHz };
  }

  effectiveFrequency(requestedMHz) {
    return requestedMHz * this.calibration.rabiScale;
  }
}

class Pulse {
  constructor({
    id,
    ion,
    targetIon = null,
    channel,
    startNs,
    durationNs,
    rabiFrequencyMHz,
    detuningMHz,
    phaseRad,
    gateType
  }) {
    if (!id || !Number.isFinite(startNs) || startNs < 0) {
      throw new ControlError('Pulse ID and non-negative start time are required.');
    }

    if (!(durationNs > 0) || !(rabiFrequencyMHz > 0)) {
      throw new ControlError('Pulse duration and Rabi frequency must be positive.');
    }

    if (!Object.values(GateType).includes(gateType)) {
      throw new ControlError('Unknown gate type.');
    }

    this.id = id;
    this.ion = ion;
    this.targetIon = targetIon;
    this.channel = channel;
    this.startNs = startNs;
    this.durationNs = durationNs;
    this.rabiFrequencyMHz = rabiFrequencyMHz;
    this.detuningMHz = detuningMHz;
    this.phaseRad = phaseRad;
    this.gateType = gateType;
  }

  get endNs() {
    return this.startNs + this.durationNs;
  }
}

class PulseScheduler extends EventEmitter {
  constructor() {
    super();
    this.pulses = [];
  }

  overlaps(a, b) {
    return a.startNs < b.endNs && b.startNs < a.endNs;
  }

  touchesSameIon(a, b) {
    const aIons = new Set([a.ion, a.targetIon].filter(Number.isInteger));
    const bIons = new Set([b.ion, b.targetIon].filter(Number.isInteger));

    for (const ion of aIons) {
      if (bIons.has(ion)) return true;
    }
    return false;
  }

  schedule(pulse) {
    for (const existing of this.pulses) {
      if (this.overlaps(existing, pulse) && this.touchesSameIon(existing, pulse)) {
        throw new ControlError(
          `Pulse conflict: ${existing.id} overlaps ${pulse.id}.`
        );
      }
    }

    this.pulses.push(pulse);
    this.pulses.sort((a, b) => a.startNs - b.startNs);
    this.emit('scheduled', pulse);
  }

  timeline() {
    return this.pulses.map((pulse) => ({
      id: pulse.id,
      startNs: pulse.startNs,
      endNs: pulse.endNs,
      ion: pulse.ion,
      targetIon: pulse.targetIon,
      gateType: pulse.gateType
    }));
  }
}

class ControlPolicy {
  constructor({ maxDetuningMHz, maxPulseNs, requireCalibration }) {
    this.maxDetuningMHz = maxDetuningMHz;
    this.maxPulseNs = maxPulseNs;
    this.requireCalibration = requireCalibration;
  }

  validate(pulse, trap, channel) {
    if (Math.abs(
      pulse.detuningMHz + channel.calibration.frequencyOffsetMHz
    ) > this.maxDetuningMHz) {
      throw new ControlError(
        `Pulse ${pulse.id} exceeds effective detuning policy.`
      );
    }

    if (pulse.durationNs > this.maxPulseNs) {
      throw new ControlError(`Pulse ${pulse.id} exceeds duration policy.`);
    }

    if (this.requireCalibration && !channel.calibration) {
      throw new ControlError('Calibrated laser channel is required.');
    }

    const estimatedPower =
      pulse.rabiFrequencyMHz * channel.calibration.rabiScale * 0.02;

    if (estimatedPower > channel.maxPowerMw) {
      throw new ControlError(`Pulse ${pulse.id} exceeds optical power.`);
    }

    if (pulse.gateType === GateType.ENTANGLING) {
      if (!Number.isInteger(pulse.targetIon) || pulse.targetIon === pulse.ion) {
        throw new ControlError(
          'An entangling pulse requires a distinct target ion.'
        );
      }

      if (trap.modeSpacingMHz() <= 0) {
        throw new ControlError('No valid motional-mode separation exists.');
      }
    }
  }
}

class IonTrapController extends EventEmitter {
  constructor(trap, ions, channels, policy) {
    super();

    this.trap = trap;
    this.ions = new Map(ions.map(ion => [ion.id, ion]));
    this.channels = new Map(channels.map(channel => [channel.name, channel]));
    this.policy = policy;
    this.scheduler = new PulseScheduler();

    this.scheduler.on('scheduled', pulse => {
      this.emit('pulseScheduled', pulse);
    });
  }

  validatePulse(pulse) {
    if (!this.ions.has(pulse.ion)) {
      throw new ControlError(`Unknown ion ${pulse.ion}.`);
    }

    if (pulse.targetIon !== null && !this.ions.has(pulse.targetIon)) {
      throw new ControlError(`Unknown target ion ${pulse.targetIon}.`);
    }

    const channel = this.channels.get(pulse.channel);
    if (!channel) {
      throw new ControlError(`Unknown laser channel ${pulse.channel}.`);
    }

    this.policy.validate(pulse, this.trap, channel);
    return channel;
  }

  submitPulse(pulse) {
    const channel = this.validatePulse(pulse);
    this.scheduler.schedule(pulse);

    const effectiveRabiMHz =
      channel.effectiveFrequency(pulse.rabiFrequencyMHz);

    this.emit('controlApplied', {
      pulseId: pulse.id,
      effectiveRabiMHz,
      detuningMHz:
        pulse.detuningMHz + channel.calibration.frequencyOffsetMHz
    });
  }

  describe() {
    return {
      ions: [...this.ions.values()].map(ion => ({
        id: ion.id,
        massAmu: ion.massAmu,
        axialFrequencyMHz: ion.axialFrequencyMHz
      })),
      trap: {
        radialFrequencyMHz: this.trap.radialFrequencyMHz,
        axialFrequencyMHz: this.trap.axialFrequencyMHz,
        modeSpacingMHz: this.trap.modeSpacingMHz()
      },
      timeline: this.scheduler.timeline()
    };
  }
}

class MeasurementService {
  constructor(seed = null) {
    this.seed = seed || crypto.randomBytes(16).toString('hex');
  }

  sample(probabilities, shots) {
    if (!Number.isInteger(shots) || shots <= 0 || shots > 1_000_000) {
      throw new ControlError('Shots must be between 1 and 1,000,000.');
    }

    const entries = Object.entries(probabilities);

    if (entries.length === 0) {
      throw new ControlError('Measurement distribution cannot be empty.');
    }

    const total = entries.reduce((sum, [, p]) => sum + p, 0);

    if (Math.abs(total - 1) > 1e-9) {
      throw new ControlError('Measurement probabilities must sum to one.');
    }

    const counts = Object.fromEntries(entries.map(([state]) => [state, 0]));

    // A cryptographic random source is used here so the measurement layer
    // does not depend on predictable application-level randomness.
    for (let shot = 0; shot < shots; shot++) {
      const randomBytes = crypto.randomBytes(6);
      const random =
        Number(randomBytes.readUIntBE(0, 6)) / 0x1000000000000;

      let cumulative = 0;

      for (const [state, probability] of entries) {
        cumulative += probability;

        if (random <= cumulative) {
          counts[state]++;
          break;
        }
      }
    }

    return counts;
  }
}

function buildBellLikeControlSequence(controller) {
  const sequence = [
    new Pulse({
      id: 'single-qubit-superposition',
      ion: 0,
      channel: '397nm-control',
      startNs: 0,
      durationNs: 250,
      rabiFrequencyMHz: 1,
      detuningMHz: 0,
      phaseRad: 0,
      gateType: GateType.SINGLE
    }),
    new Pulse({
      id: 'mølmer-sørensen-entangler',
      ion: 0,
      targetIon: 1,
      channel: '397nm-control',
      startNs: 1000,
      durationNs: 500,
      rabiFrequencyMHz: 1,
      detuningMHz: 0,
      phaseRad: Math.PI / 2,
      gateType: GateType.ENTANGLING
    })
  ];

  sequence.forEach(pulse => controller.submitPulse(pulse));
  return sequence;
}

function demonstrateFailureHandling(controller) {
  const unsafe = new Pulse({
    id: 'detuning-failure',
    ion: 0,
    channel: '397nm-control',
    startNs: 3000,
    durationNs: 100,
    rabiFrequencyMHz: 1,
    detuningMHz: 20,
    phaseRad: 0,
    gateType: GateType.SINGLE
  });

  try {
    controller.submitPulse(unsafe);
    assert.fail('Unsafe detuning should have been rejected.');
  } catch (error) {
    assert(error instanceof ControlError);
    console.log(`Rejected unsafe pulse: ${error.message}`);
  }
}

function main() {
  const trap = new Trap({
    radialFrequencyMHz: 4.5,
    axialFrequencyMHz: 1.0,
    wavelengthNm: 397
  });

  const ions = [
    new Ion(0, 40, 1.0),
    new Ion(1, 40, 1.0),
    new Ion(2, 40, 1.0)
  ];

  const laser = new LaserChannel('397nm-control', 20);
  laser.calibrate({
    rabiScale: 0.98,
    frequencyOffsetMHz: 0.01
  });

  const policy = new ControlPolicy({
    maxDetuningMHz: 5,
    maxPulseNs: 2000,
    requireCalibration: true
  });

  const controller = new IonTrapController(
    trap,
    ions,
    [laser],
    policy
  );

  controller.on('pulseScheduled', pulse => {
    console.log(
      `scheduled ${pulse.id}: ${pulse.startNs}-${pulse.endNs} ns`
    );
  });

  controller.on('controlApplied', event => {
    console.log(
      `applied ${event.pulseId}: ` +
      `effective Rabi=${event.effectiveRabiMHz.toFixed(3)} MHz, ` +
      `detuning=${event.detuningMHz.toFixed(3)} MHz`
    );
  });

  buildBellLikeControlSequence(controller);
  demonstrateFailureHandling(controller);

  const measurement = new MeasurementService();
  const counts = measurement.sample(
    {
      '00': 0.5,
      '11': 0.5
    },
    500
  );

  console.log('\nControl-system state:');
  console.log(JSON.stringify(controller.describe(), null, 2));

  console.log('\nSimulated measurement counts:');
  console.log(counts);

  assert.equal(controller.scheduler.pulses.length, 2);
  assert.equal(Object.values(counts).reduce((a, b) => a + b, 0), 500);
  assert.ok(controller.trap.modeSpacingMHz() > 0);

  console.log('\nEvent-driven control checks passed.');
}

main();
