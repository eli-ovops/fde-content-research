import Foundation
import Vision
import AppKit

// Local offline OCR via the macOS Vision framework (no API, no models, no network).
// Usage: dsh-ocr <image> [image2 ...]
// Reads PNG/JPEG/WebP/GIF/HEIC etc. and prints recognized text in reading order.

func ocrImage(at path: String) -> String {
    guard let image = NSImage(contentsOfFile: path) else {
        return "ERROR: cannot load image at \(path)"
    }
    var rect = NSRect(origin: .zero, size: image.size)
    guard let cg = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
        return "ERROR: cannot decode image at \(path)"
    }

    let request = VNRecognizeTextRequest()
    request.revision = 2
    request.usesCPUOnly = true
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true

    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([request])
    } catch {
        return "ERROR: OCR failed for \(path): \(error)"
    }

    guard let results = request.results else { return "" }

    // Reading order: top-to-bottom, then left-to-right within a line band.
    let sorted = results.sorted { a, b in
        let ay = a.boundingBox.midY
        let by = b.boundingBox.midY
        if abs(ay - by) > 0.01 { return ay > by }
        return a.boundingBox.midX < b.boundingBox.midX
    }

    var lines: [String] = []
    for obs in sorted {
        if let candidate = obs.topCandidates(1).first {
            lines.append(candidate.string)
        }
    }
    return lines.joined(separator: "\n")
}

let args = CommandLine.arguments
if args.count < 2 {
    FileHandle.standardError.write("usage: dsh-ocr <image> [image2 ...]\n".data(using: .utf8)!)
    exit(2)
}

var first = true
for path in args.dropFirst() {
    if args.count > 2 {
        if !first { print("\n--- \(path) ---") }
        print(ocrImage(at: path))
        first = false
    } else {
        print(ocrImage(at: path))
    }
}
