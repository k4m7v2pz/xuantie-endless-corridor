# 造图.py —— 把「房间意图」翻成完整地图 JSON，并做结构校验
#
# 用法（在项目根目录）：
#   python3 原型/造图.py 原型/房稿03.json      # 生成/覆盖 原型/地图03.json
#   python3 原型/造图.py --校验 原型/地图01.json ...   # 只检查现有图
#
# 意图稿只要写「几格宽、几格高、起点、门往哪张图通、柜子箱子放哪」，墙与地砖的
# 行字符串由脚本算出来。物件的「高」和「可走」一律查 原型/种类.json，不在地图里
# 各写一遍 —— 碰撞与绘制共用同一份种类表，换美术不会动到逻辑。
import json
import sys
from pathlib import Path

根 = Path(__file__).resolve().parent
图目录 = 根
种类路径 = 图目录 / "种类.json"


def 读(路径):
    return json.loads(Path(路径).read_text(encoding="utf-8"))


def 种类():
    return 读(种类路径)


def 可走吗(种, 字):
    类 = 种.get(字)
    return bool(类 and 类.get("可走"))


def 件高(种, 图名):
    类 = 种.get(图名) or {}
    return int(类.get("高", 1))


def 全地图():
    """地图集：目录里所有 地图NN.json，按名字排序。"""
    return sorted(str(p.relative_to(根.parent)) for p in 图目录.glob("地图*.json"))


def 造(稿):
    宽, 高 = int(稿["宽"]), int(稿["高"])
    障碍 = {(int(格["x"]), int(格["y"])) for 格 in 稿.get("墙", [])}

    行 = []
    for 纵 in range(高):
        if 纵 == 0 or 纵 == 高 - 1:
            行.append("#" * 宽)
            continue
        行.append("".join(
            "#" if (横 == 0 or 横 == 宽 - 1 or (横, 纵) in 障碍) else "."
            for 横 in range(宽)
        ))

    物件 = [{
        "图": 件["图"],
        "x": int(件["x"]),
        "y": int(件["y"]),
        "描述": 件["描述"],
    } for 件 in 稿.get("物件", [])]

    # 门对门：稿里只写「到门」——落点就是对方那扇门自己的格子，脚本替人算 到x/到y。
    # 剧情传送（出门后在山洞醒来那种）不对称，必须显式写 到x/到y 与 "类型":"剧情"，
    # 否则脚本当作写漏了，直接报错。
    传送 = []
    for 条 in 稿.get("传送", []):
        项 = {"x": int(条["x"]), "y": int(条["y"]), "到图": 条["到图"]}
        门 = 条.get("到门")
        if 门 is not None:
            项["到门"] = {"x": int(门["x"]), "y": int(门["y"])}
            项["到x"] = int(门["x"])
            项["到y"] = int(门["y"])
        elif 条.get("类型") == "剧情":
            项["类型"] = "剧情"
            项["到x"] = int(条["到x"])
            项["到y"] = int(条["到y"])
        else:
            raise SystemExit(
                f"传送点 ({项['x']},{项['y']}) 没写「到门」也没标「类型: 剧情」："
                "两个房间互通请写 到门，剧情单向才写 到x/到y + 类型"
            )
        传送.append(项)

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
    种 = 种类()
    错 = []
    宽, 高 = 图["宽"], 图["高"]
    行 = 图["行"]

    if len(行) != 高:
        错.append(f"行数 {len(行)} 与 高 {高} 不符")
    for 号, 串 in enumerate(行):
        if len(串) != 宽:
            错.append(f"第 {号} 行宽度 {len(串)} 与 宽 {宽} 不符")
        for 字 in set(串):
            if 字 not in 种:
                错.append(f"第 {号} 行有种类表里没有的字『{字}』")
    行检查(行, 高, 错)
    for 纵 in range(1, 高 - 1):
        if 行[纵][0] != "#" or 行[纵][-1] != "#":
            错.append(f"第 {纵} 行左右边界不是墙")

    可走 = {(横, 纵) for 纵 in range(高) for 横 in range(宽)
            if 可走吗(种, 行[纵][横])}

    起 = (图["起点"]["x"], 图["起点"]["y"])
    if 起 not in 可走:
        错.append(f"起点 {起} 不是可走地板")

    挡 = set()
    for 件 in 图["物件"]:
        脚 = (件["x"], 件["y"])
        高件 = 件高(种, 件["图"])
        if 件["图"] not in 种:
            错.append(f"物件种类『{件['图']}』不在种类表里")
        if 脚 not in 可走:
            错.append(f"物件『{件['图']}』脚格 {脚} 不是可走地板")
        if 高件 == 2:
            上 = (件["x"], 件["y"] - 1)
            if 上[1] < 0:
                错.append(f"物件『{件['图']}』上半格越界")
            elif 行[上[1]][上[0]] != "#":
                错.append(f"两格高物件『{件['图']}』上半格 {上} 不在墙行，会悬空/穿墙")
        if not 件.get("描述"):
            错.append(f"物件『{件['图']}』{脚} 没有描述")
        挡.add(脚)
        if 高件 == 2:
            挡.add((件["x"], 件["y"] - 1))

    for 条 in 图["传送"]:
        门 = (条["x"], 条["y"])
        if 门 not in 可走:
            错.append(f"传送点 {门} 不是可走地板")
        if 门 == 起:
            错.append(f"传送点 {门} 与起点重合")
        if int(条["到x"]) < 0 or int(条["到y"]) < 0:
            错.append(f"传送点 {门} 的落点坐标为负")

    # 连通性：从起点走得到的地方，必须能走到每一个传送点（物件两格都算障碍）
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


