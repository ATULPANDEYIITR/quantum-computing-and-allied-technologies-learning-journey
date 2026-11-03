"use strict";

/*
 * Neutral-atom laboratory controller simulation.
 *
 * This implementation emphasizes asynchronous experiment orchestration,
 * safety-policy evaluation, state transitions, and an event audit trail.
 * It does not send commands to physical laser, vacuum, or imaging hardware.
 *
 * Runtime: Node.js 18 or later. No npm dependencies.
 */

const { EventEmitter } = require("node:events");

class LabError extends Error {
  constructor(message, code = "LAB_ERROR") {
    super(message);
    this.name = "LabError";
    this.code = code;
  }
}

function requireFinitePositive(value, label) {
  if (!Number.isFinite(value) || value <= 0) {
    throw new LabError(`${label} must be a positive finite number.`, "INVALID_CONFIG");
  }
}

function distanceUm(a, b) {
  return Math.hypot(a.xUm - b.xUm, a.yUm - b.yUm);
}

class TrapCalibration {
  constructor({
    wavelengthM,
    waistM,
    trapDepthJ,
    atomicMassKg,
    beamPowerW,
    validUntil,
  }) {
    requireFinitePositive(wavelengthM, "Wavelength");
    requireFinitePositive(waistM, "Beam waist");
    requireFinitePositive(trapDepthJ, "Trap depth");
    requireFinitePositive(atomicMassKg, "Atomic mass");
    requireFinitePositive(beamPowerW, "Beam power");

    const expiry = new Date(validUntil);
    if (!Number.isFinite(expiry.getTime())) {
      throw new LabError("Calibration expiry must be a valid date.", "INVALID_CONFIG");
    }

    this.wavelengthM = wavelengthM;
    this.waistM = waistM;
    this.trapDepthJ = trapDepthJ;
    this.atomicMassKg = atomicMassKg;
    this.beamPowerW = beamPowerW;
    this.validUntil = expiry;
    Object.freeze(this);
  }

  get rayleighRangeM() {
    return Math.PI * this.waistM ** 2 / this.wavelengthM;
  }

  get radialFrequencyHz() {
    const omega = Math.sqrt(
      4 * this.trapDepthJ / (this.atomicMassKg * this.waistM ** 2)
    );
    return omega / (2 * Math.PI);
  }

  get axialFrequencyHz() {
    const omega = Math.sqrt(
      2 * this.trapDepthJ /
      (this.atomicMassKg * this.rayleighRangeM ** 2)
    );
    return omega / (2 * Math.PI);
  }

  potentialJ(radialDistanceM, axialDistanceM = 0) {
    if (
      !Number.isFinite(radialDistanceM) ||
      radialDistanceM < 0 ||
      !Number.isFinite(axialDistanceM)
    ) {
      throw new LabError("Trap coordinates must be finite and valid.", "INVALID_INPUT");
    }

    const zRatio = axialDistanceM / this.rayleighRangeM;
    const beamRadius = this.waistM * Math.sqrt(1 + zRatio ** 2);
    const localDepth =
      this.trapDepthJ /
      (1 + zRatio ** 2) *
      Math.exp(-2 * radialDistanceM ** 2 / beamRadius ** 2);

    return -localDepth;
  }
}

class TweezerArray {
  constructor({ rows, columns, spacingUm }) {
    if (!Number.isInteger(rows) || rows <= 0) {
      throw new LabError("Rows must be a positive integer.", "INVALID_ARRAY");
    }
    if (!Number.isInteger(columns) || columns <= 0) {
      throw new LabError("Columns must be a positive integer.", "INVALID_ARRAY");
    }
    requireFinitePositive(spacingUm, "Site spacing");

    this.rows = rows;
    this.columns = columns;
    this.spacingUm = spacingUm;

    this.sites = Object.freeze(
      Array.from({ length: rows * columns }, (_, index) => {
        const row = Math.floor(index / columns);
        const column = index % columns;
        return Object.freeze({
          id: `r${row}c${column}`,
          row,
          column,
          xUm: column * spacingUm,
          yUm: row * spacingUm,
        });
      })
    );

    this.siteById = new Map(this.sites.map((site) => [site.id, site]));
    Object.freeze(this.sites);
  }

