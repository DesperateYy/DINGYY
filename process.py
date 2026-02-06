import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.io import loadmat

# ================= 1. 关键物理参数 =================
# ⚠️ 请务必确认这两个参数与你的硬件完全一致，否则角度算不准！
DATA_FILE = "captured_tma_data_2.485ghz40.mat"
ANTENNA_DISTANCE = 0.06  # 天线间距 5cm (根据你上一个脚本的设置)
SWITCHING_FREQ = 10e3  # 调制频率 10kHz

if __name__ == "__main__":
    print(f"--- TMA De-chirp & Angle Estimation (Amplitude Ratio Method) ---")

    # --- 2. 加载数据 ---
    try:
        mat = loadmat(DATA_FILE)
        tma = mat['tma_signal_raw'].flatten()  # RXA
        ref = mat['ref_signal_raw'].flatten()  # RXB

        # 尝试读取频率配置，算波长用
        try:
            cfg = mat['config'][0, 0]
            fs = float(cfg['sample_rate'].item())
            center_freq = float(cfg['center_freq'].item())
        except:
            fs = 10e4  # 默认 100k
            center_freq = 2.485e9  # 默认 2.485G
            print("⚠️ Warning: Using default config (fs=100k, f0=2.485G)")

        # 计算波长
        lambda_val = 3e8 / center_freq
        print(f"✅ Data loaded. Freq: {center_freq / 1e9:.3f} GHz, Lambda: {lambda_val * 100:.2f} cm")

    except FileNotFoundError:
        print(f"❌ Error: File '{DATA_FILE}' not found.")
        exit()

    # --- 3. 核心处理：去斜 (Pulse Compression) ---
    # 公式: y = TMA * conj(Ref)
    y_pc = tma * np.conj(ref)

    # --- 4. 频谱提取 ---
    N = len(y_pc)
    # 加窗可以减少旁瓣泄漏，让峰值读数更准
    window = np.hamming(N)

    # 做 FFT
    fft_res = np.fft.fftshift(np.fft.fft(y_pc * window))
    freqs = np.fft.fftshift(np.fft.fftfreq(N, d=1 / fs))


    # --- 5. 核心算法：幅值提取 & 角度解算 ---

    # 辅助函数：找指定频率附近的峰值幅度
    def get_peak_amp(target_f, search_bw=500):
        # search_bw: 搜索带宽，防止频率没对准
        idx = np.argmin(np.abs(freqs - target_f))
        # 在目标附近 +/- 几个点内找最大值
        start = max(0, idx - 5)
        end = min(N, idx + 6)
        return np.max(np.abs(fft_res[start:end]))


    # A. 提取载波幅度 (0 Hz)
    amp_carrier = get_peak_amp(0)

    # B. 提取一次谐波幅度 (10 kHz)
    amp_harmonic = get_peak_amp(SWITCHING_FREQ)

    # C. 计算比值 Ratio
    if amp_carrier < 1e-6:
        ratio = 0.0
        print("⚠️ Warning: Carrier signal too weak!")
    else:
        ratio = amp_harmonic / amp_carrier

    # D. 反演角度 (幅值比公式)
    # Ratio = (2/pi) * tan(Phi/2)
    # Phi/2 = arctan(Ratio * pi / 2)
    val_tan = ratio * np.pi / 2
    phi_half = np.arctan(val_tan)

    # sin(theta) = (Phi/2 * 2 * lambda) / (2 * pi * d) ... 化简后:
    # sin(theta) = (phi_half * lambda) / (pi * d)
    sin_theta = (phi_half * lambda_val) / (np.pi * ANTENNA_DISTANCE)

    # 越界保护
    clipped = False
    if sin_theta > 1.0:
        sin_theta = 1.0
        clipped = True
    elif sin_theta < -1.0:
        sin_theta = -1.0
        clipped = True

    angle_deg = np.degrees(np.arcsin(sin_theta))

    # --- 6. 打印结果报告 ---
    print("\n" + "=" * 45)
    print(f"📊 MEASUREMENT REPORT")
    print("=" * 45)
    print(f"📡 Carrier Amp (0 Hz)   : {amp_carrier:.2f}")
    print(f"🌊 Harmonic Amp (10 kHz): {amp_harmonic:.2f}")
    print(f"📈 Amplitude Ratio      : {ratio:.4f}")
    print("-" * 45)
    print(f"📐 Estimated Angle      : {angle_deg:.2f}°")
    if clipped:
        print("⚠️ Note: Result clamped to ±90° (sin_theta out of range)")
    print("=" * 45 + "\n")

    # --- 7. 绘图验证 (只画去斜后的结果) ---
    print("▶️  Plotting spectrum...")

    mag_db = 20 * np.log10(np.abs(fft_res) + 1e-12)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=freqs / 1e3, y=mag_db, mode='lines', name='De-chirped Spectrum', line=dict(color='green')))

    # 标记关键点
    fig.add_trace(go.Scatter(
        x=[0, SWITCHING_FREQ / 1e3],
        y=[20 * np.log10(amp_carrier), 20 * np.log10(amp_harmonic)],
        mode='markers+text',
        marker=dict(color='red', size=10),
        text=['Carrier', 'Harmonic'],
        textposition='top center',
        name='Peaks'
    ))

    fig.update_layout(
        title=f"De-chirped Spectrum & Angle Estimation (Result: {angle_deg:.1f}°)",
        xaxis_title="Frequency Offset (kHz)",
        yaxis_title="Magnitude (dB)",
        template="plotly_white",
        xaxis_range=[-30, 30]  # 只看中心区域
    )

    fig.show()