'use strict';

/*
 * QUANTUM NEURAL NETWORKS: FUNDAMENTALS
 *
 * Event-driven variational quantum learning engine.
 *
 * Features:
 * - State-vector quantum simulation
 * - Quantum gate operations
 * - Feature encoding
 * - Parameterized quantum circuits
 * - Parameter-shift gradient estimation
 * - Asynchronous training
 * - Event-driven experiment monitoring
 * - Shot-based measurement
 * - Model evaluation
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only
 */

const { EventEmitter } = require('node:events');
const { writeFile } = require('node:fs/promises');

const PI = Math.PI;
const EPSILON = 1e-9;

class QuantumError extends Error {}

class ValidationError extends QuantumError {}

function validateFinite(value, name) {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
        throw new ValidationError(`${name} must be finite.`);
    }
}

class Complex {
    constructor(re = 0, im = 0) {
        this.re = re;
        this.im = im;
    }

    add(other) {
        return new Complex(
            this.re + other.re,
            this.im + other.im
        );
    }

    multiply(other) {
        return new Complex(
            this.re * other.re - this.im * other.im,
            this.re * other.im + this.im * other.re
        );
    }

    scale(value) {
        return new Complex(this.re * value, this.im * value);
    }

    magnitudeSquared() {
        return this.re * this.re + this.im * this.im;
    }
}

class QuantumRegister {
    constructor(qubits) {
        if (!Number.isInteger(qubits) || qubits < 1 || qubits > 16) {
            throw new ValidationError('Qubit count must be between 1 and 16.');
        }

        this.qubits = qubits;
        this.dimension = 2 ** qubits;
        this.state = Array.from(
            { length: this.dimension },
            () => new Complex()
        );

        this.state[0] = new Complex(1, 0);
    }

    applyGate(qubit, matrix) {
        if (!Number.isInteger(qubit) ||
            qubit < 0 ||
            qubit >= this.qubits) {
            throw new ValidationError('Invalid qubit index.');
        }

        const mask = 1 << qubit;

        for (let i = 0; i < this.dimension; i++) {
            if (i & mask) continue;

            const j = i | mask;

            const alpha = this.state[i];
            const beta = this.state[j];

            this.state[i] = matrix[0][0].multiply(alpha)
                .add(matrix[0][1].multiply(beta));

            this.state[j] = matrix[1][0].multiply(alpha)
                .add(matrix[1][1].multiply(beta));
        }
    }

    ry(qubit, angle) {
        validateFinite(angle, 'Rotation angle');

        const c = Math.cos(angle / 2);
        const s = Math.sin(angle / 2);

        this.applyGate(qubit, [
            [new Complex(c), new Complex(-s)],
            [new Complex(s), new Complex(c)]
        ]);
    }

    rz(qubit, angle) {
        validateFinite(angle, 'Rotation angle');

        const c = Math.cos(angle / 2);
        const s = Math.sin(angle / 2);

        this.applyGate(qubit, [
            [new Complex(c, -s), new Complex()],
            [new Complex(), new Complex(c, s)]
        ]);
    }

    cnot(control, target) {
        if (!Number.isInteger(control) ||
            !Number.isInteger(target) ||
            control === target ||
            control < 0 ||
            target < 0 ||
            control >= this.qubits ||
            target >= this.qubits) {
            throw new ValidationError('Invalid CNOT configuration.');
        }

        const controlMask = 1 << control;
        const targetMask = 1 << target;

        for (let i = 0; i < this.dimension; i++) {
            if ((i & controlMask) && !(i & targetMask)) {
                const j = i | targetMask;

                [this.state[i], this.state[j]] =
                    [this.state[j], this.state[i]];
            }
        }
    }

    probabilities() {
        return this.state.map(a => a.magnitudeSquared());
    }

    expectationZ(qubit) {
        if (qubit < 0 || qubit >= this.qubits) {
            throw new ValidationError('Invalid measurement qubit.');
        }

        let result = 0;

        this.state.forEach((amplitude, index) => {
            const sign = (index & (1 << qubit)) ? -1 : 1;

            result += sign * amplitude.magnitudeSquared();
        });

        return result;
    }

    measure(qubit, shots = 1000, random = Math.random) {
        if (!Number.isInteger(shots) || shots <= 0) {
            throw new ValidationError('Shots must be positive.');
        }

        const p = this.probabilities();
        const probabilityOne = p.reduce(
            (sum, value, index) =>
                sum + ((index & (1 << qubit)) ? value : 0),
            0
        );

        const counts = { 0: 0, 1: 0 };

        for (let i = 0; i < shots; i++) {
            counts[random() < probabilityOne ? 1 : 0]++;
        }

        return {
            counts,
            shots,
            expectation: (counts[0] - counts[1]) / shots
        };
    }

