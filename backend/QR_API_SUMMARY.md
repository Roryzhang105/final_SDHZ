# 二维码生成API接口说明

## 问题修复
✅ **CORS跨域问题已解决**: 支持常见开发端口 (3000, 8000, 8080, 5000)
✅ **新增快递单号直接输入功能**: 无需手动构建URL

## 可用API接口

### 1. 快递单号直接生成 (推荐)
```
POST /api/v1/qr-generation/generate-from-tracking-number
Content-Type: application/x-www-form-urlencoded

tracking_number=1151238971060
```

**功能说明:**
- 输入: 快递单号 `1151238971060`
- 系统自动构建URL: `https://mini.ems.com.cn/youzheng/mini/1151238971060`
- 二维码内容: `https://mini.ems.com.cn/youzheng/mini/1151238971060`
- 条形码内容: `1151238971060`

### 2. URL输入生成 (兼容旧版)
```
POST /api/v1/qr-generation/generate-from-url
Content-Type: application/x-www-form-urlencoded

url=https://mini.ems.com.cn/youzheng/mini/1151238971060
```

**功能说明:**
- 输入: 完整URL
- 二维码内容: URL本身
- 条形码内容: 从URL提取的数字部分

### 3. 测试生成功能
```
POST /api/v1/qr-generation/test-generation
Content-Type: application/x-www-form-urlencoded

test_tracking_number=1151238971060 (可选，默认为1151238971060)
```

### 4. 基于识别结果生成
```
POST /api/v1/qr-generation/generate-from-recognition
Content-Type: application/x-www-form-urlencoded

qr_contents=["https://mini.ems.com.cn/youzheng/mini/1151238971060"]
```

### 5. 一站式识别并生成
```
POST /api/v1/qr-generation/recognize-and-generate
Content-Type: multipart/form-data

file=<图片文件>
```

## 返回结果格式
```json
{
  "success": true,
  "message": "基于快递单号 1151238971060 生成标签成功",
  "data": {
    "url": "https://mini.ems.com.cn/youzheng/mini/1151238971060",
    "tracking_number": "1151238971060",
    "final_label_path": "/path/to/label.png",
    "qr_code_path": "/path/to/qr.png",
    "barcode_path": "/path/to/barcode.png",
    "file_size": 12345,
    "processing_time": 0.123,
    "db_updated": true,
    "input_tracking_number": "1151238971060",
    "generated_url": "https://mini.ems.com.cn/youzheng/mini/1151238971060"
  }
}
```

## 测试快递单号
- `1151238971060` (用户提供的测试单号)
- `1151242359760` (用户提供的测试单号)

## 注意事项
1. 所有生成的文件都会自动保存到数据库中
2. 如果送达回证记录不存在，系统会自动创建
3. 生成的标签包含二维码和条形码的合成图片
4. 支持下载生成的文件