use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use pyo3::{exceptions::PyRuntimeError, wrap_pyfunction};

#[derive(Debug, Clone, Copy)]
enum EdgeType {
    Transfer,
    Radiation,
    HeatInput,
}

impl EdgeType {
    fn from_i32(value: i32) -> Option<Self> {
        match value {
            0 => Some(EdgeType::Transfer),
            1 => Some(EdgeType::Radiation),
            2 => Some(EdgeType::HeatInput),
            _ => None,
        }
    }
}

/// Update the temperature changes for a single edge.
///
/// # Arguments
///
/// * `edge_type` - The type of the edge (Transfer, Radiation, HeatInput).
/// * `parameter` - The parameter associated with the edge type.
/// * `dt` - Time step.
/// * `capacities` - Slice of capacities for each node.
/// * `temperatures` - Slice of current temperatures for each node.
/// * `n1` - The index of the first node connected by this edge.
/// * `n2` - The index of the second node connected by this edge.
/// * `updates` - A vector to accumulate (node_index, delta_temperature) pairs.
fn update_edge(
    edge_type: EdgeType,
    parameter: f64,
    dt: f64,
    capacities: &[f64],
    temperatures: &[f64],
    n1: usize,
    n2: usize,
    updates: &mut Vec<(usize, f64)>,
) -> PyResult<()> {
    let delta_temp = match edge_type {
        EdgeType::Transfer => {
            // parameter is heat resistance
            (temperatures[n2] - temperatures[n1]) / parameter * dt
        }
        EdgeType::Radiation => {
            // parameter is ε * E_G * σ * A
            (temperatures[n2].powi(4) - temperatures[n1].powi(4)) * parameter * dt
        }
        EdgeType::HeatInput => {
            // parameter is Q [W] (heat input to n2)
            parameter * dt
        }
    };

    match edge_type {
        EdgeType::Transfer | EdgeType::Radiation => {
            updates.push((n1, delta_temp / capacities[n1]));
            updates.push((n2, -delta_temp / capacities[n2]));
        }
        EdgeType::HeatInput => {
            updates.push((n2, delta_temp / capacities[n2]));
        }
    }
    Ok(())
}

#[pyfunction]
/// Process thermal changes over a certain number of steps.
///
/// Parameters
/// ----------
/// temperatures : ndarray of shape (N, )
///     Initial temperatures of each node.
/// capacities : ndarray of shape (N, )
///     Heat capacities for each node.
/// parameters : ndarray of shape (E, )
///     Parameters for each edge (depending on the edge type).
/// connections : ndarray of shape (E, 2)
///     Each row represents an edge, giving the two connected node indices.
/// edge_types : ndarray of shape (E, )
///     Integer codes defining the type of each edge (0: Transfer, 1: Radiation, 2: HeatInput).
/// dt : float
///     Time step for the simulation.
/// steps : int
///     Number of steps to simulate.
///
/// Returns
/// -------
/// ndarray of shape (N, )
///     The updated temperatures after simulation.
fn process(
    py: Python,
    temperatures: PyReadonlyArray1<f64>,
    capacities: PyReadonlyArray1<f64>,
    parameters: PyReadonlyArray1<f64>,
    connections: PyReadonlyArray2<usize>,
    edge_types: PyReadonlyArray1<i32>,
    dt: f64,
    steps: i32,
) -> PyResult<Py<PyArray1<f64>>> {

    let mut temperatures = temperatures.as_array().to_owned(); // Array1<f64>
    let capacities = capacities.as_array();
    let parameters = parameters.as_array();
    let connections = connections.as_array();
    let edge_types = edge_types.as_array();

    let max_calc_size = connections.len();

    for _i in 0..steps {
        let mut update_list: Vec<(usize, f64)> = Vec::with_capacity(max_calc_size * 2);

        for (((&edge_type_int, &parameter), conn), _i)
            in edge_types.iter()
                .zip(parameters.iter())
                .zip(connections.outer_iter())
                .zip(0..) 
        {
            let edge_type = EdgeType::from_i32(edge_type_int)
                .ok_or_else(|| PyRuntimeError::new_err(format!("Undefined edge type: {}", edge_type_int)))?;
            let n1 = conn[0];
            let n2 = conn[1];

            update_edge(
                edge_type,
                parameter,
                dt,
                capacities.as_slice().unwrap(),
                temperatures.as_slice().unwrap(),
                n1,
                n2,
                &mut update_list
            )?;
        }

        // Apply updates
        for (idx, delta_temp) in update_list {
            if delta_temp.abs() > 1e8 {
                return Err(PyRuntimeError::new_err(format!(
                    "Unreasonably large temperature change at node {}: delta_temp = {}",
                    idx, delta_temp
                )));
            }
            temperatures[idx] += delta_temp;
        }
    }

    let array = PyArray1::from_vec(py, temperatures.to_vec());
    Ok(array.to_owned())
}

#[pymodule]
fn chill(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process, m)?)?;
    Ok(())
}

