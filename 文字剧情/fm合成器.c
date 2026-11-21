// ============================================================================
// 两 OP FM（相位调制）合成器 —— 备用实现，先以独立文件存放
//
// 为什么有这份文件：
//   渲染库的 合成器 是"加法叠加"（几路一起响），没有"谁调制谁"，所以做不出
//   非谐波（金属、玻璃、水滴）。官方桥里也没有 FM。本文件是把 FM 作为
//   "往桥里加一个函数"的正式草案：现在独立存着，将来要接进库时按末尾三步粘贴。
//
// 两条边界（别走偏）：
//   1. 这份代码是**库的 C 层**的草案，不是玄铁侧的东西。音频的采样循环本来就
//      在 渲染桥.c 里（整段预渲染 PCM → raylib Sound），玄铁那层只有参数壳。
//   2. 90 毫秒这样的短音在玄铁里逐样本算其实可行（实测 1984 样本约 1~2 ms），
//      但库里已有 ADSR/EQ/延迟/混响 全在 C 侧，重写一遍是纯重复劳动。
//      浮点每轮 709 字节的分配增长见 docs/玄铁缺陷-浮点逐样本运算内存暴涨.md，
//      它只让"长音频"不划算，不构成"短音不能做"。
//
// 独立用法（不接库，直接出 wav）：
//   cc -O2 -o fm fm合成器.c -lm
//   ./fm 22050 滴.wav 1200 1.41 2.5 90 30 0.5 40
//   ./fm 48000 钟.wav 440 2.76 3.0 420 160 0.45 120 2    # 末位参数：载波波形 2=锯齿
//
// 参数含义（与 文字剧情/生成音效.py 完全一致，便于互相对照）：
//   载波 音高（赫兹）  比 调制频率÷载波（整数=谐音；1.41/2.76 这类=非谐，金属感）
//   指数 调制深度（0=纯正弦；2~4 亮；6 以上容易糊）  毫秒 时长  衰减 指数衰减毫秒
//   音量 0~1  淡出 末尾线性淡出毫秒（不加会在结尾硬切）
// ============================================================================
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

// 波形码与渲染库一致：0 正弦 / 1 三角 / 2 锯齿 / 3 方波
// （库还有 4 白噪，但白噪当调制器没有意义——噪声相位调制只会随机化，不产生谐波结构）
static double 波形采样(int 波形, double 相位) {
    switch (波形) {
        case 1: {                          // 三角
            double s = sin(相位);
            double t = asin(s) * 2.0 / 3.14159265358979323846;
            return t;
        }
        case 2: {                          // 锯齿（-1..1）
            double x = 相位 / 6.283185307179586;
            x = x - floor(x + 0.5);
            return 2.0 * x;
        }
        case 3:                            // 方波
            return sin(相位) >= 0.0 ? 1.0 : -1.0;
        default:                           // 正弦
            return sin(相位);
    }
}

// 核心：把 毫秒 长度的两 OP FM 算进 输出（单声道 16 位）。
// 返回实际写入的样本数；缓冲区不够时返回 -1。
//
// 接进桥时，这个函数可以**整段**复制过去（它不依赖 raylib，只用 math.h）。
int XT_FM_渲染(int 采样率,
               double 载波, double 比, double 指数, int 载波波形, int 调制波形,
               double 毫秒, double 衰减, double 音量, double 淡出,
               short* 输出, int 最大样本) {
    if (采样率 <= 0 || 毫秒 <= 0.0 || 输出 == 0) return -1;
    double n_d = (double)采样率 * 毫秒 / 1000.0;
    int n = (int)n_d;
    if (n < 1) n = 1;
    if (n > 最大样本) return -1;

    int 淡出n = (int)((double)采样率 * 淡出 / 1000.0);
    if (淡出n < 1) 淡出n = 1;
    if (淡出n > n) 淡出n = n;

    const double 两派 = 6.283185307179586;
    const double 调制角频 = 两派 * 载波 * 比;
    const double 载波角频 = 两派 * 载波;

    for (int i = 0; i < n; i++) {
        double t = (double)i / (double)采样率;
        // 相位调制：调制器的输出直接加在载波的相位上
        double 调制 = 波形采样(调制波形, 调制角频 * t);
        double v = 波形采样(载波波形, 载波角频 * t + 指数 * 调制);
        double env = (衰减 > 0.0) ? exp(-t * 1000.0 / 衰减) : 1.0;
        if (i > n - 淡出n) env *= (double)(n - i) / (double)淡出n;
        double s = v * env * 音量 * 32767.0;
        if (s > 32767.0) s = 32767.0;
        if (s < -32768.0) s = -32768.0;
        输出[i] = (short)s;
    }
    return n;
}