  sampleOccupancy(probability, seed = 2026) {
    if (!Number.isFinite(probability) || probability < 0 || probability > 1) {
      throw new LabError(
        "Occupancy probability must be between 0 and 1.",
        "INVALID_INPUT"
      );
    }

    // Xorshift32 gives repeatable simulation results without extra packages.
    let state = seed >>> 0;
    if (state === 0) state = 0x6d2b79f5;

    const nextRandom = () => {
      state ^= state << 13;
      state ^= state >>> 17;
      state ^= state << 5;
      return (state >>> 0) / 0x100000000;
    };

    return this.sites
      .filter(() => nextRandom() < probability)
      .map((site, index) => ({
        atomId: `atom-${index + 1}`,
        sourceSiteId: site.id,
        xUm: site.xUm,
        yUm: site.yUm,
      }));
  }

  atomsFromObservedSites(siteIds) {
    if (!Array.isArray(siteIds)) {
      throw new LabError("Observed site identifiers must be an array.", "INVALID_INPUT");
    }

    const seen = new Set();
    return siteIds.map((siteId, index) => {
      if (seen.has(siteId)) {
        throw new LabError(`Duplicate occupied site: ${siteId}`, "DUPLICATE_SITE");
      }
      seen.add(siteId);

      const site = this.siteById.get(siteId);
      if (!site) {
        throw new LabError(`Unknown site: ${siteId}`, "UNKNOWN_SITE");
      }

      return {
        atomId: `atom-${index + 1}`,
        sourceSiteId: site.id,
        xUm: site.xUm,
        yUm: site.yUm,
      };
    });
  }
}

function makeTargetGrid(rows, columns, spacingUm, offsetUm) {
  if (!Number.isInteger(rows) || rows <= 0 ||
      !Number.isInteger(columns) || columns <= 0) {
    throw new LabError("Target dimensions must be positive integers.", "INVALID_TARGET");
  }
  requireFinitePositive(spacingUm, "Target spacing");
  if (!Number.isFinite(offsetUm)) {
    throw new LabError("Target offset must be finite.", "INVALID_TARGET");
  }

  return Array.from({ length: rows * columns }, (_, index) => {
    const row = Math.floor(index / columns);
    const column = index % columns;
    return Object.freeze({
      id: `target-r${row}c${column}`,
      xUm: offsetUm + column * spacingUm,
      yUm: offsetUm + row * spacingUm,
    });
  });
}

function greedyGlobalAssignment(atoms, targets) {
  /*
   * Generate all possible atom-target edges, then select the shortest edge
   * whose atom and target have not already been assigned.
   *
   * This is a deterministic heuristic, not a globally optimal assignment.
   * It uses O(S*T) memory and O(S*T log(S*T)) sorting time.
   */
  const candidates = [];

  for (const atom of atoms) {
    for (const target of targets) {
      candidates.push({
        atom,
        target,
        distanceUm: distanceUm(atom, target),
      });
    }
  }

  candidates.sort((a, b) =>
    a.distanceUm - b.distanceUm ||
    a.atom.atomId.localeCompare(b.atom.atomId) ||
    a.target.id.localeCompare(b.target.id)
  );

  const usedAtoms = new Set();
  const usedTargets = new Set();
  const moves = [];

  for (const candidate of candidates) {
    const atomId = candidate.atom.atomId;
    const targetId = candidate.target.id;

    if (usedAtoms.has(atomId) || usedTargets.has(targetId)) {
      continue;
    }

    usedAtoms.add(atomId);
    usedTargets.add(targetId);

    moves.push({
      atomId,
      sourceSiteId: candidate.atom.sourceSiteId,
      targetId,
      distanceUm: candidate.distanceUm,
    });

    if (moves.length === Math.min(atoms.length, targets.length)) {
      break;
    }
  }

  return moves;
}