    validateState() {
        const norm = this.probabilities().reduce(
            (sum, value) => sum + value,
            0
        );

        if (Math.abs(norm - 1) > EPSILON) {
            throw new QuantumError(`State normalization failed: ${norm}`);
        }
    }
}

class ParameterizedQuantumCircuit {
    static PARAMETER_COUNT = 4;

    forward(features, parameters) {
        if (!Array.isArray(features) ||
            features.length !== 2 ||
            !Array.isArray(parameters) ||
            parameters.length !== 4) {
            throw new ValidationError('Expected two features and four parameters.');
        }

        features.forEach((x, i) => validateFinite(x, `Feature ${i}`));
        parameters.forEach((x, i) => validateFinite(x, `Parameter ${i}`));

        const register = new QuantumRegister(2);

        // Classical-to-quantum feature encoding.
        register.ry(0, features[0]);
        register.ry(1, features[1]);

        // Trainable variational ansatz.
        register.ry(0, parameters[0]);
        register.ry(1, parameters[1]);
        register.cnot(0, 1);

        register.ry(0, parameters[2]);
        register.ry(1, parameters[3]);
        register.cnot(1, 0);

        register.validateState();

        return register.expectationZ(0);
    }
}

class QuantumDataset {
    constructor(examples) {
        if (!Array.isArray(examples) || examples.length === 0) {
            throw new ValidationError('Dataset cannot be empty.');
        }

        this.examples = examples.map((example, index) => {
            if (!Array.isArray(example.features) ||
                example.features.length !== 2) {
                throw new ValidationError(`Invalid features at row ${index}.`);
            }

            example.features.forEach(x => validateFinite(x, 'Feature'));

            if (![ -1, 1 ].includes(example.target)) {
                throw new ValidationError('Targets must be -1 or +1.');
            }

            return Object.freeze({
                features: Object.freeze([...example.features]),
                target: example.target
            });
        });

        Object.freeze(this.examples);
    }
}

class VariationalOptimizer {
    constructor(options = {}) {
        this.learningRate = options.learningRate ?? 0.05;

        if (!Number.isFinite(this.learningRate) ||
            this.learningRate <= 0 ||
            this.learningRate > 1) {
            throw new ValidationError('Invalid learning rate.');
        }

        this.circuit = new ParameterizedQuantumCircuit();

        this.parameters = [0.2, -0.3, 0.4, 0.1];
    }

    loss(dataset, parameters = this.parameters) {
        return dataset.examples.reduce((sum, example) => {
            const output = this.circuit.forward(
                example.features,
                parameters
            );

            return sum + (output - example.target) ** 2;
        }, 0) / dataset.examples.length;
    }

    /*
     * Parameter-shift rule:
     *
     * d<f>/d(theta) =
     * [f(theta + pi/2) - f(theta - pi/2)] / 2
     *
     * Valid here because each trainable parameter occurs
     * in exactly one standard rotation gate.
     */
    gradient(dataset) {
        return this.parameters.map((parameter, index) => {
            const plus = [...this.parameters];
            const minus = [...this.parameters];

            plus[index] = parameter + PI / 2;
            minus[index] = parameter - PI / 2;

            return (
                this.loss(dataset, plus) -
                this.loss(dataset, minus)
            ) / 2;
        });
    }

    accuracy(dataset) {
        let correct = 0;

        for (const example of dataset.examples) {
            const output = this.circuit.forward(
                example.features,
                this.parameters
            );

            const predicted = output >= 0 ? 1 : -1;

            if (predicted === example.target) correct++;
        }

        return correct / dataset.examples.length;
    }
}

class QuantumExperiment extends EventEmitter {
    constructor(dataset, options = {}) {
        super();

        this.dataset = dataset;
        this.optimizer = new VariationalOptimizer(options);
        this.status = 'CREATED';
        this.epoch = 0;
        this.history = [];
    }

