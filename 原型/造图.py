# 造图.py —— 把「房间意图」翻成完整地图 JSON，并做结构校验
#
# 用法（在项目根目录）：
#   python3 原型/造图.py 原型/房稿03.json      # 生成/覆盖 原型/地图03.json
#   python3 原型/造图.py --校验 原型/地图01.json 原型/地图02.json   # 只检查现有图
#
# 意图稿只要写「几格宽、几格高、起点、门往哪张图通、柜子箱子放哪」，墙和地砖的行
# 字符串由脚本算出来。这样大模型只出少量有意义的坐标，手不用去数 16 个 # 号。
import json
import sys
from pathlib import Path

根 = Path(__file__).resolve().parent
图目录 = 根


def 读(路径):
    return json.loads(Path(路径).read_text(encoding="utf-8"))


def 全地图():
    """地图集：目录里所有 地图NN.json，按名字排序。"""
    return sorted(str(p.relative_to(根.parent)) for p in 图目录.glob("地图*.json"))


def 造(稿, 稿路径):
    宽 = int(稿["宽"])
    高 = int(稿["高"])
    障碍 = {}
    for 格 in 稿.get("墙", []):
        障碍[(int(格["x"]), int(格["y"]))] = "#"

    行 = []
    for 纵 in range(高):
        if 纵 == 0 or 纵 == 高 - 1:
            行.append("#" * 宽)
            continue
        行.append("".join(
            "#" if (横 == 0 or 横 == 宽 - 1 or 障碍.get((横, 纵)) == "#") else "."
            for 横 in range(宽)
        ))

    物件 = []
    for 件 in 稿.get("物件", []):
        物件.append({
            "图": 件["图"],
            "x": int(件["x"]),
            "y": int(件["y"]),
            "高": int(件.get("高", 1)),
            "描述": 件["描述"],
        })

    传送 = []
    for 条 in 稿.get("传送", []):
        传送.append({
            "x": int(条["x"]),
            "y": int(条["y"]),
            "到图": 条["到图"],
            "到x": int(条["到x"]),
            "到y": int(条["到y"]),
        })

    return {
        "格": int(稿.get("格", 48)),
        "宽": 宽,
        "高": 高,
        "行": 行,
        "物件": 物件,
        "起点": {"x": int(稿["起点"]["x"]), "y": int(稿["起点"]["y"])},
        "传送": 传送,
        "地图集": 全地图(),
    }


def 查(图, 名):
    """结构校验：错就抛，别生成一张走不通的图。"""
    错 = []
    宽, 高 = 图["宽"], 图["高"]
    行 = 图["行"]

    if len(行) != 高:
        错.append(f"行数 {len(行)} 与 高 {高} 不符")
    for 号, 串 in enumerate(行):
        if len(串) != 宽:
            错.append(f"第 {号} 行宽度 {len(串)} 与 宽 {宽} 不符")
    for 纵 in (0, 高 - 1):
        if set(行[纵]) != {"#"}:
            错.append(f"第 {纵} 行不是整行墙")
    for 纵 in range(1, 高 - 1):
        if 行[纵][0] != "#" or 行[纵][-1] != "#":
            错.append(f"第 {纵} 行左右边界不是墙")

    可走 = set()
    for 纵 in range(高):
        for 横 in range(宽):
            if 行[纵][横] == ".":
                可走.add((横, 纵))

    起 = (图["起点"]["x"], 图["起点"]["y"])
    if 起 not in 可走:
        错.append(f"起点 {起} 不是可走地板")

    for 件 in 图["物件"]:
        脚 = (件["x"], 件["y"])
        if 脚 not in 可走:
            错.append(f"物件『{件['图']}』脚格 {脚} 不是可走地板")
        if 件["高"] == 2:
            上 = (件["x"], 件["y"] - 1)
            if 上[1] < 0:
                错.append(f"物件『{件['图']}』上半格越界")
            elif 行[上[1]][上[0]] != "#":
                错.append(f"两格高物件『{件['图']}』上半格 {上} 不在墙行，会悬空/穿墙")
        if not 件.get("描述"):
            错.append(f"物件『{件['图']}』{脚} 没有描述")

    for 条 in 图["传送"]:
        门 = (条["x"], 条["y"])
        if 门 not in 可走:
            错.append(f"传送点 {门} 不是可走地板")
        if 门 == 起:
            错.append(f"传送点 {门} 与起点重合")
        if int(条["到x"]) < 0 or int(条["到y"]) < 0:
            错.append(f"传送点 {门} 的落点坐标为负")

    # 连通性：从起点走得到的地方，必须能走到每一个传送点（物件两格都算障碍）
    挡 = set()
    for 件 in 图["物件"]:
        挡.add((件["x"], 件["y"]))
        if 件["高"] == 2:
            挡.add((件["x"], 件["y"] - 1))
    可达 = {起}
    待走 = [起]
    while 待走:
        横, 纵 = 待走.pop()
        for 邻 in ((横 + 1, 纵), (横 - 1, 纵), (横, 纵 + 1), (横, 纵 - 1)):
            if 邻 in 可走 and 邻 not in 挡 and 邻 not in 可达:
                可达.add(邻)
                待走.append(邻)
    for 条 in 图["传送"]:
        门 = (条["x"], 条["y"])
        if 门 not in 可达:
            错.append(f"传送点 {门} 从起点走不到（被墙或物件挡住）")

    孤儿 = 可走 - 可达 - 挡
    if len(孤儿) > 8:
        错.append(f"有 {len(孤儿)} 格地板从起点走不到，可能是多出来的封闭区")

    if 错:
        raise SystemExit("【" + 名 + "】校验失败：\n  - " + "\n  - ".join(错))
    return len(可走), len(图["物件"]), len(图["传送"])


def main(参):
    if not 参:
        raise SystemExit("用法：造图.py <房稿.json> | --校验 <地图.json>...")

    if 参[0] in ("--校验", "-c"):
        for 路径 in 参[1:]:
            图 = 读(路径)
            地格, 物件数, 门数 = 查(图, Path(路径).name)
            print(f"✅ {Path(路径).name}: 可走 {地格} 格 / 物件 {物件数} / 门 {门数}")
        return

    稿路径 = 参[0]
    稿 = 读(稿路径)
    图 = 造(稿, 稿路径)
    地格, 物件数, 门数 = 查(图, 稿.get("名", Path(稿路径).stem))
    出 = 图目录 / (稿.get("名", Path(稿路径).stem) + ".json")
    出.write_text(json.dumps(图, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ 已生成 {出.name}: 可走 {地格} 格 / 物件 {物件数} / 门 {门数}")
    print(f"   地图集: {' '.join(Path(p).name for p in 图['地图集'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
