import AppKit

// Render a 44x44 (retina @2x for 22x22 pt) monochrome template icon for the
// menu bar. Five rounded bars + a thin caret nub — the same motif as the
// floating preview / app icon, distilled to a single color so setTemplate_
// lets AppKit recolor for light/dark mode.

let pt = 22
let scale = 2
let size = NSSize(width: pt * scale, height: pt * scale)
let image = NSImage(size: size)
image.lockFocus()

let canvas = NSRect(origin: .zero, size: size)
NSColor.clear.setFill()
canvas.fill()
NSColor.black.setFill()

let heights: [CGFloat] = [10, 18, 26, 18, 10]
let barWidth: CGFloat = 4
let gap: CGFloat = 3
let totalCount = CGFloat(heights.count)
let totalWidth = totalCount * barWidth + (totalCount - 1) * gap
var x = (CGFloat(pt * scale) - totalWidth) / 2
let centerY = CGFloat(pt * scale) / 2

for h in heights {
    let rect = NSRect(x: x, y: centerY - h / 2, width: barWidth, height: h)
    let bar = NSBezierPath(roundedRect: rect, xRadius: barWidth / 2, yRadius: barWidth / 2)
    bar.fill()
    x += barWidth + gap
}

// Caret nub on the right — same motif as the app icon's text-cursor anchor.
let caret = NSBezierPath(roundedRect: NSRect(
    x: CGFloat(pt * scale) - 7,
    y: centerY - 7,
    width: 3,
    height: 14
), xRadius: 1.5, yRadius: 1.5)
caret.fill()

image.unlockFocus()
image.isTemplate = true

guard let data = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: data),
      let png = bitmap.representation(using: .png, properties: [:]) else {
    fatalError("Unable to render status bar icon")
}

let output = CommandLine.arguments.count > 1
    ? CommandLine.arguments[1]
    : "StatusBarIcon.png"
try png.write(to: URL(fileURLWithPath: output))