class ExperimentController extends EventEmitter {
  constructor(policy) {
    super();

    this.policy = Object.freeze({
      maximumVacuumPressurePa: policy.maximumVacuumPressurePa,
      maximumSites: policy.maximumSites,
      maximumBeamPowerW: policy.maximumBeamPowerW,
      minimumSiteSpacingUm: policy.minimumSiteSpacingUm,
    });

    requireFinitePositive(
      this.policy.maximumVacuumPressurePa,
      "Maximum vacuum pressure"
    );
    requireFinitePositive(this.policy.maximumSites, "Maximum site count");
    requireFinitePositive(this.policy.maximumBeamPowerW, "Maximum beam power");
    requireFinitePositive(this.policy.minimumSiteSpacingUm, "Minimum site spacing");

    this.state = "IDLE";
    this.busy = false;
    this.eventLog = [];
    this.allowedTransitions = new Map([
      ["IDLE", new Set(["PREFLIGHT"])],
      ["PREFLIGHT", new Set(["VALIDATED", "ABORTED"])],
      ["VALIDATED", new Set(["LOADED", "ABORTED"])],
      ["LOADED", new Set(["REARRANGED", "ABORTED"])],
      ["REARRANGED", new Set(["READY", "ABORTED"])],
      ["READY", new Set()],
      ["ABORTED", new Set()],
    ]);
  }

  record(type, details = {}) {
    const event = Object.freeze({
      timestamp: new Date().toISOString(),
      type,
      state: this.state,
      details,
    });

    this.eventLog.push(event);
    this.emit("lab-event", event);
  }

  transition(nextState, details = {}) {
    const allowed = this.allowedTransitions.get(this.state);
    if (!allowed || !allowed.has(nextState)) {
      throw new LabError(
        `Illegal state transition: ${this.state} -> ${nextState}`,
        "INVALID_STATE_TRANSITION"
      );
    }

    const previousState = this.state;
    this.state = nextState;
    this.record("STATE_CHANGED", { previousState, nextState, ...details });
  }

  evaluateSafety({ array, calibration, telemetry, targets }) {
    const findings = [];
    const now = Date.now();

    if (!(calibration instanceof TrapCalibration)) {
      findings.push("A valid trap calibration is required.");
    } else {
      if (calibration.validUntil.getTime() <= now) {
        findings.push("Trap calibration has expired.");
      }
      if (calibration.beamPowerW > this.policy.maximumBeamPowerW) {
        findings.push("Beam power exceeds the facility limit.");
      }
    }

    if (array.sites.length > this.policy.maximumSites) {
      findings.push("Array site count exceeds the facility limit.");
    }

    if (array.spacingUm < this.policy.minimumSiteSpacingUm) {
      findings.push("Tweezer spacing is below the configured minimum.");
    }

    if (!telemetry || !Number.isFinite(telemetry.vacuumPressurePa) ||
        telemetry.vacuumPressurePa < 0) {
      findings.push("Valid vacuum telemetry is required.");
    } else if (
      telemetry.vacuumPressurePa > this.policy.maximumVacuumPressurePa
    ) {
      findings.push("Vacuum pressure exceeds the permitted limit.");
    }

    if (!telemetry || telemetry.interlockHealthy !== true) {
      findings.push("Laser interlock is not healthy.");
    }
    if (!telemetry || telemetry.emergencyStop !== false) {
      findings.push("Emergency-stop condition prevents operation.");
    }

    if (!Array.isArray(targets) || targets.length === 0) {
      findings.push("At least one target site is required.");
    } else if (targets.length > array.sites.length) {
      findings.push("Target count exceeds the number of available trap sites.");
    }

    if (findings.length > 0) {
      this.record("SAFETY_REJECTION", { findings });
    }

    return findings;
  }

