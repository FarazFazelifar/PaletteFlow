use image::GenericImageView;
use std::env;
use std::process;

const MAX_DIM: u32 = 300;
const K: usize = 10;
const MAX_ITER: usize = 50;
const DIVERSITY_THRESHOLD: f64 = 8.0;
const CONVERGENCE_EPSILON: f64 = 0.1;

fn main() {
    let args: Vec<String> = env::args().collect();

    let path = args.get(1).cloned().unwrap_or_else(|| {
        eprintln!("Usage: {} <image_path> [num_colors]", args[0]);
        process::exit(1);
    });

    let _num_colors: usize = args
        .get(2)
        .and_then(|s| s.parse().ok())
        .filter(|&n| (4..=12).contains(&n))
        .unwrap_or(8);

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

    let pixels: Vec<[u8; 3]> = small.pixels().map(|p| [p.0[0], p.0[1], p.0[2]]).collect();
    let n = pixels.len();

    if n == 0 {
        eprintln!("Error: image has no pixels");
        process::exit(1);
    }

    // Convert to LAB
    let lab_pixels: Vec<[f64; 3]> = pixels.iter().map(|&rgb| rgb_to_lab(rgb)).collect();

    // K-Means
    let centroids = kmeans(&lab_pixels);

    // Assign each pixel to nearest centroid
    let assignments: Vec<usize> = lab_pixels
        .iter()
        .map(|p| nearest_centroid(p, &centroids))
        .collect();

    // Count dominance
    let mut cluster_counts = vec![0usize; K];
    for &a in &assignments {
        cluster_counts[a] += 1;
    }

    // Snap each centroid to nearest exact pixel
    let snapped: Vec<[u8; 3]> = centroids
        .iter()
        .map(|&lab| {
            let idx = lab_pixels
                .iter()
                .enumerate()
                .map(|(i, p)| (i, lab_distance(*p, lab)))
                .min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
                .unwrap()
                .0;
            pixels[idx]
        })
        .collect();

    // Combine with dominance and sort descending
    let mut colors: Vec<([u8; 3], usize)> =
        snapped.into_iter().zip(cluster_counts.into_iter()).collect();
    colors.sort_by(|a, b| b.1.cmp(&a.1));

    // Filter by diversity: remove colors too similar to higher-dominance ones
    let mut filtered: Vec<([u8; 3], usize)> = Vec::new();
    for color in colors {
        let too_close = filtered.iter().any(|&(existing, _)| {
            lab_distance(rgb_to_lab(existing), rgb_to_lab(color.0)) < DIVERSITY_THRESHOLD
        });
        if !too_close {
            filtered.push(color);
        }
    }

    // Output hex codes, one per line, sorted by dominance
    for (rgb, _) in &filtered {
        println!("#{:02X}{:02X}{:02X}", rgb[0], rgb[1], rgb[2]);
    }
}

fn lab_distance(a: [f64; 3], b: [f64; 3]) -> f64 {
    ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2) + (a[2] - b[2]).powi(2)).sqrt()
}

fn nearest_centroid(pixel: &[f64; 3], centroids: &[[f64; 3]]) -> usize {
    centroids
        .iter()
        .enumerate()
        .map(|(i, c)| (i, lab_distance(*pixel, *c)))
        .min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
        .unwrap()
        .0
}

fn kmeans(pixels: &[[f64; 3]]) -> Vec<[f64; 3]> {
    let n = pixels.len();
    let k = K.min(n);

    // Initialize: pick first centroid as mean, then furthest points
    let mean = {
        let mut sum = [0.0; 3];
        for p in pixels {
            sum[0] += p[0];
            sum[1] += p[1];
            sum[2] += p[2];
        }
        [
            sum[0] / n as f64,
            sum[1] / n as f64,
            sum[2] / n as f64,
        ]
    };

    let mut centroids = vec![mean];
    for _ in 1..k {
        let distances: Vec<f64> = pixels
            .iter()
            .map(|p| centroids.iter().map(|c| lab_distance(*p, *c)).sum())
            .collect();
        let max_idx = distances
            .iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .unwrap()
            .0;
        centroids.push(pixels[max_idx]);
    }

    // Iterate
    for _ in 0..MAX_ITER {
        let assignments: Vec<usize> = pixels
            .iter()
            .map(|p| nearest_centroid(p, &centroids))
            .collect();

        let mut new_centroids = vec![[0.0; 3]; k];
        let mut counts = vec![0usize; k];

        for (i, &cluster) in assignments.iter().enumerate() {
            new_centroids[cluster][0] += pixels[i][0];
            new_centroids[cluster][1] += pixels[i][1];
            new_centroids[cluster][2] += pixels[i][2];
            counts[cluster] += 1;
        }

        for i in 0..k {
            if counts[i] > 0 {
                new_centroids[i][0] /= counts[i] as f64;
                new_centroids[i][1] /= counts[i] as f64;
                new_centroids[i][2] /= counts[i] as f64;
            } else {
                new_centroids[i] = centroids[i];
            }
        }

        let max_shift = centroids
            .iter()
            .zip(new_centroids.iter())
            .map(|(a, b)| lab_distance(*a, *b))
            .max_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap_or(0.0);

        centroids = new_centroids;

        if max_shift < CONVERGENCE_EPSILON {
            break;
        }
    }

    centroids
}

fn linearize(c: f64) -> f64 {
    if c <= 0.04045 {
        c / 12.92
    } else {
        ((c + 0.055) / 1.055).powf(2.4)
    }
}

fn rgb_to_lab(rgb: [u8; 3]) -> [f64; 3] {
    let r = linearize(rgb[0] as f64 / 255.0);
    let g = linearize(rgb[1] as f64 / 255.0);
    let b = linearize(rgb[2] as f64 / 255.0);

    let x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b;
    let y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;
    let z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b;

    fn lab_f(t: f64) -> f64 {
        if t > 0.008856 {
            t.powf(1.0 / 3.0)
        } else {
            7.787 * t + 16.0 / 116.0
        }
    }

    let fx = lab_f(x / 0.95047);
    let fy = lab_f(y / 1.0);
    let fz = lab_f(z / 1.08883);

    let l = 116.0 * fy - 16.0;
    let a = 500.0 * (fx - fy);
    let b_val = 200.0 * (fy - fz);

    [l, a, b_val]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rgb_to_lab_black() {
        let lab = rgb_to_lab([0, 0, 0]);
        assert!((lab[0] - 0.0).abs() < 1.0);
    }

    #[test]
    fn test_rgb_to_lab_white() {
        let lab = rgb_to_lab([255, 255, 255]);
        assert!((lab[0] - 100.0).abs() < 5.0);
    }

    #[test]
    fn test_lab_distance_same() {
        let a = rgb_to_lab([100, 150, 200]);
        let d = lab_distance(a, a);
        assert!(d < 1e-10);
    }

    #[test]
    fn test_lab_distance_different() {
        let a = rgb_to_lab([0, 0, 0]);
        let b = rgb_to_lab([255, 255, 255]);
        let d = lab_distance(a, b);
        assert!(d > 50.0);
    }
}