def 行检查(行, 高, 错):
    for 纵 in (0, 高 - 1):
        if set(行[纵]) != {"#"}:
            错.append(f"第 {纵} 行不是整行墙")


def 落点(条):
    """落点以 到门 优先：门对门时 到x/到y 只是它的副本，人只看一处。"""
    门 = 条.get("到门")
    if 门:
        return int(门["x"]), int(门["y"])
    return int(条.get("到x", -1)), int(条.get("到y", -1))


def 查门(文件们):
    """门的关系校验。互通门必须对偶；剧情单向门只提示不拦（不对称是它存在的理由）。"""
    名册 = {}
    for 路径 in 文件们:
        名册[str(Path(路径).resolve())] = 读(路径)
    错, 告 = [], []
    if len(名册) < 2:
        return 错, 告
    for 路, 图 in 名册.items():
        名 = Path(路).name
        for 条 in 图.get("传送", []):
            到路 = (根.parent / 条["到图"]).resolve()
            门 = (int(条["x"]), int(条["y"]))
            if str(到路) not in 名册:
                if Path(到路).exists():
                    告.append(f"{名} 的门 {门} 指向 {条['到图']}，那张图这次没一起校验，跳过")
                else:
                    错.append(f"{名} 的门 {门} 指向不存在的图 {条['到图']}")
                continue
            到图 = 名册[str(到路)]
            落 = 落点(条)

            if 条.get("类型") == "剧情":
                告.append(f"{名} 的门 {门} → {Path(到路).name}{落}：剧情单向传送，不做对偶校验")
                continue

            if "到门" not in 条:
                错.append(f"{名} 的门 {门} → {Path(到路).name} 缺「到门」：互通门必须指明对方门格")
                continue
            同格门 = [t for t in 到图.get("传送", [])
                      if (int(t["x"]), int(t["y"])) == 落]
            if not 同格门:
                错.append(f"{名} 的门 {门} → {Path(到路).name}{落}：那格不是门，门对门要求落点就是对方的门")
                continue
            回门 = 同格门[0]
            if 回门.get("类型") == "剧情":
                错.append(f"{Path(到路).name} 的门 {落} 标了剧情单向，却被 {名} 的门 {门} 当成互通目标")
            elif 落点(回门) != 门:
                错.append(f"{名} 的门 {门} 与 {Path(到路).name} 的门 {落} 不对偶（那边回落到 {落点(回门)}）")
    return 错, 告


def 规整(文件们):
    """把每扇互通门的 到x/到y 按 到门 重算，人不写副本、不抄坐标。"""
    改动 = []
    for 路径 in 文件们:
        图 = 读(路径)
        变 = False
        for 条 in 图.get("传送", []):
            门 = 条.get("到门")
            if not 门:
                continue
            if (条.get("到x"), 条.get("到y")) != (门["x"], 门["y"]):
                改动.append(
                    f"{Path(路径).name} 门 ({条['x']},{条['y']}) 落点 "
                    f"({条.get('到x')},{条.get('到y')}) → ({门['x']},{门['y']})"
                )
                条["到x"], 条["到y"] = int(门["x"]), int(门["y"])
                变 = True
        if 变:
            Path(路径).write_text(json.dumps(图, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 改动


def main(参):
    if not 参:
        raise SystemExit("用法：造图.py <房稿.json> | --校验 <地图.json>...")

    if 参[0] in ("--规整", "-n"):
        for 行 in 规整(参[1:]):
            print(f"· {行}")
        print("✅ 规整完成：落点已按「到门」重算")
        门错, 门告 = 查门(参[1:])
        for 行 in 门告:
            print(f"⚠ {行}")
        if 门错:
            raise SystemExit("【门】校验失败：\n  - " + "\n  - ".join(门错))
        return

    if 参[0] in ("--校验", "-c"):
        for 路径 in 参[1:]:
            图 = 读(路径)
            地格, 物件数, 门数 = 查(图, Path(路径).name)
            print(f"✅ {Path(路径).name}: 可走 {地格} 格 / 物件 {物件数} / 门 {门数}")
        门错, 门告 = 查门(参[1:])
        for 行 in 门告:
            print(f"⚠ {行}")
        if 门错:
            raise SystemExit("【门】校验失败：\n  - " + "\n  - ".join(门错))
        print("✅ 门：全部对偶（落点即对方门格）")
        return

    稿路径 = 参[0]
    稿 = 读(稿路径)
    图 = 造(稿)
    地格, 物件数, 门数 = 查(图, 稿.get("名", Path(稿路径).stem))
    出 = 图目录 / (稿.get("名", Path(稿路径).stem) + ".json")
    出.write_text(json.dumps(图, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ 已生成 {出.name}: 可走 {地格} 格 / 物件 {物件数} / 门 {门数}")
    print(f"   地图集: {' '.join(Path(p).name for p in 图['地图集'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
