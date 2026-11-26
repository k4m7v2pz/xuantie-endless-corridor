import CoreGraphics
// 列出窗口号与逻辑坐标边界，供 scripts/截窗口.sh 取"指定进程的窗口"
let 参数 = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : ""
let 表 = CGWindowListCopyWindowInfo([.optionOnScreenOnly], kCGNullWindowID) as! [[String: Any]]
for 窗 in 表 {
    let 主 = 窗[kCGWindowOwnerName as String] as? String ?? ""
    let 题 = 窗[kCGWindowName as String] as? String ?? ""
    if 参数.isEmpty || 主.contains(参数) || 题.contains(参数) {
        let 界 = 窗[kCGWindowBounds as String] as! [String: Any]
        let 号 = 窗[kCGWindowNumber as String] as! Int
        print("\(号) \(界["X"]!) \(界["Y"]!) \(界["Width"]!) \(界["Height"]!) \(主) \(题)")
    }
}
