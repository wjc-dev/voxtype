import Foundation

enum HotkeyConfig {
    static let defaultSpec = "keycode:49;mods:control+option"
    static let defaultLabel = "⌃⌥Space"
    static let modifierOnlySpecs: Set<String> = [
        "fn",
        "left_option", "right_option",
        "left_command", "right_command",
        "left_control", "right_control",
    ]
    static let registeredModifiers: Set<String> = [
        "control", "option", "shift", "command", "function",
    ]

    static func registeredSpec(keyCode: Int, modifiers: [String]) -> String? {
        guard (0...127).contains(keyCode), !modifiers.isEmpty else { return nil }
        let unique = Set(modifiers)
        guard unique.count == modifiers.count,
              unique.isSubset(of: registeredModifiers)
        else { return nil }
        return "keycode:\(keyCode);mods:\(modifiers.joined(separator: "+"))"
    }

    static func parseRegisteredSpec(_ spec: String) -> (keyCode: Int, modifiers: [String])? {
        var parts: [String: String] = [:]
        for raw in spec.split(separator: ";") {
            let pair = raw.split(separator: ":", maxSplits: 1).map(String.init)
            guard pair.count == 2, parts[pair[0]] == nil else { return nil }
            parts[pair[0]] = pair[1]
        }
        guard let keyCodeText = parts["keycode"],
              let keyCode = Int(keyCodeText),
              let modifierText = parts["mods"]
        else { return nil }
        let modifiers = modifierText.split(separator: "+").map(String.init)
        guard registeredSpec(keyCode: keyCode, modifiers: modifiers) == spec else {
            return nil
        }
        return (keyCode, modifiers)
    }

    static func isSupported(_ spec: String) -> Bool {
        modifierOnlySpecs.contains(spec) || parseRegisteredSpec(spec) != nil
    }

    static func backend(for spec: String) -> String {
        parseRegisteredSpec(spec) == nil ? "passive" : "registered"
    }
}

enum ModifierCaptureDecision: Equatable {
    case waiting
    case singleModifier(Int)
    case incompleteChord
}

struct ModifierCaptureAccumulator {
    private var pressedKeyCodes: Set<Int> = []
    private var firstKeyCode: Int?
    private var sawMultipleModifiers = false

    mutating func modifierChanged(
        keyCode: Int,
        aggregateFlagIsSet: Bool
    ) -> ModifierCaptureDecision {
        if aggregateFlagIsSet && !pressedKeyCodes.contains(keyCode) {
            pressedKeyCodes.insert(keyCode)
            if firstKeyCode == nil { firstKeyCode = keyCode }
            if pressedKeyCodes.count > 1 { sawMultipleModifiers = true }
            return .waiting
        }

        if pressedKeyCodes.contains(keyCode) {
            pressedKeyCodes.remove(keyCode)
        }
        guard pressedKeyCodes.isEmpty else { return .waiting }

        defer { reset() }
        guard let firstKeyCode else { return .waiting }
        return sawMultipleModifiers
            ? .incompleteChord
            : .singleModifier(firstKeyCode)
    }

    mutating func reset() {
        pressedKeyCodes.removeAll()
        firstKeyCode = nil
        sawMultipleModifiers = false
    }
}

enum SettingsEnvironment {
    static func read(_ url: URL) -> [String: String] {
        guard let text = try? String(contentsOf: url, encoding: .utf8) else { return [:] }
        var result: [String: String] = [:]
        for rawLine in text.split(separator: "\n", omittingEmptySubsequences: false) {
            let line = String(rawLine)
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard !trimmed.hasPrefix("#"), let equal = line.firstIndex(of: "=") else {
                continue
            }
            let key = line[..<equal].trimmingCharacters(in: .whitespaces)
            result[key] = String(line[line.index(after: equal)...])
        }
        return result
    }

    static func update(_ url: URL, updates: [String: String]) throws {
        let existing = (try? String(contentsOf: url, encoding: .utf8)) ?? ""
        var pending = updates
        var lines: [String] = []
        for line in existing.split(
            separator: "\n", omittingEmptySubsequences: false
        ).map(String.init) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if !trimmed.hasPrefix("#"), let equal = line.firstIndex(of: "=") {
                let key = line[..<equal].trimmingCharacters(in: .whitespaces)
                if let value = pending.removeValue(forKey: key) {
                    lines.append("\(key)=\(value)")
                    continue
                }
            }
            lines.append(line)
        }
        if lines.last != "" { lines.append("") }
        for key in pending.keys.sorted() { lines.append("\(key)=\(pending[key]!)") }
        try privateWrite(Data((lines.joined(separator: "\n") + "\n").utf8), to: url)
    }

    static func privateWrite(_ data: Data, to url: URL) throws {
        try FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        try data.write(to: url, options: .atomic)
        try FileManager.default.setAttributes(
            [.posixPermissions: 0o600], ofItemAtPath: url.path
        )
    }
}
