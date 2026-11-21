#!/usr/bin/env python3
"""文字剧情结构校验（纯标准库，不依赖 jsonschema）。

用法：
    python3 文字剧情/校验剧情.py 文字剧情/我还会回来
    python3 文字剧情/校验剧情.py 文字剧情/恐哀

检查两件事：
1. 字段类型与必填（对照 剧情.schema.json 的硬约束）；
2. 引用完整性 —— 起始/后继/选项·到/谜题·对/错/变体·对/调查·出口/按件数·到
   指向的节点必须真的存在（"后继": null 与空串表示本幕结束）。
"""

import json
import os
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def walk_nodes(events):
    for name, node in events.items():
        yield name, node


def check(directory):
    errors = []
    story_dir = os.path.dirname(directory.rstrip("/")) or "."
    toc_path = os.path.join(directory, "剧情/目录.json")
    if not os.path.exists(toc_path):
        return [f"找不到 {toc_path}"]

    toc = load(toc_path)
    if not isinstance(toc.get("作品"), str) or not toc["作品"]:
        errors.append("目录.json: 作品 必须是非空字符串")
    acts = toc.get("幕")
    if not isinstance(acts, list) or not acts:
        return errors + ["目录.json: 幕 必须是非空数组"]

    for act_rel in acts:
        act_path = os.path.join(directory, act_rel)
        if not os.path.exists(act_path):
            errors.append(f"目录.json: 幕文件不存在 {act_rel}")
            continue
        act = load(act_path)
        rel = act_rel

        for key, typ in (("幕编号", int), ("幕名", str), ("起始", str)):
            if not isinstance(act.get(key), typ):
                errors.append(f"{rel}: {key} 缺失或类型不对")
        events = act.get("事件")
        if not isinstance(events, dict) or not events:
            errors.append(f"{rel}: 事件 必须是非空对象")
            continue

        target_keys = ("起始",)

        if act.get("起始") not in events:
            errors.append(f"{rel}: 起始「{act.get('起始')}」不存在")

        for name, node in walk_nodes(events):
            where = f"{rel}:{name}"
            if not isinstance(node.get("标题"), str) or not node["标题"]:
                errors.append(f"{where}: 标题 缺失")
            body = node.get("正文")
            if not isinstance(body, list) or not all(isinstance(x, str) for x in body):
                errors.append(f"{where}: 正文 必须是字符串数组")
            if node.get("红字") is not None and not (
                isinstance(node["红字"], list) and all(isinstance(x, str) for x in node["红字"])
            ):
                errors.append(f"{where}: 红字 必须是字符串数组")

            # 后继
            if "后继" in node:
                nxt = node["后继"]
                if nxt is not None and not isinstance(nxt, str):
                    errors.append(f"{where}: 后继 必须是字符串或 null")
                elif nxt not in (None, "") and nxt not in events:
                    errors.append(f"{where}: 后继「{nxt}」不存在")

            # 选项
            if node.get("选项") is not None:
                opts = node["选项"]
                if not isinstance(opts, list) or not opts:
                    errors.append(f"{where}: 选项 必须是非空数组")
                else:
                    for i, o in enumerate(opts, 1):
                        if not isinstance(o.get("文字"), str) or not o["文字"]:
                            errors.append(f"{where}: 选项 {i} 缺 文字")
                        if o.get("到") not in events:
                            errors.append(f"{where}: 选项 {i} 的 到「{o.get('到')}」不存在")

            # 谜题
            if node.get("谜题") is not None:
                q = node["谜题"]
                for k in ("提示", "对白", "对", "错白", "错"):
                    if not isinstance(q.get(k), str):
                        errors.append(f"{where}: 谜题缺 {k}")
                for k in ("对", "错"):
                    if q.get(k) not in events:
                        errors.append(f"{where}: 谜题的 {k}→「{q.get(k)}」不存在")
                for i, v in enumerate(q.get("变体") or [], 1):
                    if not isinstance(v.get("接受"), list) or not v["接受"]:
                        errors.append(f"{where}: 变体 {i} 缺 接受")
                    if v.get("对") not in events:
                        errors.append(f"{where}: 变体 {i} 的 对「{v.get('对')}」不存在")

            # 调查
            if node.get("调查") is not None:
                s = node["调查"]
                if s.get("出口") not in events:
                    errors.append(f"{where}: 调查 出口「{s.get('出口')}」不存在")
                objs = s.get("对象")
                if not isinstance(objs, list) or not objs:
                    errors.append(f"{where}: 调查 对象 必须是非空数组")
                else:
                    for i, o in enumerate(objs, 1):
                        if not isinstance(o.get("名"), str) or not o["名"]:
                            errors.append(f"{where}: 调查对象 {i} 缺 名")
                        if not isinstance(o.get("话"), str):
                            errors.append(f"{where}: 调查对象 {i} 缺 话")
                        if "给" in o and o["给"] is not None and not isinstance(o["给"], str):
                            errors.append(f"{where}: 调查对象 {i} 的 给 必须是字符串或 null")
                for i, r in enumerate(s.get("按件数") or [], 1):
                    if not isinstance(r.get("件数"), int) or r["件数"] < 1:
                        errors.append(f"{where}: 按件数 {i} 的 件数 必须是正整数")
                    if r.get("到") not in events:
                        errors.append(f"{where}: 按件数 {i} 的 到「{r.get('到')}」不存在")

            # 注：只允许对象，内容自由
            if "注" in node and not isinstance(node["注"], dict):
                errors.append(f"{where}: 注 必须是对象")

        del target_keys

    return errors


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    failed = False
    for d in sys.argv[1:]:
        errs = check(d)
        if errs:
            failed = True
            print(f"✗ {d} —— {len(errs)} 个问题")
            for e in errs:
                print("   " + e)
        else:
            print(f"✓ {d} —— 结构通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
