# ホタルがやってきたぞっ｜流萤来了哦 V5

以 GYARI《アカリがやってきたぞっ》为参考的流萤主题手书 PV 工程。最新版本为 V5，全长301.0985秒，1920×1080，9021帧，原音轨和全部画面时间戳保持一致。

## 最新修改

4:50后采用流萤24张、星18张完整全身绘画差分，去除上下身局部遮罩拼接。星从看垃圾桶转头注意流萤，流萤逐渐察觉、脸红、抬手遮嘴。开场与返场标题改为「ホタルがやってきたぞっ」，按原作倾斜大字、分行及双层描边设计。

## 下载完整工程与成片

完整素材、原片、时序文件及完整工程 ZIP 位于本仓库 Releases 的 `v5` 版本，成片和23秒修改预览也在该处。仓库正文保留可浏览的代码与说明；只克隆仓库尚不包含大体积素材。请先下载完整工程ZIP并解压，进入 `firefly_arrived_v5/` 后执行下面命令。

## 复现

需要 Python 3、ffmpeg 和 ffprobe。

```bash
python -m pip install -r requirements.txt
python scripts/render_v5.py --render
python scripts/verify_v5.py
```

成片位于 `output/流萤来了哦_V5_全身重绘与日文标题.mp4`。生成修改短预览：`python scripts/review_reel_v5.py`。

## 工程内容

- `assets/generated/`：GPT image源图，包括完整人物图集和日文标题。
- `assets/animation_v5/`：42张完整全身差分与播放时序。
- `assets/sprites/`：此前镜头复用素材。
- `scripts/`：V1–V5渲染、裁切、时间轴和核验脚本。
- `source/original.mp4`：复现所需原片。
- `timeline*.json`：原片时序与各版本演出安排。
- `docs/精修说明_V5.md`、`docs/verification_v5.json`：修改说明和全片核验结果。

## 创作与来源

新增角色图像由内置GPT image绘制；原曲、原作动画及演出框架来自 GYARI《アカリがやってきたぞっ》，流萤与星角色来自《崩坏：星穹铁道》。这是粉丝二创工程；第三方音乐、角色和参考作品的权利归各自权利人。保留有限帧手书质感，人物轮廓有细微绘画差异。