// 标准 44 字节 WAV（fmt 块里压缩方式/声道/块对齐/位深各 2 字节，不能拿 4 字节整数糊过去）
static int 写wav(const char* 路径, const short* pcm, int n, int 采样率) {
    FILE* f = fopen(路径, "wb");
    if (!f) return -1;
    uint32_t 数据字节 = (uint32_t)n * 2;
    uint32_t 标记;
    标记 = 0x46464952; fwrite(&标记, 4, 1, f);            // "RIFF"
    标记 = 36 + 数据字节; fwrite(&标记, 4, 1, f);
    标记 = 0x45564157; fwrite(&标记, 4, 1, f);            // "WAVE"
    标记 = 0x20746d66; fwrite(&标记, 4, 1, f);            // "fmt "
    标记 = 16;         fwrite(&标记, 4, 1, f);
    uint16_t 短片;
    短片 = 1; fwrite(&短片, 2, 1, f);                     // PCM
    短片 = 1; fwrite(&短片, 2, 1, f);                     // 单声道
    标记 = (uint32_t)采样率; fwrite(&标记, 4, 1, f);
    标记 = (uint32_t)采样率 * 2; fwrite(&标记, 4, 1, f);
    短片 = 2;  fwrite(&短片, 2, 1, f);
    短片 = 16; fwrite(&短片, 2, 1, f);                    // 16 位
    标记 = 0x61746164; fwrite(&标记, 4, 1, f);            // "data"
    fwrite(&数据字节, 4, 1, f);
    fwrite(pcm, 2, (size_t)n, f);
    fclose(f);
    return 0;
}

// 定义 XT_无主函数 可把 main 摘掉，便于整文件被桥 include 或链接
#ifndef XT_无主函数
int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr,
                "用法: %s <采样率> <输出.wav> [载波 比 指数 毫秒 衰减 音量 淡出 载波波形 调制波形]\n"
                "  例: %s 22050 滴.wav 1200 1.41 2.5 90 30 0.5 40\n"
                "  例: %s 48000 钟.wav 440 2.76 3.0 420 160 0.45 120 2 0\n",
                argv[0], argv[0], argv[0]);
        return 1;
    }
    int 采样率 = atoi(argv[1]);
    double 载波   = argc > 3 ? atof(argv[3]) : 1200.0;
    double 比     = argc > 4 ? atof(argv[4]) : 1.41;
    double 指数   = argc > 5 ? atof(argv[5]) : 2.5;
    double 毫秒   = argc > 6 ? atof(argv[6]) : 90.0;
    double 衰减   = argc > 7 ? atof(argv[7]) : 30.0;
    double 音量   = argc > 8 ? atof(argv[8]) : 0.5;
    double 淡出   = argc > 9 ? atof(argv[9]) : 40.0;
    int 载波波形  = argc > 10 ? atoi(argv[10]) : 0;
    int 调制波形  = argc > 11 ? atoi(argv[11]) : 0;

    int 上限 = (int)((double)采样率 * (毫秒 + 1.0) / 1000.0) + 8;
    short* pcm = (short*)calloc((size_t)上限, sizeof(short));
    if (!pcm) { fprintf(stderr, "内存不足\n"); return 1; }
    int n = XT_FM_渲染(采样率, 载波, 比, 指数, 载波波形, 调制波形,
                       毫秒, 衰减, 音量, 淡出, pcm, 上限);
    if (n < 0) { fprintf(stderr, "渲染失败\n"); free(pcm); return 1; }
    if (写wav(argv[2], pcm, n, 采样率) != 0) { fprintf(stderr, "写盘失败\n"); free(pcm); return 1; }
    printf("%s  采样率=%d  样本=%d  %d 字节\n", argv[2], 采样率, n, n * 2);
    free(pcm);
    return 0;
}
#endif

// ============================================================================
// 将来接进渲染库的三步（现在不做，因为要改包或改构建链，先只存代码）
//
// 1) 把上面的 波形采样 + XT_FM_渲染 **整段** 复制进 渲染桥.c（它只用 math.h，
//    与库现有的 xt_osc_sample 不冲突）。若要复用库的波形实现，可把
//    波形采样(...) 换成 xt_osc_sample(波形, 相位, 1.0) 系列，二选一。
//
// 2) 在桥里加一个句柄包装（结构照抄 XT_SynthSoundMulti 的开头/结尾）：
//      uintptr_t XT_SynthSoundFM(uintptr_t freq_hz, uintptr_t ms, uintptr_t 载波波形,
//                                uintptr_t 调制波形, uintptr_t 比, uintptr_t 指数, ...)
//      {
//          int slot = xt_snd_alloc();  if (slot < 0) return XT_FROM_INT(0);
//          short* pcm = malloc(...);
//          XT_FM_渲染(22050, 载波, 比, 指数, 载波波形, 调制波形, 毫秒, 衰减, 音量, 淡出, pcm, 上限);
//          Wave w = { .frameCount = n, .sampleRate = 22050, .sampleSize = 16, .channels = 1, .data = pcm };
//          Sound s = LoadSoundFromWave(w);  UnloadWave(w);
//          xt_snd_set(slot, s);  return XT_FROM_INT(slot + 1);
//      }
//    注意：库的采样率固定 22050，且音频"整段预渲染"，没有流式回调。
//
// 3) 在 渲染.xt 里加两行：一条 外 函 XT_SynthSoundFM(...): 整，一个 公 函
//    合成FM(频率, 毫秒, 选项) 壳（选项键沿用 合成器 的词表，另加
//    调制: { 比, 指数, 波形 }），然后剧情 JSON 就能直接写 FM，不需要 wav 文件。
//
// 已知限制：22050 采样率下，当 载波×比×(指数+1) 超过约 11 kHz 就会混叠成毛刺；
// 短音效（几十~几百毫秒）通常够用，长铃音会糊。真要高保真得让库支持更高采样率。
// ============================================================================
