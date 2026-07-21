# AI行动简报语音播报配置

## 当前方案

每日构建时生成近 7 天中文简报 MP3，输出到：

```text
docs/audio/daily/YYYY-MM-DD-zh.mp3
```

小程序通过 JSON 中的 `audio_url` 播放 Cloudflare Pages 上的静态 MP3。

## 腾讯云 TTS

本地 `.env` 或 GitHub Secrets/Variables 需要配置：

```env
HORIZON_TTS_PROVIDER=tencent
TENCENTCLOUD_SECRET_ID=你的 SecretId
TENCENTCLOUD_SECRET_KEY=你的 SecretKey
HORIZON_TENCENT_TTS_REGION=ap-guangzhou
HORIZON_TENCENT_TTS_VOICE_TYPE=101001
HORIZON_TENCENT_TTS_CODEC=mp3
HORIZON_TTS_KEEP_DAYS=7
```

说明：

- `TENCENTCLOUD_SECRET_ID` 和 `TENCENTCLOUD_SECRET_KEY` 不要提交到 Git。
- `HORIZON_TENCENT_TTS_VOICE_TYPE` 可根据腾讯云控制台音色列表调整。
- `TextToVoice` 单次文本有长度限制，脚本会自动分段合成后拼接 MP3。

## 本地生成

```powershell
$env:HORIZON_TTS_PROVIDER='tencent'
$env:HORIZON_TTS_FORCE='1'
python scripts/build_static_pages.py
```

如果未配置腾讯云密钥，脚本不会中断页面构建，但不会生成新的腾讯云音频。

## GitHub Actions

在 `horizon-news-pages` 对应仓库配置：

Secrets：

```text
TENCENTCLOUD_SECRET_ID
TENCENTCLOUD_SECRET_KEY
```

Variables：

```text
HORIZON_TTS_PROVIDER=tencent
HORIZON_TENCENT_TTS_REGION=ap-guangzhou
HORIZON_TENCENT_TTS_VOICE_TYPE=101001
HORIZON_TENCENT_TTS_CODEC=mp3
```

配置后每日 workflow 会自动生成 MP3，并随 `docs/audio` 一起部署到 Cloudflare Pages。
