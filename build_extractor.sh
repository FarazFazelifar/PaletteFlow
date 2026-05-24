#!/bin/bash
# Build the Rust color extractor for faster palette extraction.
set -euo pipefail
cd "$(dirname "$0")/extractor"
cargo build --release
echo "Extractor built: target/release/paletteflow-extract"
