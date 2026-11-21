#!/usr/bin/env python3
"""按 FM 参数生成音效 WAV（全部由参数合成，不带任何外部素材）。

玄铁侧没有 FM：渲染库的 合成器 只能叠 4 个振荡器，运行时逐样本算 PCM 太慢
（实测几十毫秒的音频要跑几分钟并把内存吃爆）。所以 FM 放在这里生成成 wav，
播放器只用 渲染.加载音效(文件) 播。

用法:
    python3 生成音效.py <输出目录> [音效表.json]
    例: python3 文字剧情/生成音效.py 文字剧情/我还会回来/音效

音效表格式（每条一个音，键名即输出文件名）:
    "滴": { "载波": 1200, "比": 1.41, "指数": 2.5,
            "毫秒": 90, "衰减": 30, "音量": 0.5, "淡出": 30 }

参数含义（给写剧情的人/AI）:
    载波  音高（赫兹）。低频 50~150 像电机/闷响，1000~2000 像金属小件。
    比    调制频率 ÷ 载波。整数（1/2/3）= 和谐、像乐器；
          非整数（1.41/2.76/3.71）= 非谐、金属或说不清的东西。
    指数  调制深度。0 = 纯正弦（干净），2~4 = 亮、金属感强，6 以上容易糊成噪音。
    毫秒  时长。90~300 是"敲一下"，1000 以上是持续嗡鸣。
    衰减  指数衰减时间常数（毫秒）。小 = 干脆，大 = 拖尾长。
    音量  0~1。
    淡出  末尾线性淡出的毫秒数，默认 30。不加会在结尾硬切（"钟声突然被截断"）。

这些音都是自己算出来的，没有版权问题，可以随仓库分发。
"""
import json
import math
import struct
import sys
import wave
from pathlib import Path

RATE = 48000


def render(载波, 比, 指数, 毫秒, 衰减, 音量, 淡出=30):
    n = int(RATE * 毫秒 / 1000)
    fade_n = max(1, int(RATE * 淡出 / 1000))
    if fade_n > n:
        fade_n = n
    frames = bytearray()
    for i in range(n):
        t = i / RATE
        v = math.sin(2 * math.pi * 载波 * t + 指数 * math.sin(2 * math.pi * 载波 * 比 * t))
        env = math.exp(-t * 1000 / 衰减) if 衰减 and 衰减 > 0 else 1.0
        if i > n - fade_n:
            env *= (n - i) / fade_n
        s = int(v * env * 音量 * 32767)
        frames += struct.pack('<h', max(-32768, min(32767, s)))
    return bytes(frames)


def main():
    输出目录 = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    表路径 = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name('音效表.json')
    输出目录.mkdir(parents=True, exist_ok=True)
    表 = json.loads(表路径.read_text(encoding='utf-8'))
    for 名, 参 in 表.items():
        数据 = render(
            参['载波'], 参['比'], 参['指数'],
            参['毫秒'], 参['衰减'], 参['音量'], 参.get('淡出', 30),
        )
        路径 = 输出目录 / (名 + '.wav')
        with wave.open(str(路径), 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(数据)
        print(f'{路径}  {len(数据)} 字节')


if __name__ == '__main__':
    main()
