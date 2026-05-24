use image::GenericImageView;
use std::env;
use std::process;

const MAX_DIM: u32 = 300;
const QUALITY: u8 = 5;
const DEFAULT_NUM_COLORS: u8 = 6;

fn main() {
    let args: Vec<String> = env::args().collect();

    let path = args.get(1).cloned().unwrap_or_else(|| {
        eprintln!("Usage: {} <image_path> [num_colors]", args[0]);
        process::exit(1);
    });

    let num_colors: u8 = args
        .get(2)
        .and_then(|s| s.parse().ok())
        .filter(|&n| (4..=12).contains(&n))
        .unwrap_or(DEFAULT_NUM_COLORS);

    let img = image::open(&path).unwrap_or_else(|e| {
        eprintln!("Error opening image: {e}");
        process::exit(1);
    });

    let (w, h) = img.dimensions();
    let (nw, nh) = if w > MAX_DIM || h > MAX_DIM {
        let scale = MAX_DIM as f64 / w.max(h) as f64;
        (
            (w as f64 * scale).round() as u32,
            (h as f64 * scale).round() as u32,
        )
    } else {
        (w, h)
    };

    let small = if (nw, nh) != (w, h) {
        img.resize_exact(nw, nh, image::imageops::FilterType::Lanczos3)
            .to_rgba8()
    } else {
        img.to_rgba8()
    };

    let pixels = small.into_raw();

    let palette =
        color_thief::get_palette(&pixels, color_thief::ColorFormat::Rgba, QUALITY, num_colors)
            .unwrap_or_else(|e| {
                eprintln!("Error extracting palette: {e}");
                process::exit(1);
            });

    let mut out: Vec<String> = palette
        .iter()
        .map(|c| format!("#{:02X}{:02X}{:02X}", c.r, c.g, c.b))
        .collect();

    while out.len() < num_colors as usize {
        out.push(out.last().unwrap().clone());
    }

    for c in &out {
        println!("{c}");
    }
}