  async execute({
    array,
    calibration,
    telemetry,
    targets,
    occupiedSiteIds,
    loadingProbability = 0.55,
    seed = 2026,
  }) {
    if (this.busy) {
      throw new LabError("Another experiment is already running.", "BUSY");
    }
    if (this.state !== "IDLE") {
      throw new LabError("This controller has already processed a run.", "USED");
    }

    this.busy = true;

    try {
      if (!(array instanceof TweezerArray)) {
        throw new LabError("A configured tweezer array is required.", "INVALID_ARRAY");
      }

      this.transition("PREFLIGHT", {
        siteCount: array.sites.length,
        targetCount: Array.isArray(targets) ? targets.length : null,
      });

      const findings = this.evaluateSafety({
        array,
        calibration,
        telemetry,
        targets,
      });

      if (findings.length > 0) {
        throw new LabError(findings.join(" "), "SAFETY_REJECTION");
      }

      this.transition("VALIDATED", {
        calibrationExpiry: calibration.validUntil.toISOString(),
      });

      // Represents an asynchronous imaging or control-system boundary.
      await Promise.resolve();

      let atoms;
      if (occupiedSiteIds !== undefined) {
        atoms = array.atomsFromObservedSites(occupiedSiteIds);
      } else {
        atoms = array.sampleOccupancy(loadingProbability, seed);
      }

      this.record("LOADING_OBSERVED", {
        occupiedSites: atoms.map((atom) => atom.sourceSiteId),
        atomCount: atoms.length,
      });

      if (atoms.length < targets.length) {
        throw new LabError(
          `Insufficient atoms: ${atoms.length} loaded for ${targets.length} targets.`,
          "INSUFFICIENT_ATOMS"
        );
      }

      this.transition("LOADED", { atomCount: atoms.length });

      const moves = greedyGlobalAssignment(atoms, targets);
      if (moves.length !== targets.length) {
        throw new LabError(
          "The rearrangement plan does not fill every target.",
          "INCOMPLETE_PLAN"
        );
      }

      this.record("REARRANGEMENT_PLANNED", {
        moveCount: moves.length,
        totalDistanceUm: moves.reduce((sum, move) => sum + move.distanceUm, 0),
      });

      await Promise.resolve();
      this.transition("REARRANGED", { moveCount: moves.length });

      const result = {
        finalState: "READY",
        siteCount: array.sites.length,
        loadedAtomCount: atoms.length,
        targetCount: targets.length,
        unusedAtomCount: atoms.length - moves.length,
        moves,
        trapCharacteristics: {
          rayleighRangeM: calibration.rayleighRangeM,
          radialFrequencyHz: calibration.radialFrequencyHz,
          axialFrequencyHz: calibration.axialFrequencyHz,
          trapPotentialAtCenterJ: calibration.potentialJ(0),
        },
      };

      this.transition("READY", { targetCount: targets.length });
      return Object.freeze({
        ...result,
        eventLog: [...this.eventLog],
      });
    } catch (error) {
      if (
        this.state !== "ABORTED" &&
        this.state !== "READY" &&
        this.allowedTransitions.get(this.state)?.has("ABORTED")
      ) {
        this.transition("ABORTED", {
          errorCode: error.code || "UNEXPECTED_ERROR",
          message: error.message,
        });
      }
      throw error;
    } finally {
      this.busy = false;
    }
  }
}

async function main() {
  const calibration = new TrapCalibration({
    wavelengthM: 850e-9,
    waistM: 0.8e-6,
    trapDepthJ: 1.380649e-26,
    atomicMassKg: 1.4431606e-25,
    beamPowerW: 0.003,
    validUntil: "2027-11-03T00:00:00.000Z",
  });

  const array = new TweezerArray({
    rows: 4,
    columns: 4,
    spacingUm: 5.0,
  });

  const targets = makeTargetGrid(3, 3, 5.0, 2.5);
  const controller = new ExperimentController({
    maximumVacuumPressurePa: 1e-7,
    maximumSites: 256,
    maximumBeamPowerW: 0.01,
    minimumSiteSpacingUm: 3.5,
  });

  controller.on("lab-event", (event) => {
    process.stdout.write(
      `[${event.type}] ${JSON.stringify(event.details)}\n`
    );
  });

  const occupiedSiteIds = [
    "r0c1",
    "r0c3",
    "r1c0",
    "r1c2",
    "r2c1",
    "r2c3",
    "r3c0",
    "r3c2",
    "r3c3",
    "r1c3",
  ];

  try {
    const result = await controller.execute({
      array,
      calibration,
      telemetry: {
        vacuumPressurePa: 2e-8,
        interlockHealthy: true,
        emergencyStop: false,
      },
      targets,
      occupiedSiteIds,
    });

    process.stdout.write("\nExperiment result:\n");
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } catch (error) {
    process.stderr.write(
      `Experiment rejected: ${error.code || error.name}: ${error.message}\n`
    );
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`Fatal error: ${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  ExperimentController,
  LabError,
  TrapCalibration,
  TweezerArray,
  greedyGlobalAssignment,
  makeTargetGrid,
};
