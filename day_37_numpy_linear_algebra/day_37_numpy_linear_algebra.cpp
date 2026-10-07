#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Vector = std::vector<double>;

class Matrix {
private:
    std::size_t rows_;
    std::size_t cols_;
    std::vector<double> data_;

    std::size_t index(std::size_t row, std::size_t col) const {
        return row * cols_ + col;
    }

public:
    Matrix(std::size_t rows, std::size_t cols, double initial = 0.0)
        : rows_(rows), cols_(cols), data_(rows * cols, initial) {
        if (rows == 0 || cols == 0) {
            throw std::invalid_argument("Matrix dimensions must be positive");
        }
    }

    Matrix(std::initializer_list<std::initializer_list<double>> values) {
        if (values.size() == 0) {
            throw std::invalid_argument("Matrix cannot be empty");
        }

        rows_ = values.size();
        cols_ = values.begin()->size();

        if (cols_ == 0) {
            throw std::invalid_argument("Matrix cannot have zero columns");
        }

        data_.reserve(rows_ * cols_);

        for (const auto& row : values) {
            if (row.size() != cols_) {
                throw std::invalid_argument("Matrix rows must have equal length");
            }
            data_.insert(data_.end(), row.begin(), row.end());
        }
    }

    double& operator()(std::size_t row, std::size_t col) {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Matrix index out of range");
        }
        return data_[index(row, col)];
    }

    double operator()(std::size_t row, std::size_t col) const {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Matrix index out of range");
        }
        return data_[index(row, col)];
    }

    std::size_t rows() const { return rows_; }
    std::size_t cols() const { return cols_; }

    static Matrix identity(std::size_t size) {
        Matrix result(size, size);
        for (std::size_t i = 0; i < size; ++i) {
            result(i, i) = 1.0;
        }
        return result;
    }

    Matrix transpose() const {
        Matrix result(cols_, rows_);
        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result(col, row) = (*this)(row, col);
            }
        }
        return result;
    }

    Matrix operator*(const Matrix& other) const {
        if (cols_ != other.rows_) {
            throw std::invalid_argument(
                "Matrix multiplication requires A.columns == B.rows"
            );
        }

        Matrix result(rows_, other.cols_);

        for (std::size_t i = 0; i < rows_; ++i) {
            for (std::size_t k = 0; k < cols_; ++k) {
                const double value = (*this)(i, k);
                for (std::size_t j = 0; j < other.cols_; ++j) {
                    result(i, j) += value * other(k, j);
                }
            }
        }

        return result;
    }

    Vector operator*(const Vector& vector) const {
        if (cols_ != vector.size()) {
            throw std::invalid_argument(
                "Matrix columns must match vector size"
            );
        }

        Vector result(rows_, 0.0);

        for (std::size_t row = 0; row < rows_; ++row) {
            for (std::size_t col = 0; col < cols_; ++col) {
                result[row] += (*this)(row, col) * vector[col];
            }
        }

        return result;
    }

    void print(const std::string& label) const {
        std::cout << label << "\n";
        for (std::size_t row = 0; row < rows_; ++row) {
            std::cout << "  ";
            for (std::size_t col = 0; col < cols_; ++col) {
                std::cout << std::setw(10) << std::setprecision(5)
                          << (*this)(row, col);
            }
            std::cout << '\n';
        }
    }
};

double dot(const Vector& a, const Vector& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Dot-product dimensions must match");
    }

    double result = 0.0;
    for (std::size_t i = 0; i < a.size(); ++i) {
        result += a[i] * b[i];
    }
    return result;
}

double norm2(const Vector& vector) {
    return std::sqrt(dot(vector, vector));
}

Vector normalize(const Vector& vector) {
    const double length = norm2(vector);

    if (length <= std::numeric_limits<double>::epsilon()) {
        throw std::invalid_argument("Cannot normalize the zero vector");
    }

    Vector result = vector;
    for (double& value : result) {
        value /= length;
    }
    return result;
}