    async train(options = {}) {
        if (this.status === 'RUNNING') {
            throw new QuantumError('Experiment is already running.');
        }

        if (this.status === 'COMPLETED') {
            throw new QuantumError('Experiment has already completed.');
        }

        const epochs = options.epochs ?? 100;

        if (!Number.isInteger(epochs) || epochs <= 0) {
            throw new ValidationError('Epochs must be positive.');
        }

        this.status = 'RUNNING';
        this.emit('started', {
            parameters: [...this.optimizer.parameters]
        });

        try {
            for (let epoch = 1; epoch <= epochs; epoch++) {
                const gradients = this.optimizer.gradient(this.dataset);

                this.optimizer.parameters =
                    this.optimizer.parameters.map(
                        (parameter, index) =>
                            parameter -
                            this.optimizer.learningRate * gradients[index]
                    );

                const loss = this.optimizer.loss(this.dataset);

                const metrics = {
                    epoch,
                    loss,
                    accuracy: this.optimizer.accuracy(this.dataset)
                };

                this.history.push(metrics);
                this.epoch = epoch;

                this.emit('epoch', metrics);

                // Yield to the event loop for monitoring and responsiveness.
                if (epoch % 5 === 0) {
                    await new Promise(resolve => setImmediate(resolve));
                }

                if (loss < 1e-7) break;
            }

            this.status = 'COMPLETED';

            const result = {
                status: this.status,
                epochs: this.epoch,
                parameters: [...this.optimizer.parameters],
                finalLoss: this.optimizer.loss(this.dataset),
                accuracy: this.optimizer.accuracy(this.dataset)
            };

            this.emit('completed', result);

            return result;
        } catch (error) {
            this.status = 'FAILED';
            this.emit('failed', {
                message: error.message,
                epoch: this.epoch
            });

            throw error;
        }
    }

    async saveReport(path) {
        if (this.status !== 'COMPLETED') {
            throw new QuantumError('Only completed experiments can be exported.');
        }

        const report = {
            status: this.status,
            epochs: this.epoch,
            parameters: this.optimizer.parameters,
            history: this.history
        };

        // Restrict export paths at the application layer in production.
        await writeFile(
            path,
            JSON.stringify(report, null, 2),
            { encoding: 'utf8', mode: 0o600 }
        );
    }
}

async function main() {
    console.log('QUANTUM NEURAL NETWORK FUNDAMENTALS');
    console.log('====================================');

    const register = new QuantumRegister(2);

    register.ry(0, PI / 2);
    register.cnot(0, 1);

    console.log('\nBell-state probabilities:');
    console.log(register.probabilities());

    console.log('\nBell-state measurements:');
    console.log(register.measure(0, 1000));

    const dataset = new QuantumDataset([
        { features: [0.2, 0.3], target: 1 },
        { features: [0.3, 0.5], target: 1 },
        { features: [2.8, 2.5], target: -1 },
        { features: [2.5, 2.9], target: -1 },
        { features: [0.5, 0.2], target: 1 },
        { features: [2.9, 2.7], target: -1 }
    ]);

    const experiment = new QuantumExperiment(dataset, {
        learningRate: 0.05
    });

    experiment.on('started', () => {
        console.log('\nTraining started.');
    });

    experiment.on('epoch', metrics => {
        if (metrics.epoch % 10 === 0) {
            console.log(
                `Epoch ${metrics.epoch}: ` +
                `loss=${metrics.loss.toFixed(6)}, ` +
                `accuracy=${metrics.accuracy.toFixed(3)}`
            );
        }
    });

    experiment.on('completed', result => {
        console.log('\nTraining completed.');
        console.log(result);
    });

    experiment.on('failed', error => {
        console.error('Experiment failed:', error);
    });

    const result = await experiment.train({ epochs: 100 });

    console.log('\nFinal predictions:');

    for (const example of dataset.examples) {
        const output = experiment.optimizer.circuit.forward(
            example.features,
            result.parameters
        );

        console.log({
            features: example.features,
            expected: example.target,
            output,
            predicted: output >= 0 ? 1 : -1
        });
    }

    await experiment.saveReport('qnn_experiment_js.json');
    console.log('\nExperiment report exported.');
}

async function runTests() {
    const register = new QuantumRegister(1);

    register.ry(0, PI / 2);

    if (Math.abs(register.expectationZ(0)) > EPSILON) {
        throw new Error('RY gate test failed.');
    }

    const bell = new QuantumRegister(2);
    bell.ry(0, PI / 2);
    bell.cnot(0, 1);

    const probabilities = bell.probabilities();

    if (Math.abs(probabilities[0] - 0.5) > EPSILON ||
        Math.abs(probabilities[3] - 0.5) > EPSILON) {
        throw new Error('Entanglement test failed.');
    }

    try {
        new QuantumRegister(0);
        throw new Error('Invalid qubit count was accepted.');
    } catch (error) {
        if (!(error instanceof ValidationError)) throw error;
    }

    console.log('All JavaScript quantum tests passed.');
}

if (require.main === module) {
    runTests()
        .then(main)
        .catch(error => {
            console.error(error);
            process.exitCode = 1;
        });
}

module.exports = {
    Complex,
    QuantumRegister,
    ParameterizedQuantumCircuit,
    QuantumDataset,
    VariationalOptimizer,
    QuantumExperiment,
    ValidationError
};
