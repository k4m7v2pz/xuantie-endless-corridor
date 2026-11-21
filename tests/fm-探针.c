// 两 OP FM（相位调制）探针：验证把 python 版公式搬进 C 后是否等价，
// 并对比库版采样率（22050）与 python 版（48000）的听感差异。
//
// 编译: cc -O2 -o fm-probe fm-探针.c -lm
// 用法: ./fm-probe <采样率> <输出.wav> [载波 比 指数 毫秒 衰减 音量 淡出]
//
// 公式与 文字剧情/生成音效.py 完全一致（同一参数应生成同一段波形）：
//   v   = sin(2π·载波·t + 指数·sin(2π·载波·比·t))
//   env = exp(-t·1000/衰减)，末尾 淡出 毫秒线性淡出
//
// 唯一差别是采样率：python 版 48000，渲染库内部固定 22050。
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// 标准 44 字节头（字段宽度必须按规范逐段写：fmt 块里压缩方式/声道各 2 字节，
// 块对齐/位深各 2 字节，不能拿 4 字节整数糊过去）
static void 写wav(const char* 路径, const short* pcm, int n, int rate) {
    FILE* f = fopen(路径, "wb");
    if (!f) { fprintf(stderr, "打不开 %s\n", 路径); exit(1); }
    uint32_t 数据字节 = (uint32_t)n * 2;
    uint32_t 标记;
    标记 = 0x46464952; fwrite(&标记, 4, 1, f);             // "RIFF"
    标记 = 36 + 数据字节; fwrite(&标记, 4, 1, f);          // 块大小
    标记 = 0x45564157; fwrite(&标记, 4, 1, f);             // "WAVE"
    标记 = 0x20746d66; fwrite(&标记, 4, 1, f);             // "fmt "
    标记 = 16;         fwrite(&标记, 4, 1, f);
    uint16_t 短片;
    短片 = 1; fwrite(&短片, 2, 1, f);                      // 压缩方式：PCM
    短片 = 1; fwrite(&短片, 2, 1, f);                      // 声道数
    标记 = (uint32_t)rate; fwrite(&标记, 4, 1, f);
    标记 = (uint32_t)rate * 2; fwrite(&标记, 4, 1, f);
    短片 = 2;  fwrite(&短片, 2, 1, f);                     // 块对齐
    短片 = 16; fwrite(&短片, 2, 1, f);                     // 位深
    标记 = 0x61746164; fwrite(&标记, 4, 1, f);             // "data"
    fwrite(&数据字节, 4, 1, f);
    fwrite(pcm, 2, (size_t)n, f);
    fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "用法: %s <采样率> <输出.wav> [载波 比 指数 毫秒 衰减 音量 淡出]\n", argv[0]);
        return 1;
    }
    int rate = atoi(argv[1]);
    double 载波  = argc > 3 ? atof(argv[3]) : 1200.0;
    double 比    = argc > 4 ? atof(argv[4]) : 1.41;
    double 指数  = argc > 5 ? atof(argv[5]) : 2.5;
    double 毫秒  = argc > 6 ? atof(argv[6]) : 90.0;
    double 衰减  = argc > 7 ? atof(argv[7]) : 30.0;
    double 音量  = argc > 8 ? atof(argv[8]) : 0.5;
    double 淡出  = argc > 9 ? atof(argv[9]) : 40.0;

    int n = (int)((double)rate * 毫秒 / 1000.0);
    if (n < 1) n = 1;
    int 淡出n = (int)((double)rate * 淡出 / 1000.0);
    if (淡出n < 1) 淡出n = 1;
    if (淡出n > n) 淡出n = n;

    short* pcm = (short*)calloc((size_t)n, sizeof(short));
    const double 两派 = 6.283185307179586;
    for (int i = 0; i < n; i++) {
        double t = (double)i / (double)rate;
        double v = sin(两派 * 载波 * t + 指数 * sin(两派 * 载波 * 比 * t));
        double env = (衰减 > 0.0) ? exp(-t * 1000.0 / 衰减) : 1.0;
        if (i > n - 淡出n) env *= (double)(n - i) / (double)淡出n;
        double s = v * env * 音量 * 32767.0;
        if (s > 32767.0) s = 32767.0;
        if (s < -32768.0) s = -32768.0;
        pcm[i] = (short)(s);
    }
    写wav(argv[2], pcm, n, rate);
    printf("%s  采样率=%d  样本=%d  %d 字节\n", argv[2], rate, n, n * 2);
    free(pcm);
    return 0;
}