Vector solveLinearSystem(Matrix matrix, Vector rhs) {
    if (matrix.rows() != matrix.cols()) {
        throw std::invalid_argument("System matrix must be square");
    }

    if (rhs.size() != matrix.rows()) {
        throw std::invalid_argument("Right-hand side dimension mismatch");
    }

    const std::size_t n = matrix.rows();

    /*
     * Gaussian elimination with partial pivoting is used here. Pivoting
     * reduces the effect of dividing by very small diagonal values and is
     * substantially safer than naive elimination.
     */
    for (std::size_t pivot = 0; pivot < n; ++pivot) {
        std::size_t best = pivot;

        for (std::size_t row = pivot + 1; row < n; ++row) {
            if (std::abs(matrix(row, pivot)) >
                std::abs(matrix(best, pivot))) {
                best = row;
            }
        }

        if (std::abs(matrix(best, pivot)) <
            std::numeric_limits<double>::epsilon()) {
            throw std::runtime_error("Singular or numerically singular matrix");
        }

        if (best != pivot) {
            for (std::size_t col = 0; col < n; ++col) {
                std::swap(matrix(pivot, col), matrix(best, col));
            }
            std::swap(rhs[pivot], rhs[best]);
        }

        for (std::size_t row = pivot + 1; row < n; ++row) {
            const double factor = matrix(row, pivot) / matrix(pivot, pivot);

            matrix(row, pivot) = 0.0;

            for (std::size_t col = pivot + 1; col < n; ++col) {
                matrix(row, col) -= factor * matrix(pivot, col);
            }

            rhs[row] -= factor * rhs[pivot];
        }
    }

    Vector solution(n, 0.0);

    for (std::size_t row = n; row-- > 0;) {
        double value = rhs[row];

        for (std::size_t col = row + 1; col < n; ++col) {
            value -= matrix(row, col) * solution[col];
        }

        solution[row] = value / matrix(row, row);
    }

    return solution;
}

double determinant(Matrix matrix) {
    if (matrix.rows() != matrix.cols()) {
        throw std::invalid_argument("Determinant requires a square matrix");
    }

    const std::size_t n = matrix.rows();
    double result = 1.0;
    int sign = 1;

    for (std::size_t pivot = 0; pivot < n; ++pivot) {
        std::size_t best = pivot;

        for (std::size_t row = pivot + 1; row < n; ++row) {
            if (std::abs(matrix(row, pivot)) >
                std::abs(matrix(best, pivot))) {
                best = row;
            }
        }

        if (std::abs(matrix(best, pivot)) <
            std::numeric_limits<double>::epsilon()) {
            return 0.0;
        }

        if (best != pivot) {
            for (std::size_t col = 0; col < n; ++col) {
                std::swap(matrix(pivot, col), matrix(best, col));
            }
            sign *= -1;
        }

        const double pivotValue = matrix(pivot, pivot);
        result *= pivotValue;

        for (std::size_t row = pivot + 1; row < n; ++row) {
            const double factor = matrix(row, pivot) / pivotValue;

            for (std::size_t col = pivot + 1; col < n; ++col) {
                matrix(row, col) -= factor * matrix(pivot, col);
            }
        }
    }

    return result * sign;
}

Matrix covarianceMatrix(const std::vector<Vector>& observations) {
    if (observations.empty()) {
        throw std::invalid_argument("At least one observation is required");
    }

    const std::size_t features = observations.front().size();

    if (features == 0) {
        throw std::invalid_argument("Observations need at least one feature");
    }

    for (const auto& observation : observations) {
        if (observation.size() != features) {
            throw std::invalid_argument("All observations need equal dimensions");
        }
    }

    Vector mean(features, 0.0);

    for (const auto& observation : observations) {
        for (std::size_t feature = 0; feature < features; ++feature) {
            mean[feature] += observation[feature];
        }
    }

    for (double& value : mean) {
        value /= static_cast<double>(observations.size());
    }

    Matrix covariance(features, features);

    for (const auto& observation : observations) {
        Vector centered(features);

        for (std::size_t feature = 0; feature < features; ++feature) {
            centered[feature] = observation[feature] - mean[feature];
        }

        for (std::size_t row = 0; row < features; ++row) {
            for (std::size_t col = 0; col < features; ++col) {
                covariance(row, col) +=
                    centered[row] * centered[col];
            }
        }
    }

    const double denominator =
        observations.size() > 1
            ? static_cast<double>(observations.size() - 1)
            : 1.0;

    for (std::size_t row = 0; row < features; ++row) {
        for (std::size_t col = 0; col < features; ++col) {
            covariance(row, col) /= denominator;
        }
    }

    return covariance;
}

