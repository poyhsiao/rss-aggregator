//! Sidecar management module
//!
//! This module handles the lifecycle of the Python backend process
//! and provides JSON-RPC client functionality for communication.

mod client;
mod process;

pub use client::*;
pub use process::*;
