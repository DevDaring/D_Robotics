

Below are the exact, reproducible steps your friend can follow on an **RDK X5 (Ubuntu 22.04 / ARM64)** to get PaddleOCR working the same way (CPU inference + output image), including all the fixes you hit (OpenSSL 1.1, NumPy/OpenCV pinning, Hobot `LD_LIBRARY_PATH`, and font).[^1][^2][^3]

## System prerequisites

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip wget ca-certificates fontconfig
```


### Install OpenSSL 1.1 (needed by many Paddle ARM wheels)

Ubuntu 22.04 often lacks `libssl.so.1.1`, so install it from the Ubuntu ports pool.[^3][^4]

```bash
cd /tmp
wget -O libssl1.1_arm64.deb \
  http://ports.ubuntu.com/ubuntu-ports/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_arm64.deb
sudo dpkg -i ./libssl1.1_arm64.deb || true
sudo apt -f install -y
sudo ldconfig
```


## Create virtualenv

```bash
python3 -m venv ~/venv_ocr
source ~/venv_ocr/bin/activate
pip install -U pip setuptools wheel
```


## Install PaddlePaddle (ARM64 wheel)

Install the same ARM64 Paddle wheel you used (XPU build runs on CPU if XPU isn’t configured).[^4]

```bash
pip install -U \
  https://paddle-whl.bj.bcebos.com/paddlex/xpu/paddlepaddle_xpu-2.6.1-cp310-cp310-linux_aarch64.whl
```

Verify import works (run with clean env later if Hobot libs interfere):

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 -c "import paddle; print(paddle.__version__)"
```


## Install PaddleOCR 2.7.0.3 + correct NumPy/OpenCV pins

PaddleOCR 2.7.0.3 expects OpenCV `<=4.6.0.66`, and mixing newer OpenCV wheels can drag in NumPy 2.x and break `cv2`.[^2][^1]

```bash
# Clean anything conflicting
pip uninstall -y numpy opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless paddleocr paddlex

# Pin NumPy < 2 to avoid _ARRAY_API / multiarray import errors
pip install "numpy==1.26.4"

# Install exact OpenCV versions PaddleOCR 2.7.x expects, without pulling deps that re-upgrade NumPy
pip install --no-deps "opencv-python==4.6.0.66" "opencv-contrib-python==4.6.0.66"

# Install PaddleOCR (keep deps stable)
pip install --no-deps "paddleocr==2.7.0.3"
```

Quick sanity:

```bash
python3 -c "import numpy as np, cv2; print('numpy', np.__version__, 'cv2', cv2.__version__)"
```


## Fix draw_ocr font (for output image)

If you want an annotated output image using `draw_ocr`, you must point to a valid `.ttf`; otherwise Pillow throws `OSError: cannot open resource`.[^2]

### Option A: download simfang.ttf (recommended)

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
mkdir -p doc/fonts
wget -O doc/fonts/simfang.ttf \
  "https://huggingface.co/spaces/PaddlePaddle/PaddleOCR/resolve/main/simfang.ttf?download=true"
```


### Option B: use system font

```bash
sudo apt install -y fonts-dejavu-core
```


## Run command (the key: clean LD_LIBRARY_PATH)

On RDK images, `LD_LIBRARY_PATH` often contains `/usr/hobot/lib`, which can break `import paddle`. So always run with a clean env.[^3]

From your PaddleOCR demo folder:

```bash
cd ~/rdk_model_zoo/demos/OCR/PaddleOCR
source ~/venv_ocr/bin/activate

# Pick one font path that exists
export PADDLE_PDX_LOCAL_FONT_FILE_PATH=./doc/fonts/simfang.ttf
# OR:
# export PADDLE_PDX_LOCAL_FONT_FILE_PATH=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

env -u LD_LIBRARY_PATH -u LD_PRELOAD DISABLE_MODEL_SOURCE_CHECK=True \
  python3 cpu_paddle_ocr.py \
  --image_path data/paddleocr_test.jpg \
  --output_folder output/predict.jpg \
  --font_path "$PADDLE_PDX_LOCAL_FONT_FILE_PATH"
```

If your friend follows this exactly, they should get the printed OCR lines and an output image at `output/predict.jpg`.[^5]

If you want, paste your final working `cpu_paddle_ocr.py` and I’ll align the steps to that exact file (paths/flags).
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://github.com/PaddlePaddle/PaddleOCR/issues/12034

[^2]: https://github.com/PaddlePaddle/PaddleOCR/discussions/8839

[^3]: https://gist.github.com/joulgs/c8a85bb462f48ffc2044dd878ecaa786

[^4]: https://gist.github.com/DPS0340/5a59a83f0515a658bf16d18b958baff5

[^5]: https://pypi.org/project/paddleocr/2.7.0.3/

[^6]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/49f11d0c-364e-47ab-9ad0-b02fd6e91cca/image.jpg

[^7]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/c624b86b-1d59-411a-8699-7f21ba8cb293/image.jpg

[^8]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/6442ef48-1228-4075-90ae-bd3dcd6c218c/image.jpg

[^9]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/62c88486-85ef-4014-8504-9a482c67f665/image.jpg

[^10]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/a15e6248-d3f7-40c0-a877-4e1de411d83b/image.jpg

[^11]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/ad5b93f1-3b80-4513-88d3-edb55923d00f/image.jpg

[^12]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54422958/d0eee433-74d0-4170-ad2a-dd2cb13548f5/paddle_ocr.py

[^13]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/54422958/77cdbf8a-2899-44cf-b483-32be76d245c7/image.jpg

[^14]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54422958/26776e32-a79d-4504-8a36-6e75b787790e/cpu_paddle_ocr.py

[^15]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54422958/da70d702-846e-41c9-b62c-097996b3febc/cpu_paddle_ocr.py

[^16]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/54422958/fe8a7fbc-591f-4943-9a2a-93d5e8cd0996/cpu_paddle_ocr.py

[^17]: https://github.com/PaddlePaddle/PaddleOCR/issues/11079

[^18]: https://www.kaggle.com/code/shrutimukhtyar/testing-ocr-libraries

[^19]: https://github.com/PaddlePaddle/PaddleOCR/issues/10265

[^20]: https://github.com/PaddlePaddle/PaddleOCR/issues/17359

[^21]: https://pypi.org/project/paddleocr/

[^22]: https://github.com/PaddlePaddle/PaddleOCR/issues/8188

[^23]: https://wenku.csdn.net/answer/6y18j3gfaf

[^24]: https://huggingface.co/spaces/phlippseitz/Image-Text-Extraction-PaddleOCR

[^25]: https://stackoverflow.com/questions/47694421/pil-issue-oserror-cannot-open-resource

[^26]: https://github.com/PaddlePaddle/PaddleOCR/issues/17349

[^27]: https://gist.github.com/ststeiger/746520d73713455662f9174cfaf4c635

[^28]: https://ipcamtalk.com/threads/alpr-ocr-not-working.84061/

[^29]: https://github.com/python-pillow/Pillow/issues/3730

[^30]: https://github.com/PaddlePaddle/PaddleOCR/discussions/12774

[^31]: https://stackoverflow.com/questions/73251468/e-package-libssl1-1-has-no-installation-candidate