void printVector(const std::string& label, const Vector& vector) {
    std::cout << label << "[";
    for (std::size_t i = 0; i < vector.size(); ++i) {
        if (i != 0) {
            std::cout << ", ";
        }
        std::cout << std::setprecision(6) << vector[i];
    }
    std::cout << "]\n";
}

int main() {
    try {
        std::cout << std::fixed << std::setprecision(5);

        std::cout << "\n=== Vector geometry ===\n";

        Vector customerProfile{3.0, 4.0, 12.0};
        Vector featureWeights{0.5, 0.25, 0.75};

        printVector("Profile: ", customerProfile);
        printVector("Weights: ", featureWeights);
        std::cout << "Dot product: "
                  << dot(customerProfile, featureWeights) << '\n';
        std::cout << "L2 norm: "
                  << norm2(customerProfile) << '\n';

        Vector normalized = normalize(customerProfile);
        printVector("Normalized profile: ", normalized);

        const double projectionScale =
            dot(customerProfile, featureWeights) /
            dot(featureWeights, featureWeights);

        Vector projection = featureWeights;
        for (double& value : projection) {
            value *= projectionScale;
        }
        printVector("Projection onto weight direction: ", projection);

        std::cout << "\n=== Matrix transformation ===\n";

        Matrix transformation{
            {1.0, 0.2, 0.0},
            {0.0, 1.0, 0.5},
            {0.1, 0.0, 1.0}
        };

        transformation.print("Transformation:");

        Vector transformed = transformation * customerProfile;
        printVector("Transformed profile: ", transformed);

        std::cout << "\n=== Solving a system ===\n";

        Matrix system{
            {3.0, 2.0, -1.0},
            {2.0, -2.0, 4.0},
            {-1.0, 0.5, -1.0}
        };

        Vector target{1.0, -2.0, 0.0};

        Vector solution = solveLinearSystem(system, target);
        printVector("Solution: ", solution);

        Vector reconstructed = system * solution;
        printVector("A*x: ", reconstructed);

        double residualSquared = 0.0;
        for (std::size_t i = 0; i < target.size(); ++i) {
            const double error = reconstructed[i] - target[i];
            residualSquared += error * error;
        }

        std::cout << "Residual L2 norm: "
                  << std::sqrt(residualSquared) << '\n';

        std::cout << "\n=== Matrix determinant ===\n";
        std::cout << "det(A): " << determinant(system) << '\n';

        std::cout << "\n=== Batch observations and covariance ===\n";

        std::vector<Vector> observations{
            {2.0, 1.0, 4.0},
            {3.0, 2.0, 5.0},
            {4.0, 3.0, 7.0},
            {5.0, 4.0, 8.0},
            {6.0, 5.0, 10.0}
        };

        Matrix covariance = covarianceMatrix(observations);
        covariance.print("Covariance:");

        std::cout << "\n=== Matrix multiplication case ===\n";

        Matrix featureTransform{
            {1.0, 0.0, 2.0},
            {0.0, 1.0, 1.0}
        };

        Matrix featureTransformTranspose = featureTransform.transpose();
        Matrix gram = featureTransform * featureTransformTranspose;

        featureTransform.print("Feature transform:");
        featureTransformTranspose.print("Transpose:");
        gram.print("Transform * transpose:");

        std::cout << "\n=== Edge-case handling ===\n";

        try {
            Vector zero{0.0, 0.0, 0.0};
            normalize(zero);
        } catch (const std::exception& error) {
            std::cout << "Zero-vector failure: "
                      << error.what() << '\n';
        }

        try {
            Matrix singular{
                {1.0, 2.0},
                {2.0, 4.0}
            };
            solveLinearSystem(singular, {3.0, 6.0});
        } catch (const std::exception& error) {
            std::cout << "Singular-system failure: "
                      << error.what() << '\n';
        }

        try {
            Matrix left{{1.0, 2.0}};
            Matrix right{{1.0, 2.0}};
            left * right;
        } catch (const std::exception& error) {
            std::cout << "Shape failure: "
                      << error.what() << '\n';
        }

        /*
         * The case study keeps matrix storage contiguous in row-major order.
         * This makes the representation compact and predictable. Matrix
         * multiplication is O(n^3) for square matrices, while matrix-vector
         * multiplication is O(n^2). Real production systems commonly replace
         * handwritten kernels with optimized BLAS/LAPACK implementations.
         */

        std::cout << "\nCase study completed successfully.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
