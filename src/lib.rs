use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyfunction]
fn process(
    py: Python,
    temperatures: PyReadonlyArray1<f64>,  // Node
    capacities: PyReadonlyArray1<f64>,  // Node
    parameters: PyReadonlyArray1<f64>,    // Edge
    connections: PyReadonlyArray2<usize>, // Edge
    edge_types: PyReadonlyArray1<i32>,     // Edge // Note: 0->Transfer, 1->Radiation, 2->HeatInput
    dt: f64,
    steps: i32,
) -> Py<PyArray1<f64>> {

    let mut temperatures = temperatures.as_array().to_owned();
    let capacities = capacities.as_array();
    let parameters = parameters.as_array();
    let connections = connections.as_array();
    let edge_types = edge_types.as_array();

    let max_calc_size = connections.len();
    for _ in 0..steps {
        let mut update_list: Vec<(usize, f64)> = Vec::with_capacity(max_calc_size);
        for ((conn, &parameter), &edge_type) in connections.outer_iter().zip(parameters.iter()).zip(edge_types.iter()) {
            let n1 = conn[0];
            let n2 = conn[1];
            match edge_type {
                0 => {
                    // In this type, parameter is heat resistance (Transfer)
                    let delta_temp = (temperatures[n2] - temperatures[n1]) / parameter * dt;
                    update_list.push((n1,     delta_temp/capacities[n1]));
                    update_list.push((n2, -1.*delta_temp/capacities[n2]));
                }
                1 => {
                    // In this type, parameter is \epsilon E_G \sigma A (Radiation)
                    let delta_temp = (temperatures[n2].powi(4) - temperatures[n1].powi(4)) * parameter * dt;
                    update_list.push((n1,     delta_temp/capacities[n1]));
                    update_list.push((n2, -1.*delta_temp/capacities[n2]));
                }
                2 => {
                    // In this type, parameter is Q [W] A->B (Heat Input)
                    let delta_temp = parameter * dt;
                    update_list.push((n2, delta_temp/capacities[n2]));
                }
                _ => {
                    panic!("This edge type between {} hasn't been defined", conn);
                }
            }
        }
        // update all
        for (idx, delta_temp) in update_list {
            if delta_temp.abs() > 1e8 {  // Check if delta_temp is unreasonably large
                panic!("Unreasonably large temperature change: in edge {}, delta_temp = {}", idx, delta_temp);
            }
            temperatures[idx] += delta_temp;
        }
    }
    let array = PyArray1::from_vec(py, temperatures.to_vec());
    array.to_owned()
}

#[pymodule]
fn chill(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process, m)?)?;
    Ok(())
}
